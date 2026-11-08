"""figure_names.py: one constant per name printed on a plate or in a legend, and the forms that are never printed.

The table is A4 of findings/audits/figure_design_2026-11-01/spec/build_order.md, with its rulings F5 (Papers precision)
and F13 (out-of-scope questions). This module holds strings and the NEVER table and nothing else: it reads no file and
draws nothing. New plate and legend text takes its words from here.

NEVER lists each form the table refuses. Each entry names the table row it comes from, the words, a regular expression
(applied with case ignored), the places it is refused in, and the places it is allowed in as an exception.
scripts/figure_names_test.py applies them to a folder; the test also holds every constant here against A4's table.

    uv run --frozen python scripts/figure_names_test.py
"""
from __future__ import annotations

from dataclasses import dataclass

# Main figure numbers (D283, Valerio, 6 November 2026, "I like. Let's go."): the depth panels a and b of Supplementary
# Figure 7 became main Figure 4, and the pipeline, signals and code-generation figures moved from 4, 5 and 6 to 5, 6
# and 7. The plate folders keep their names (fig4 holds Figure 5, fig5 Figure 6, fig6 Figure 7; fig4_depth Figure 4).
FIG_DEPTH = 4
FIG_PIPELINE = 5
FIG_SIGNALS = 6
FIG_CODE = 7

# Three signals
JUDGE = "Judge"
CONCEPTS = "Concepts"
PAPERS = "Papers"
SIGNALS = (JUDGE, CONCEPTS, PAPERS)

# The Papers measure (F5: Figure 1 and Figure 5 both print this, and S456's regex becomes PAPERS_MEASURE_RE)
PAPERS_PRECISION = "Papers precision"

# MiniCheck
MINICHECK_AGAINST_KEY = "MiniCheck against the key"
PAPERS_MEASURE_RE = f"MiniCheck|{PAPERS_PRECISION}"

# Judge calls
JUDGE_PLAIN_CALL = "plain call"
JUDGE_CALL_WITH_PASSAGES = "call with passages"

# The 39 (F13: these words on every plate and legend; the data key stays)
OUT_OF_SCOPE_QUESTIONS = "out-of-scope questions"
NOT_ANSWERABLE_KEY = "not_answerable"

# The 10
FALSE_PREMISE_QUESTIONS = "false-premise questions"

# Strategies
SINGLE_PASS = "single pass"
MULTI_HOP = "multi-hop"
VERIFIED_PASS = "verified pass"
RLM_5 = "RLM-5"
RLM_10 = "RLM-10"
RLM_20 = "RLM-20"
STRATEGIES = (SINGLE_PASS, MULTI_HOP, VERIFIED_PASS, RLM_5, RLM_10, RLM_20)

# Long RLM names, on the plates listed (Supplementary numbers D302's, 7 November 2026: S17 was S15, S8 was S7, S7 was S8;
# under D257 S15 was S6, S7 was S8, S8 was S10; the depth fit, S11 before 2 November, is removed). MENTORI_RLM and
# PACKAGE_RLM are the bare keys of S8 (supp C2).
# PACKAGE_RLM prints "Zhang RLM", the RLM package of Zhang et al. (ref 25), capital Z also at a sentence start
# (Valerio, 5 November 2026, Q2: "package RLM" became "Zhang RLM" in every figure); the constant's name stays.
# MENTORI_RLM prints "RLM", our implementation's one name in text and figures (D282, Valerio, 6 November 2026: "our
# implementation is called RLM and the one from the authors' package is called Zhang RLM. then we remove every version of
# Mentor::i RLM from text and figures"; it replaces D272's "Mentor::i RLM"); the constant's name, data ids and run names stay.
# MENTORI prints the system's name (Valerio, 5 November 2026: "change everywhere Mentori as Mentor::i. Also in the figures.")
MENTORI = "Mentor::i"
MENTORI_RLM = "RLM"
PACKAGE_RLM = "Zhang RLM"
MENTORI_RLM_N = MENTORI_RLM + "-{n}"
PACKAGE_RLM_N = PACKAGE_RLM + "-{n}"
MENTORI_RLM_PLATES = ("3a", "3b", "S17")   # S17 (S15 before D302, S6 before D257): Valerio's note, 2 November 2026, beside Zhang RLM-n
PACKAGE_RLM_PLATES = ("3a", "S17", "S8", "S7")

# Authors' name: only where NEVER's exception allows it. S7's title (S8 before D302, S10 before D257) spells it out (supp.md section 9)
AUTHORS_RLM = "authors' RLM"

# Matched budget ("matched budget" on 3a)
SINGLE_PASS_AT_MATCHED_BUDGET = "single pass at matched budget"
MATCHED_BUDGET = "matched budget"

# Figure 4 rows
NO_RETRIEVAL = "no retrieval"
NAIVE_RAG = "naive RAG"
FULL_PIPELINE = "full pipeline"
NO_ANALYSER = "no analyser"
NO_PLANNER = "no planner"
NO_SUPERVISOR = "no supervisor"
NO_SYNTHESIZER = "no synthesizer"
ROUTING_FIX = "routing fix"
ALWAYS_DISTIL = "always distil"
ALWAYS_DISTIL_F1 = "always distil F1"
FIGURE_4_ROWS = (NO_RETRIEVAL, NAIVE_RAG, FULL_PIPELINE, NO_ANALYSER, NO_PLANNER, NO_SUPERVISOR, NO_SYNTHESIZER,
                 ROUTING_FIX, ALWAYS_DISTIL, ALWAYS_DISTIL_F1, RLM_10)

# Model groups
GEMINI = "Gemini"
OPEN_WEIGHT = "open-weight"

# People
RATERS = "Raters"
RATER_ONE_RATER_MODE = "Rater"

# Colour word: one l in a legend, two as the key of house_style's OKABE table
VERMILION = "vermilion"
OKABE_VERMILLION_KEY = "vermillion"

# The places a form can be printed in. TITLE is the title of a legend, which is a part of LEGEND
PLATE = "plate"
LEGEND = "legend"
TITLE = "legend title"


@dataclass(frozen=True)
class Never:
    row: str                      # the row of A4's table ("Thing" column)
    form: str                     # the words
    pattern: str                  # regular expression, case ignored; \s+ between words, so a line break matches
    places: tuple = (PLATE, LEGEND)
    allowed: tuple = ()           # (plate, place) pairs where the form stands, the plate as "S1"


NEVER = (
    Never("The Papers measure", "Paper precision", r"\bpaper\s+precision\b"),
    # "alone": the name with nothing after it saying what it is checked against. "against the key" and "against
    # papers" both name a reference; "MiniCheck precision" does not (fig1 C3). A legend may name MiniCheck.
    Never("MiniCheck", "MiniCheck", r"\bMiniCheck\b(?!\s+against\b)", places=(PLATE,)),
    # the hyphen, the two Unicode hyphens, or a space; the data key's underscore does not match
    Never("The 39", "not-answerable", r"\bnot[\s\-\u2010\u2011]+answerable\b"),
    # the short form and S7's spelled-out form are one name: S7's title (S8 before D302, S10 before D257), the row's exception, uses the long one
    Never("Authors' name", AUTHORS_RLM, r"\bauthors['\u2019]?\s+(?:RLM|recursive\s+language\s+model)\b",
          allowed=(("S1", PLATE), ("S1", LEGEND), ("S7", TITLE))),
    Never("Figure 4 rows", "analyser off", r"\banalyser\s+off\b"),
    Never("Figure 4 rows", "distiller on every step", r"\bdistiller\s+on\s+every\s+step\b"),
    Never("Model groups", "cloud", r"\bcloud\b", places=(PLATE,)),
    Never("Colour word", OKABE_VERMILLION_KEY, r"\bvermillion\b", places=(LEGEND,)),
)
