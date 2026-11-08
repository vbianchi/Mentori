#!/usr/bin/env python3
"""S496 - Supplementary Figure 1, the experiment graph of the revised study (D160 (9), Q24: "Yes, build it now").

WHY. The submitted Supplementary Figure 1 drew one box per experiment with its design and its count, April's design,
read left to right: the corpus, the foundation choices (retrieval set-up, models), the core experiments, then scale,
ablation and replication built on them. D160 (9) asks for the same picture for the revised experiments: one box per
experiment, answers as the unit, each box's design and answer count read from S492's registry and
experiments/draws.csv, the strategy replication (T2) marked as running, and arrows that mean "uses the output or the
choice of". Its boxes and arrows go to Valerio for review (D160 (9)); they are the two tables BOXES and ARROWS below.
Valerio, 28 Oct: the plate shows no progress (no answer count, no "running" or "not started", no dashed box): a box
gives the experiment, its design and its draws. The counts and status words stay in the data workbook's boxes sheet
and in the provenance, and reproduce-first still checks them against the registry.
D183 FD6 B (Valerio, 30 Oct): Figure 1's draws block moves here, so Figure 1 fits 170 mm. It is drawn as a key under
the graph (DRAWS KEY): one line per draw kind a box uses, its name and what it means, in Figure 1's words
(figure1_provenance.json "draw_kinds", written by S456 from its DRAW_KINDS and RUN_ONCE); each box already names its
own kind, so the key does not list the experiments again. The retrieval optimisation box gains its draws, "1 run"
(Figure 1's "1 run" settings are that box's embedding models, chunkings and search strategies).
D196 (1 Nov): G10 (flat wide call) and G11 (short-passage single pass) join column 5 with their arrows. FF5: a box also prints
its LLM calls as its last line, from S520's summary, read only once SHA256SUMS lists all of S520's frozen files
(load_s520()); until then no box prints a count, the calls column of the boxes sheet is blank and the stamp is the
answers stamp. RO and MS print none (their runs are kept and have no call logs), and T3 prints none while its count is 0
(fig1 C9).
D201 Q6 (Valerio, 2 November 2026, yes): "answers" replaces "evaluations" in the legend, the stamp and the count words,
which amends D139's word and not its count. "Evaluation corpus" is a name and stays.
Box G9 prints "Always distil (stress)" (PLATE_NAMES): draws.csv's name is a form figure_names.NEVER refuses, and
figure_names_test cannot see it here, as the wrapped name is two text calls. The sheets keep draws.csv's name.

ONE COMMAND (D155), from the repository root:

    uv run --frozen python scripts/S496_supp_fig1_experiment_graph.py [--out DIR]
    uv run --frozen python scripts/S448_figure_rules_check.py --figure 1 --supplementary \
        --dir findings/figures_provisional/supp_fig1

writes into findings/figures_provisional/supp_fig1/ (or --out; files of an earlier state deleted first):
  Supplementary Figure 1 (provisional, n of m).{pdf,svg,png}   one page, [page] width_double_mm wide, at most
        height_max_mm high; every text at [type] font_min_pt in [type] font_families[0]; black text, column labels in
        a grey that reaches [type] contrast_min_ratio; boxes and arrows in black at 0.6 pt, every box solid;
        hs.check_figure_colours checks the colours, then S457.finish_plate (build order F4) refuses a text off the page or
        on another and writes the PDF, the SVG and the PNG, the PDF rasterised by MuPDF at 600 dpi (S448 R7)
  Supplementary Figure 1 data (provisional, n of m).xlsx   sheets "Supp. Fig. 1 lines" (one row per printed line),
        "Supp. Fig. 1 boxes" (one row per box: design, draws, answers, and the draws.csv and registry text beside
        them), "Supp. Fig. 1 arrows" (one row per arrow, with its basis); no write time, fixed zip dates
  Supplementary Figure 1 data caption (provisional, n of m).md, legend_draft.md,
  supplementary_figure1_numbers.json (every sheet, and every printed line tied to its sheet row, S448 R8 (6)),
  supplementary_figure1_provenance.json (each input's sha256, the figure lock's, every output's)
"n of m": the experiments with answers counted, of all experiments (draws.csv's rows); once S520's output is frozen,
the experiments with calls printed.

INPUTS, all committed:
  findings/recompute/S492_answer_registry/registry.json   the answers stored per experiment (S492's unit), the two
        experiments kept from April with S13's counts, and which experiment is not counted yet and why
  experiments/draws.csv     one row per experiment: its name, plan row, design, draws and status; only these are
        read, the status by its first word only (the rest of it is a progress note that changes with every
        dashboard update), and the provenance records the sha256 of exactly those values, not of the file (D155)
  findings/figures_provisional/fig1/figure1_provenance.json   Figure 1's design facts and rows ("design", "rows"), so
        each box's design is the one Figure 1 draws (E8), and its draw kinds ("draw_kinds", D183 FD6 B); S494 runs this
        after Figure 1 and S492
  findings/recompute/frozen_inputs/SHA256SUMS   read only for its lines under findings/recompute/S520_inputs/, the files
        S520's freeze writes (S520_FROZEN). Some of them listed and not all is refused
  findings/recompute/S520_llm_calls/summary.json   read only when SHA256SUMS lists all of them, and refused unless its
        provenance gives those files' sha256: "s1_boxes" (calls per box), "figure1_legend_total", "by_role". Committed is
        not enough: S520's report cannot be rerun from the repository until its inputs are frozen (fig1, Readers still
        to build)
  experiments/rlm_ref/pyproject.toml   read only for its pin "rlms==<version>", the package RLM version the legend
        names (D228)
REPRODUCE FIRST (README.md:75-79): nothing is written unless draws.csv's experiments are exactly the registry's
experiments plus its two kept from April, once each, and the counts this script draws sum to the registry's own totals
(stored_new_counted, kept, total_counted). D201 Q2 (Valerio, 2 November 2026, yes; fig1:210): once S520's summary is
read, box_sum_check() refuses unless the numeric s1_boxes plus the named rows of SUM_EXCEPTIONS add up to
figure1_legend_total, and S520's "not in a box" row holds exactly those named rows and nothing else. S508's 59 calls
(R49) sit in no box, so they are one such row until Valerio rules where they sit: the row goes into the boxes sheet, the
provenance and the printed reproduction, never into another box. While SHA256SUMS lists no S520 file no summary is read,
so this gate does not run on the build; the test runs it on made-up summaries. The legend says the boxes add up only
when they do, which is never while an exception stands. LAYOUT GATE: no arrow passes through a box other than its two ends, no two
arrows of different sources run along the same line, and the plate fits the page; else nothing is written (exit 2).

No model call; reads files only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro as FR  # noqa: E402
import figure_names as fn  # noqa: E402

N = 1
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig1"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
REGISTRY = ROOT / "findings" / "recompute" / "S492_answer_registry" / "registry.json"
DRAWS = ROOT / "experiments" / "draws.csv"
RLM_PYPROJECT = ROOT / "experiments" / "rlm_ref" / "pyproject.toml"   # package RLM's pinned rlms version (D228)
FIG1_PROV = ROOT / "findings" / "figures_provisional" / "fig1" / "figure1_provenance.json"
SUMS = ROOT / "findings" / "recompute" / "frozen_inputs" / "SHA256SUMS"
S520_SUMMARY = ROOT / "findings" / "recompute" / "S520_llm_calls" / "summary.json"
S520_INPUTS = "findings/recompute/S520_inputs/"   # the prefix of S520's frozen files in SHA256SUMS (fig1 Readers)
S520_FROZEN = ("laptop_gates.json", "s520_beelink.json", "s520_laptop.json", "s520_studio.json")   # what S520's freeze
# writes (S520_llm_calls.py freeze), which report --frozen records in summary.json's provenance inputs_sha256
NOT_IN_BOX = "not in a box"                      # S520.NO_BOX, the s1_boxes row of calls no box holds
SUM_EXCEPTIONS = {"R49": "Judge on the 49 rated answers"}   # D201 Q2: S520's experiment id and draws.csv-style name of
# calls that sit in no box, each to stay here until Valerio rules where it sits (S508's 49 answers and 10 rechecks)
DRAWN_COLUMNS = ("experiment", "plan_row", "design", "draws", "status")   # the draws.csv fields this script reads
# (the status by its first word only, status_word(): the rest is the dashboard's progress note)

FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
SI_LABEL = FLOCK["files"]["supplementary_name"].format(n=N)
SIDE = f"supplementary_figure{N}"
PT = float(FLOCK["type"]["font_min_pt"])
FONT = FLOCK["type"]["font_families"][0]
CONTRAST_MIN = float(FLOCK["type"]["contrast_min_ratio"])
LINE_PT = max(0.6, float(FLOCK["lines"]["line_min_pt"]))
W_MM = float(FLOCK["page"]["width_double_mm"])
H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
MM_PER_PT = 25.4 / 72
LEAD = PT * MM_PER_PT * 1.18          # line pitch, mm
PAD = 1.1                             # mm inside a box, each side
MARGIN = 1.0                          # mm, page edge to the outer boxes
CHANNEL = 7.0                         # mm between two columns, where the arrows turn
VGAP = 4.2                            # mm between two boxes of a column
KEY_GAP = 5.0                         # mm between the lowest box and the draws key (D183 FD6 B)
KEY_COL = 3.0                         # mm between a draw kind's name and its meaning in the key
HEAD = 1.4                            # arrowhead length, mm
SHEETS = {"lines": f"Supp. Fig. {N} lines", "boxes": f"Supp. Fig. {N} boxes", "arrows": f"Supp. Fig. {N} arrows"}
INK, FILL_CORPUS = "#000000", "#EEEEEE"

# ---------------------------------------------------------------------------------------------------------------
# The graph (D160 (9): for Valerio's review). A box: (id, plan row, draws.csv experiment, column). The corpus is not
# an experiment and has no draws.csv row. The columns follow the submitted figure's reading order.
# ---------------------------------------------------------------------------------------------------------------
COLUMNS = ["Corpus and choices", "Core experiments", "Built on the core", "Ablation",
           "Replication and reuse"]   # one line each (5 Nov: the three added boxes need the room)
BOXES = [("RO", "", "Retrieval optimisation", 0), ("CORPUS", None, None, 0), ("MS", "", "Model selection", 0),
         ("G1", "G1", "Generation strategies", 1), ("G3B", "G3", "No retrieval and naive RAG", 1),
         ("G5", "G5", "Retrieval depth", 1), ("T1", "T1", "Retrieval depth, local models", 1),
         ("S2", "S2", "Code generation", 1),
         ("G2", "G2", "Matched-budget arm", 2), ("G4", "G4", "Corpus scaling", 2),
         ("G6C", "G6", "Package RLM at caps 5 10 20", 2), ("G6D", "G6", "Package RLM depth caps", 2),
         ("G9", "G9", "Distiller on every step (stress)", 3), ("G3A", "G3", "Pipeline ablation", 3),
         ("T3C", "T3", "Component benchmarks", 3), ("T3D", "T3", "Distiller intervention", 3),
         ("T2", "T2", "Strategy replication", 4), ("I2", "I2", "Plant-science reuse demonstration", 4),
         ("G11", "G11", "Short-passage single pass", 4), ("G10", "G10", "Flat wide call", 4),
         # Valerio, 5 Nov (Q1, "yes"): the RLM ablation, its gemma3 run and the judge with evidence
         ("S18F", "S12", "Judge with evidence", 2), ("G17", "G17", "RLM ablation", 3),
         ("G19", "G19", "RLM ablation, gemma3:27b", 4)]
# A box's name on the plate where draws.csv's name is a form figure_names.NEVER refuses (build order A4). The plate takes
# Figure 4's name for the row; every sheet's experiment column keeps draws.csv's.
PLATE_NAMES = {"G9": f"{fn.ALWAYS_DISTIL.capitalize()} (stress)",
               # Valerio, 5 Nov: Zhang RLM in every figure; draws.csv keeps its experiment names
               "G6C": "Zhang RLM at caps 5, 10 and 20", "G6D": "Zhang RLM at the depth caps",
               # N4b (proposal): the paper's Oxford spelling (manuscript: "retrieval optimization", 2 of 2 uses)
               "RO": "Retrieval optimization"}
# D291 (Valerio, 7 Nov): the plate prints the paper's name for the generation model; the box sheet's design column and
# draws.csv keep the API id (only the drawn line, sheet "lines", carries the printed name)
GEN_DISPLAY = {"gemini-3-flash-preview": "gemini-3-flash"}
# An arrow from A to B: B uses the output or the choice of A. (from, to, basis)
ARROWS = [
    ("CORPUS", "RO", "the retrieval settings were chosen on the corpus (submitted Supplementary Figure 1)"),
    ("CORPUS", "MS", "the models were chosen on the corpus's questions (submitted Supplementary Figure 1)"),
    ("RO", "G1", "the index every strategy searches is built with the retrieval settings kept from April "
                 "(submitted Supplementary Figure 1)"),
    ("RO", "G3B", "naive RAG searches with the same retrieval settings (submitted Supplementary Figure 1)"),
    ("MS", "G1", "the generation model, gemini-3-flash-preview (submitted Supplementary Figure 1)"),
    ("MS", "T1", "the local models (submitted Supplementary Figure 1: model selection to retrieval depth)"),
    ("MS", "S2", "the code-generation models (submitted Supplementary Figure 1)"),
    ("G1", "G2", "single pass given each question's passage count from G1's RLM-10 call records (exp_01 "
                 "matched_budget; experiments/runner/matched_budget.py)"),
    ("G1", "G4", "corpus scaling runs the same six strategies (S456: exp_02 CONFIG_NAMES equal exp_01's)"),
    ("G1", "G6C", "package RLM is run at the caps of G1's RLM-5, RLM-10 and RLM-20 (run_rlm_ref.py FIGURE2_CAPS)"),
    ("G1", "G3A", f"Figure {fn.FIG_PIPELINE} sets the pipeline beside G1's RLM-10 answers, which G3 does not run again "
                  "(G3_runs/README.md: rlm_10 not run, Figure 4 uses G1's RLM-10 answers)"),
    ("G1", "T2", "T2 runs G1's six strategies on G1's index with other generation models (check_t2.py CONFIGS, "
                 "t2_lib.sh)"),
    ("G1", "I2", "the reuse demonstration runs G1's six strategies (D160 (14), Q-I2b O-b)"),
    ("G5", "T1", "T1's turn caps are a subset of G5's (S456 check on T1_runs/assignment.toml)"),
    ("G5", "G6D", "package RLM's depth caps with caps 5, 10 and 20 are G5's ten caps (S456: FIGURE2_CAPS + "
                  "DEPTH_SWEEP_CAPS = exp_06 DEFAULT_DEPTHS)"),
    ("G6C", "G6D", "the depth curve of package RLM takes its caps 5, 10 and 20 from these runs, the 86 "
                   "questions kept (S459: b4_rlm_ref__cap<c>__all135 for caps 5, 10, 20)"),
    ("G3A", "G9", "the distiller never ran in the full pipeline's draw 1, so the stress set-ups run it on every step "
                  "(D154 as amended; draws.csv G9 basis, Q82)"),
    ("G3A", "T3C", "the components benchmarked are the orchestrator's (submitted Supplementary Figure 1)"),
    ("T3C", "T3D", "the distiller prompts are varied on the distiller's benchmark items (submitted Supplementary "
                   "Figure 1)"),
    ("G1", "G11", "paired with G1 by question, on G1's index (D196)"),
    ("G4", "G10", "its top_k comes from G4's token counts and it pairs with G4 by question (D196; S519)"),
    ("G1", "G17", "the control is G1's RLM-10 on today's code, and G1's RLM-10 draw 1 checks what the code changed (D240)"),
    ("G6C", "G17", "the package arm is G6's cap-10 answers, stored and judged (D240, D249 O1)"),
    ("G17", "G19", "the same three switches on gemma3:27b (D249 O2)"),
    ("G1", "S18F", "judges G1's draw-1 answers with no source, their own papers or unrelated papers (D107; S18f)"),
]


class Refused(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def ints(s: str) -> list:
    return [int(x) for x in re.findall(r"\d+", str(s).replace(",", ""))]


# ---------------------------------------------------------------------------------------------------------------
# Inputs and the box texts
# ---------------------------------------------------------------------------------------------------------------
def load():
    reg = json.loads(REGISTRY.read_text())
    rows = list(csv.DictReader(io.StringIO(DRAWS.read_text(), newline="")))
    prov = json.loads(FIG1_PROV.read_text())
    return reg, rows, prov


def s520_listed() -> dict:
    """{file name: sha256} of SHA256SUMS's lines under S520_INPUTS."""
    pairs = (ln.split(None, 1) for ln in SUMS.read_text().splitlines() if ln.strip())
    return {path.strip()[len(S520_INPUTS):]: sha for sha, path in pairs if path.strip().startswith(S520_INPUTS)}


def s520_frozen() -> bool:
    """True when SHA256SUMS lists every file of S520_FROZEN, False when it lists none; refused in between, a part freeze."""
    listed = s520_listed()
    left = [f for f in S520_FROZEN if f not in listed]
    if listed and left:
        raise Refused(f"SHA256SUMS lists S520 files {sorted(listed)} and not {left}")
    return bool(listed)


def load_s520() -> dict | None:
    """S520's summary once its output is frozen, else None: no count line, and the answers stamp. Refused when the
    summary's provenance does not give the listed files' sha256 (a summary not written by report --frozen from them), a
    machine went unread or a box has no entry in s1_boxes (S520 maps G10 and G11 to their boxes before the freeze)."""
    if not s520_frozen():
        return None
    listed = s520_listed()
    s = json.loads(S520_SUMMARY.read_text())
    written_from = s.get("provenance", {}).get("inputs_sha256", {})
    stale = [f for f in S520_FROZEN if written_from.get(f) != listed[f]]
    if stale:
        raise Refused(f"S520's summary was not written from the frozen {stale}: run its report --frozen")
    if s.get("machines_not_read"):
        raise Refused(f"S520's summary did not read {s['machines_not_read']}")
    missing = [b[0] for b in BOXES if b[1] is not None and b[0] not in s["s1_boxes"]]
    if missing:
        raise Refused(f"S520's s1_boxes has no entry for {missing}")
    return s


def calls_by_box(s520) -> dict:
    """{box id: calls} from S520's "s1_boxes" (an int, or a word for a kept box), or {} with no frozen summary."""
    return {} if s520 is None else dict(s520["s1_boxes"])


def box_sum_check(s520) -> dict:
    """D201 Q2 (fig1:210): the boxes must add up to the total. Returns {"boxes", "total", "exceptions": [{exp_id,
    experiment, calls}]}. Refused when the numeric s1_boxes, the row NOT_IN_BOX included, do not sum to
    figure1_legend_total, when a key of s1_boxes names no box, or when NOT_IN_BOX is not exactly the sum of the named
    SUM_EXCEPTIONS (so an unmapped experiment such as G10 stays a refusal, and a named row cannot go unreported)."""
    sb, total = s520["s1_boxes"], s520["figure1_legend_total"]
    ids = {b[0] for b in BOXES}
    strange = sorted(k for k in sb if k not in ids and k != NOT_IN_BOX)
    if strange:
        raise Refused(f"S520's s1_boxes names {strange}, which are no box of BOXES")
    in_boxes = sum(v for k, v in sb.items() if k != NOT_IN_BOX and isinstance(v, int))
    outside = sb.get(NOT_IN_BOX, 0)
    if in_boxes + outside != total:
        raise Refused(f"the boxes hold {in_boxes:,} calls and {outside:,} sit in no box, not the total {total:,}")
    rows = []
    for e, name in SUM_EXCEPTIONS.items():
        got = (s520.get("by_experiment", {}).get(e) or {}).get("calls")
        if not got:
            raise Refused(f"SUM_EXCEPTIONS names {e}, and S520's by_experiment gives it no calls: rule it out by name")
        rows.append({"exp_id": e, "experiment": name, "calls": got})
    named = sum(r["calls"] for r in rows)
    if outside != named:
        raise Refused(f"{outside:,} calls sit in no box, and the named exceptions {sorted(SUM_EXCEPTIONS)} hold "
                      f"{named:,}: {outside - named:,} calls have neither a box nor a name")
    return {"boxes": in_boxes, "total": total, "exceptions": rows}


def exception_rows(check, cols) -> list:
    """The boxes sheet's row for each named exception: box NOT_IN_BOX, its experiment, its calls, the rest blank."""
    out = []
    for r in check["exceptions"]:
        row = dict.fromkeys(cols, "")
        row.update(box=NOT_IN_BOX, experiment=r["experiment"], calls=r["calls"], count_kind="calls in no box (D201 Q2)")
        out.append([row[c] for c in cols])
    return out


def calls_line(calls) -> str | None:
    """A box's count line: "{n:,} calls" for a count above 0 (fig1 C9), else None."""
    return f"{calls:,} calls" if isinstance(calls, int) and calls > 0 else None


def status_word(status: str) -> str:
    """draws.csv's status as this script reads it: its first word ("running", "open", "done", "draw")."""
    return re.split(r"[ (]", (status or "").strip(), maxsplit=1)[0]


def drawn_fields_sha(rows) -> str:
    """sha256 of the draws.csv values this script reads (DRAWN_COLUMNS, the status by its first word), one
    tab-separated line per row. Audit 27 Oct (fig1 review): the whole status field was hashed until then, so each
    dashboard update of T2's progress note changed the provenance file (D155)."""
    return sha256_bytes("".join("\t".join(status_word(r[c]) if c == "status" else r[c] for c in DRAWN_COLUMNS)
                                + "\n" for r in rows).encode())


def draw_kind(text: str) -> str | None:
    """draws.csv's draws column as the plate says it: "3 draws", "1 + 2 draws" (D98's text), "1 draw", or None."""
    t = (text or "").strip()
    if t == "3":
        return "3 draws"
    if t.startswith(("1, and 2 and 3 on a fixed third", "1 on 135 questions, 2 and 3 on a fixed third")):
        return "1 + 2 draws"
    if re.fullmatch(r"1( \(.*\))?", t):
        return "1 draw"
    if t in ("", "0"):
        return None
    raise Refused(f"draws.csv draws {t!r}: not '3', D98's text or '1'")


def reproduce(reg, rows) -> list:
    """Known numbers first: draws.csv's experiments are the registry's plus the two kept from April, once each; every
    box's experiment is one of them and every experiment has a box; the counts sum to the registry's totals."""
    today = reg["today"]
    kept = today["kept_from_april"]
    exps = [(e["plan_row"], e["experiment"]) for e in today["experiments"]] + [("", k) for k in kept]
    csv_exps = [(r["plan_row"], r["experiment"]) for r in rows]
    if sorted(csv_exps) != sorted(exps) or len(set(csv_exps)) != len(csv_exps):
        raise Refused(f"draws.csv's experiments {sorted(csv_exps)} are not the registry's {sorted(exps)}")
    boxed = [(b[1], b[2]) for b in BOXES if b[1] is not None]
    if sorted(boxed) != sorted(exps):
        raise Refused(f"BOXES {sorted(boxed)} are not draws.csv's experiments {sorted(exps)}")
    counted = sum(e["stored"] for e in today["experiments"] if e["counted"])
    checks = [("answers stored and counted (registry stored_new_counted)", counted, today["stored_new_counted"]),
              ("answers kept from April (registry kept_from_april)", sum(kept.values()),
               reg["anchor"]["kept"] and sum(reg["anchor"]["kept"].values())),
              ("total counted (registry total_counted)", counted + sum(kept.values()), today["total_counted"]),
              ("not counted (registry not_counted)",
               sorted(f"{e['experiment']} ({e['plan_row']})" for e in today["experiments"] if not e["counted"]),
               sorted(today["not_counted"]))]
    bad = [f"{w}: {g!r}, registry {k!r}" for w, g, k in checks if g != k]
    if bad:
        raise Refused("reproduce-first failed, nothing written: " + "; ".join(bad))
    ids = {b[0] for b in BOXES}
    for a, b, _ in ARROWS:
        if a not in ids or b not in ids:
            raise Refused(f"arrow {a} -> {b} names a box that is not in BOXES")
    return [f"{w}: {g if not isinstance(g, list) else len(g)} = registry" for w, g, _ in checks]


def plain_design(text: str) -> str:
    """draws.csv's design as the plate says it: no decision or script reference ("(S18f, key v2.5)"), × for x."""
    return re.sub(r"\s*\((?:design to come|D\d+|Q\d+|S\d+[a-z]?\b)[^)]*\)", "", text).replace(" x ", " × ")


def g10_design(r) -> list:
    """G10's design lines: draws.csv's text, then which index takes draw 1 only. Refused unless draws.csv still gives 3
    indexes and draws 2 and 3 on two of them (D196), the facts the second line states."""
    design = plain_design(r["design"])
    if not design.startswith("3 indexes ") or not r["draws"].endswith(" on two indexes"):
        raise Refused(f"G10: design {r['design']!r}, draws {r['draws']!r}: not 3 indexes with draws 2 and 3 on two")
    return [design, "third index: draw 1 only"]


def i2_design(r, n_strategies: int) -> list:
    """I2's design line: Figure 1's strategy count, then draws.csv's words after "strategies x" (draws.csv says "Figure
    2's six strategies", the old figure number)."""
    m = re.fullmatch(r".*\bstrategies x (.+)", r["design"])
    if not m:
        raise Refused(f"I2: design {r['design']!r} has no 'strategies x'")
    # N4b (proposal): the key's internal name ("key PB v1.1") is not printed; the legend names the five papers
    rest = re.sub(r",\s*key PB v[0-9.]+$", "", m.group(1))
    return [f"{n_strategies} strategies × {rest}"]


# The maker of each language model family (Valerio, 5 Nov, Q5: the models of the whole study by maker); a model whose
# name starts with none of these is refused, so a new family is named here before it is counted.
MAKERS = {"claude": "Anthropic", "deepseek": "DeepSeek", "devstral": "Mistral AI", "gemini": "Google", "gemma": "Google",
          "glm": "Z.ai", "gpt-oss": "OpenAI", "qwen": "Alibaba", "nemotron": "NVIDIA", "olmo": "Ai2", "llama": "Meta"}


def models_line() -> list:
    """The Model selection box (Valerio, 5 Nov, Q5): the language models that made a call in this study, from S520's
    summary by_model (the call logs of every machine; "?" is a call with no model and is not a model), and their makers."""
    by_model = json.loads(S520_SUMMARY.read_text())["by_model"]
    models = sorted(m for m, v in by_model.items() if m != "?" and v["calls"] > 0)
    makers = set()
    for m in models:
        k = next((k for k in MAKERS if m.startswith(k)), None)
        if k is None:
            raise Refused(f"model {m!r} has no maker in MAKERS")
        makers.add(MAKERS[k])
    return [f"{len(models)} language models from {len(makers)} makers"]


def designs(prov, rows) -> dict:
    """Each box's design lines, from Figure 1's design facts and rows (the design Figure 1 draws), or for G10 and I2
    from draws.csv's rows; None where neither applies (the box then takes draws.csv's design text as it stands)."""
    f = prov["design"]
    by_row = {r["plan_row"]: r for r in rows}
    lv = {r["axis"]: r for r in prov["rows"]}
    nq = f["n_questions"]
    g1 = ints(lv["Generation strategy"]["levels_as"])[0]
    emb, chunk, search = (ints(lv[a]["levels_as"])[0] for a in ("Embedding model", "Chunking", "Search strategy"))
    base = [c for c in f["system"] if c not in ("full_orchestrator", "rlm_10")]
    t2 = f["t2_generators"]
    return {
        # Valerio, 5 Nov (Q6): the whole question set on the 50 core papers, and the distractors; (Q7) no "the
        # submitted study's runs, not run again"; (Q5) Model selection gives the models of the whole study
        "CORPUS": [f"{f['per_size'][str(max(f['core']))] if str(max(f['core'])) in f['per_size'] else f['per_size'][max(f['core'])]} "
                   f"questions on {max(f['core'])} core papers", f"{max(f['core']) * max(f['noise'])} distractor papers"],
        "RO": [f"{emb} embedding models, {chunk} chunkings, {search} search strategies"],
        "MS": models_line(),
        "G1": [f"{g1} strategies × {nq} questions", f"{f['gen_model']}"],
        "G2": [f"single pass at matched budget × {nq} questions"],
        "G6C": [f"{fn.PACKAGE_RLM} at {len(f['cap2'])} turn caps × {nq} questions"],
        "G3B": [f"{len(base)} baselines × {nq} questions"],
        "G5": [f"{fn.MENTORI_RLM} at {len(f['depths'])} turn caps × {f['n86']} questions"],
        "T1": [f"{fn.MENTORI_RLM} at {len(f['t1_caps'])} turn caps × {len(f['t1_models'])} local models × "
               f"{f['t1_questions']} questions"],
        "G6D": [f"{fn.PACKAGE_RLM} at {len(f['capd'])} more turn caps × {f['n86']} questions"],
        "G4": [f"{len(f['core']) * len(f['noise'])} indexes × {f['g4_strats']} strategies × the questions in scope"],
        "G3A": [f"{len(f['orch_run'])} orchestrator set-ups × {nq} questions"],
        "G9": [f"{len(f['stress'])} stress set-ups × {nq} questions"],
        "S2": [f"{f['cg']} strategies × {f['variants']} model variants × {f['n_ops']} operations"],
        "T2": [f"{len(t2)} generation models × {f['t2_configs']} strategies × {nq} questions"],
        "G10": g10_design(by_row["G10"]),
        "I2": i2_design(by_row["I2"], g1),
    }


def draw_kinds(prov) -> list:
    """Figure 1's draw kinds (D183 FD6 B): [{key, name, means, settings}], in Figure 1's order, from
    figure1_provenance.json "draw_kinds" (S456 DRAW_KINDS and RUN_ONCE); refused when absent or when a name this script
    reads draws.csv's text as (draw_kind()) is not among them."""
    dk = prov.get("draw_kinds")
    if not dk or not all({"key", "name", "means"} <= set(d) for d in dk):
        raise Refused(f"{rel(FIG1_PROV)} records no draw_kinds (S456 since D183 FD6 B): run S456 first")
    missing = {"3 draws", "1 + 2 draws", "1 draw"} - {d["name"] for d in dk}
    if missing:
        raise Refused(f"{rel(FIG1_PROV)} draw_kinds lack {sorted(missing)}, which draw_kind() writes")
    return dk


def t2_draws(prov) -> str:
    """The T2 box's draws on the plate: the common kind only (Valerio, 5 Nov: a shorter box; the other kinds go to the
    legend, t2_draws_full())."""
    return t2_draws_full(prov).split("; ")[0]


def t2_draws_full(prov) -> str:
    """T2's draws from Figure 1's facts (check_t2.py's rule): the common kind, then the generators of each other kind
    (D175 Q3 and D176: "rlm45", a local generator's RLM set-ups on D98's third at every draw, its other set-ups on all
    135). Each kind by its name in Figure 1's draw_kinds."""
    name = {d["key"]: d["name"] for d in draw_kinds(prov)}
    kinds = {}
    for m, k in prov["design"]["t2_draws"].items():
        if k not in name:
            raise Refused(f"T2 {m}: draw kind {k!r} is not in Figure 1's draw_kinds")
        kinds.setdefault(name[k], []).append(m)
    if len(kinds) == 1:
        return next(iter(kinds))
    (k_many, _), *rest = sorted(kinds.items(), key=lambda kv: -len(kv[1]))
    # "<kind> for <models>", by kind: "claude-haiku-4-5 3 draws" read as a range to S448 R9
    return "; ".join([k_many] + [f"{k_few} for {' and '.join(few)}" for k_few, few in sorted(rest)])


def box_table(reg, rows, prov, calls=None) -> list:
    """One dict per box: its texts (name, design lines, draws, count) and the values beside them. calls: {box id: calls}
    from calls_by_box(), empty until S520's output is frozen."""
    calls = calls or {}
    today = reg["today"]
    by_exp = {(e["plan_row"], e["experiment"]): e for e in today["experiments"]}
    kept = today["kept_from_april"]
    csv_by = {(r["plan_row"], r["experiment"]): r for r in rows}
    des = designs(prov, rows)
    out = []
    for bid, plan_row, exp, col in BOXES:
        if plan_row is None:
            out.append({"id": bid, "plan_row": "", "experiment": "Evaluation corpus", "column": col,
                        "name": "Evaluation corpus", "design": des["CORPUS"], "draws": None, "count": None,
                        "answers": None, "calls": None, "count_kind": "corpus", "dashed": False, "csv_design": "",
                        "csv_draws": "", "csv_status": "", "registry_basis": ""})
            continue
        r = csv_by[(plan_row, exp)]
        design = des.get(bid) or [plain_design(r["design"])]
        if exp in kept:
            n, kind, count = kept[exp], "answers, kept from April", f"{kept[exp]:,} answers"
            basis = "registry today.kept_from_april (S13's count)"
        else:
            e = by_exp[(plan_row, exp)]
            basis = e["basis"]
            if not e["counted"]:
                # not counted: draws.csv's status word must be the one the registry read (S492 writes "<word>
                # (experiments/draws.csv status), not frozen ..."), and a word of a run that has started. "running"
                # only until 30 Oct, when I2's word became "scored" (90 of 90 answers judged, records not frozen)
                word = status_word(r["status"])
                if word in ("", "open", "planned") or not basis.startswith(f"{word} (experiments/draws.csv status)"):
                    raise Refused(f"{exp} is not counted (registry: {basis[:60]!r}) but draws.csv's status is "
                                  f"{r['status'][:40]!r}")
                n, kind, count = None, word, word
            elif e["stored"] == 0 and e.get("special_case") and status_word(r["status"]) not in ("", "open", "planned"):
                # D281: an experiment that ran and stores no answer of its own (S12: judge calls on G1's answers);
                # counted at 0, its reason in the registry's special_case
                n, kind, count = 0, "answers", "no answers of its own"
            elif e["stored"] == 0:
                n, kind, count = 0, "not started", "not started"
                if status_word(r["status"]) not in ("open", "planned"):
                    raise Refused(f"{exp}: 0 stored, but draws.csv's status is {r['status'][:40]!r}")
            else:
                n, kind, count = e["stored"], "answers", f"{e['stored']:,} answers"
        draws = t2_draws(prov) if bid == "T2" else draw_kind(r["draws"])
        draws_legend = t2_draws_full(prov) if bid == "T2" else None
        if bid == "RO":
            # D183 FD6 B: Figure 1's "1 run" settings (embedding model, chunking, search strategy) are this box's
            run = [d for d in draw_kinds(prov) if d["key"] == "run"]
            if draws is not None or len(run) != 1 or not run[0].get("settings"):
                raise Refused(f"retrieval optimisation: draws.csv draws {r['draws']!r}, Figure 1's run kind {run!r}")
            draws = run[0]["name"]
        out.append({"id": bid, "plan_row": plan_row, "experiment": exp, "column": col,
                    "name": PLATE_NAMES.get(bid, exp), "design": design, "draws": draws, "count": count, "answers": n, "calls": calls.get(bid),
                    "count_kind": kind, "draws_legend": draws_legend,
                    "dashed": False, "csv_design": r["design"], "csv_draws": r["draws"],   # no progress drawn (28 Oct)
                    "csv_status": status_word(r["status"]), "registry_basis": basis})
    return out


# ---------------------------------------------------------------------------------------------------------------
# Layout and routing
# ---------------------------------------------------------------------------------------------------------------
_TW = {}


def text_width_mm(s, bold=False):
    key = (s, bold)
    if key not in _TW:
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextToPath
        fp = FontProperties(family=FONT, size=PT, weight="bold" if bold else "normal")
        _TW[key] = TextToPath().get_text_width_height_descent(s, fp, ismath=False)[0] * MM_PER_PT
    return _TW[key]


def wrap(s, width, bold=False):
    out, cur = [], ""
    for w in s.split(" "):
        cand = f"{cur} {w}" if cur else w
        if cur and text_width_mm(cand, bold) > width:
            out.append(cur)
            cur = w
        else:
            cur = cand
    out.append(cur)
    wide = [x for x in out if text_width_mm(x, bold) > width + 0.01]
    if wide:
        raise Refused(f"a word is wider than the {width:.1f} mm box: {wide}")
    return out


def grey_text(want="#5A5A5A"):
    def lum(c):
        c = tuple(int(c.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    ratio = (1.05) / (lum(want) + 0.05)
    if ratio < CONTRAST_MIN:
        raise Refused(f"grey {want} reaches {ratio:.2f}:1 on white, under [type] contrast_min_ratio")
    return want


GREY = grey_text()


def key_rows(boxes, prov) -> list:
    """The draws key (D183 FD6 B): (name, meaning) of each of Figure 1's draw kinds that a box draws, in Figure 1's
    order. T2's box names several kinds in one line (t2_draws()); each of them counts."""
    dk = draw_kinds(prov)
    name = {d["key"]: d["name"] for d in dk}
    used = {b["draws"] for b in boxes if b["draws"] and b["id"] != "T2"}
    used |= {name[k] for k in prov["design"]["t2_draws"].values()} if any(b["id"] == "T2" for b in boxes) else set()
    unknown = used - set(name.values())
    if unknown:
        raise Refused(f"boxes draw kinds {sorted(unknown)} that Figure 1's draw_kinds do not define")
    return [(d["name"], d["means"]) for d in dk if d["name"] in used]


def layout(boxes, key=None):
    """Positions (mm from the top left): column labels, then boxes stacked per column. Column 1's first box (G1, the
    source of the long arrows) sets a band: columns 2 and 3 start below its centre, and the last column's first box is
    centred on it, or starts under the column labels if that box is too tall, so the arrows from G1 to the later columns
    run along that band without crossing a box. Under the
    lowest box, the draws key (key_rows(); D183 FD6 B): a grey "Draws" label, then one line per kind, its name in bold
    and its meaning beside it, across the page."""
    ncol = len(COLUMNS)
    bw = (W_MM - 2 * MARGIN - (ncol - 1) * CHANNEL) / ncol
    tw = bw - 2 * PAD
    x0 = [MARGIN + c * (bw + CHANNEL) for c in range(ncol)]
    texts = []
    y_lab = MARGIN + PT * MM_PER_PT * 0.85
    lab_lines = {c: wrap(COLUMNS[c], bw) for c in range(ncol)}
    nlab = max(len(v) for v in lab_lines.values())
    for c, ls in lab_lines.items():
        for j, ln in enumerate(ls):
            texts.append(dict(x=x0[c], y=y_lab + j * LEAD, s=ln, bold=False, color=GREY, box="column " + str(c + 1),
                              kind="column label", line=j + 1))
    top = y_lab + (nlab - 1) * LEAD + 2.6
    for b in boxes:
        lines = [("name", ln, True) for ln in wrap(b["name"], tw, True)]
        lines += [("design", ln, False) for d in b["design"] for ln in wrap(GEN_DISPLAY.get(d, d), tw)]
        if b["draws"]:
            lines += [("draws", ln, False) for ln in wrap(b["draws"], tw)]
        # no count of answers (Valerio, 28 Oct: the plate shows no progress); b["count"] stays in the workbook. The
        # last line is the box's LLM calls (FF5), when S520's frozen summary gives a count above 0
        if calls_line(b["calls"]):
            lines += [("calls", calls_line(b["calls"]), False)]
        b["lines"] = lines
        b["w"], b["h"] = bw, 2 * PAD + PT * MM_PER_PT * 0.75 + (len(lines) - 1) * LEAD + PT * MM_PER_PT * 0.3
        b["x"] = x0[b["column"]]
    by_col = {c: [b for b in boxes if b["column"] == c] for c in range(ncol)}
    first = by_col[1][0]
    first["y"] = top
    band = top + first["h"] / 2
    for c, bs in by_col.items():
        if c == 1:
            y = top
        elif c in (2, 3):
            y = band + 3.0
        elif c == ncol - 1:
            y = max(top, band - bs[0]["h"] / 2)
        else:                                       # column 0: centred on column 1's stack
            c1 = by_col[1]
            span1 = sum(b["h"] for b in c1) + VGAP * (len(c1) - 1)
            span0 = sum(b["h"] for b in bs) + VGAP * 2 * (len(bs) - 1)
            y = top + (span1 - span0) / 2
        gap = VGAP * 2 if c == 0 else VGAP
        for b in bs:
            b["y"] = y
            y += b["h"] + gap
    bottom = max(b["y"] + b["h"] for b in boxes)
    key_texts, key_top = [], None
    if key:
        key_top = bottom + KEY_GAP
        y = key_top + PT * MM_PER_PT * 0.75
        key_texts.append(dict(x=MARGIN, y=y, s="Draws", bold=False, color=GREY, box="draws key", kind="key label",
                              line=1))
        x_means = MARGIN + max(text_width_mm(nm, True) for nm, _ in key) + KEY_COL
        for i, (nm, means) in enumerate(key):
            y += LEAD
            key_texts.append(dict(x=MARGIN, y=y, s=nm, bold=True, color=INK, box="draws key", kind="key name",
                                  line=i + 1))
            for j, ln in enumerate(wrap(means, W_MM - MARGIN - x_means)):
                if j:
                    y += LEAD
                key_texts.append(dict(x=x_means, y=y, s=ln, bold=False, color=INK, box="draws key", kind="key text",
                                      line=i + 1))
        bottom = y + PT * MM_PER_PT * 0.3
    H = bottom + MARGIN
    if H > H_MAX_MM - 0.05:
        raise Refused(f"the graph needs {H:.1f} mm, over [page] height_max_mm {H_MAX_MM}")
    for b in boxes:
        y = b["y"] + PAD + PT * MM_PER_PT * 0.75
        for j, (kind, ln, bold) in enumerate(b["lines"]):
            texts.append(dict(x=b["x"] + PAD, y=y + j * LEAD, s=ln, bold=bold, color=INK, box=b["id"], kind=kind,
                              line=j + 1))
    texts += key_texts
    return texts, H, {"box_mm": round(bw, 3), "channel_mm": CHANNEL, "lead_mm": round(LEAD, 3), "top_mm": round(top, 3),
                      "key_top_mm": None if key_top is None else round(key_top, 3)}


def crossings(paths) -> int:
    """How many times a segment of one source's arrows crosses a segment of another source's (strictly inside both)."""
    segs = [(p["from"], s) for p in paths for s in zip(p["points"], p["points"][1:])]
    n = 0
    for i, (a, ((x1, y1), (x2, y2))) in enumerate(segs):
        for b, ((u1, v1), (u2, v2)) in segs[i + 1:]:
            if a == b:
                continue
            hv = [((x1, y1), (x2, y2)), ((u1, v1), (u2, v2))]
            hz = [s_ for s_ in hv if s_[0][1] == s_[1][1] and s_[0][0] != s_[1][0]]
            vt = [s_ for s_ in hv if s_[0][0] == s_[1][0] and s_[0][1] != s_[1][1]]
            if len(hz) == 1 and len(vt) == 1:
                (hx1, hy), (hx2, _) = hz[0]
                (vx, vy1), (_, vy2) = vt[0]
                if min(hx1, hx2) + 0.01 < vx < max(hx1, hx2) - 0.01 and min(vy1, vy2) + 0.01 < hy < max(vy1, vy2) - 0.01:
                    n += 1
    return n


def route_best(boxes, arrows):
    """route() under every order of the sources in each channel's lanes; the order with fewest crossings (the first
    such in a fixed enumeration, so the result is deterministic)."""
    import itertools
    B = {b["id"]: b for b in boxes}
    chans = {}
    for a, t, _ in arrows:
        ca, ct = B[a]["column"], B[t]["column"]
        if ct > ca:
            for k in (ca, ct - 1):
                chans.setdefault(k, [])
                if a not in chans[k]:
                    chans[k].append(a)
    keys = sorted(chans)
    best = None
    for combo in itertools.product(*[list(itertools.permutations(sorted(chans[k], key=lambda s: B[s]["y"])))
                                     for k in keys]):
        order = dict(zip(keys, combo))
        paths = route(boxes, arrows, order)
        n = crossings(paths)
        if best is None or n < best[0]:
            best = (n, paths)
    return best[1], best[0]


def route(boxes, arrows, order=None):
    """Orthogonal paths. Same column: a vertical arrow between two boxes with none between them. Column c to a later
    column: out of the source's right edge, along a lane of the channel after c (one lane per source), along the
    source's row while every column between is free there (else the nearest free gap), down or up a lane of the
    channel before the target column, into the target's left edge. A source leaves from one point; a target's
    entries are spread along its left edge by source height."""
    B = {b["id"]: b for b in boxes}

    def cy(b):
        return b["y"] + b["h"] / 2

    lanes = {}                                     # channel index (after column k) -> sources using it
    for a, t, _ in arrows:
        ca, ct = B[a]["column"], B[t]["column"]
        if ct > ca:
            lanes.setdefault(ca, []).append(a)
            lanes.setdefault(ct - 1, []).append(a)
    lane_x = {}
    for k, srcs in lanes.items():
        srcs = list(order[k]) if order and k in order else sorted(set(srcs), key=lambda s: cy(B[s]))
        left = B[next(b["id"] for b in boxes if b["column"] == k)]["x"] + B[next(b["id"] for b in boxes
                                                                               if b["column"] == k)]["w"]
        for i, s in enumerate(srcs):
            lane_x[(k, s)] = left + CHANNEL * (i + 1) / (len(srcs) + 1)
    entries = {}
    for a, t, _ in arrows:
        if B[t]["column"] > B[a]["column"]:
            entries.setdefault(t, []).append(a)
    port_in = {}
    for t, srcs in entries.items():
        srcs = sorted(srcs, key=lambda s: cy(B[s]))
        bt = B[t]
        for i, s in enumerate(srcs):
            port_in[(s, t)] = bt["y"] + bt["h"] * (i + 1) / (len(srcs) + 1)

    def free_in(col, y):
        return all(not (b["y"] - 0.8 <= y <= b["y"] + b["h"] + 0.8) for b in boxes if b["column"] == col)

    paths = []
    for a, t, basis in arrows:
        ba, bt = B[a], B[t]
        ca, ct = ba["column"], bt["column"]
        if ca == ct:
            col = sorted((b for b in boxes if b["column"] == ca), key=lambda b: b["y"])
            ia, it = col.index(ba), col.index(bt)
            if abs(ia - it) != 1:
                raise Refused(f"{a} -> {t}: same column, not neighbours")
            x = ba["x"] + ba["w"] / 2
            pts = [(x, ba["y"] + ba["h"]), (x, bt["y"])] if it > ia else [(x, ba["y"]), (x, bt["y"] + bt["h"])]
        elif ct < ca:
            raise Refused(f"{a} -> {t}: an arrow must run left to right")
        else:
            ys, yt = cy(ba), port_in[(a, t)]
            xa = ba["x"] + ba["w"]
            la, lb = lane_x[(ca, a)], lane_x[(ct - 1, a)]
            inside = lambda y: bt["y"] + 1.5 <= y <= bt["y"] + bt["h"] - 1.5
            if ct == ca + 1:
                if inside(ys):                     # Valerio, 5 Nov (Q2): straight where the source's row meets the target
                    yt = ys
                pts = [(xa, ys), (la, ys), (la, yt), (bt["x"], yt)]
            else:
                mid = range(ca + 1, ct)
                if all(free_in(c, ys) for c in mid):
                    yc = ys
                else:
                    cands = sorted({v for b in boxes if b["column"] in mid for v in
                                    (b["y"] - VGAP / 2, b["y"] + b["h"] + VGAP / 2)}, key=lambda v: abs(v - yt))
                    yc = next((v for v in cands if all(free_in(c, v) for c in mid)), None)
                    if yc is None:
                        raise Refused(f"{a} -> {t}: no free row across columns {list(mid)}")
                if inside(yc):                     # Q2: no last jog where the crossing row meets the target
                    yt = yc
                pts = [(xa, ys), (la, ys), (la, yc), (lb, yc), (lb, yt), (bt["x"], yt)]
        clean = [pts[0]]
        for p in pts[1:]:
            if p != clean[-1]:
                clean.append(p)
        k = 1
        while k < len(clean) - 1:                  # collinear middle points
            (x1, y1), (x2, y2), (x3, y3) = clean[k - 1], clean[k], clean[k + 1]
            if (x1 == x2 == x3) or (y1 == y2 == y3):
                clean.pop(k)
            else:
                k += 1
        paths.append({"from": a, "to": t, "points": [(round(x, 4), round(y, 4)) for x, y in clean], "basis": basis})
    return paths


def gate(boxes, paths):
    """The layout gate: no segment passes through a box other than its arrow's two ends; segments of arrows from
    different sources never run along the same line; every last segment is longer than the arrowhead."""
    probs = []
    for p in paths:
        for (x1, y1), (x2, y2) in zip(p["points"], p["points"][1:]):
            for b in boxes:
                if b["id"] in (p["from"], p["to"]):
                    continue
                lo_x, hi_x, lo_y, hi_y = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
                if hi_x > b["x"] + 0.2 and lo_x < b["x"] + b["w"] - 0.2 and hi_y > b["y"] + 0.2 and \
                        lo_y < b["y"] + b["h"] - 0.2:
                    probs.append(f"{p['from']} -> {p['to']} crosses box {b['id']}")
        (xa, ya), (xb, yb) = p["points"][-2], p["points"][-1]
        if abs(xb - xa) + abs(yb - ya) < HEAD + 0.6:
            probs.append(f"{p['from']} -> {p['to']}: last segment shorter than its arrowhead")
    segs = [(p["from"], s) for p in paths for s in zip(p["points"], p["points"][1:])]
    for i, (a, ((x1, y1), (x2, y2))) in enumerate(segs):
        for b, ((u1, v1), (u2, v2)) in segs[i + 1:]:
            if a == b:
                continue
            if x1 == x2 == u1 == u2 and min(max(y1, y2), max(v1, v2)) - max(min(y1, y2), min(v1, v2)) > 0.01:
                probs.append(f"arrows from {a} and {b} share a vertical line at x {x1:.2f}")
            if y1 == y2 == v1 == v2 and min(max(x1, x2), max(u1, u2)) - max(min(x1, x2), min(u1, u2)) > 0.01:
                probs.append(f"arrows from {a} and {b} share a horizontal line at y {y1:.2f}")
    if probs:
        raise Refused("layout gate: " + "; ".join(sorted(set(probs))))


# ---------------------------------------------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------------------------------------------
def draw(boxes, texts, paths, H, sheet_rows, files):
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Polygon, Rectangle
    import house_style as hs
    import S457_fig2_panels as S457
    plt.rcParams.update({"font.family": FONT, "font.size": PT, "svg.fonttype": "none", "pdf.fonttype": 42,
                         "text.color": INK, **FR.matplotlib_rc("S496")})
    fig = plt.figure(figsize=(W_MM / 25.4, H / 25.4), facecolor="#FFFFFF")
    X = lambda x: x / W_MM          # noqa: E731
    Y = lambda y: 1 - y / H         # noqa: E731
    for b in boxes:
        corpus = b["count_kind"] == "corpus"
        fig.add_artist(Rectangle((X(b["x"]), Y(b["y"] + b["h"])), b["w"] / W_MM, b["h"] / H, transform=fig.transFigure,
                                 facecolor=FILL_CORPUS if corpus else "none", edgecolor=INK,     # outlined too (D161 (3))
                                 linewidth=LINE_PT, linestyle=(0, (3, 2)) if b["dashed"] else "-"))
    for p in paths:
        pts = p["points"]
        (xa, ya), (xb, yb) = pts[-2], pts[-1]
        d = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
        ux, uy = (xb - xa) / d, (yb - ya) / d
        stem = pts[:-1] + [(xb - ux * HEAD * 0.9, yb - uy * HEAD * 0.9)]
        fig.add_artist(Line2D([X(x) for x, _ in stem], [Y(y) for _, y in stem], transform=fig.transFigure,
                              color=INK, linewidth=LINE_PT, solid_joinstyle="miter", solid_capstyle="butt"))
        half = HEAD * 0.42
        tri = [(xb, yb), (xb - ux * HEAD - uy * half, yb - uy * HEAD + ux * half),
               (xb - ux * HEAD + uy * half, yb - uy * HEAD - ux * half)]
        fig.add_artist(Polygon([(X(x), Y(y)) for x, y in tri], closed=True, transform=fig.transFigure,
                               facecolor=INK, edgecolor="none", linewidth=0))
    printed = {}
    for i, t in enumerate(texts):
        a = fig.text(X(t["x"]), Y(t["y"]), t["s"], ha="left", va="baseline", fontsize=PT,
                     fontweight="bold" if t["bold"] else "normal", color=t["color"], family=FONT)
        gid = f"s448num_{len(printed)}"
        a.set_gid(gid)
        printed[gid] = {"sheet": SHEETS["lines"], "row": sheet_rows[i], "format": "{text}"}
    bad = hs.check_figure_colours(fig)
    if bad:
        plt.close(fig)
        raise Refused(f"colours outside the house palette: {bad}")
    try:                                           # build order F4: ligatures off, no text off the page or on another
        S457.finish_plate(fig, W_MM, H, files, title=SI_LABEL)
    except SystemExit as e:
        raise Refused(str(e)) from None
    return printed


# ---------------------------------------------------------------------------------------------------------------
# Legend, caption, workbook
# ---------------------------------------------------------------------------------------------------------------
def calls_sentences(boxes, s520) -> str:
    """The legend's sentences on LLM calls, from S520's frozen summary. "The boxes add up" is stated only when they do,
    and the RAGChecker clause only when by_role shows it: RAGChecker's calls that sit in a box are over half of the
    whole total, so they are over half of the calls in the boxes it scored, a part of that total."""
    total = s520["figure1_legend_total"]
    in_boxes = sum(b["calls"] for b in boxes if isinstance(b["calls"], int))
    outside = total - in_boxes
    rag = sum(v["calls"] for k, v in s520["by_role"].items() if k.startswith("RAGChecker"))
    return ("A box gives the experiment, its design, its draws and its language-model (LLM) calls: each prompt sent to "
            "a language model for generation, either judge, a recheck, RAGAS or RAGChecker."
            + (f" The boxes add up to the {total:,} calls of Figure 1." if outside == 0 else "")
            + " MiniCheck, concept recall and the bge-m3 encoder make no such call."
            + (" RAGChecker makes most of the calls in the boxes it scored." if 2 * (rag - outside) > total else "")
            + " One answer can take many calls.")


def rlms_version() -> str:
    """The rlms version experiments/rlm_ref/pyproject.toml pins, the package RLM the legend names (D228)."""
    m = re.search(r'"rlms==([\d.]+)"', RLM_PYPROJECT.read_text())
    if not m:
        raise Refused(f"{rel(RLM_PYPROJECT)} pins no rlms version")
    return m.group(1)


def legend_text(boxes, stamp, n_exp, s520=None) -> str:
    kept = [b["name"].lower() for b in boxes if b["count_kind"] == "answers, kept from April"]
    say = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]   # noqa: E731
    # no answer counts and no running or not-started clause (Valerio, 28 Oct: the plate shows no progress)
    gives = calls_sentences(boxes, s520) if s520 else "A box gives the experiment, its design and its draws."
    t2 = next((b for b in boxes if b.get("draws_legend") and b["draws_legend"] != b["draws"]), None)
    if t2:
        gives += f" The {t2['name'].lower()}'s draws: {t2['draws_legend']}."
    body = (
        f"Each white box is one experiment of the study (n = {n_exp} experiments); the shaded box is the "
        f"evaluation corpus they share. {gives} The key under the graph says what each kind of draw means. Sent the "
        f"same seed, a local model nearly always repeats its answer, so its draws differ through their seeds; "
        f"Gemini's draws are independent samples. The {say(kept).replace('optimisation', 'optimization')} were made "
        f"before the experiments reported here and not run again"
        f"{', so they carry no count' if s520 else ''}; retrieval optimization used its own queries, and the model "
        f"selection box counts the language models that made a call in this study, from the call logs. An "
        f"arrow from one box to another means that the second experiment uses the output or a choice of the first. "
        f"{fn.PACKAGE_RLM[:1].upper() + fn.PACKAGE_RLM[1:]} is the RLM package released by the method's authors (rlms {rlms_version()}), "
        f"drawn as {fn.PACKAGE_RLM_N.format(n=10)} in Figure 3 at its cap of 10 turns; {fn.MENTORI_RLM} is Mentor::i's own "
        f"implementation. RAG, retrieval-augmented generation.")
    return (f"Legend DRAFT for {SI_LABEL} (provisional; written by scripts/S496_supp_fig1_experiment_graph.py). "
            f"Data stamp: {stamp}.\n\n**{SI_LABEL} | How the experiments of the study connect.**\n\n{body}\n")


def write_workbook(sheets: dict, path: Path):
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
            ws.append(r)
    wb.save(path)
    FR.deterministic_xlsx(path)


def build(out: Path, argv) -> dict:
    if FLOCK.get("status") != "agreed":
        raise Refused(f"{rel(FIGURE_LOCK)} status {FLOCK.get('status')!r}, not 'agreed' (D87)")
    reg, rows, prov = load()
    reproduced = reproduce(reg, rows)
    s520 = load_s520()
    sum_check = box_sum_check(s520) if s520 else None      # D201 Q2
    if sum_check:
        reproduced = reproduced + [f"boxes {sum_check['boxes']:,} calls + " + " + ".join(
            f"{r['experiment']} {r['calls']:,} (in no box)" for r in sum_check["exceptions"])
            + f" = total {sum_check['total']:,}"]
    boxes = box_table(reg, rows, prov, calls_by_box(s520))
    key = key_rows(boxes, prov)
    texts, H, geom = layout(boxes, key)
    paths, n_cross = route_best(boxes, ARROWS)
    gate(boxes, paths)
    geom["arrow_crossings"] = n_cross
    n_exp = sum(1 for b in boxes if b["count_kind"] != "corpus")
    n_counted = sum(1 for b in boxes if b["count_kind"] in ("answers", "answers, kept from April"))
    if s520:
        n_counted = sum(1 for b in boxes if calls_line(b["calls"]))
    tag = f" (provisional, {n_counted} of {n_exp})"
    total = reg["today"]["total_counted"]
    # audit 27 Oct: was a fixed text; 30 Oct: each not-counted experiment with its draws.csv status word (box_table())
    started = [f"the {b['name'].lower()} {b['count_kind']}" for b in boxes if b["answers"] is None
               and b["count_kind"] not in ("corpus", "answers", "answers, kept from April")]
    stamp = (f"PROVISIONAL: {n_counted} of {n_exp} experiments with answers counted ({total:,} answers, "
             f"scripts/S492_answer_registry.py)"
             + (f"; {' and '.join(started)}, not counted" if started else ""))
    if s520:
        stamp = (f"PROVISIONAL: {n_counted} of {n_exp} experiments with calls counted "
                 f"({s520['figure1_legend_total']:,} LLM calls, scripts/S520_llm_calls.py)")
    cols_l = ["box", "plan_row", "experiment", "kind", "line", "text"]
    lines_rows = [[t["box"], next((b["plan_row"] for b in boxes if b["id"] == t["box"]), ""),
                   next((b["experiment"] for b in boxes if b["id"] == t["box"]), COLUMNS[int(t["box"].split()[-1]) - 1]
                        if t["box"].startswith("column") else ""), t["kind"], t["line"], t["s"]] for t in texts]
    cols_b = ["box", "plan_row", "experiment", "column", "design", "draws", "answers", "calls", "count_kind",
              "draws_csv_design", "draws_csv_draws", "draws_csv_status", "registry_basis"]
    box_rows = [[b["id"], b["plan_row"], b["experiment"], COLUMNS[b["column"]], " | ".join(b["design"]),
                 b["draws"] or "", b["answers"], b["calls"], b["count_kind"], b["csv_design"], b["csv_draws"],
                 b["csv_status"],
                 b["registry_basis"]] for b in boxes] + (exception_rows(sum_check, cols_b) if sum_check else [])
    cols_a = ["from", "to", "from_experiment", "to_experiment", "meaning", "basis", "path_mm"]
    name = {b["id"]: b["experiment"] for b in boxes}
    arrow_rows = [[p["from"], p["to"], name[p["from"]], name[p["to"]], "uses the output or the choice of",
                   p["basis"], " ".join(f"{x:.2f},{y:.2f}" for x, y in p["points"])] for p in paths]
    sheets = {SHEETS["lines"]: (cols_l, lines_rows), SHEETS["boxes"]: (cols_b, box_rows),
              SHEETS["arrows"]: (cols_a, arrow_rows)}
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob(f"{SI_LABEL}*"):
        old.unlink()
    files = {x: out / f"{SI_LABEL}{tag}.{x}" for x in ("pdf", "svg", "png")}
    printed = draw(boxes, texts, paths, H, list(range(len(texts))), files)
    FR.check_pdf_deterministic(files["pdf"])
    FR.check_svg_deterministic(files["svg"])
    sd = out / f"{SI_LABEL} data{tag}.xlsx"
    write_workbook(sheets, sd)
    numbers = out / f"{SIDE}_numbers.json"
    numbers.write_text(json.dumps({
        "stamp": stamp, "what": f"every value {SI_LABEL} draws, sheet by sheet as the data workbook holds them",
        "sheets": {k: {"columns": c, "rows": r} for k, (c, r) in sheets.items()}, "printed": printed,
        "printed_what": "every text on the plate: the SVG group id of its text, the lines sheet's 0-based data row "
                        "and format it is written from (S448 R8 (6))"}, indent=1, ensure_ascii=False) + "\n")
    legend = legend_text(boxes, stamp, n_exp, s520)
    (out / "legend_draft.md").write_text(legend)
    capf = out / f"{SI_LABEL} data caption{tag}.md"
    capf.write_text(
        f"**{SI_LABEL} data{tag} |** The boxes, arrows and draws key drawn in {SI_LABEL}. Sheet {SHEETS['lines']}: "
        f"one row per printed line (its box, plan row, experiment, kind and text; the key's lines under box \"draws "
        f"key\"). Sheet {SHEETS['boxes']}: one row per box, with "
        f"the design and draws drawn, the answers stored, "
        + ("the LLM calls from scripts/S520_llm_calls.py" if s520 else "a calls column left blank until "
           "scripts/S520_llm_calls.py's inputs are frozen")
        + f", and beside them experiments/draws.csv's design, draws and status words "
        f"and the registry's basis for the count (findings/recompute/S492_answer_registry/registry.json). Sheet "
        f"{SHEETS['arrows']}: one row per arrow, with the basis for it and its path in mm from the page's top left. "
        f"The experiment columns keep experiments/draws.csv's names; box "
        + ", ".join(f"{k} is printed as {v}" for k, v in PLATE_NAMES.items()) + ". "
        f"Generated by `uv run --frozen python scripts/S496_supp_fig1_experiment_graph.py`.\n\n"
        f"{stamp}.\n")
    inputs = {rel(REGISTRY): sha256_file(REGISTRY), rel(FIG1_PROV): sha256_file(FIG1_PROV),
              rel(DRAWS) + " (fields " + ", ".join(DRAWN_COLUMNS) + ")": drawn_fields_sha(rows),
              rel(RLM_PYPROJECT): sha256_file(RLM_PYPROJECT)}
    if s520:
        inputs[rel(S520_SUMMARY)] = sha256_file(S520_SUMMARY)
    prov_out = {
        "provenance": {"script": "scripts/S496_supp_fig1_experiment_graph.py",
                       "script_sha256": sha256_file(Path(__file__)),
                       "command": "uv run --frozen python scripts/S496_supp_fig1_experiment_graph.py",
                       "python": platform.python_version(),
                       "deterministic": "D155: no build time and no repository HEAD are recorded; draws.csv is "
                                        "recorded by the sha256 of the fields drawn, not of the file",
                       "inputs_sha256": inputs, "model_calls": 0},
        "reproduced": reproduced, "box_sum_check": sum_check, "stamp": stamp, "figure": SI_LABEL,
        "named": f"{SI_LABEL}: FIGURE_LOCK [files] supplementary_name (D92 Q194)",
        "page_mm": [W_MM, round(H, 3)], "geometry_mm": geom,
        "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": sha256_file(FIGURE_LOCK), "status": FLOCK.get("status")},
        "type_pt": {"all text": PT}, "font": FONT, "line_pt": LINE_PT,
        "colours": {"text, boxes, arrows": INK, "column labels": GREY, "corpus box": FILL_CORPUS},
        "boxes": [{k: b[k] for k in ("id", "plan_row", "experiment", "column", "design", "draws", "answers", "calls",
                                     "count_kind", "dashed")} for b in boxes],
        "arrows": [{"from": p["from"], "to": p["to"], "basis": p["basis"]} for p in paths],
        "files": {p.name: sha256_file(p) for p in [*files.values(), sd, capf, numbers, out / "legend_draft.md"]}}
    (out / f"{SIDE}_provenance.json").write_text(json.dumps(prov_out, indent=1, ensure_ascii=False) + "\n")
    return {"stamp": stamp, "H": H, "files": files, "boxes": boxes, "paths": paths, "reproduced": reproduced}


def main(argv=None):
    global OUT
    FR.pin_hash_seed()                     # D155: the PDF's font subsets depend on the string-hash seed
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="default findings/figures_provisional/supp_fig1")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.out:
        OUT = Path(a.out).resolve()
    try:
        res = build(OUT, argv)
    except Refused as e:
        print(f"S496 REFUSED: {e}", file=sys.stderr)
        sys.exit(2)
    print("reproduced: " + "; ".join(res["reproduced"]))
    print(res["stamp"])
    print(f"wrote {', '.join(p.name for p in res['files'].values())} ({W_MM:g} x {res['H']:.1f} mm), data workbook, "
          f"caption, numbers, legend_draft.md, provenance into {rel(OUT)}")
    for b in res["boxes"]:
        print(f"  {b['id']:6s} col {b['column'] + 1}  {b['experiment']:36s} {b['count'] or ''}")
    for p in res["paths"]:
        print(f"  {p['from']} -> {p['to']}")


if __name__ == "__main__":
    main()
