#!/usr/bin/env python3
"""S459 - Supplementary Figure 7: the original RLM package (rlms 0.1.3, released by the method's
authors, not Mentori's RLM) at ten turn caps, how each answer ended and its turns.

D217 (Valerio, 3 November, experiments/README.md "D217"): panel c (tokens per answer by cap) is dropped; its tokens are
measured in Supplementary Figure 17 b at the caps the paper compares. The time panel, d until then, became c.
D224 Q5 (Valerio, 3 November, experiments/README.md "D224"): the time panel (c since D217) is dropped as well. The two
panels left stand in one row (a, b), each with its own turn-cap rows at the same height, sharing the page's width.

WHERE IT GOES (D123, Valerio, 23 October, experiments/README.md "D123"): Supplementary Figure 8 (main Figure 3 at D123)
shows concept recall against the turn cap for both RLMs, the local models, corpus scale and the share of answers
reaching the cap; this plate (the package's endings and turns per cap; time too until D224 Q5) moves to the Supplementary. Its
number, 8, comes from the manuscript's order of first citation (D257; 10 under FF3 a's one list). Named by FIGURE_LOCK [files] supplementary_name (D92 Q194) and checked with
S448 --supplementary, as S461 does for Supplementary Figure 2.

The history below (17 October) is the plate's first version, drawn as Figure 3.

WHY. Valerio, 17 October (night): "Can we already generate drafts of other figures with the current data? For
example Figure 1? And for other figures too?" D84: exploratory phase, the results are drawn as they are and no
analysis rule is written here. Figure 3 as submitted (manuscript/sections/32_figure_3.md) has six panels, all of them
judged or fitted quantities (concept recall saturation, multi-model saturation, fit quality, strategy crossover by
corpus size, noise robustness, out-of-domain refusal). None could be drawn on 17 October: G5 (Mentori's RLM depth sweep)
and G4 (corpus scaling) had written no answer, and no answer was judged (S3) or scored for concept recall (L2). S459
reads no G4 or G5 record (their draw-1 answers written since are unjudged and not drawn here). The only
Figure 3 records are G6's: the RLM authors' package (rlms 0.1.3, D31, D73) at turn caps 1, 2, 3, 5, 7, 10, 15, 20,
30 and 50 on the depth sweep's 86 questions (D75 Q50), three draws. They need no judge for what they record about
each answer: how it ended and how many turns it used (its tokens and time are recorded but no longer drawn, D217,
D224 Q5). That is what this plate draws.
WRITTEN DESIGN. D31 answered Q19 (experiments/LIST.md, "RLM package (Q19)": both RLMs, the package a reference arm);
D78 Q116 gives "the authors' depth caps" three draws under Figure 3 (LIST.md, "Not settled here"; README D78), and
D75 Q50 the depth sweep's 86 questions "for both RLMs". LIST.md's Figure 3 section now states "Q19 is settled"
(it read "Waiting on Q19" until 96d75c0, 18 October). Open for Valerio: whether caps 5, 10 and 20, taken from Figure 2's runs (run_rlm_ref.py FIGURE2_CAPS), and
these two unjudged panels make the plate. The line numbers are found at run time and printed in legend_draft.md.

ONE COMMAND (D155), from the repository root, rebuilds the committed plate from frozen inputs only:

    uv run --frozen python scripts/S459_fig3_rlm_ref_caps.py [--out <dir>]

On a fresh clone, make the authors' RLM venv first, once (the legend cites its installed rlms package's METADATA,
and experiments/rlm_ref/.venv is gitignored; S494 does this itself):

    (cd experiments/rlm_ref && uv sync --frozen)

It writes every file of findings/figures_provisional/supp_fig7_package_caps/ (or of --out) byte-equal to the
committed one (26 October: PDF, SVG, PNG, data workbook, caption, legend, numbers and provenance; run twice, the same
bytes). Before anything is read further, every frozen input must have the sha256 the committed provenance records. It
re-executes itself under PYTHONHASHSEED=0 (fig_repro.pin_hash_seed: a PDF's font subsets depend on it).

READS (the trust boundary, README.md:13-27: run records are trusted, nothing else gives a number):
  G6's records as they stood on 23 October, before the D89 rerun of 24 October rewrote them in the gitignored
  findings/runs/ (the stamp says "before the D89 and D90 reruns"), from their frozen copy (D155):
  findings/recompute/L2_inputs/g6/b4_rlm_ref__cap<c>__depthsweep86/answers.jsonl   caps 1, 2, 3, 7, 15, 30, 50 (86 x 3)
  findings/recompute/L2_inputs/g6/b4_rlm_ref__cap<c>__all135/answers.jsonl         caps 5, 10, 20 (135 x 3; the 86 kept)
  findings/recompute/g6_d135_inputs/<run>/answers.jsonl, SOURCE_MTIMES.json   D160 (7) Q23: once frozen
                                                                  (frozen_inputs/freeze_g6_d135.py), G6's records after
                                                                  the D135 reruns, which every panel and sheet then
                                                                  draws; the gates (1) to (4) below keep reading the
                                                                  records before them (provenance "readings")
  findings/recompute/frozen_inputs/g6_before_d89_mtimes.json      their source mtimes (the stamp's "records of", printed
                                                                  in Europe/Amsterdam), each beside its sha256
  experiments/rlm_ref/run_rlm_ref.py                              DEPTH_SWEEP86, FIGURE2_CAPS, DEPTH_SWEEP_CAPS
                                                                  (read with ast, never imported or run)
  findings/recompute/Q145/S455_d92_affected.json                  the answers D89 and D90 list, each with its D92 action
                                                                  (rerun, rebuild, stays_failed; D115 L1c): the laptop's
                                                                  scan, the one holding G6's runs (the _studio_ scans
                                                                  hold G1 and Figure 6)
  experiments/plan.csv                                            row G6: the counts reproduced first
  experiments/LIST.md, experiments/README.md                      the lines of the written design (found, not assumed)
  (these three: their values as they stood at DESIGN_AT, e44e636a, the commit the plate was drawn at, read from
  fig_design's design_facts.json since D2, never the documents or git; today's text changes daily, D155)
(planned_total() reads G4_runs/README.md, G5_runs/README.md and D98_subset/d98_subset.json for main Figure 3's "of N";
S475 calls it, this plate does not.)
  experiments/rlm_ref/.venv/.../rlms-0.1.3.dist-info/METADATA     the package's author and paper URL (a gitignored
                                                                  venv: run uv sync in experiments/rlm_ref first)
  manuscript/sections/29_references.md                            the reference that cites that URL (its number only)
  git history of experiments/LOCK.toml and experiments/rlm_ref/adapter.py (read only): the versions the records name
  experiments/FIGURE_LOCK.toml                                    every size, font, colour and width (D84, D87)

REPRODUCE FIRST (README.md:75-79). Before anything is written: (1) plan.csv row G6 states the failed answers per draw
of each depth cap ("cap 1 16/20/26, ..."); every one must equal the count in the records. (2) Its note states that
after the D75 Q48 rerun the three all135 files hold "1,187 answer_ready, 10 turn_cap, 18 failed"; the records must
give the same. (3) S455 must have read these very files (the sha256 of every answers.jsonl equal to the one S455
records), so its rerun lists name these answers, and its list must be D92's. (4) check_actions(): S455's G6 action
totals are rebuilt from its rows, each row found in a run S459 reads, a rebuilt answer a failed closing call, an answer
left failed a failed turn, and per cap the three actions add to the listed answers and each equals S455's rows of
that cap's run on the figure's questions. Any difference stops the run
(exit 2), nothing written. scripts/S459_fig3_rlm_ref_caps_test.py runs (4) on the records and on mutants.

WRITES findings/figures_provisional/supp_fig7_package_caps/ (files of an earlier data state, "Supplementary Figure
10*", are deleted first; findings/figures_provisional/fig3/, where this plate was drawn as Figure 3 until D123, is not
written):
  Supplementary Figure 7.{pdf,svg,png}   one page, [page] width_double_mm wide, under height_max_mm; every
        text at [type] font_min_pt in the first of [type] font_families, embedded TrueType; panel letters
        panel_letter_pt bold lowercase; no panel titles; [colour] categorical only, grey and black; no line under
        [lines] line_min_pt; a and b side by side in one row (D217, D224 Q5); the PNG is the PDF rasterised by MuPDF at 600 dpi (S448 R7). Nothing on the plate but
        the figure: the data state is in the stamp (numbers, provenance and caption).
  Supplementary Figure 7 data.xlsx (the data workbook, sheets "Supplementary Fig. 7a" and "10b"),
        its caption .md, supplementary_figure7_numbers.json (the same sheets, and "printed": every number printed on
        the plate, by SVG group id, with its sheet, row and format), supplementary_figure7_provenance.json (inputs and
        outputs with sha256, the lock's sha256, the reproduction), legend_draft.md.
  n = the G6 answers drawn (10 caps x 86 x 3 = 2,580). N = the answers this plate's written plan holds: the authors'
  depth caps (D78 Q116), the 86 questions at the design's caps, three draws each (D98: Figure 2's experiments keep
  their three full draws), from run_rlm_ref.py's constants. Before D123 N was main Figure 3's whole plan (G4 and G5
  under D98 added, planned_total()); those answers are not on this plate.

THE PANELS (rows: the ten caps, 1 at the top; every answer of the 86 questions x 3 draws at each cap):
LINE CITATIONS of the adapter are to the version that wrote draws 2 and 3 of the depth caps, commit fbbcfb3 (adapter
sha256 413f46c9; `git show fbbcfb3:experiments/rlm_ref/adapter.py`). The same statements stand at 3d98613 (f8676d5f,
caps 5, 10, 20) and a3f0cf1 (b6c8a3f4, draw 1 of the depth caps and the D75 Q48 reruns); the working-tree file is
never cited. supplementary_figure7_provenance.json maps each record's adapter_sha256 to its commit.
  a  how each answer ended, as a share of the 258 answers at the cap (the record's stop_reason, fbbcfb3:1044-1052):
     answer_ready (the package returned an answer of its own within the cap, on any turn up to the cap's last, with no
     closing call: stop = "answer_ready" whenever the closing call was not forced, fbbcfb3:1048; at caps 1 and 2 most
     such answers come on the cap's last turn), turn_cap (the cap was reached and the package's
     closing call answered; split by the record's forced_final_has_code into a reply with no ```repl block and one
     holding one, fbbcfb3:1084-1086), forced_final_failed (that closing call failed), root_call_failed (a model
     call of a turn failed). An answer of status ok whose text is empty or whitespace only is drawn as its own slice,
     "answer with no text", whatever its stop_reason (the Source Data gives both). D161 (1) N1: an answer the
     package's own code failed on (stop_reason "error" with the TypeError package_error() names; 2 after the D135
     reruns) is its own slice, "the package's own code failed", bluish green, keyed only when drawn. No n on
     the plate (Valerio, 11 Nov: 258 answers per cap, 86 questions x 3 draws, in the legend). D161 (2) N2: with the D135 set frozen, sheet a gives every
     column but cap and answers_n twice, <name>_before_reruns (the gated reading the legend's Reruns and Failures
     paragraphs quote) and <name>_after_reruns (drawn).
  b  root turns used per answered answer (status ok, fbbcfb3:1081, the answers with no text included; turns_used = the
     root calls, fbbcfb3:1083, so the closing call is not counted): box from the first to the third quartile (numpy
     linear interpolation), median line, whiskers to the smallest and largest value, no point left out as an outlier;
     a black triangle above the box marks the cap, so a box that sits on the cap stays visible. Log axis. The answered
     answers per cap ("n =") are in the legend, not on the plate (Valerio, 11 Nov).
  (D224 Q5: the time panel, the answer's wall_s, is no longer drawn and has no sheet.)
No hypothesis test, no interval. No model call; no Ollama port contacted; no ssh.
"""
from __future__ import annotations

import ast
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import io
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro as FR  # noqa: E402  (D155: frozen inputs, deterministic files)
import pinned_history as PH  # noqa: E402  (O3: history reads, pinned in the tree)
import house_style as hs  # noqa: E402  one drawing style for every plate
from S457_fig2_panels import finish_plate  # noqa: E402  the last step of a plate, shared (S457, S463, S472)
# D155: the records this plate draws are G6's as they stood on 23 October, before the D89 rerun of 24 October rewrote
# them in the gitignored findings/runs/ (the plate's stamp: "before the D89 and D90 reruns"). Their frozen copy is
# findings/recompute/L2_inputs/g6/<run>/answers.jsonl (committed; each file checked against frozen_inputs/SHA256SUMS),
# found on first use (runs_dir()); RUNS_AS is the folder they were read at, the name S455 and the provenance give them.
RUNS = None
RUNS_AS = "findings/runs"
G6_MTIMES_JSON = ROOT / "findings" / "recompute" / "frozen_inputs" / "g6_before_d89_mtimes.json"
# D160 (7) Q23 (Valerio, 27 October, "Yes, as D156"): the plate draws G6's records after the D135 reruns (24 and 25
# October: D92's rerun and rebuild actions; frozen by frozen_inputs/freeze_g6_d135.py in findings/recompute/
# g6_d135_inputs/, with their mtimes in SOURCE_MTIMES.json), and every gate below (plan.csv's counts, S455's inputs,
# check_actions, the D92 paragraphs of the legend's header) keeps reading the records before them (L2_inputs/g6/).
# Until that set is frozen the plate draws the records before the reruns, as before D160.
G6_D135 = ROOT / "findings" / "recompute" / "g6_d135_inputs"
STAMP_TZ = "Europe/Amsterdam"                    # the zone the stamp prints its time in, on every machine (D155)
# The design documents whose lines the legend cites and whose plan.csv row G6 is reproduced first are read as they
# stood at the commit the committed plate was drawn at (its provenance's repo_head, 23 October; LIST.md 7766a32c,
# README.md c3ff0755, plan.csv efa050f9 there, the sha256 it recorded): those files change daily, and a citation or a
# stated count read from today's text would make the plate differ from build to build (D155).
DESIGN_AT = "e44e636a"
SUPP_N = 7                                       # D302 (8 before), the manuscript's order of first citation (docstring)
OUT = ROOT / "findings" / "figures_provisional" / f"supp_fig{SUPP_N}_package_caps"
RUN_RLM_REF = ROOT / "experiments" / "rlm_ref" / "run_rlm_ref.py"
S455 = ROOT / "findings" / "recompute" / "Q145" / "S455_d92_affected.json"   # D115 L1c: the D92 list, with actions
PLAN = ROOT / "experiments" / "plan.csv"
G4_README = ROOT / "findings" / "recompute" / "G4_runs" / "README.md"
G5_README = ROOT / "findings" / "recompute" / "G5_runs" / "README.md"
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"   # S464, LIST.md's D98 rule
LOCK = ROOT / "experiments" / "LOCK.toml"
ADAPTER = ROOT / "experiments" / "rlm_ref" / "adapter.py"
LIST_MD = ROOT / "experiments" / "LIST.md"
README_EXP = ROOT / "experiments" / "README.md"
REFERENCES = ROOT / "manuscript" / "sections" / "29_references.md"   # named in the legend; read by S616, not here
# D2 (Valerio, 8 Nov): figures are built from data only. plan.csv's row G6 and the LIST.md and README.md lines at
# DESIGN_AT, and the reference number the list gives the rlms paper, are read from design_facts.json (S616 extract,
# each source with its commit and blob id; S616 check holds them to the files): never plan.csv, LIST.md, README.md or
# the reference list themselves, and never git show.
import fig_design  # noqa: E402
# D303: the revised paper's reference list (manuscript tab, rev 3688, accepted by Valerio 7 Nov) numbers the rlms paper
# (Zhang, Kraska & Khattab, arXiv 2512.24601) 27; the legend cites that number. The list is not yet in the repository
# (it enters with the .docx move), so package_citation() checks the URL against the submitted list above and the
# legend takes this number; once the revised list is a repository file, read the number from it instead.
REVISED_REFERENCE = {"url": "https://arxiv.org/abs/2512.24601", "number": 27, "source": "manuscript tab rev 3688"}
PKG_METADATA = ROOT / "experiments" / "rlm_ref" / ".venv" / "lib"     # .../site-packages/rlms-<v>.dist-info/METADATA
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
MM_PER_PT = 25.4 / 72

FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
SI_LABEL = FLOCK["files"]["supplementary_name"].format(n=SUPP_N)   # "Supplementary Figure 7" (D92 Q194)
SIDE = f"supplementary_figure{SUPP_N}"           # the numbers and provenance files S448 --supplementary reads
SHEET = f"Supplementary Fig. {SUPP_N}"           # the data workbook's sheets, "<SHEET>a" and "<SHEET>b", as S461's
PT_TEXT = float(FLOCK["type"]["font_min_pt"])
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]
LETTER_CASE = str.lower if FLOCK["type"]["panel_letter_case"] == "lowercase" else str.upper
FONT = FLOCK["type"]["font_families"][0]
CONTRAST_MIN = float(FLOCK["type"]["contrast_min_ratio"])
LINE_MIN_PT = float(FLOCK["lines"]["line_min_pt"])
FIG_W_MM = float(FLOCK["page"]["width_double_mm"])
FIG_H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
_CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
assert len(_CAT) == 8, f"[colour] categorical holds {len(_CAT)} colours; S459 names Okabe and Ito's eight"
OKABE = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"],
                 _CAT))
# panel a: how an answer ended (outcome_of: the record's stop_reason, with turn_cap split by the record's
# forced_final_has_code), in the order the bar stacks them, with the key's words and colour
OUTCOMES = [("answer_ready", "answer within the cap", OKABE["blue"]),
            ("turn_cap_answer", "answer from the closing call", OKABE["sky blue"]),
            ("turn_cap_code", "closing call returned code", OKABE["reddish purple"]),
            ("no_text", "answer with no text", OKABE["yellow"]),
            ("forced_final_failed", "closing call failed", OKABE["orange"]),
            ("root_call_failed", "a turn's model call failed", OKABE["vermillion"]),
            ("package_error", "the package's own code failed", OKABE["black"])]   # D161 (1) N1; black: bluish green means better
ANSWERED = ("answer_ready", "turn_cap_answer", "turn_cap_code", "no_text")   # status ok (fbbcfb3:1081)
# D161 (1) N1: an answer the package's own code failed on. The adapter that wrote the D135 reruns (1cc59090, adapter
# sha256 7f4fa711) stores stop_reason "error" and the exception's "<type>: <message>" (1cc59090:1171) for an exception
# that leaves the package's completion() after the first root turn and is neither a failed model call (RootCallError,
# 1cc59090:1156) nor one of the adapter's own errors (re-raised, nothing stored, 1cc59090:1162-1170). The one such
# error in G6's records: a root reply Gemini blocked goes back to the package as None (1cc59090:780-784, D92 Q185),
# and the package's search for code blocks in it, re.finditer over None (rlm/utils/parsing.py:18, called at
# rlm/core/rlm.py:658, rlms 0.1.3), raises this TypeError. Matched exactly: any other "error" refuses (compute()).
PACKAGE_TYPEERROR = "TypeError: expected string or bytes-like object, got 'NoneType'"


def no_text(r):
    """An answer of status ok whose text is empty or whitespace only."""
    return r["status"] == "ok" and not (r.get("answer") or "").strip()


def package_error(r):
    """A failed answer whose record states the package's TypeError on a root reply of None (PACKAGE_TYPEERROR), at a
    root turn (no closing call made)."""
    return (r["status"], r["stop_reason"], r.get("error"), r.get("forced_final")) == \
        ("failed", "error", PACKAGE_TYPEERROR, False)


def outcome_of(r):
    """The record's stop_reason, except: an answer of status ok with no text is no_text, whatever its stop_reason; a
    turn_cap answer whose text holds a ```repl block (forced_final_has_code, the package's own parser,
    fbbcfb3:1084-1086) is turn_cap_code, the rest turn_cap_answer; an answer the package's own code failed on
    (package_error()) is package_error."""
    if no_text(r):
        return "no_text"
    if package_error(r):
        return "package_error"
    if r["stop_reason"] == "turn_cap":
        return "turn_cap_code" if r.get("forced_final_has_code") else "turn_cap_answer"
    return r["stop_reason"]
BOX_FILL = OKABE["sky blue"]
LW = max(0.5, LINE_MIN_PT)                        # axes, ticks, box edges, whiskers
LW_MED = max(1.0, LINE_MIN_PT)                    # the median line


# ---------------------------------------------------------------------------------------------------------------
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def as_read(p: Path) -> str:
    """The name a G6 answers file had where it was read (RUNS_AS/<run>/answers.jsonl), as S455 records it."""
    return f"{RUNS_AS}/{p.parent.name}/{p.name}"


def half_up(x, nd=0):
    """As S447 and S448 print a number: to 1e-9 first, then half away from zero."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f"{abs(q) if q == 0 else q:.{nd}f}"


def fmt_int(n: int) -> str:
    return f"{n:,}"


def wcag_ratio(c1, c2):
    def lum(c):
        c = tuple(int(c.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


# ---------------------------------------------------------------------------------------------------------------
# The design's constants, read from run_rlm_ref.py's source (ast; the module is never imported or run)
# ---------------------------------------------------------------------------------------------------------------
def design_constants():
    tree = ast.parse(RUN_RLM_REF.read_text())
    want = {"DEPTH_SWEEP86", "FIGURE2_CAPS", "DEPTH_SWEEP_CAPS", "DEPTH_SWEEP_SIZE", "EXPERIMENT"}
    got = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in want:
            got[node.targets[0].id] = eval(compile(ast.Expression(node.value), str(RUN_RLM_REF), "eval"),
                                           {"__builtins__": {"range": range}}, {})
    missing = want - set(got)
    if missing:
        raise SystemExit(f"{rel(RUN_RLM_REF)}: {sorted(missing)} not found as plain assignments")
    ids = tuple(got["DEPTH_SWEEP86"])
    if len(ids) != got["DEPTH_SWEEP_SIZE"] or len(set(ids)) != len(ids):
        raise SystemExit(f"DEPTH_SWEEP86 holds {len(ids)} ids ({len(set(ids))} distinct), not "
                         f"{got['DEPTH_SWEEP_SIZE']}")
    caps = tuple(sorted(set(got["FIGURE2_CAPS"]) | set(got["DEPTH_SWEEP_CAPS"])))
    return ids, caps, set(got["FIGURE2_CAPS"]), got["EXPERIMENT"]


def runs_dir() -> Path:
    """The frozen G6 answers (findings/recompute/L2_inputs/g6/), each file checked against frozen_inputs/SHA256SUMS."""
    global RUNS
    if RUNS is None:
        RUNS = FR.check_committed(FR.frozen("L2", "g6"))
    return RUNS


def run_dir(experiment, cap, fig2_caps, base: Path | None = None):
    return (base or runs_dir()) / f"{experiment}__cap{cap}__{'all135' if cap in fig2_caps else 'depthsweep86'}"


def drawn_dir() -> Path | None:
    """D160 Q23: G6's frozen records after the D135 reruns, each file checked against frozen_inputs/SHA256SUMS; None
    while they are not frozen."""
    return FR.check_committed(FR.frozen("g6_d135")) if G6_D135.exists() else None


def read_answers(p: Path):
    rows = [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]
    keys = Counter(r["answer_key"] for r in rows)
    dup = [k for k, v in keys.items() if v > 1]
    if dup:
        raise SystemExit(f"{rel(p)}: answer keys stored twice: {dup[:3]}")
    return rows


# ---------------------------------------------------------------------------------------------------------------
# Reproduce first
# ---------------------------------------------------------------------------------------------------------------
def plan_row(rid):
    """plan.csv's row rid as it stood at DESIGN_AT, from design_facts.json (D2)."""
    rows = fig_design.facts()[f"plan_csv_at_{DESIGN_AT}"]
    if rid not in rows:
        raise SystemExit(f"{rel(fig_design.FACTS)}: no plan.csv row {rid} at {DESIGN_AT}")
    return rows[rid]


def reproduce(full, caps, fig2_caps, files):
    """(1) plan.csv G6's failed answers per draw of each depth cap; (2) its all135 stop reasons after D75 Q48;
    (3) S455 read these files, and its list is D92's. Returns what was compared; exits 2 on any difference."""
    g6 = plan_row("G6")
    text = " ".join(g6.values())
    probs, out = [], {"plan_csv_G6": {}, "plan_csv_G6_all135": {}, "S455_inputs": {}}
    m = re.search(r"failed per draw:(.*?)(?:, Gemini-side|\))", text)
    stated = {int(c): tuple(int(x) for x in (a, b, d)) for c, a, b, d in
              re.findall(r"cap (\d+) (\d+)/(\d+)/(\d+)", m.group(1) if m else "")}
    depth_caps = [c for c in caps if c not in fig2_caps]
    if sorted(stated) != depth_caps:
        probs.append(f"plan.csv G6 states failed-per-draw counts for caps {sorted(stated)}, the design's depth caps "
                     f"are {depth_caps}")
    for c in depth_caps:
        got = tuple(sum(1 for r in full[c] if r["draw"] == d and r["status"] == "failed") for d in (1, 2, 3))
        out["plan_csv_G6"][f"cap {c}"] = {"stated": stated.get(c), "records": got}
        if stated.get(c) != got:
            probs.append(f"cap {c}: plan.csv G6 states failed per draw {stated.get(c)}, the records {got}")
    m = re.search(r"files hold ([\d,]+) answer_ready, ([\d,]+) turn_cap, ([\d,]+) failed", text)
    want = tuple(int(x.replace(",", "")) for x in m.groups()) if m else None
    rows135 = [r for c in sorted(fig2_caps) for r in full[c]]
    got = (sum(r["stop_reason"] == "answer_ready" for r in rows135), sum(r["stop_reason"] == "turn_cap" for r in rows135),
           sum(r["status"] == "failed" for r in rows135))
    out["plan_csv_G6_all135"] = {"stated (answer_ready, turn_cap, failed)": want, "records": got}
    if want != got:
        probs.append(f"all135 caps: plan.csv G6 states (answer_ready, turn_cap, failed) {want}, the records {got}")
    s455 = json.loads(S455.read_text())
    seen = {a["path"]: a["sha256"] for i in s455["provenance"]["inputs"] for a in i.get("answers", [])}
    for c in caps:
        p = as_read(files[c])
        out["S455_inputs"][p] = {"S455": (seen.get(p) or "")[:16], "now": sha256_file(files[c])[:16]}
        if seen.get(p) != sha256_file(files[c]):
            probs.append(f"{p}: S455 read sha256 {(seen.get(p) or 'nothing')[:16]}, the file is now "
                         f"{sha256_file(files[c])[:16]}: its rerun lists would not name these answers")
    if s455.get("gate") != "pass":
        probs.append(f"S455's gate is {s455.get('gate')!r}, not 'pass'")
    if "D92" not in s455.get("provenance", {}).get("decision", ""):
        probs.append(f"{rel(S455)} is not D92's list (decision {s455.get('provenance', {}).get('decision')!r})")
    if probs:
        print("REPRODUCTION FAILED, nothing written:\n  " + "\n  ".join(probs), file=sys.stderr)
        sys.exit(2)
    return out, s455


def planned_total(ids, caps):
    """The answers Figure 3's written plan holds under D98 (Valerio, 18 October: every Gemini experiment still to run
    answers every question once, draw 1, and draws 2 and 3 only on the fixed subset; D112 Q11 O1, 21 October: the
    subset's 45 questions only, not a third of G4's 109 size-50 questions). Draw 1 of G4 is its README's dry run per
    draw (checked against the table's own rows, which also give its 6 strategies and 12 indexes); draw 1 of G5 is its
    README's 86 x 10 caps (checked against 86 x 10 x 3 draws); draws 2 and 3 run on the questions of
    findings/recompute/D98_subset/d98_subset.json (S464) that each asks: all 45 on every G4 index (the subset is drawn
    from the 135 questions every index asks, LIST.md "D98 subset and analysis rule"), the subset's questions among
    DEPTH_SWEEP86 for G5. The G6 answers drawn here are added by the caller (Figure 2's experiments keep their three
    full draws, D98)."""
    n_ids = len(ids)
    g4 = G4_README.read_text()
    m = re.search(r"\| all 12 \| ([\d,]+) \| ([\d,]+); ([\d,]+) for draws 1 to 3 \|", g4)
    rows = re.findall(r"^\| ([^|]+?) \| ([\d,]+) \| ([\d,]+) each \|$", g4, re.M)
    if not m or len(rows) != 2:
        raise SystemExit(f"{rel(G4_README)}: the table of indexes and answers is not where S459 reads it")
    num = lambda s: int(s.replace(",", ""))
    per_draw, total = num(m.group(2)), num(m.group(3))
    # a row names its indexes ("exp_v4_s50_n3, s50_n1, s50_n0") or counts them in words ("the nine at ...")
    words = {"three": 3, "nine": 9}
    k = [next((v for w, v in words.items() if re.search(rf"\b{w}\b", nm)), None) or len(nm.split(","))
         for nm, _, _ in rows]
    if sum(k) != 12 or sum(x * num(a) for x, (_, _, a) in zip(k, rows)) != per_draw or 3 * per_draw != total:
        raise SystemExit(f"{rel(G4_README)}: its rows ({k} indexes) do not add to 12 indexes, {per_draw} a draw, "
                         f"{total} in all")
    strategies = {num(a) // num(q) for _, q, a in rows if num(a) % num(q) == 0}
    if len(strategies) != 1 or any(num(a) % num(q) for _, q, a in rows):
        raise SystemExit(f"{rel(G4_README)}: its rows do not give one number of strategies (answers / questions)")
    n_strat = strategies.pop()
    m5 = re.search(r"86 x 10 x 3 draws = \*\*([\d,]+) answers\*\*", G5_README.read_text())
    g5 = num(m5.group(1)) if m5 else None
    if g5 != n_ids * len(caps) * 3:
        raise SystemExit(f"{rel(G5_README)} states {g5} answers; {n_ids} questions x {len(caps)} caps x 3 draws "
                         f"give {n_ids * len(caps) * 3}")
    sub = json.loads(D98_SUBSET.read_text())
    sub_ids = sub.get("ids") or []
    if sub.get("n") != len(sub_ids) or len(set(sub_ids)) != len(sub_ids) or not sub_ids:
        raise SystemExit(f"{rel(D98_SUBSET)}: n {sub.get('n')} and {len(sub_ids)} distinct ids differ")
    g5_sub = sum(1 for q in ids if q in set(sub_ids))
    g4_d98 = per_draw + 2 * len(sub_ids) * n_strat * sum(k)
    g5_d98 = n_ids * len(caps) + 2 * g5_sub * len(caps)
    return {"G4": g4_d98, "G5": g5_d98,
            "how": {"rule": "D98 (draw 1 on every question, draws 2 and 3 on the D98 subset); D112 Q11 O1 (the "
                            "subset's 45 questions only)",
                    "subset": {"file": rel(D98_SUBSET), "questions": len(sub_ids),
                               "among_the_depth_sweep_86": g5_sub},
                    "G4": {"draw_1": per_draw, "draws_2_and_3": 2 * len(sub_ids) * n_strat * sum(k),
                           "indexes": sum(k), "strategies": n_strat, "three_full_draws_before_D98": total},
                    "G5": {"draw_1": n_ids * len(caps), "draws_2_and_3": 2 * g5_sub * len(caps), "caps": len(caps),
                           "three_full_draws_before_D98": g5}}}


# ---------------------------------------------------------------------------------------------------------------
# What the records name: the code and lock versions, the written design's lines, the package and its citation
# ---------------------------------------------------------------------------------------------------------------
def git_versions(path: Path) -> dict:
    """sha256 of every committed version of `path` -> the earliest commit (short) holding it, from the git history
    as pinned in the tree (O3: `git log --format=%H -- path` and each version's bytes, held to its git blob id;
    scripts/S617_pin_history.py, whose verify checks the list against git in Mentori-reanalysis)."""
    out = {}
    try:
        for c in PH.log(rel(path)):                                   # newest first; the last one seen wins
            if not PH.has(c, rel(path)):
                continue                                              # git show failed there (no such file)
            blob = PH.show(c, rel(path))
            out[hashlib.sha256(blob).hexdigest()] = (c[:7], blob)   # 7 characters always (git's --short grows)
    except PH.PinError as e:
        print(f"VERSIONS NOT READ, nothing written: {e}", file=sys.stderr)
        sys.exit(2)
    return out


def subject(c: str) -> str:
    """`git log -1 --format=%s c`, as pinned (O3) for every commit of the pinned logs; exit 2 when it is not."""
    try:
        return PH.subject(c)
    except PH.PinError as e:
        print(f"VERSIONS NOT READ, nothing written: {e}", file=sys.stderr)
        sys.exit(2)


def versions_of_records(allr):
    """Each adapter_sha256 and lock_sha256 the records carry, mapped to its commit; the lock versions compared table
    by table. Exits 2 when a record names a version no commit holds."""
    av, lv = git_versions(ADAPTER), git_versions(LOCK)
    out = {"adapter": {}, "lock": {}, "lock_tables_that_differ": None}
    probs = []
    for field, vers, key in (("adapter_sha256", av, "adapter"), ("lock_sha256", lv, "lock")):
        for sha, k in sorted(Counter(r[field] for r in allr).items()):
            if sha not in vers:
                probs.append(f"{field} {sha[:8]} ({k} records): no commit of {key} holds it")
                continue
            c = vers[sha][0]
            out[key][sha[:8]] = {"commit": c, "records": k,
                                 "commit_subject": subject(c)[:160]}
    if probs:
        print("VERSIONS NOT FOUND, nothing written:\n  " + "\n  ".join(probs), file=sys.stderr)
        sys.exit(2)
    locks = [tomllib.loads(lv[sha][1].decode()) for sha in {r["lock_sha256"] for r in allr}]

    def flat(d, pre=""):
        f = {}
        for k, v in d.items():
            if isinstance(v, dict) and pre.count(".") < 2:
                f.update(flat(v, f"{pre}{k}."))
            else:
                f[f"{pre}{k}"] = v
        return f
    fl = [flat(x) for x in locks]
    keys = set().union(*fl)
    out["lock_tables_that_differ"] = sorted(k for k in keys if len({json.dumps(f.get(k), sort_keys=True)
                                                                     for f in fl}) > 1)
    out["lock_gemini_tables_equal"] = all(json.dumps(x.get("gemini"), sort_keys=True)
                                          == json.dumps(locks[0].get("gemini"), sort_keys=True) for x in locks)
    root_len = Counter(r["adapter_sha256"][:8] for r in allr if (r["calls"].get("root_length") or 0) > 0)
    out["answers_with_a_root_or_closing_call_cut_at_the_output_limit_by_adapter"] = dict(root_len)
    out["answers_stored_as_the_text_None"] = sum(1 for r in allr if r.get("answer") == "None")
    return out


def find_line(path: Path, pattern: str) -> int:
    """The first line of `path` matching `pattern` (1-based); exits when none does, so a cited line is never assumed."""
    text = path.read_text()
    for i, ln in enumerate(text.splitlines(), 1):
        if re.search(pattern, ln):
            return i
    raise SystemExit(f"{rel(path)}: no line matches {pattern!r}")


def design_lines():
    """The lines the legend cites: LIST.md's and README.md's at DESIGN_AT from design_facts.json (D2; S616 finds them
    with the patterns this function used until D2), run_rlm_ref.py's in the file."""
    at = fig_design.facts()[f"design_lines_at_{DESIGN_AT}"]
    return {"d31": at["d31"], "fig3_q19": at["fig3_q19"], "list_q116": at["list_q116"],
            "readme_q116": at["readme_q116"], "readme_q50": at["readme_q50"],
            "fig2_caps": f"{rel(RUN_RLM_REF)}:{find_line(RUN_RLM_REF, r'^FIGURE2_CAPS\s*=')}",
            "d123": at["d123"]}


def package_citation():
    """The package's author and paper URL from its installed METADATA, and the reference of the submitted manuscript
    that cites that URL (its number only)."""
    meta = sorted(PKG_METADATA.glob("python*/site-packages/rlms-*.dist-info/METADATA"))
    if len(meta) != 1:
        raise SystemExit(f"{rel(PKG_METADATA)}: {len(meta)} rlms METADATA files, want 1")
    t = meta[0].read_text()
    ver = re.search(r"^Version: (\S+)", t, re.M).group(1)
    author = re.search(r"^Author-email: ([^<\n]+?)\s*<", t, re.M).group(1)
    url = re.search(r"https://arxiv\.org/abs/[\d.]+", t).group(0)
    ref = fig_design.facts()["references"].get(url)   # D2: S616 read the number from manuscript/sections/29_references.md
    if ref is None:
        raise SystemExit(f"{rel(fig_design.FACTS)}: no reference cites {url}")
    num = ref["number"]
    if url != REVISED_REFERENCE["url"]:
        raise SystemExit(f"the installed rlms cites {url}, not the revised reference's {REVISED_REFERENCE['url']}")
    return {"version": ver, "author": author, "url": url, "reference": int(num),
            "reference_revised": REVISED_REFERENCE["number"],
            "metadata": rel(meta[0]), "reference_line": ref["line"]}


# ---------------------------------------------------------------------------------------------------------------
# The numbers
# ---------------------------------------------------------------------------------------------------------------
def box_stats(vals):
    import numpy as np
    v = np.asarray(vals, dtype=float)
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return {"n": int(v.size), "minimum": float(v.min()), "q1": float(q1), "median": float(med), "q3": float(q3),
            "maximum": float(v.max())}


def gemini_status(err):
    """The failing call's status as the record's error states it ("status <word>: ..."); an error with no finish
    reason and an error of the connection told apart."""
    m = re.search(r"status (\w+):\s*(.*)", err or "")
    if not m:
        return "other"
    s = m.group(1)
    if s == "error":
        return NOFINISH if "finishReason" in m.group(2) else "error, other"
    return s


NOFINISH = "error, stream ended without a finishReason"    # an empty Gemini reply: no finish reason, no part (D89)
PACKAGE_STATUS = "the package's TypeError"                 # D161 (1): a package_error() answer's error names no status


def fail_label(r):
    """A failed answer's status for the counts by status: the Gemini status its error states, or PACKAGE_STATUS."""
    return PACKAGE_STATUS if package_error(r) else gemini_status(r["error"])


ACTIONS = ("rerun", "rebuild", "stays_failed")      # S455 action(), D92 (Q187 rebuild, Q185 stays_failed)


def s455_listed(s455):
    """S455's listed rows by (run name, answer_key): the D92 list holds rows of several runs, so each cap's records are
    matched to the rows of their own run. A key listed twice would be caught by check_actions() part (1)."""
    return {(r["run"], r["answer_key"]): r for r in s455["rows"] if r.get("answer_key")}


def unlisted_txt(r):
    """A failed answer S455 does not list, as the legend's Reruns paragraph names it: its key and its error."""
    return f"{r['answer_key']} ({(r['error'] or '').split(': ', 1)[-1][:150]})"


def compute(sel, caps, s455, runs):
    """runs: cap -> the run folder S459 reads its records from."""
    listed = s455_listed(s455)
    listed_failed_status, unlisted_failed, answered_listed_calls = Counter(), Counter(), set()
    a_rows, b_rows = [], []
    fail_status = {}
    for c in caps:
        R = sel[c]
        n = len(R)
        L = {r["answer_key"]: listed[(runs[c], r["answer_key"])] for r in R if (runs[c], r["answer_key"]) in listed}
        d89 = {k for k, x in L.items() if x["since"] == "D89"}
        d90 = {k for k, x in L.items() if x["since"] == "D90"}
        s455_calls = {k: x["calls"] for k, x in L.items()}
        acts = Counter(L[k]["action"] for k in d89 | d90)
        if set(acts) - set(ACTIONS):
            raise SystemExit(f"cap {c}: S455 actions {sorted(set(acts) - set(ACTIONS))} the legend does not name")
        cnt = Counter(outcome_of(r) for r in R)
        unknown = set(cnt) - {o for o, _, _ in OUTCOMES}
        if unknown:
            raise SystemExit(f"cap {c}: stop reasons {sorted(unknown)} that panel a does not draw")
        failed = [r for r in R if r["status"] == "failed"]
        if {r["stop_reason"] for r in failed} - {"forced_final_failed", "root_call_failed", "error"} or \
                sum(r["status"] == "ok" for r in R) != sum(cnt[o] for o in ANSWERED):
            raise SystemExit(f"cap {c}: status and stop_reason disagree (fbbcfb3:1081)")
        row = {"cap": c, "answers_n": n}
        for o, _, _ in OUTCOMES:
            row[f"{o}_n"] = cnt[o]
            row[f"{o}_pct"] = 100.0 * cnt[o] / n
        for sr in ("answer_ready", "turn_cap"):
            row[f"no_text_{sr}_n"] = sum(1 for r in R if no_text(r) and r["stop_reason"] == sr)
        row["listed_S455_D89_n"] = sum(r["answer_key"] in d89 for r in R)
        row["listed_S455_malformed_D90_n"] = sum(r["answer_key"] in d90 for r in R)
        row["failed_listed_n"] = sum(r["answer_key"] in d89 | d90 for r in failed)
        row["failed_not_listed_n"] = len(failed) - row["failed_listed_n"]
        row["failed_not_listed_keys"] = "; ".join(sorted(unlisted_txt(r) for r in failed
                                                         if r["answer_key"] not in d89 | d90))
        row["failed_listed_by_status"] = "; ".join(f"{k} {v}" for k, v in sorted(Counter(
            fail_label(r) for r in failed if r["answer_key"] in d89 | d90).items())) or "none"
        row["answered_listed_n"] = sum(1 for r in R if r["status"] == "ok" and r["answer_key"] in d89 | d90)
        row["answered_listed_keys"] = "; ".join(sorted(r["answer_key"] for r in R
                                                       if r["status"] == "ok" and r["answer_key"] in d89 | d90))
        for a in ACTIONS:                            # D115 L1c: the listed answers by their D92 action
            row[f"S455_D92_{a}_n"] = acts[a]
        row["root_length_answers_n"] = sum(1 for r in R if (r["calls"].get("root_length") or 0) > 0)
        fs = Counter(fail_label(r) for r in failed)
        # D94 Q-d: the legend counts the empty Gemini replies as turns of panel a's "a turn's model call failed"
        # (the label kept); a closing call that failed on one would make that sentence false, so it stops here
        if any(r["stop_reason"] != "root_call_failed" for r in failed if gemini_status(r["error"]) == NOFINISH):
            raise SystemExit(f"cap {c}: an answer failed on an empty Gemini reply at its closing call; the legend's "
                             f"empty-reply sentence counts turns only")
        listed_failed_status.update(fail_label(r) for r in failed if r["answer_key"] in d89 | d90)
        unlisted_failed.update(unlisted_txt(r) for r in failed if r["answer_key"] not in d89 | d90)
        answered_listed_calls.update(c["call"] for r in R if r["status"] == "ok" and r["answer_key"] in d89 | d90
                                     for c in s455_calls[r["answer_key"]])
        fail_status[c] = dict(fs)
        row["failed_by_status"] = "; ".join(f"{k} {v}" for k, v in sorted(fs.items())) or "none"
        row["answers_stored_as_the_text_None_n"] = sum(1 for r in R if r.get("answer") == "None")
        row["record_lock_sha256"] = "; ".join(f"{k[:8]} {v}" for k, v in
                                              sorted(Counter(r["lock_sha256"] for r in R).items()))
        row["record_adapter_sha256_by_draw"] = "; ".join(
            f"d{d} {k[:8]} {v}" for (d, k), v in sorted(Counter((r["draw"], r["adapter_sha256"]) for r in R).items()))
        a_rows.append(row)
        ok = [r for r in R if r["status"] == "ok"]
        for out, val in ((b_rows, lambda r: r["turns_used"]),):   # D217, D224 Q5: tokens and time no longer drawn
            vals = [val(r) for r in ok]
            st = box_stats(vals)
            out.append({"row": "cap", "cap": c, "question_id": None, "draw": None, "value": None, **st})
            for r in sorted(ok, key=lambda r: (r["question_id"], r["draw"])):
                out.append({"row": "answer", "cap": c, "question_id": r["question_id"], "draw": r["draw"],
                            "value": val(r), "n": None, "minimum": None, "q1": None, "median": None, "q3": None,
                            "maximum": None})
    if min(r["value"] for r in b_rows if r["row"] == "answer") <= 0:
        raise SystemExit("a value of b is 0 or less: the log axis cannot draw it")
    return {"a": a_rows, "b": b_rows, "fail_status": fail_status,
            "listed_failed_status": dict(listed_failed_status), "unlisted_failed": dict(unlisted_failed),
            "answered_listed_calls": sorted(answered_listed_calls)}


def check_actions(fn, full, sel, runs, s455):
    """D115 L1c: the legend's count of each D92 action. (1) S455's G6 rows each name a run S459 reads and an answer
    in it, and the actions they carry over every record of those runs add to S455's own totals for G6; (2) on the
    figure's answers, a rebuilt answer failed at its closing call (forced_final_failed) and one left failed failed at
    a turn (root_call_failed), as S455 action() sets them; (3) per cap, Sheet a's three action counts add to the
    listed answers (failed and not); (4) per cap, each of the three equals the count of S455's rows of that cap's run
    whose question is one of the figure's, so no action moves between columns or caps. Returns the problems; none is
    the pass."""
    probs = []
    listed = s455_listed(s455)
    g6 = [r for r in s455["rows"] if r["experiment"].startswith("G6")]
    keys = {(runs[c], r["answer_key"]) for c in runs for r in full[c]}
    for r in g6:
        if (r["run"], r["answer_key"]) not in keys:
            probs.append(f"S455 lists {r['run']} {r['answer_key']}, not an answer of the runs S459 reads")
    got = Counter(listed[k]["action"] for k in keys if k in listed)
    want = {a: (s455.get("answers_by_experiment", {}).get("G6 (b4_rlm_ref)", {}).get(f"action {a}", 0))
            for a in ACTIONS}
    if {a: got[a] for a in ACTIONS} != want or sum(got.values()) != len(g6):
        probs.append(f"S455's G6 actions over the runs' records {dict(got)}, its own totals {want}, rows {len(g6)}")
    rule = {"rebuild": "forced_final_failed", "stays_failed": "root_call_failed"}
    for c in sel:
        for r in sel[c]:
            x = listed.get((runs[c], r["answer_key"]))
            if x and x["action"] in rule and (r["status"], r["stop_reason"]) != ("failed", rule[x["action"]]):
                probs.append(f"cap {c} {r['answer_key']}: S455 action {x['action']}, the record "
                             f"{r['status']} {r['stop_reason']}")
    for row in fn["a"]:
        n_act = sum(row[f"S455_D92_{a}_n"] for a in ACTIONS)
        if n_act != row["failed_listed_n"] + row["answered_listed_n"]:
            probs.append(f"cap {row['cap']}: the D92 actions add to {n_act}, the listed answers are "
                         f"{row['failed_listed_n']} failed + {row['answered_listed_n']} not")
        c = row["cap"]
        qs = {r["question_id"] for r in sel[c]}
        direct = Counter(r["action"] for r in s455["rows"] if r["run"] == runs[c] and r["item"] in qs)
        sheet = {a: row[f"S455_D92_{a}_n"] for a in ACTIONS}
        if sheet != {a: direct[a] for a in ACTIONS}:
            probs.append(f"cap {c}: Sheet a's D92 actions {sheet}, S455's rows of {runs[c]} on the figure's "
                         f"questions {dict(direct)}")
    return probs


def action_totals(fn):
    """The figure's listed answers by D92 action, over the caps (the legend's counts)."""
    return {a: sum(r[f"S455_D92_{a}_n"] for r in fn["a"]) for a in ACTIONS}


BEFORE, AFTER = "_before_reruns", "_after_reruns"   # D161 (2): sheet a's two readings, a suffix on each column name
SHARED = ("cap", "answers_n")                      # the same in both readings (drawn_records() checks the answer keys)


def both_readings(after, before):
    """D161 (2) N2: sheet a's rows with both readings (D160 Q23): cap and answers_n once, then every other column of
    compute()'s row twice, <name>_before_reruns (the records the gates and the legend's Reruns and Failures paragraphs
    read) beside <name>_after_reruns (the records drawn)."""
    if [[r[k] for k in SHARED] for r in after] != [[r[k] for k in SHARED] for r in before] or \
            [list(r) for r in after] != [list(r) for r in before]:
        raise SystemExit("sheet a: the readings before and after the D135 reruns differ in their caps, answers or "
                         "columns")
    return [{**{k: a[k] for k in SHARED},
             **{f"{k}{s}": x[k] for k in a if k not in SHARED for s, x in ((BEFORE, b), (AFTER, a))}}
            for a, b in zip(after, before)]


def sheets_of(fn, fn_gate=None):
    """One sheet per panel; sheet a with both readings when fn_gate (the records before the D135 reruns) is given."""
    out = []
    for letter in "ab":
        rows = both_readings(fn["a"], fn_gate["a"]) if letter == "a" and fn_gate is not None else fn[letter]
        cols = list(rows[0])
        assert all(list(r) == cols for r in rows), letter
        out.append((f"{SHEET}{LETTER_CASE(letter)}", cols, [[r[c] for c in cols] for r in rows]))
    return out


def write_source_data(sheets, path):
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


# ---------------------------------------------------------------------------------------------------------------
# The plate
# ---------------------------------------------------------------------------------------------------------------
def draw_figure(fn, caps, paths):
    """The plate in the house style: house_style's box (no fill, every answer a grey dot under the lines, range
    whiskers with caps), bars 0.70 of the row, keys above their panels and centred, sentence-case axis labels."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    hs.apply_rc("S459")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

    tw = hs._text_width_mm
    W = FIG_W_MM
    M, LINE, PAD = 1.5, PT_TEXT * MM_PER_PT * 1.2, 2 * MM_PER_PT
    XAX = 2 * MM_PER_PT + PAD + LINE + PAD + LINE     # ticks, tick labels, one-line axis label
    ROW = 4.6                                         # one cap
    nC = len(caps)
    AX_H = nC * ROW
    GAP_COL = 5.0
    ylab_w = LINE + PAD + max(tw(str(c)) for c in caps) + PAD + 2 * MM_PER_PT
    # Valerio, 11 Nov: the plate holds only the figure; the n of each cap is in the legend, so no n column at a's or
    # b's right (na_w, nb_w kept as 0 so the layout arithmetic below is unchanged in form)
    na_w = 0.0
    nb_w = 0.0
    # D217, D224 Q5: a and b in one row, the two axes equally wide; the row ends at b's right edge, at the page's right
    # margin, so the time panel's place leaves no hole
    ax_w = (W - 2 * M - 2 * ylab_w - na_w - nb_w - GAP_COL) / 2
    col_a = M
    xa, wa = col_a + ylab_w, ax_w
    col_b = xa + wa + na_w + GAP_COL
    xb, wb_ = col_b + ylab_w, ax_w
    if abs(xb + wb_ + nb_w - (W - M)) > 1e-6 or ax_w < 30:
        raise SystemExit(f"{SI_LABEL}: the row of two panels does not fit ({ax_w:.1f} mm a panel)")
    # a's key: an ending that may be empty is keyed only when drawn (D161 (1); S10 note of PF for forced_final_failed)
    key_a = [("swatch", col, lab) for o, lab, col in OUTCOMES
             if o not in ("package_error", "forced_final_failed") or any(r[f"{o}_n"] for r in fn["a"])]
    KEY_PITCH = 3.7

    KEY_A_W = wa + na_w                               # a's key sits within a's axes
    # a's key in columns, each entry starting at its column's left edge, so the swatches line up (D217 review): the
    # most columns that fit, filled row by row
    KEY_COL_GAP = 2.4
    ka_w = [hs._glyph_w(k) + 0.8 + tw(t) for k, _, t in key_a]
    # 11 Nov (Valerio, doc comment): a's key in two columns of three, filled down; the rows it frees go to the axes
    nka = math.ceil(len(key_a) / 2)
    ka_cols = 2 if len(key_a) > 1 else 1
    ka_colws = [max(ka_w[j * nka:(j + 1) * nka]) for j in range(ka_cols)]
    KEY_Y = M + PT_TEXT * MM_PER_PT                  # the first key line's baseline, and every panel letter's
    H = KEY_Y + (len(key_a) - 1) * KEY_PITCH + 3.2 + AX_H + XAX + M   # the page as with the key in one column
    top1 = KEY_Y + (nka - 1) * KEY_PITCH + 3.2
    AX_H = H - top1 - XAX - M
    ROW = AX_H / nC
    if H > FIG_H_MAX_MM - 0.05:
        raise SystemExit(f"{SI_LABEL}: the page would be {H:.1f} mm high, over [page] height_max_mm {FIG_H_MAX_MM}")
    fig = hs.figure(W, H)
    printed = {}

    def num(artist, entry):
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = entry
        return artist

    ypos = {c: i + 1 for i, c in enumerate(caps)}
    CAP_MM = hs.MARK_MM                               # the cap's triangle
    CAP_DY = hs.BAND_FRAC / 2 + (CAP_MM / 2 + 0.15) / ROW   # its centre above the row's centre, in rows (over the dots)
    if CAP_DY + CAP_MM / 2 / ROW >= 1 - hs.BAND_FRAC / 2:
        raise SystemExit("b: the cap's triangle would reach the dots of the row above")

    def rows_axis(ax):
        ax.set_ylim(nC + 0.5, 0.5)
        ax.yaxis.set_major_locator(FixedLocator([ypos[c] for c in caps]))
        ax.yaxis.set_major_formatter(FixedFormatter([str(c) for c in caps]))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_ylabel(hs.axis_label("turn cap"), labelpad=2)

    def log_axis(ax, ticks, labels, lo, hi):
        ax.set_xscale("log")
        ax.set_xlim(lo, hi)
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FixedFormatter(labels))
        ax.xaxis.set_minor_locator(NullLocator())

    readback = {"a": [], "b": []}
    overlaps = {}

    def boxes(ax, letter, w_mm):
        """House boxes on a log axis: the dots are placed apart in log space (the axis the reader sees), then the
        box is drawn from the script's own summary (stats), so no number is computed here."""
        rows = [r for r in fn[letter] if r["row"] == "cap"]
        lo_, hi_ = (math.log10(v) for v in ax.get_xlim())
        mm_dec = w_mm / (hi_ - lo_)
        across_mm = ROW
        for r in rows:
            vals = [a["value"] for a in fn[letter] if a["row"] == "answer" and a["cap"] == r["cap"]]
            if len(vals) != r["n"]:
                raise SystemExit(f"{letter} cap {r['cap']}: {len(vals)} answer rows, n = {r['n']}")
            dmm = hs.DOT_MM if len(vals) > 30 else hs.DOT_SPARSE_MM
            half_band = hs.BAND_FRAC * across_mm / 2
            off, over = hs.swarm([math.log10(v) * mm_dec for v in vals], half=half_band - dmm / 2,
                                 pitch=hs.DOT_PITCH_MM if dmm <= hs.DOT_MM else dmm + 0.05, dot=dmm)
            overlaps[(letter, r["cap"])] = over
            ax.plot(vals, [ypos[r["cap"]] + o / across_mm for o in off], ls="none", marker="o",
                    ms=dmm / hs.MM_PT, mfc=hs.GREY["dot"], mec="none", mew=0, zorder=2, clip_on=False)
            st = {"q1": r["q1"], "median": r["median"], "q3": r["q3"], "whisker_low": r["minimum"],
                  "whisker_high": r["maximum"]}
            art = hs.boxplot(ax, ypos[r["cap"]], stats=st, orient="h", slot=1.0, dots=False)
            (art.get("box") or art["median"]).set_gid(f"s459_{letter}_box_{r['cap']}")
            readback[letter].append((r["cap"], float(art["median"].get_xdata()[0]), r["median"]))
        return rows

    # ---- a: how each answer ended
    ax_a = hs.axes_mm(fig, xa, top1, wa, AX_H)
    rows_axis(ax_a)
    ax_a.set_xlim(0, 100)
    ax_a.xaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax_a.xaxis.set_major_formatter(FixedFormatter(["0", "25", "50", "75", "100"]))
    ax_a.set_xlabel(hs.axis_label("answers", "%"), labelpad=2)
    half_bar = hs.BAR_FRAC / 2
    for i, r in enumerate(fn["a"]):
        left = 0.0
        first = None
        for o, _, col in OUTCOMES:
            wv = r[f"{o}_pct"]
            if wv <= 0:
                continue
            rect = Rectangle((left, ypos[r["cap"]] - half_bar), wv, 2 * half_bar, facecolor=col, edgecolor="none",
                             lw=0)
            ax_a.add_patch(rect)
            readback["a"].append((r["cap"], o, rect.get_width(), wv))
            if first is None:
                first = rect
                rect.set_gid(f"s459_a_bar_{r['cap']}")
            left += wv
        if abs(left - 100.0) > 1e-9:
            raise SystemExit(f"a, cap {r['cap']}: the shares add to {left}, not 100")
    # 11 Nov: with the n labels off, the plate prints no number but tick labels; panel a's letter is entered in the
    # printed map as fixed text (as S524 enters its panel letters), so S448 R8 (6) reads a map that is not empty
    t_a = hs.panel_letter(fig, M, KEY_Y, "a")
    num(t_a, {"fixed": t_a.get_text(), "why": "panel letter"})
    ka_tot = sum(ka_colws) + (ka_cols - 1) * KEY_COL_GAP
    ka_x0 = max(xa + (KEY_A_W - ka_tot) / 2, M + 4.0)
    if ka_x0 + ka_tot > col_b - 1.0:
        raise SystemExit(f"a's key ({ka_tot:.1f} mm) would reach b's letter")
    for i_, (item, w_) in enumerate(zip(key_a, ka_w)):
        j_ = i_ // nka
        x0 = ka_x0 + sum(ka_colws[:j_]) + j_ * KEY_COL_GAP
        hs.key(fig, [item], centre_x=x0 + w_ / 2, y=KEY_Y + (i_ % nka) * KEY_PITCH)

    # ---- b: root turns used
    ax_b = hs.axes_mm(fig, xb, top1, wb_, AX_H)
    rows_axis(ax_b)
    # 11 Nov (Valerio, doc comment): the caps evenly spaced, every cap labelled; a value between two caps sits at its
    # linear place between them; no cap triangle and no key
    import numpy as np
    cidx = list(range(nC))

    def b_t(v):
        if v < caps[0] or v > caps[-1]:
            raise SystemExit(f"b: a value {v} outside the caps {caps[0]} to {caps[-1]}")
        return float(np.interp(v, caps, cidx))
    ax_b.set_xlim(-0.4, nC - 0.6)
    ax_b.xaxis.set_major_locator(FixedLocator(cidx))
    ax_b.xaxis.set_major_formatter(FixedFormatter([str(c) for c in caps]))
    ax_b.xaxis.set_minor_locator(NullLocator())
    b_mm = wb_ / (nC - 0.2)
    rb = [r for r in fn["b"] if r["row"] == "cap"]
    for r in rb:
        vals = [a["value"] for a in fn["b"] if a["row"] == "answer" and a["cap"] == r["cap"]]
        if len(vals) != r["n"]:
            raise SystemExit(f"b cap {r['cap']}: {len(vals)} answer rows, n = {r['n']}")
        dmm = hs.DOT_MM if len(vals) > 30 else hs.DOT_SPARSE_MM
        off, over = hs.swarm([b_t(v) * b_mm for v in vals], half=hs.BAND_FRAC * ROW / 2 - dmm / 2,
                             pitch=hs.DOT_PITCH_MM if dmm <= hs.DOT_MM else dmm + 0.05, dot=dmm)
        overlaps[("b", r["cap"])] = over
        ax_b.plot([b_t(v) for v in vals], [ypos[r["cap"]] + o / ROW for o in off], ls="none", marker="o",
                  ms=dmm / hs.MM_PT, mfc=hs.GREY["dot"], mec="none", mew=0, zorder=2, clip_on=False)
        st = {k_: b_t(r[f_]) for k_, f_ in (("q1", "q1"), ("median", "median"), ("q3", "q3"),
                                            ("whisker_low", "minimum"), ("whisker_high", "maximum"))}
        art = hs.boxplot(ax_b, ypos[r["cap"]], stats=st, orient="h", slot=1.0, dots=False)
        (art.get("box") or art["median"]).set_gid(f"s459_b_box_{r['cap']}")
        readback["b"].append((r["cap"], float(np.interp(art["median"].get_xdata()[0], cidx, caps)), r["median"]))
    ax_b.set_xlabel(hs.axis_label("turns used per answer"), labelpad=2)
    hs.panel_letter(fig, col_b, KEY_Y, "b")

    bad_c = hs.check_figure_colours(fig)
    if bad_c:
        plt.close(fig)
        raise SystemExit(f"{SI_LABEL}: colours outside the house palette: {bad_c}")
    finish_plate(fig, W, H, paths, title=SI_LABEL)
    print("dots with no free slot (overlapping), by panel: "
          + ", ".join(f"{L} {sum(v for (l_, _), v in overlaps.items() if l_ == L)}" for L in "b"))
    return W, H, printed, readback


def check_drawn(readback):
    """Every bar segment of a drawn at its data workbook share, every median line of b at its median."""
    bad, n = [], 0
    if set(readback) != {"a", "b"}:                   # D224 Q5: two panels drawn, a and b
        bad.append(f"panels drawn {sorted(readback)}, not a and b")
    for cap, o, got, want in readback["a"]:
        n += 1
        if abs(got - want) > 1e-9:
            bad.append(f"a cap {cap} {o}: drawn {got}, data workbook {want}")
    for letter in "b":
        for cap, got, want in readback[letter]:
            n += 1
            if abs(got - want) > 1e-9 * max(1.0, abs(want)):
                bad.append(f"{letter} cap {cap}: median drawn {got}, data workbook {want}")
    return bad, n


# ---------------------------------------------------------------------------------------------------------------
# Legend and caption
# ---------------------------------------------------------------------------------------------------------------
def legend_and_caption(fn, caps, n_ids, stamp, tag, ctx, fn_gate=None):
    """ctx: the package and its citation, the versions the records name, the written design's lines, the corpus's
    paper count and the package's max_depth as the records hold them. fn_gate (D160 Q23): the numbers of the records
    before the D135 reruns, which the header's Reruns and Failures paragraphs describe while fn (after them) is
    drawn; None: fn is both."""
    fg = fn if fn_gate is None else fn_gate
    sa = f"{SHEET}{LETTER_CASE('a')}"
    # D161 (2): with fn_gate, sheet a holds each reading under its own column suffix; name the one a paragraph quotes
    col_gate, col_drawn = ("", "") if fn_gate is None else (f" (columns ending {BEFORE})", f" (columns ending {AFTER})")
    A, B = (f"**{LETTER_CASE(x)}**" for x in "ab")
    per_cap = fn["a"][0]["answers_n"]
    assert all(r["answers_n"] == per_cap for r in fn["a"])
    caps_txt = ", ".join(str(c) for c in caps[:-1]) + f" and {caps[-1]}"
    nb = [r for r in fn["b"] if r["row"] == "cap"]
    n_b = "; ".join(f"cap {r['cap']}, n = {r['n']}" for r in nb)
    failed = sum(r["forced_final_failed_n"] + r["root_call_failed_n"] + r["package_error_n"] for r in fg["a"])
    listed = sum(r["failed_listed_n"] for r in fg["a"])
    nt = sum(r["no_text_n"] for r in fg["a"])
    nt_tc = sum(r["no_text_turn_cap_n"] for r in fg["a"])
    nt_ar = sum(r["no_text_answer_ready_n"] for r in fg["a"])
    ans_listed = sum(r["answered_listed_n"] for r in fg["a"])
    ls = fg["listed_failed_status"]                 # the listed failed answers by the Gemini status their error states
                                                    # (or the package's TypeError, D161 (1))
    root_failed = sum(r["root_call_failed_n"] for r in fg["a"])
    empty = {c: fg["fail_status"][c].get(NOFINISH, 0) for c in caps}     # all turns (compute() stops otherwise)
    empty_txt = (f"{sum(empty.values())} of the {root_failed} answers in which a model call of a turn failed are "
                 f"turns where Gemini returned an empty reply, with no finish reason and no content ("
                 + "; ".join(f"cap {c}, {k}" for c, k in empty.items() if k) + "). ") if sum(empty.values()) else ""
    known = {"malformed": ls.get("malformed_response", 0) + ls.get("malformed_function_call", 0),
             "nofinish": ls.get(NOFINISH, 0),
             "recitation": ls.get("recitation", 0)}
    if sum(known.values()) != listed:
        raise SystemExit(f"the {listed} failed answers listed for rerun end on statuses {ls}: the legend names only "
                         f"malformed, no finishReason and recitation")
    parts = []
    for k, one, many, how in (("malformed", "a malformed reply", "malformed replies",
                               "now passed on, the status recorded, under D90 Q2"),
                              ("nofinish", "a stream that ended without a finish reason",
                               "streams that ended without a finish reason",
                               "now passed on as no text, as the package's own client returns it, under D89 and D92 "
                               "Q185"),
                              ("recitation", "a recitation stop", "recitation stops",
                               "now passed on as the text sent before the stop under D90 Q1")):
        if known[k]:
            parts.append(f"{known[k]} on {one if known[k] == 1 else many}, {how}")
    sub_only = fg["answered_listed_calls"] == ["sub"]
    act = action_totals(fg)
    if sum(act.values()) != listed + ans_listed:
        raise SystemExit(f"the D92 actions {act} do not add to the {listed + ans_listed} listed answers")
    rb, sf = act["rebuild"], act["stays_failed"]
    act_txt = (f"{act['rerun']} {'is' if act['rerun'] == 1 else 'are'} run again; "
               + (f"{rb} answer whose only failed call is its closing call takes that call's stored reply as its "
                  if rb == 1 else f"{rb} answers whose only failed call is their closing call take that call's "
                                  f"stored reply as their ")
               + "answer with no model call (Q187); and "
               + (f"{sf} answer whose failed turn reply holds no text part stays failed, since the package itself "
                  f"fails on it" if sf == 1 else f"{sf} answers whose failed turn reply holds no text part stay "
                                                 f"failed, since the package itself fails on them")
               + " (Q185)")
    pk = ctx["package"]
    title = "Outcome and turns of Zhang RLM on the depth-sweep questions, across turn caps"   # D228: package RLM everywhere; Zhang RLM since Valerio's 5 November rename
    # Valerio, 23 October: the caption describes the image only, panel by panel, under 350 words, in the style of the
    # resubmission's captions (resubmission/05_figures/Figure_<n>_caption.md); no data-state words, no script names,
    # paths or decision codes. The failure detail, the D92 actions and the old caption's longer wording are in the
    # header below (failures_txt), not lost.
    pkg = {r["cap"]: r["package_error_n"] for r in fn["a"] if r["package_error_n"]}    # D161 (1) N1, drawn reading
    k_pkg = sum(pkg.values())
    pkg_txt = (f"; or the package's own code failed, a TypeError raised inside it ({k_pkg} "
               f"answer{'' if k_pkg == 1 else 's'}: " + "; ".join(f"cap {c}, {v}" for c, v in pkg.items()) + ")"
               if k_pkg else "")
    nbs = [str(r["n"]) for r in nb]
    # Valerio, 8 November (editor row 45): an "n = X <unit>" only in a panel that draws derived statistics (b's boxes),
    # once, in that panel; a carries no n; every panel described in full, no reference to another panel.
    n_b_short = (f"n = {', '.join(nbs[:-1])} and {nbs[-1]} answers from cap {nb[0]['cap']} to cap "
                 f"{nb[-1]['cap']}")
    legend = (
        f"Each answer is one of {n_ids} depth-sweep questions answered by gemini-3-flash in Zhang RLM, "
        f"the RLM package released by the method's authors (rlms {pk['version']}; ref. {pk['reference_revised']}), in which the model writes "
        f"and runs code over the {ctx['papers']}-paper corpus for up to a set number of turns, the turn cap. "
        f"Each question was answered three times at each cap ({caps_txt}). "
        f"{A}, How each answer ended: one bar per turn cap (vertical axis), divided by the share (%) of that cap's "
        f"answers (horizontal axis) that ended each way, each way a colour named in the key: an answer within the "
        f"cap; an answer from the closing call the package makes when the cap is reached; a closing call that "
        f"returned code, kept as the answer; an answer with no text; "
        f"{'' if k_pkg else 'or '}a failed model call in a turn{pkg_txt}. {B}, Turns used per answer (horizontal "
        f"axis, caps evenly spaced) at each turn cap (vertical axis), for the answers that did not fail; the closing call is "
        f"not counted. Each grey dot is one answer, boxes span the first to the third quartile, the line is the "
        f"median and whiskers reach the smallest and largest value; "
        f"{n_b_short}.")
    failures_txt = (
        ("**Failures and D92 (moved from the caption, 23 October).** " if fn_gate is None else
         "**Failures and D92, in the records before the D135 reruns, which the gates read (moved from the caption, 23 "
         "October).** ")
        + f"{empty_txt}{listed} of the {failed} failed "
        f"answers ended on a Gemini reply that a later change of the client passes on instead of failing "
        f"({'; '.join(parts)}). These, and {ans_listed} answers that did not fail but "
        + ("whose code's model calls " if sub_only else "one of whose model calls ")
        + f"received such replies, are handled under D92: {act_txt}. Answers with no text: {nt} ({nt_tc} from the "
        f"closing call, {nt_ar} within the cap). "
        + f"The package runs at maximum depth {ctx['max_depth']}.")
    dl, vr = ctx["design_lines"], ctx["versions"]
    unlisted = {k: v for k, v in fg["unlisted_failed"].items()}
    if fn_gate is not None:                          # D160 Q23: what the drawn records hold after the reruns
        f_now = sum(r["forced_final_failed_n"] + r["root_call_failed_n"] + r["package_error_n"] for r in fn["a"])
        failures_txt += (
            f"\n\n**After the D135 reruns (drawn, D160 Q23).** The plate draws the records after the reruns of 24 and "
            f"25 October (D135), which applied these D92 actions; in the data workbook's sheet {sa}, the columns "
            f"ending {AFTER} (those ending {BEFORE} hold the records before the reruns, which the Reruns and "
            f"Failures paragraphs quote). Failed answers now: {f_now} (a failed closing call "
            f"{sum(r['forced_final_failed_n'] for r in fn['a'])}, a failed model call in a turn "
            f"{sum(r['root_call_failed_n'] for r in fn['a'])}, the package's own code (D161 (1)) "
            f"{sum(r['package_error_n'] for r in fn['a'])}: a TypeError the package raised on a root reply of None, "
            f"a reply Gemini blocked or one with no text part); answers with no text: "
            f"{sum(r['no_text_n'] for r in fn['a'])} ({sum(r['no_text_turn_cap_n'] for r in fn['a'])} from the closing "
            f"call, {sum(r['no_text_answer_ready_n'] for r in fn['a'])} within the cap); failed answers by the status "
            f"their error states, per cap: "
            + "; ".join(f"cap {c}, {', '.join(f'{k} {v}' for k, v in sorted(fn['fail_status'][c].items())) or 'none'}"
                        for c in caps) + ".")
    adapters = "; ".join(f"{k} = commit {v['commit']} ({v['records']} records)" for k, v in vr["adapter"].items())
    locks = "; ".join(f"{k} = commit {v['commit']} ({v['records']} records)" for k, v in vr["lock"].items())
    header = [
        f"# {SI_LABEL}, title and legend (draft)", "",
        f"Written by `uv run --frozen python scripts/S459_fig3_rlm_ref_caps.py` from the plotted numbers.", "",
        f"**Place.** D123 ({dl['d123']}) moves this plate, drawn as Figure 3 until then, to the Supplementary; "
        f"Supplementary Figure 8 (main Figure 3 at D123) shows concept recall against the turn cap for both RLMs, the "
        f"local models, corpus scale and the share of answers reaching the cap. Number {SUPP_N} comes from the "
        f"manuscript's order of first citation (D257).", "",
        f"**Written design.** D31 answered Q19, both RLMs with the package as a reference arm "
        f"({dl['d31']}); D78 Q116 gives the authors' depth caps three draws under "
        f"Figure 3 ({dl['list_q116']}, {dl['readme_q116']}); D75 Q50 gives "
        f"the depth sweep's {n_ids} questions to both RLMs ({dl['readme_q50']}). LIST.md's Figure 3 section states "
        f"Q19 settled ({dl['fig3_q19']}). Open for Valerio: whether caps 5, 10 and 20, taken "
        f"from Figure 3's runs ({dl['fig2_caps']}), and these two unjudged panels make the plate (D217 dropped the tokens panel, D224 Q5 the "
        f"time panel).",
        "",
        f"**Reruns.** {'S455' if fn_gate is None else 'In the records before the D135 reruns, S455'} lists {listed} "
        f"of the {failed} failed answers and {ans_listed} answers that did not fail "
        f"({'; '.join(r['answered_listed_keys'] for r in fg['a'] if r['answered_listed_keys'])}). Its D92 actions "
        f"on them ({rel(S455)}): rerun {act['rerun']}, rebuild {act['rebuild']}, stays_failed "
        f"{act['stays_failed']}; per cap in the data workbook's sheet {sa}{col_gate}. Not listed: "
        f"{'; '.join(k if v == 1 else f'{k}, {v} times' for k, v in unlisted.items()) or 'none'}.", "",
        f"**Code and lock versions the records name.** Adapter (experiments/rlm_ref/adapter.py): {adapters}; per "
        f"cap and draw in the data workbook's sheet {sa}{col_drawn}. Between these versions the handling of a root "
        f"or closing "
        f"call cut at the output limit changed (D75 Q48, then D78 Q114); answers with such a cut, by adapter: "
        f"{vr['answers_with_a_root_or_closing_call_cut_at_the_output_limit_by_adapter']}; answers stored as the "
        f"text 'None': {vr['answers_stored_as_the_text_None']}. Run lock (experiments/LOCK.toml): {locks}; the "
        f"keys that differ between them: {', '.join(vr['lock_tables_that_differ']) or 'none'}; the [gemini] table "
        f"{'is equal in all' if vr['lock_gemini_tables_equal'] else 'DIFFERS'}.", "",
        f"**Citation.** The package's METADATA ({pk['metadata']}) names {pk['author']} and {pk['url']}; the "
        f"submitted manuscript cites that URL as reference {pk['reference']} ({pk['reference_line']}). Whether that "
        f"entry's author and title match the preprint is not checked here.", "",
        failures_txt, "",
    ]
    lines = header + [f"**{SI_LABEL} | {title}.** {legend}", ""]
    s = {x: f"{SHEET}{LETTER_CASE(x)}" for x in "ab"}
    cap = [f"# {SI_LABEL} data, caption", "",
           (f"**{SI_LABEL} data{tag} |** The numbers drawn in {SI_LABEL} (Zhang RLM, the RLM package released "
            f"by the method's authors, Zhang et al., across turn caps), one sheet per panel. Sheet {s['a']}: per turn cap, the answers (n), the "
            f"count and share (%) of each way an answer ended (the record's stop_reason, turn_cap split by the "
            f"record's forced_final_has_code, and an answer of status ok with no text drawn as its own way whatever "
            f"its stop_reason: answer_ready, turn_cap_answer, turn_cap_code, no_text, forced_final_failed, "
            f"root_call_failed, and package_error, an answer the package's own code failed on with a TypeError), "
            f"the answers with no text by stop_reason, the answers listed as changed by the "
            f"client's handling of empty Gemini replies and of malformed replies, the failed answers listed and not "
            f"listed for rerun (the listed ones by the status their error states, the others by key and error), "
            f"the answers that did not fail but are listed (count and keys), the listed answers by "
            f"the action each is given (rerun, rebuild from the stored closing reply, stays_failed), the answers "
            f"with a root or closing call cut at the output limit, the answers stored as the text 'None', the failed "
            f"answers by the Gemini status their error states (or the package's TypeError), and the lock and adapter sha256 prefixes the records "
            f"carry with their counts (the adapter's per draw)"
            + ("" if fn_gate is None else
               f". Every column but cap and answers_n is given twice: ending {BEFORE}, the records before the reruns "
               f"of 24 and 25 October, and ending {AFTER}, the records after them, which the plate draws")
            + f". Sheet {s['b']}: one 'cap' row per turn cap with n, "
            f"minimum, first quartile, median, third quartile and maximum (the box), then one 'answer' row per "
            f"answer that did not fail (question, draw, value): root turns used."),
           "", f"Data stamp: {stamp}.", ""]
    return "\n".join(lines), "\n".join(cap)


# ---------------------------------------------------------------------------------------------------------------
REBUILD_CMD = "uv run --frozen python scripts/S459_fig3_rlm_ref_caps.py"


def load_records(files, ids, caps, fig2_caps):
    """Each cap's records (full) and those of the figure's questions (sel), checked: every question once per draw
    1, 2, 3, no record outside DEPTH_SWEEP86 in a depth run, each record of its cap, one model, context and package,
    max_iterations its cap, one corpus."""
    full = {c: read_answers(files[c]) for c in caps}
    want = set(ids)
    sel = {}
    for c in caps:
        R = [r for r in full[c] if r["question_id"] in want]
        got = Counter((r["question_id"], r["draw"]) for r in R)
        if set(got) != {(q, d) for q in ids for d in (1, 2, 3)} or any(v != 1 for v in got.values()):
            raise SystemExit(f"cap {c}: the records do not hold each of the {len(ids)} questions once per draw 1, 2, 3")
        if c not in fig2_caps and len(R) != len(full[c]):
            raise SystemExit(f"cap {c}: {len(full[c]) - len(R)} records outside DEPTH_SWEEP86")
        if any(r["cap"] != c for r in R):
            raise SystemExit(f"cap {c}: a record of another cap in {rel(files[c])}")
        sel[c] = R
    allr = [r for c in caps for r in sel[c]]
    for field, get in (("model", lambda r: r["model"]), ("context", lambda r: r["context"]["context_sha256"]),
                       ("package", lambda r: (r["package"]["name"], r["package"]["version"],
                                              r["package"]["rlm_kwargs"]["max_depth"]))):
        vals = {get(r) for r in allr}
        if len(vals) != 1:
            raise SystemExit(f"the records hold more than one {field}: {sorted(map(str, vals))}")
    if any(r["package"]["rlm_kwargs"]["max_iterations"] != r["cap"] for r in allr):
        raise SystemExit("a record's max_iterations differs from its cap")
    papers = {len(r["passages"]["papers"]) for r in allr}
    if len(papers) != 1:
        raise SystemExit(f"the records name corpora of {sorted(papers)} papers")
    return full, sel, allr, papers


def drawn_records(post: Path, ids, caps, fig2_caps, experiment, full_gate):
    """D160 Q23: the records after the D135 reruns (files, full, sel, allr, papers, mtimes), each file the one
    SOURCE_MTIMES.json records, each cap holding the same answer keys as before the reruns; an answer that ended in a
    way panel a has no slice for refuses (how to draw it is a design choice, not made here)."""
    files = {c: run_dir(experiment, c, fig2_caps, post) / "answers.jsonl" for c in caps}
    mt = json.loads((post / "SOURCE_MTIMES.json").read_text())["files"]
    for c in caps:
        if sha256_file(files[c]) != mt[as_read(files[c])]["sha256"]:
            raise SystemExit(f"{rel(files[c])}: not the file SOURCE_MTIMES.json records for {as_read(files[c])}")
    full, sel, allr, papers = load_records(files, ids, caps, fig2_caps)
    for c in caps:
        if {r["answer_key"] for r in full[c]} != {r["answer_key"] for r in full_gate[c]}:
            raise SystemExit(f"cap {c}: the records after the D135 reruns hold other answers than those before")
    known = {o for o, _, _ in OUTCOMES}
    odd = sorted(f"cap {r['cap']} {r['answer_key']} ({r['status']} {r['stop_reason']})" for r in allr
                 if outcome_of(r) not in known)
    if odd:
        raise SystemExit(f"D160 Q23: {len(odd)} answers after the D135 reruns ended in a way panel a has no slice for "
                         f"(e.g. {odd[:3]}); how to draw them (a slice of their own, its colour and the legend's "
                         f"words) is Valerio's choice, so nothing is drawn")
    return files, full, sel, allr, papers, mt


def recorded_as_frozen(key: str) -> str:
    """A G6 answers file the provenance of 23 October names by findings/runs/<run>/answers.jsonl: its frozen label."""
    m = re.fullmatch(r"findings/runs/(b4_rlm_ref__cap\d+__\w+)/answers\.jsonl", key)
    return f"frozen:L2/g6/{m.group(1)}/answers.jsonl" if m else key


def main(argv=None):
    global RUNS, OUT
    FR.pin_hash_seed()                              # D155: PDF font subsets depend on the string-hash seed
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help=f"default {OUT.relative_to(ROOT)}; the committed record is read from there anyway")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    prov_p = OUT / f"{SIDE}_provenance.json"
    if not prov_p.exists():
        raise SystemExit(f"{rel(prov_p)} is missing: there is no committed plate to rebuild")
    recorded = json.loads(prov_p.read_text())["inputs_sha256"]
    runs_dir()
    mtimes = json.loads(FR.check_committed(G6_MTIMES_JSON).read_text())["files"]
    if a.out:
        OUT = Path(a.out).resolve()
    if FLOCK.get("status") != "agreed":
        raise SystemExit(f"{rel(FIGURE_LOCK)} has status {FLOCK.get('status')!r}, not 'agreed' (D87): no plate")
    for c in [o[2] for o in OUTCOMES] + [BOX_FILL]:
        if c not in _CAT:
            raise SystemExit(f"{c} is not in [colour] categorical")
    if len({o[2] for o in OUTCOMES}) != len(OUTCOMES):    # D161 (1): each of a's colours one meaning
        raise SystemExit("panel a: two outcomes share a colour")
    if wcag_ratio("#000000", "#FFFFFF") < CONTRAST_MIN:
        raise SystemExit("black on white under [type] contrast_min_ratio")
    ids, caps, fig2_caps, experiment = design_constants()
    files = {c: run_dir(experiment, c, fig2_caps) / "answers.jsonl" for c in caps}
    for c in caps:                                  # each frozen file is the one whose source mtime is recorded
        if sha256_file(files[c]) != mtimes[as_read(files[c])]["sha256"]:
            raise SystemExit(f"{rel(files[c])}: not the file {G6_MTIMES_JSON.name} records for {as_read(files[c])}")
    post = drawn_dir()                              # D160 Q23: the records drawn, after the D135 reruns (or None)
    read_now = {FR.frozen_label(files[c]): sha256_file(files[c]) for c in caps}
    if post is not None:
        for c in caps:
            q = run_dir(experiment, c, fig2_caps, post) / "answers.jsonl"
            read_now[FR.frozen_label(q)] = sha256_file(q)
        mts = post / "SOURCE_MTIMES.json"           # read by drawn_records and recorded below: compared as well
        read_now[FR.frozen_label(mts)] = sha256_file(mts)
    try:
        seen = FR.check_recorded(read_now, recorded, recorded_as_frozen)
    except FR.FrozenInputError as e:
        raise SystemExit(f"REFUSED: {e}") from None
    print(f"frozen inputs: {seen['compared']} recorded by the committed plate, each equal; "
          f"{len(seen['not_recorded_before'])} read and not recorded before")
    full, sel, allr, papers = load_records(files, ids, caps, fig2_caps)
    reproduced, s455 = reproduce(full, caps, fig2_caps, files)     # the gates: the records before the D135 reruns
    runs = {c: files[c].parent.name for c in caps}
    fn_gate = compute(sel, caps, s455, runs)
    probs = check_actions(fn_gate, full, sel, runs, s455)
    if probs:
        print("D92 ACTIONS DO NOT ADD UP, nothing written:\n  " + "\n  ".join(probs[:10]), file=sys.stderr)
        sys.exit(2)
    files_gate, full_gate = files, full
    mt_post = None
    if post is not None:
        files, full, sel, allr, papers, mt_post = drawn_records(post, ids, caps, fig2_caps, experiment, full_gate)
        fn = compute(sel, caps, s455, runs)
        print("drawn (D160 Q23): G6 after the D135 reruns; the gates read the records before them")
    else:
        fn = fn_gate
    ctx = {"package": package_citation(), "versions": versions_of_records(allr), "design_lines": design_lines(),
           "papers": papers.pop(), "max_depth": allr[0]["package"]["rlm_kwargs"]["max_depth"]}
    if ctx["package"]["version"] != allr[0]["package"]["version"]:
        raise SystemExit(f"installed rlms {ctx['package']['version']}, the records name "
                         f"{allr[0]['package']['version']}")
    n = len(allr)
    N = len(ids) * len(caps) * 3                    # this plate's written plan: the 86 questions x the caps x 3 draws
    #                                                 (D78 Q116, D98); main Figure 3's plan is planned_total() (S475)
    newest = max((mt_post if post is not None else mtimes)[as_read(files[c])]["mtime"] for c in caps)   # a copy keeps none
    from zoneinfo import ZoneInfo
    when = dt.datetime.fromtimestamp(newest, ZoneInfo(STAMP_TZ)).strftime("%Y-%m-%d %H:%M %Z")
    stamp = (f"{fmt_int(n)} of {fmt_int(N)} answers, Zhang RLM at {len(caps)} turn caps (G6, "
             f"records of {when}), no judge; "
             + ("after the D89 and D90 reruns (D135), the gates on the records before them" if post is not None
                else "before the D89 and D90 reruns"))
    tag = ""                                        # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob(f"{SI_LABEL}*"):           # the plate, its data workbook and caption of another data state
        old.unlink()
    paths = {x: OUT / f"{SI_LABEL}{tag}.{x}" for x in ("pdf", "svg", "png")}
    W, H, printed, readback = draw_figure(fn, caps, paths)
    FR.check_pdf_deterministic(paths["pdf"])        # D155: saved with no date; refuse one
    FR.check_svg_deterministic(paths["svg"])
    sheets = sheets_of(fn, fn_gate if post is not None else None)
    sd = OUT / f"{SI_LABEL} data{tag}.xlsx"
    write_source_data(sheets, sd)
    FR.deterministic_xlsx(sd)                       # D155: no write time; every cell as written
    numbers = OUT / f"{SIDE}_numbers.json"
    numbers.write_text(json.dumps({"stamp": stamp, "what": f"every number {SI_LABEL} draws, sheet by sheet as the "
                                   "data workbook holds them (S448 --supplementary R8 (2) to (6) compares the "
                                   "workbook with this file, D94 O-b)",
                                   "sheets": {nm: {"columns": cols, "rows": rows} for nm, cols, rows in sheets},
                                   "printed": printed,
                                   "printed_what": "every number printed on the plate: the SVG group id of its text, "
                                                   "and the data workbook's sheet, row and format it is written "
                                                   "from"},
                                  indent=1, default=str) + "\n")
    bad, n_checked = check_drawn(readback)
    legend, cap = legend_and_caption(fn, caps, len(ids), stamp, tag, ctx,
                                     fn_gate=fn_gate if post is not None else None)
    (OUT / "legend_draft.md").write_text(legend)
    capf = OUT / f"{SI_LABEL} data caption{tag}.md"
    capf.write_text(cap)
    inputs = {**{FR.frozen_label(p): sha256_file(p) for p in files_gate.values()},
              **{FR.frozen_label(p): sha256_file(p) for p in files.values()},
              **({FR.frozen_label(post / "SOURCE_MTIMES.json"): sha256_file(post / "SOURCE_MTIMES.json")}
                 if post is not None else {}),
              **{rel(p): sha256_file(p) for p in [RUN_RLM_REF, S455, LOCK, FIGURE_LOCK, fig_design.FACTS,
                                                  ROOT / ctx["package"]["metadata"], G6_MTIMES_JSON]}}
    prov = {"script": rel(Path(__file__)), "script_sha256": sha256_file(Path(__file__)),
            "command": REBUILD_CMD,
            "python": platform.python_version(),
            "deterministic": f"D155: no build time and no repository HEAD are recorded; the script's and every "
                             f"input's sha256 identify the build; the design documents' values as they stood at {DESIGN_AT} "
                             f"are read from {rel(fig_design.FACTS)} (D2)",
            "inputs_sha256": inputs, "model_calls": 0,
            "stamp": stamp, "page_mm": [W, H],
            "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": sha256_file(FIGURE_LOCK), "status": FLOCK["status"]},
            "run_lock_now": {"path": rel(LOCK), "sha256": sha256_file(LOCK)},
            "record_lock_sha256": dict(Counter(r["lock_sha256"] for r in allr)),
            "record_versions": ctx["versions"],
            "record_adapter_sha256_by_cap_and_draw": {f"cap {c} d{d}": dict(Counter(r["adapter_sha256"][:8]
                                                      for r in sel[c] if r["draw"] == d)) for c in caps for d in (1, 2, 3)},
            "adapter_cited": "line citations in S459 are to `git show fbbcfb3:experiments/rlm_ref/adapter.py`",
            "design_lines": ctx["design_lines"], "package": ctx["package"],
            "figure": SI_LABEL, "named": f"{SI_LABEL}: FIGURE_LOCK [files] supplementary_name (D92 Q194); D123 moved "
                                         f"the plate from Figure 3",
            "reproduced": reproduced,
            "planned_answers": {"rule": "the authors' depth caps, three draws (D78 Q116; D98 keeps Figure 2's "
                                        "experiments' three full draws)", "questions": len(ids), "caps": len(caps),
                                "draws": 3, "N": N, "drawn": n},
            "d92_actions": {"check_actions": "pass", **action_totals(fn_gate)},
            "readings": ({"gated": "findings/recompute/L2_inputs/g6 (G6 before the D135 reruns): plan.csv G6's "
                                   "counts, S455's inputs, check_actions, the legend header's D92 paragraphs and sheet a's "
                                   "_before_reruns columns (D161 (2))",
                          "drawn": f"{rel(G6_D135)} (G6 after the D135 reruns, D160 Q23): every panel, sheet b and sheet a's "
                                  "_after_reruns columns",
                          "fail_status_by_cap_gated": fn_gate["fail_status"]} if post is not None else
                         {"gated": "findings/recompute/L2_inputs/g6 (G6 before the D135 reruns)",
                          "drawn": f"the same: G6 after the reruns not frozen yet ({rel(G6_D135)} missing)"}),
            "drawn_check": f"check_drawn(): {n_checked} drawn values equal their data workbook"
                           + ("" if not bad else " | FAILED: " + "; ".join(bad[:5])),
            "fail_status_by_cap": fn["fail_status"],
            "design": {"questions": len(ids), "caps": list(caps), "caps from all135 runs": sorted(fig2_caps),
                       "draws": [1, 2, 3]},
            "panels": {"a": "share of the answers at each cap by stop_reason (turn_cap split by forced_final_has_code; "
                            "an answer of status ok with no text its own slice; the package's own TypeError, "
                            "package_error(), its own slice, D161 (1)), n printed per row",
                       "b": "root turns used per answered answer (no-text answers included), box (quartiles, median, "
                            "range), n printed per row, the caps evenly spaced (11 Nov), no cap triangle and no key",
                       "dropped": "tokens per answer (D217), wall_s per answer (D224 Q5)"},
            "type_pt": {"panel letters": PT_LETTER, "all other text": PT_TEXT}, "font": FONT,
            "colours_panel_a": {o: col for o, _, col in OUTCOMES}, "box_fill": BOX_FILL,
            "files": {p.name: sha256_file(p) for p in [*paths.values(), sd, capf, numbers, OUT / "legend_draft.md"]}}
    (OUT / f"{SIDE}_provenance.json").write_text(json.dumps(prov, indent=1, default=str) + "\n")
    if bad:
        for p in [*paths.values(), sd, capf, numbers, OUT / "legend_draft.md", OUT / f"{SIDE}_provenance.json"]:
            p.unlink(missing_ok=True)
        print("check_drawn FAILED, nothing kept: " + "; ".join(bad[:5]), file=sys.stderr)
        sys.exit(1)
    print(stamp)
    print(f"reproduced: plan.csv G6 failed per draw for {len(reproduced['plan_csv_G6'])} depth caps, its all135 "
          f"stop reasons {reproduced['plan_csv_G6_all135']['records']}, S455 inputs {len(reproduced['S455_inputs'])} "
          f"files equal")
    print(f"check_drawn: {n_checked} drawn values equal their data workbook")
    print(f"check_actions: pass; D92 actions on the figure's listed answers: "
          + ", ".join(f"{a} {k}" for a, k in action_totals(fn).items()))
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W:.0f} x {H:.1f} mm), {sd.name}, {capf.name}, "
          f"{numbers.name}, legend_draft.md, {SIDE}_provenance.json into "
          f"{rel(OUT) if OUT.is_relative_to(ROOT) else OUT}")


if __name__ == "__main__":
    main()
