"""S492: the answer registry, stored answers per experiment counted from run records (inventory A16, F15; D155).

One command, from the repository root:
    uv run python scripts/S492_answer_registry.py            reproduce, then write
    uv run python scripts/S492_answer_registry.py --check    reproduce, then compare with the committed output only

THE UNIT is S13's (scripts/S13_evaluation_total.py:9-11): one generation row, one evaluation item under one
configuration, counted whether or not a judge scored it and including the not-answerable (out-of-domain) half. Not
judge calls, not scored observations. A stored answer with an error and no text is a generation row and counts.

REPRODUCE FIRST (any difference exits 2, nothing written). S13's 37,449 from the sources S13 reads that are committed:
S04b's per-experiment table (findings/recompute/S04b_counts_audit.json, which S04b counted from April's records) for
the eight answer experiments, the four retrieval experiments and the three model-selection phases, plus the two
replication files in data/replication_inputs/ counted here row by row (each file's sha256 checked against that
folder's MANIFEST.sha256). Each group subtotal and the total must equal findings/recompute/S13_evaluation_total.json.
Then 50,835: the 37,449 plus S141's campaign counted here as the rows of findings/recompute/S141_phase5_tidy_corrected.csv
(12,420) plus S187's two side arms (966, S187's design arithmetic 138 + 828: no record of them is in the repository),
equal to findings/recompute/S187_si_experiment_inventory.json.

THEN TODAY'S COUNT under the same unit, experiment by experiment (experiments/draws.csv's rows), each from run records
in the repository or a frozen set (findings/recompute/frozen_inputs/, read through scripts/fig_repro.frozen()):
  Model selection, Retrieval optimisation   kept from April (not re-run): S04b's counts, as in the anchor
  G1 generation strategies, G2 matched budget   s457_mirror_20261022.tar: each strategy's answers.jsonl
  G6 package RLM at caps 5, 10, 20            answer_lengths_20261020.tar: G6/runs/b4_rlm_ref__cap{5,10,20}__all135
  G5 retrieval depth (Gemini), draws 1 to 3   committed L2_d284_inputs (52541967): the draw-1 results file and D284's
                                               12 share files, each tracked and equal to its PULL.json sha256, the
                                               draw-1 file equal to L2_inputs' (52abab86, SHA256SUMS); a key in two
                                               files must hold the same row (D287 (1), 7 Nov; draw 1 only before)
  T1 retrieval depth, local models             fig3_t1.tar: the union of the results_v4 files, one row per model and key
  G6 package RLM depth caps                   committed L2_inputs/g6/b4_rlm_ref__cap{1,2,3,7,15,30,50}__depthsweep86,
                                               counted only when each file is tracked by git and listed in
                                               frozen_inputs/SHA256SUMS with its sha256; otherwise listed as not counted
  G4 corpus scaling, draws 1 to 3             g4_draws_20261101.tar (freeze_g4_draws.py): every run's answers.jsonl,
                                               each with fig3_g4_inputs.tar's draw-1 file of the run as a byte prefix
                                               (D287 (1), 7 Nov; fig3_g4_inputs.tar, draw 1 only, before)
  G3 pipeline ablation set-ups, G3 baselines,  count_records_20261108.tar (freeze_count_records_1108.py): g3/runs,
  G9 distiller on every step (stress),         each set-up's answers.json, every draw (Valerio, 8 Nov: draws 2 and 3
     draws 1 to 3                              are in Source Data Fig. 5, sheet Fig. 5a); reproduced first: the
                                               earlier sources, fig4_records_1023.tar (G3: draw 1, 34 of
                                               orch_no_supervisor's draw 2, the baselines' three draws) and the
                                               committed g9_inputs (G9: draw 1), give 844, 810 and 270, and each of
                                               their keys holds the same row in the new set
  S2 code generation                           s2_length_retries_20261021.tar: the 121 runs Figure 6's committed
                                               records_manifest.json names (the 11 variants of D116), each answers.json
                                               checked against the manifest's sha256; stored runs outside them are
                                               reported beside the count, not in it
  I2 plant-science reuse demonstration         committed i2_inputs (S569, ecf1e368), each file listed in
                                               frozen_inputs/SHA256SUMS with its sha256: the six configs'
                                               sinks/exp_01__<config>__i2_plant5/answers.jsonl, 15 keys each, 90 in
                                               all. A SPECIAL CASE (D232, Valerio, 4 Nov: "You should count the 90
                                               answers. This should simply be a special case."): its keys are checked
                                               against I2's own key, PB v1.1 (experiments/reuse_demo/plant_key.py,
                                               sha256 pinned here as S569 pins it), not the main D5 key; the row
                                               carries special_case saying so. It counts in the total under the same
                                               unit, one stored answer
  Since D281 (6 Nov, rulings page COUNT), from count_records_20261106.tar (frozen_inputs/freeze_count_records.py: the
  copies each experiment's judging read, each equal to its own manifest) and committed files:
  T2 strategy replication                      the tar's t2/<generator>/runs: 4 generators x 6 strategies' answers.jsonl;
                                               with T2X (D241: RLM-10 of gemma3:27b and qwen3-coder:30b, draw 1, on
                                               the 17 many-paper questions outside D98's subset, 34 answers; in Figure
                                               3e and Supplementary Figure 6), from count_records_20261108.tar's
                                               t2x/<generator>/runs, reproduced against the main judge's committed
                                               T2X collects (T2X_runs/collect), no key shared with T2's own records
  G10 flat wide call, G11 short passages       the tar's g10/runs (3 indexes) and g11/runs, keys checked against
                                               G4's question sets of each index (g4_qids)
  G17 RLM ablation                             committed G17_runs/inputs (draw 1) and inputs_d23 (draws 2 and 3), each
                                               file tracked and equal to its folder's MANIFEST.sha256
  G19, G20 RLM ablation, local generators     the tar's g19/runs (gemma3:27b) and count_records_20261109.tar's g20/runs
                                               (qwen3-coder:30b, D309 A26): arms B and C, and arm A (package RLM, cap10)
  T3 component benchmarks, distiller           the tar's t3/T3_frozen_20261104T131439Z (the set S524 and S534 read):
     intervention                              each sink's answers.jsonl, rows equal to its MANIFEST.json
                                               answers_per_sink, keys <model>|<item>|d<n>; totals equal draws.csv's
                                               6,656 and 1,164
  S12 judge with evidence                      0: it stores no answer. Its 1,464 rows are judge calls (4 arms) on 366
                                               of G1's draw-1 answers (S18f_v25_results.json analysis_set), which G1
                                               counts; the row carries special_case saying so
  REPRODUCE (any difference refuses): each key set equals the rows already committed for it, the judge's collects for
  T2 (S518_inputs, t2_local_v25_inputs), G10 and G11 (g10_g11_v25_inputs), S573's concept-recall rows for G17 and G19,
  MANIFEST.json's answers_per_sink for T3; a stored answer the judge did not read is allowed only when its generation
  text is empty (it counts, under the unit), and is listed in the row's note.
Every count is of distinct answer keys (an append-only file's later line of a key replaces the earlier, as exp_01
and S447 read them), each key checked against its run (run id, question in the D5 key (I2: in PB v1.1), draw 1 to 3).
An experiment in STATUS_ONLY takes its state from experiments/draws.csv's status: one with no run yet ("open" or
"planned") counts 0; one that has run or is running but whose records are in neither the repository nor a frozen set
is listed as not counted, with the reason. When such an experiment's records are frozen it takes a counter above and
leaves STATUS_ONLY, so a stale status cannot stand for a count (I2 left it on 4 Nov, D232; T2, T3, G10, G11, G17, G19
and S12 on 6 Nov, D281, leaving it empty). WHICH SETS COUNT (Valerio, 8 Nov): a stored set counts only when it ends up
in a figure or a table of this paper (main figures, Supplementary Figures, Supplementary Tables, Source Data). G20 (D260,
the RLM ablation with qwen3-coder:30b, 138 answers) was in none of them and had no row until D309 A26 O1 (9 Nov) joined
it to G19 as "RLM ablation, local generators" (count_records_20261109.tar). The 2,336 retrieval-
optimisation records stay in the total, and orch_no_supervisor's 23 off-design draw-2 answers stay in G3's count.

Writes findings/recompute/S492_answer_registry/registry.json (no time in it, so a rerun is byte-equal): the anchor, the
count per experiment with its source files and their sha256, the total, and the inventory's F15 values beside it.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import fig_repro  # noqa: E402

REC = REPO / "findings/recompute"
S04B = REC / "S04b_counts_audit.json"
S13_JSON = REC / "S13_evaluation_total.json"
S187_JSON = REC / "S187_si_experiment_inventory.json"
S141_CSV = REC / "S141_phase5_tidy_corrected.csv"
REPL = REPO / "data/replication_inputs"
REPL_FILES = ["reviewer_strategy_replication.json", "reviewer_strategy_replication_122b.json"]
SUMS = REC / "frozen_inputs/SHA256SUMS"
FIG6_MANIFEST = REPO / "findings/figures_provisional/fig6/records_manifest.json"
OUT = REC / "S492_answer_registry"
DRAWS = REPO / "experiments/draws.csv"
NOT_RUN = ("open", "planned")              # draws.csv status words of an experiment with no run yet
# The experiments with no counter yet: (experiment, plan row), read from draws.csv's status (status_rows()). Empty since
# D281 (6 Nov): T3's two rows, T2, G10, G11, G17, G19 and S12 have counters (count_rows()); I2 since D232 (4 Nov).
STATUS_ONLY: tuple = ()
# D281: the frozen set of T2's, G10's, G11's, G19's and T3's records (frozen_inputs/freeze_count_records.py)
COUNT_SET = "count_records_20261106"
T2_GENERATORS = ("claude-haiku-4-5", "gemini-2.5-pro", "gemma3-27b", "qwen3-coder-30b")   # D160 (2)
T2_COLLECTS = {"claude-haiku-4-5": ["S518_inputs/claude-haiku-4-5/t2_v24_collect.jsonl",
                                    "S518_inputs/claude-haiku-4-5/s6t2_collect.jsonl"],
               "gemini-2.5-pro": ["S518_inputs/gemini-2.5-pro/t2g_collect.jsonl",
                                  "S518_inputs/gemini-2.5-pro/s6t2g_collect.jsonl"],
               "gemma3-27b": ["t2_local_v25_inputs/t2lgemma_collect.jsonl"],
               "qwen3-coder-30b": ["t2_local_v25_inputs/t2lqcoder_collect.jsonl"]}      # judge_rows_v25.T2_SOURCES
G10_G11 = (("Flat wide call", "G10", "g10", "matched_budget", "g10_g11_v25_inputs/g10_collect.jsonl"),
           ("Short-passage single pass", "G11", "g11", "single_pass_cut800", "g10_g11_v25_inputs/g11_collect.jsonl"))
G17_ARMS = ("rlm_10_ctrl", "rlm_10_nogate", "rlm_10_nosearch")                      # D240
G17_DIRS = (("inputs", (1,)), ("inputs_d23", (2, 3)))
G17_ROWS = ["G17_concept_recall/concept_recall.jsonl", "G17_concept_recall_d23/concept_recall.jsonl"]   # S573
G19_RUNS = (("exp_01__rlm_10_nosearch__exp_v4_s20_n0+gemma3-27b", "exp_v4_s20_n0|rlm_10_nosearch", "B"),
            ("exp_01__rlm_10_nogate__exp_v4_s20_n0+gemma3-27b", "exp_v4_s20_n0|rlm_10_nogate", "C"),
            ("b4_rlm_ref_gemma3__cap10__d239a46", "cap10", "A"))                    # D249 O2; G19_runs/README.md
G19_ROWS = "G19_concept_recall/concept_recall.jsonl"                                  # S573, arms A, B, C (R is T2's)
# D309 A26 O1 (Valerio, 9 Nov): G20, G19's design with qwen3-coder:30b, joins G19 in one row, "RLM ablation, local
# generators" (gemma3:27b 138, qwen3-coder:30b 138); its records frozen by frozen_inputs/freeze_count_records_1109.py
COUNT_SET_1109 = "count_records_20261109"
G20_RUNS = (("exp_01__rlm_10_nosearch__exp_v4_s20_n0+qwen3-coder-30b", "exp_v4_s20_n0|rlm_10_nosearch", "B"),
            ("exp_01__rlm_10_nogate__exp_v4_s20_n0+qwen3-coder-30b", "exp_v4_s20_n0|rlm_10_nogate", "C"),
            ("b4_rlm_ref_qwen3coder__cap10__d239a46", "cap10", "A"))                # findings/recompute/G20_runs/README.md
G20_ROWS = "G20_concept_recall/concept_recall.jsonl"                                  # S594, arms A, B, C (R is T2's)
T3_DIR = "t3/T3_frozen_20261104T131439Z"
T3_ROWS = (("Component benchmarks", "exp_04__", 6656), ("Distiller intervention", "exp_04b__", 1164))  # draws.csv answers
S18F = REC / "S18f_v25_results.json"
S12_ANSWERS = 366                                                                     # draws.csv design: 4 arms x 366
S12_SPECIAL = ("stores no answer of its own: its judge calls (4 arms) are on 366 of G1's draw-1 answers, which G1 "
               "counts (D281)")
# I2 (D232): the frozen set i2 (S569, ecf1e368), scored on its own key PB v1.1, not the D5 key
I2_SET = "i2"
I2_INDEX = "i2_plant5"
I2_CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")   # Figure 2's six (S569 CONFIGS)
I2_PER_CONFIG = 15                                                                        # 5 questions x draws 1 to 3
I2_KEY_PY = REPO / "experiments/reuse_demo/plant_key.py"
I2_KEY_SHA256 = "eb58a724f10382f478a25c68ec3b52260c398ce912e071ff8ba5a7647d9e5487"         # PB v1.1, as plant_key.py
I2_SPECIAL = "scored on I2's own key (PB v1.1), not the main key (D232)"

# S13's groups, by S04b table key (scripts/S13_evaluation_total.py CORE, IR, SELECTION)
CORE = ["exp04_generation", "exp05_scaling", "exp06_orchestration", "exp07_component_bench", "exp07b_intervention",
        "exp08_coder", "exp09_depth", "naive_baseline"]
IR = ["exp01_embedding", "exp02_search", "exp03a_chunking", "exp03b_scalability"]
SELECTION = ["exp00_rlm_models", "exp00_phase2", "exp00_triage"]

INDEX = "exp_v4_s20_n0"
G1_STRATEGIES = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
G3_SETUPS = ["full_orchestrator", "orch_no_analyser", "orch_no_planner", "orch_no_supervisor", "orch_no_synthesiser",
             "orch_factual_to_documents"]
G3_BASELINES = ["raw_gemini", "naive_rag"]
G9_SETUPS = ["orch_distil_every_step", "orch_distil_every_step_f1"]   # Q82's two stress set-ups (plan row G9)
G6_CAPS_ALL135 = [5, 10, 20]
G6_CAPS_DEPTH = [1, 2, 3, 7, 15, 30, 50]
G5_FILE = "results_v4/v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview_127.0.0.1-11453_20261018_095502.json"
G5_ALL = REC / "L2_d284_inputs"            # D287 (1): G5's three draws (D284), committed with PULL.json (52541967)
G4_SET = "g4_draws_20261101"               # D287 (1): G4's three draws, frozen_inputs/freeze_g4_draws.py
# Valerio, 8 Nov (a stored set counts only when it ends up in a figure or a table of the paper): G3's and G9's set-ups
# with draws 2 and 3 (Source Data Fig. 5, sheet Fig. 5a) and T2X (Figure 3e, Supplementary Figure 6), frozen by
# frozen_inputs/freeze_count_records_1108.py. G20 joined G19's row under D309 A26 O1 (COUNT_SET_1109).
COUNT_SET_1108 = "count_records_20261108"
# The counts of the earlier sources, as the registry committed in 368a088a (7 Nov) holds them: reproduced first
G3_G9_BEFORE = {"Pipeline ablation": 844, "No retrieval and naive RAG": 810, "Distiller on every step (stress)": 270}
G3_G9_BEFORE_SOURCE = {"G3": "fig4_records_1023.tar", "G9": "committed g9_inputs"}
T2X_GENERATORS = {"gemma3-27b": "T2X_runs/collect/t2xgemma_collect.jsonl",
                  "qwen3-coder-30b": "T2X_runs/collect/t2xqcoder_collect.jsonl"}   # the main judge's collects (d7283f72)
T2X_QUESTIONS = REC / "T2X_runs/t2x_questions.json"                                # D241: the 17
T2X_CONFIG = "rlm_10"

# The inventory's F15 values, for the comparison only (nothing here is an anchor or a target). count50k.md F4 lists
# 'stored today' per experiment from experiments/progress.csv, not from records.
INVENTORY_F15 = {"stored_new": 23062, "kept": 2744, "total": 25806}
COUNT50K_STORED = {"Model selection": 408, "Retrieval optimisation": 2336,
                   "Generation strategies (G1, G2, G6 caps 5/10/20)": 4050,
                   "Retrieval depth (G5, G6 depth caps, T1)": 2986, "Corpus scaling (G4)": 11682,
                   "Pipeline ablation + naive RAG (G3, baselines, G9)": 1924, "Code generation (S2)": 2420}


class Refused(Exception):
    pass


def sha(p: Path) -> str:
    return fig_repro.sha256_file(p)


def rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def jl(p: Path) -> list:
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def listed_sha() -> dict:
    out = {}
    for ln in SUMS.read_text().splitlines():
        if ln.strip():
            h, name = ln.split(None, 1)
            out[name.strip()] = h
    return out


def tar_sha(stem: str, sums: dict) -> str:
    h = sums.get(f"{stem}.tar")
    if h is None:
        raise Refused(f"{stem}.tar is not listed in {rel(SUMS)}")
    return h


def tracked(p: Path) -> bool:
    """True when git tracks p and the working copy equals the committed blob (read only)."""
    r = subprocess.run(["git", "ls-files", "-s", "--", rel(p)], cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return False
    blob = r.stdout.split()[1]
    h = subprocess.run(["git", "hash-object", "--", rel(p)], cwd=REPO, capture_output=True, text=True).stdout.strip()
    return h == blob


def key():
    from experiments.runner.experiment import questions
    qs = questions()
    if len(qs) != 135:
        raise Refused(f"the D5 key gives {len(qs)} questions, want 135")
    return {q["id"] for q in qs}


def g4_qids(index: str) -> set:
    """G4's questions on one index: the 135 and the D5 key's questions in scope at its core size (Q105; experiment.py
    scaling_questions)."""
    from experiments.runner.experiment import scaling_questions
    core = int(index.split("_s")[1].split("_")[0])
    sets = scaling_questions(core)
    return {q["id"] for q in sets["common"]} | {q["id"] for q in sets["per_size"]}


# ------------------------------------------------------------------------------------------------ the anchor
def anchor() -> dict:
    tbl = json.loads(S04B.read_text())["3_4_evaluation_counts"]["per_experiment_table"]
    man = {}
    for ln in (REPL / "MANIFEST.sha256").read_text().splitlines():
        if ln.strip():
            h, n = ln.split(None, 1)
            man[n.strip()] = h
    rep, rep_files = 0, {}
    for n in REPL_FILES:
        p = REPL / n
        h = sha(p)
        if man.get(n) != h:
            raise Refused(f"{rel(p)} sha256 {h[:12]}, its MANIFEST.sha256 {str(man.get(n))[:12]}")
        rep += len(json.loads(p.read_text())["qwen3_results"])
        rep_files[rel(p)] = h
    a = sum(tbl[k]["records"] for k in CORE) + rep
    b = sum(tbl[k]["records_per_query"] for k in IR)
    c = sum(tbl[k]["records"] for k in SELECTION)
    s13 = json.loads(S13_JSON.read_text())
    want = {k: g["subtotal"] for k, g in s13["groups"].items()}
    got = {"A_scored_answer_evaluations": a, "B_retrieval_evaluations": b, "C_selection_and_reference_runs": c}
    bad = [f"S13 {k}: {want.get(k)}, recomputed {v}" for k, v in got.items() if want.get(k) != v]
    if a + b + c != s13["total_evaluation_runs"]:
        bad.append(f"S13 total {s13['total_evaluation_runs']}, recomputed {a + b + c}")
    s141_rows = sum(1 for _ in csv.DictReader(open(S141_CSV, newline="")))
    s187 = json.loads(S187_JSON.read_text())
    side = s187["added_by_revision"]["side_arms"]
    if s141_rows != s187["added_by_revision"]["campaign"]:
        bad.append(f"S187 campaign {s187['added_by_revision']['campaign']}, S141 rows counted {s141_rows}")
    if a + b + c + s141_rows + side != s187["total_evaluations"]:
        bad.append(f"S187 total {s187['total_evaluations']}, recomputed {a + b + c + s141_rows + side}")
    if bad:
        raise Refused("REPRODUCTION FAILED, nothing written: " + "; ".join(bad))
    return {"S13_total": a + b + c, "S13_groups": got, "replication_rows_counted": rep,
            "S141_rows_counted": s141_rows, "S187_side_arms_design_arithmetic": side,
            "S187_total": a + b + c + s141_rows + side,
            "kept": {"Model selection": c, "Retrieval optimisation": b},
            "kept_parts": {"Model selection": {k: tbl[k]["records"] for k in SELECTION},
                           "Retrieval optimisation": {k: tbl[k]["records_per_query"] for k in IR}},
            "inputs": {rel(S04B): sha(S04B), **rep_files, rel(REPL / "MANIFEST.sha256"): sha(REPL / "MANIFEST.sha256"),
                       rel(S13_JSON): sha(S13_JSON), rel(S141_CSV): sha(S141_CSV), rel(S187_JSON): sha(S187_JSON)}}


# ------------------------------------------------------------------------------------------------ the counters
def check_key(k: str, prefix: str, qids: set, where: str):
    parts = k.split("|")
    if "|".join(parts[:-2]) != prefix or parts[-2] not in qids or parts[-1] not in ("d1", "d2", "d3"):
        raise Refused(f"{where}: answer key {k!r} is not {prefix}|<question of its key>|d<1 to 3>")
    return int(parts[-1][1:])


def count_jsonl(p: Path, run_id: str, prefix: str, qids: set) -> tuple[int, Counter]:
    last = {}
    for r in jl(p):
        if r.get("run_id") != run_id:
            raise Refused(f"{rel(p)}: a row of run {r.get('run_id')!r}, not {run_id}")
        last[r["answer_key"]] = r
    draws = Counter(check_key(k, prefix, qids, rel(p)) for k in last)
    return len(last), draws


def count_results_json(p: Path, run_id: str, prefix: str, qids: set) -> tuple[int, Counter]:
    last = {}
    for r in json.loads(p.read_text())["results"]:
        if r.get("run_id") != run_id:
            raise Refused(f"{rel(p)}: a result of run {r.get('run_id')!r}, not {run_id}")
        last[r["answer_key"]] = r
    draws = Counter(check_key(k, prefix, qids, rel(p)) for k in last)
    return len(last), draws


def registry(qids: set, sums: dict) -> list:
    rows = []

    def add(exp, plan, n, basis, files, draws=None, note=None, counted=True, special=None):
        rows.append({"experiment": exp, "plan_row": plan, "counted": counted, "stored": n if counted else None,
                     "draws": dict(sorted(draws.items())) if draws else None, "basis": basis,
                     "files_sha256": files, **({"note": note} if note else {}),
                     **({"special_case": special} if special else {})})

    # G1 and G2: s457_mirror
    stem = "s457_mirror_20261022"
    base = fig_repro.frozen(stem, stem)
    for exp, plan, confs in (("Generation strategies", "G1", G1_STRATEGIES), ("Matched-budget arm", "G2",
                                                                               ["matched_budget"])):
        n, dr, files = 0, Counter(), {}
        for c in confs:
            p = base / c / "answers.jsonl"
            k, d = count_jsonl(p, f"exp_01__{c}__{INDEX}", f"{INDEX}|{c}", qids)
            n += k
            dr += d
            files[f"{stem}.tar:{p.relative_to(base.parent)}"] = sha(p)
        add(exp, plan, n, f"{stem}.tar (sha256 {tar_sha(stem, sums)[:12]}), distinct answer keys", files, dr)

    # G6 caps 5, 10, 20: answer_lengths
    stem = "answer_lengths_20261020"
    base = fig_repro.frozen(stem, f"{stem}/G6/runs")
    n, dr, files = 0, Counter(), {}
    for cap in G6_CAPS_ALL135:
        rid = f"b4_rlm_ref__cap{cap}__all135"
        p = base / rid / "answers.jsonl"
        k, d = count_jsonl(p, rid, f"cap{cap}", qids)
        n += k
        dr += d
        files[f"{stem}.tar:{stem}/G6/runs/{rid}/answers.jsonl"] = sha(p)
    add("Package RLM at caps 5 10 20", "G6", n, f"{stem}.tar (sha256 {tar_sha(stem, sums)[:12]}), distinct answer "
        "keys", files, dr)

    # G5: committed L2_d284_inputs, every draw (D287 (1)); its draw-1 file is L2_inputs' frozen one
    p1 = fig_repro.frozen("L2", G5_FILE)
    if sums.get(rel(p1)) != sha(p1):
        raise Refused(f"{rel(p1)} is not the file {rel(SUMS)} lists")
    pull = json.loads((G5_ALL / "PULL.json").read_text())["files"]
    if not tracked(G5_ALL / "PULL.json"):
        raise Refused(f"{rel(G5_ALL / 'PULL.json')} is not committed, or differs from its committed blob")
    gfiles = sorted((G5_ALL / "results_v4").glob("*.json"))
    if sorted(f.name for f in gfiles) != sorted(pull):
        raise Refused(f"{rel(G5_ALL)}: results_v4 holds {len(gfiles)} files, PULL.json lists {len(pull)}")
    if sha(G5_ALL / G5_FILE) != sha(p1):
        raise Refused(f"{rel(G5_ALL / G5_FILE)} is not {rel(p1)}")
    last, files = {}, {}
    for p in gfiles:
        h = sha(p)
        if not tracked(p) or h != pull[p.name]["sha256"]:
            raise Refused(f"{rel(p)}: not committed, or not its PULL.json sha256")
        for r in json.loads(p.read_text())["results"]:
            k = r["answer_key"]
            if k in last and last[k] != r:
                raise Refused(f"{rel(p)}: key {k} holds another row than an earlier file")
            last[k] = r
        files[rel(p)] = h
    dr = Counter()
    for k, r in last.items():
        dr[check_key(k, f"rlm_{r['depth']}", qids, rel(G5_ALL))] += 1
    add("Retrieval depth", "G5", len(last), f"committed L2_d284_inputs (PULL.json, {len(files)} files; the draw-1 "
        "file equal to L2_inputs' frozen one), distinct answer keys over every draw", files, dr)

    # T1: fig3_t1, the union of every results file
    stem = "fig3_t1"
    base = fig_repro.frozen(stem, f"{stem}/results_v4")
    last, files = {}, {}
    for p in sorted(base.glob("*.json")):
        for r in json.loads(p.read_text())["results"]:
            check_key(r["answer_key"], f"rlm_{r['depth']}", qids, rel(p))
            last[(r["model"], r["answer_key"])] = r
        files[f"{stem}.tar:{stem}/results_v4/{p.name}"] = sha(p)
    dr = Counter(int(k[1].rsplit("|d", 1)[1]) for k in last)
    per_model = Counter(m for m, _ in last)
    add("Retrieval depth, local models", "T1", len(last), f"{stem}.tar (sha256 {tar_sha(stem, sums)[:12]}): the "
        f"union of {len(files)} results files, distinct (model, answer key)", files, dr,
        note={"per_model": dict(sorted(per_model.items()))})

    # G6 depth caps: committed L2_inputs/g6, only when tracked and listed
    files, n, dr, missing = {}, 0, Counter(), []
    for cap in G6_CAPS_DEPTH:
        rid = f"b4_rlm_ref__cap{cap}__depthsweep86"
        p = REC / "L2_inputs" / "g6" / rid / "answers.jsonl"
        if not p.is_file() or not tracked(p) or sums.get(rel(p)) != sha(p):
            missing.append(rel(p))
            continue
        k, d = count_jsonl(p, rid, f"cap{cap}", qids)
        n += k
        dr += d
        files[rel(p)] = sha(p)
    if missing:
        l2 = [r for r in jl(REC / "L2" / "concept_recall.jsonl") if r["system"] == "G6" and r["cap"] in G6_CAPS_DEPTH]
        add("Package RLM depth caps", "G6", None, "not counted: the run records are in neither the repository nor "
            "a frozen set at this commit (the run's answers.jsonl files are in the gitignored findings/runs/)", {},
            counted=False, note={"missing": missing, "derived_rows_in_repo": "findings/recompute/L2/"
                                 "concept_recall.jsonl (S474) lists this run's answers, but it is a derived table, "
                                 "not the run records", "derived_rows": len(l2),
                                 "derived_rows_sha256": sha(REC / "L2" / "concept_recall.jsonl")})
    else:
        add("Package RLM depth caps", "G6", n, "committed L2_inputs/g6 (frozen, listed in SHA256SUMS), distinct "
            "answer keys", files, dr)

    # G4: g4_draws_20261101, every draw (D287 (1)); draw 1 reproduced against fig3_g4_inputs
    stem, old = G4_SET, "fig3_g4_inputs"
    base = fig_repro.frozen(stem, f"{stem}/runs")
    base1 = fig_repro.frozen(old, f"{old}/runs")
    n, dr, files = 0, Counter(), {}
    for d_ in sorted(x for x in base.iterdir() if x.is_dir()):
        rid = d_.name
        cfg, idx = rid.split("__")[1], rid.split("__")[2]
        if not (d_ / "answers.jsonl").read_bytes().startswith((base1 / rid / "answers.jsonl").read_bytes()):
            raise Refused(f"{stem}: {rid}'s answers.jsonl does not start with {old}.tar's draw-1 file")
        k, d = count_jsonl(d_ / "answers.jsonl", rid, f"{idx}|{cfg}", g4_qids(idx))
        n += k
        dr += d
        files[f"{stem}.tar:{stem}/runs/{rid}/answers.jsonl"] = sha(d_ / "answers.jsonl")
    if len(files) != 72 or len([x for x in base1.iterdir() if x.is_dir()]) != 72:
        raise Refused(f"{stem}: {len(files)} runs, want 72 (12 indexes x 6 strategies), as {old}")
    add("Corpus scaling", "G4", n, f"{stem}.tar (sha256 {tar_sha(stem, sums)[:12]}), distinct answer keys over every "
        f"draw; each run's draw-1 file of {old}.tar (sha256 {tar_sha(old, sums)[:12]}) a byte prefix", files, dr)

    g3_g9_rows(add, qids, sums)

    # S2: the runs Figure 6's manifest names, from the frozen set that manifest is written from (s2_after_s4_20261105
    # since D252, 5 Nov; s2_length_retries_20261021 before, whose answers.json no longer match the manifest)
    stem = "s2_after_s4_20261105"
    base = fig_repro.frozen(stem, stem)
    man = json.loads(FIG6_MANIFEST.read_text())
    n, per_variant, files, in_design = 0, Counter(), {}, set()
    for rid, info in sorted(man["runs"].items()):
        machine = "studio" if info["machine"] == "studio" else "laptop"
        p = base / machine / Path(info["clone"].removeprefix("~/")).name / "runs" / rid / "answers.json"
        h = sha(p)
        if h != info["files"]["answers.json"]["sha256"]:
            raise Refused(f"{rel(p)}: sha256 {h[:12]}, the manifest's {info['files']['answers.json']['sha256'][:12]}")
        keys = {a["answer_key"] for a in json.loads(p.read_text())["results"]}
        n += len(keys)
        per_variant[rid.split("__", 2)[2]] += len(keys)
        files[f"{stem}.tar:{p.relative_to(base.parent)}"] = h
        in_design.add(p.resolve())
    outside = Counter()
    for p in sorted(base.glob("*/*/runs/exp_05__*/answers.json")):
        if p.resolve() in in_design:
            continue
        rid = p.parent.name
        outside[rid.split("__", 2)[2]] += len({a["answer_key"] for a in json.loads(p.read_text())["results"]})
    add("Code generation", "S2", n, f"{stem}.tar (sha256 {tar_sha(stem, sums)[:12]}): the {len(man['runs'])} runs "
        f"{rel(FIG6_MANIFEST)} names, distinct answer keys", files,
        note={"per_variant": dict(sorted(per_variant.items())), "manifest_sha256": sha(FIG6_MANIFEST),
              "stored_outside_the_design": dict(sorted(outside.items())),
              "stored_outside_the_design_total": sum(outside.values()),
              "why_outside": "not among the 121 runs (11 variants) Figure 7 draws: nemotron removed (D116), two "
                             "variants demoted (D100), or a variant incomplete in this 21 Oct copy"})

    i2_row(add)
    count_rows(add, qids, sums)
    status_rows(add)
    return rows


# ------------------------------------------------------------------------------------------------ G3 and G9, every draw
def last_results(p: Path, run_id: str) -> dict:
    """{answer key: its last result} of an answers.json, refused on a result of another run."""
    last = {}
    for r in json.loads(p.read_text())["results"]:
        if r.get("run_id") != run_id:
            raise Refused(f"{rel(p)}: a result of run {r.get('run_id')!r}, not {run_id}")
        last[r["answer_key"]] = r
    return last


def g3_g9_rows(add, qids: set, sums: dict, base: Path | None = None):
    """G3's two rows and G9 from count_records_20261108.tar's g3/runs, every draw (Valerio, 8 Nov: these draws are in
    Source Data Fig. 5, sheet Fig. 5a). REPRODUCE FIRST: the earlier sources, fig4_records_1023.tar (G3) and the
    committed g9_inputs (G9), are counted as before and must give G3_G9_BEFORE; every key they hold must hold the same
    row in the new set; the new set holds exactly the ten set-ups. base: the set's g3/runs (the test's mutant); None
    reads the frozen set."""
    stem = COUNT_SET_1108
    if base is None:
        base = fig_repro.frozen(stem, f"{stem}/g3/runs")
    old = fig_repro.frozen("fig4_records_1023", "fig4_records_1023/findings/runs")
    groups = (("Pipeline ablation", "G3", G3_SETUPS), ("No retrieval and naive RAG", "G3", G3_BASELINES),
              ("Distiller on every step (stress)", "G9", G9_SETUPS))
    want_runs = {f"exp_03__{c}__{INDEX}" for _, _, cs in groups for c in cs}
    have_runs = {d.name for d in base.iterdir() if d.is_dir()}
    if have_runs != want_runs:
        raise Refused(f"{stem}: g3/runs holds {sorted(have_runs ^ want_runs)} beyond or short of the ten set-ups")
    for exp, plan, confs in groups:
        n, n_before, dr, files, per_setup = 0, 0, Counter(), {}, {}
        for c in confs:
            rid = f"exp_03__{c}__{INDEX}"
            p = base / rid / "answers.json"
            if plan == "G9":
                q = fig_repro.check_committed(fig_repro.frozen("g9", f"runs/{rid}/answers.json"))
                q_name = rel(q)
            else:
                q = old / rid / "answers.json"
                q_name = f"fig4_records_1023.tar:fig4_records_1023/findings/runs/{rid}/answers.json"
            before = last_results(q, rid)
            for k in before:
                check_key(k, f"{INDEX}|{c}", qids, q_name)
            now = last_results(p, rid)
            changed = [k for k, r in before.items() if now.get(k) != r]
            if changed:
                raise Refused(f"{rel(p)}: {len(changed)} key(s) of {q_name} missing or holding another row, e.g. "
                              f"{changed[0]}")
            k, d = count_results_json(p, rid, f"{INDEX}|{c}", qids)
            n += k
            n_before += len(before)
            dr += d
            per_setup[c] = dict(sorted(d.items()))   # D309 N5 O1: each set-up's answer records per draw
            files[f"{stem}.tar:{stem}/g3/runs/{rid}/answers.json"] = sha(p)
            files[q_name] = sha(q)
        if n_before != G3_G9_BEFORE[exp]:
            raise Refused(f"{exp}: the earlier source counts {n_before}, the committed registry {G3_G9_BEFORE[exp]}")
        add(exp, plan, n, f"{stem}.tar (sha256 {tar_sha(stem, sums)[:12]}): g3/runs, distinct answer keys over every "
            f"draw; the {n_before} keys of the earlier source ({G3_G9_BEFORE_SOURCE[plan]}) reproduced, each holding "
            "the same row", files, dr, note={"per_setup_draws": per_setup})


# ------------------------------------------------------------------------------------------------ D281's counters
def last_rows(p: Path, run_id: str) -> dict:
    """{answer key: its last row} of an answers.jsonl, refused on a row of another run."""
    last = {}
    for r in jl(p):
        if r.get("run_id") != run_id:
            raise Refused(f"{rel(p)}: a row of run {r.get('run_id')!r}, not {run_id}")
        last[r["answer_key"]] = r
    return last


def no_text(r: dict) -> bool:
    g = r.get("generation")
    return not (g.get("answer") if isinstance(g, dict) else None)


def committed_keys(paths: list, field: str = "answer_key", pick=lambda x: True) -> tuple[set, dict]:
    """{(run_id, answer key)} of committed rows, each file tracked by git and unchanged; and {file: sha256}."""
    out, files = set(), {}
    for sub in paths:
        p = REC / sub
        if not tracked(p):
            raise Refused(f"{rel(p)} is not committed, or differs from its committed blob")
        for x in jl(p):
            if pick(x):
                out.add((x["run_id"], x[field]))
        files[rel(p)] = sha(p)
    return out, files


def reproduce_keys(where: str, rec: dict, known: set, allow_unread: bool) -> list:
    """rec {(run_id, key): row} must equal known; a stored key the known rows lack is allowed only when allow_unread
    and its generation text is empty (the judge reads no empty answer). Returns those keys."""
    extra, missing = set(rec) - known, known - set(rec)
    unread = sorted(k for k in extra if allow_unread and no_text(rec[k]))
    if missing or set(extra) - set(unread):
        raise Refused(f"{where}: stored keys differ from the committed rows: {len(missing)} only in the rows "
                      f"({sorted(missing)[:2]}), {len(extra) - len(unread)} only in the records "
                      f"({sorted(set(extra) - set(unread))[:2]})")
    return ["|".join(k) for k in unread]


def t2x_questions() -> set:
    """D241's 17 question ids, refused unless the file is committed and holds n = 17 ids."""
    if not tracked(T2X_QUESTIONS):
        raise Refused(f"{rel(T2X_QUESTIONS)} is not committed, or differs from its committed blob")
    q = json.loads(T2X_QUESTIONS.read_text())
    ids = set(q["ids"])
    if len(ids) != q["n"] or q["n"] != 17:
        raise Refused(f"{rel(T2X_QUESTIONS)}: {len(ids)} ids, n {q['n']}, want 17")
    return ids


def t2x_part(g: str, t2_keys: set, sums: dict, base: Path | None = None) -> tuple[dict, Counter, dict]:
    """T2X's answers of one local generator: RLM-10, draw 1, D241's 17 questions, from count_records_20261108.tar's
    t2x/<generator>/runs. REPRODUCE FIRST: the keys equal the main judge's committed T2X collect (17 rows), and none is
    a key T2's own records hold. base: the set's t2x folder (the test's mutant); None reads the frozen set."""
    stem = COUNT_SET_1108
    if base is None:
        base = fig_repro.frozen(stem, f"{stem}/t2x")
    rid = f"exp_01__{T2X_CONFIG}__{INDEX}+{g}"
    p = base / g / "runs" / rid / "answers.jsonl"
    qx = t2x_questions()
    rec, dr = {}, Counter()
    where = f"{stem}.tar:{stem}/t2x/{g}/runs/{rid}/answers.jsonl"
    for k, r in last_rows(p, rid).items():
        dw = check_key(k, f"{INDEX}|{T2X_CONFIG}", qx, where)
        if dw != 1:
            raise Refused(f"{where}: key {k} is not draw 1")
        if (rid, k) in t2_keys:
            raise Refused(f"{where}: key {k} is also in T2's records")
        dr[dw] += 1
        rec[(rid, k)] = r
    known, cf = committed_keys([T2X_GENERATORS[g]])
    reproduce_keys(f"T2X {g}", rec, known, allow_unread=False)
    if len(rec) != 17:
        raise Refused(f"{where}: {len(rec)} keys, want 17")
    return rec, dr, {where: sha(p), **cf}


def count_rows(add, qids: set, sums: dict, base: Path | None = None):
    """D281: T3's two rows, T2, G10, G11, G17, G19 and S12, in STATUS_ONLY's former order. base: the tar's top folder
    (the test's mutant); None reads the frozen set."""
    stem = COUNT_SET
    if base is None:
        base = fig_repro.frozen(stem, stem)
    tar_h = tar_sha(stem, sums)
    t = lambda p: f"{stem}.tar:{p.relative_to(base.parent)}"   # noqa: E731

    # T3: every sink of the set's MANIFEST.json; keys <model>|<item>|d<n>, the model the sink's
    t3 = base / T3_DIR
    man = json.loads((t3 / "MANIFEST.json").read_text())["answers_per_sink"]
    for exp, pre, want in T3_ROWS:
        n, dr, files, per_model = 0, Counter(), {}, Counter()
        for sink, n_man in sorted(man.items()):
            if not sink.startswith(pre):
                continue
            p = t3 / "sinks" / sink / "answers.jsonl"
            rows_ = jl(p)
            last = last_rows(p, sink)
            model = sink.split("__")[-1]
            for k in last:
                parts = k.split("|")
                if len(parts) != 3 or parts[0] != model or parts[2] not in ("d1", "d2", "d3"):
                    raise Refused(f"{t(p)}: answer key {k!r} is not {model}|<item>|d<1 to 3>")
                dr[int(parts[2][1:])] += 1
            if len(last) != len(rows_) or len(last) != n_man:
                raise Refused(f"{t(p)}: {len(rows_)} rows, {len(last)} keys, MANIFEST.json {n_man}")
            n += len(last)
            per_model[model] += len(last)
            files[t(p)] = sha(p)
        if n != want:
            raise Refused(f"{exp} (T3): {n} stored, draws.csv's design gives {want}")
        add(exp, "T3", n, f"{stem}.tar (sha256 {tar_h[:12]}): {T3_DIR}, each sink's rows equal to its MANIFEST.json "
            "answers_per_sink, distinct answer keys", files, dr, note={"per_model": dict(sorted(per_model.items()))})

    # T2: four generators x six strategies; reproduced against the judge's committed collects
    n, dr, files, per_gen, unread, per_t2x = 0, Counter(), {}, {}, [], {}
    for g in T2_GENERATORS:
        rec = {}
        for c in G1_STRATEGIES:
            rid = f"exp_01__{c}__{INDEX}+{g}"
            p = base / "t2" / g / "runs" / rid / "answers.jsonl"
            last = last_rows(p, rid)
            for k in last:
                dr[check_key(k, f"{INDEX}|{c}", qids, t(p))] += 1
                rec[(rid, k)] = last[k]
            files[t(p)] = sha(p)
        known, cf = committed_keys(T2_COLLECTS[g])
        unread += reproduce_keys(f"T2 {g}", rec, known, allow_unread=True)
        files.update(cf)
        per_gen[g] = len(rec)
        n += len(rec)
        t2_keys = {k for k in rec}
        if g in T2X_GENERATORS:
            x_rec, x_dr, x_files = t2x_part(g, t2_keys, sums)
            per_t2x[g] = len(x_rec)
            per_gen[g] += len(x_rec)                  # per_generator sums to the row's count, T2X included
            n += len(x_rec)
            dr += x_dr
            files.update(x_files)
    add("Strategy replication", "T2", n, f"{stem}.tar (sha256 {tar_h[:12]}): t2/<generator>/runs, distinct answer "
        "keys, equal to the judge's committed collects but for answers with no text; with T2X (D241), RLM-10 of "
        f"gemma3:27b and qwen3-coder:30b on the 17 many-paper questions outside D98's subset, from {COUNT_SET_1108}.tar "
        f"(sha256 {tar_sha(COUNT_SET_1108, sums)[:12]}): t2x/<generator>/runs, equal to the judge's committed T2X "
        "collects", files, dr,
        note={"per_generator": per_gen, "t2x_per_generator": per_t2x, "t2x_total": sum(per_t2x.values()),
              "t2x_why": "in Figure 3e and Supplementary Figure 6 (S518's t2x_rows; Valerio, 8 Nov: a stored set "
                         "counts when it is in a figure or a table)",
              "stored_with_no_text_not_judged": unread})

    # G10 and G11: reproduced against S600's frozen collects
    for exp, plan, sub, cfg, coll in G10_G11:
        rec, dr, files = {}, Counter(), {}
        for rd in sorted(x for x in (base / sub / "runs").iterdir() if x.is_dir()):
            idx = rd.name.split("__")[2]
            if rd.name != f"exp_01__{cfg}__{idx}":
                raise Refused(f"{t(rd)}: not a run of {cfg}")
            p = rd / "answers.jsonl"
            last = last_rows(p, rd.name)
            for k in last:
                dr[check_key(k, f"{idx}|{cfg}", g4_qids(idx), t(p))] += 1
                rec[(rd.name, k)] = last[k]
            files[t(p)] = sha(p)
        known, cf = committed_keys([coll])
        un = reproduce_keys(plan, rec, known, allow_unread=True)
        files.update(cf)
        add(exp, plan, len(rec), f"{stem}.tar (sha256 {tar_h[:12]}): {sub}/runs, distinct answer keys, equal to the "
            "judge's committed collect (S600)", files, dr, note={"stored_with_no_text_not_judged": un} if un else None)

    # G17: committed run records, each file equal to its folder's MANIFEST.sha256; reproduced against S573's rows
    rec, dr, files = {}, Counter(), {}
    for sub, draws_ in G17_DIRS:
        d = REC / "G17_runs" / sub
        mans = {}
        for ln in (d / "MANIFEST.sha256").read_text().splitlines():
            if ln.strip():
                h, f = ln.split(None, 1)
                mans[f.strip()] = h
        for arm in G17_ARMS:
            rid = f"exp_01__{arm}__{INDEX}"
            p = d / "runs" / rid / "answers.jsonl"
            if not tracked(p) or mans.get(f"runs/{rid}/answers.jsonl") != sha(p):
                raise Refused(f"{rel(p)}: not committed, or not its MANIFEST.sha256 line")
            for k, r in last_rows(p, rid).items():
                dw = check_key(k, f"{INDEX}|{arm}", qids, rel(p))
                if dw not in draws_ or (rid, k) in rec:
                    raise Refused(f"{rel(p)}: key {k} outside draws {draws_} or stored twice")
                dr[dw] += 1
                rec[(rid, k)] = r
            files[rel(p)] = sha(p)
    known, cf = committed_keys(G17_ROWS)
    reproduce_keys("G17", rec, known, allow_unread=False)
    files.update(cf)
    add("RLM ablation", "G17", len(rec), "committed G17_runs/inputs (draw 1) and inputs_d23 (draws 2 and 3), each "
        "equal to its MANIFEST.sha256, distinct answer keys, equal to S573's concept-recall rows", files, dr)

    # G19: arms A, B and C; reproduced against S573's rows of those arms
    rec, dr, files = {}, Counter(), {}
    for rid, prefix, _arm in G19_RUNS:
        p = base / "g19" / "runs" / rid / "answers.jsonl"
        for k, r in last_rows(p, rid).items():
            dr[check_key(k, prefix, qids, t(p))] += 1
            rec[(rid, k)] = r
        files[t(p)] = sha(p)
    known, cf = committed_keys([G19_ROWS], pick=lambda x: x["arm"] in ("A", "B", "C"))
    reproduce_keys("G19", rec, known, allow_unread=False)
    files.update(cf)
    n19 = len(rec)
    # G20 (D309 A26 O1): the same three arms with qwen3-coder:30b, from count_records_20261109.tar; reproduced against
    # S594's rows of those arms
    stem20 = COUNT_SET_1109
    base20 = fig_repro.frozen(stem20, stem20)
    rec20 = {}
    for rid, prefix, _arm in G20_RUNS:
        p = base20 / "g20" / "runs" / rid / "answers.jsonl"
        for k, r in last_rows(p, rid).items():
            dr[check_key(k, prefix, qids, f"{stem20}.tar:{p.relative_to(base20.parent)}")] += 1
            rec20[(rid, k)] = r
        files[f"{stem20}.tar:{p.relative_to(base20.parent)}"] = sha(p)
    known20, cf20 = committed_keys([G20_ROWS], pick=lambda x: x["arm"] in ("A", "B", "C"))
    reproduce_keys("G20", rec20, known20, allow_unread=False)
    files.update(cf20)
    add("RLM ablation, local generators", "G19, G20", n19 + len(rec20),
        f"{stem}.tar (sha256 {tar_h[:12]}): g19/runs (gemma3:27b) and {stem20}.tar (sha256 "
        f"{tar_sha(stem20, sums)[:12]}): g20/runs (qwen3-coder:30b), arms A (package RLM), B and C, distinct answer "
        "keys, equal to S573's and S594's concept-recall rows", files, dr,
        note={"per_model": {"gemma3-27b": n19, "qwen3-coder-30b": len(rec20)}})

    # S12: no answer of its own
    s18 = json.loads(S18F.read_text())
    if not tracked(S18F) or s18["analysis_set"]["answers"] != S12_ANSWERS:
        raise Refused(f"{rel(S18F)}: not committed, or its analysis set is not {S12_ANSWERS} answers")
    add("Judge with evidence", "S12", 0, f"no answer of its own: judge calls on {S12_ANSWERS} of G1's draw-1 answers "
        f"({rel(S18F)} analysis_set), counted in G1", {rel(S18F): sha(S18F)}, special=S12_SPECIAL)


def i2_key() -> tuple[set, str]:
    """I2's own key, PB v1.1: its question ids and sha256, refused unless plant_key.py's pin and the file's sha256 are
    I2_KEY_SHA256 (the pin S569 checks) and it holds five questions."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("plant_key", I2_KEY_PY)
    pk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pk)
    if pk.KEY_SHA256 != I2_KEY_SHA256:
        raise Refused(f"{rel(I2_KEY_PY)} pins {pk.KEY_SHA256[:12]}, not PB v1.1's {I2_KEY_SHA256[:12]}")
    try:
        k = pk.load(pk.KEY, I2_KEY_SHA256)
    except pk.KeyProblem as e:
        raise Refused(f"PB v1.1: {e}") from None
    ids = set(k.ids)
    if len(ids) != 5:
        raise Refused(f"PB v1.1 gives {len(ids)} questions, want 5")
    return ids, k.sha256


def i2_row(add, base: Path | None = None):
    """I2 (D232): the six configs' answers.jsonl in the committed frozen set i2, each file checked against
    frozen_inputs/SHA256SUMS (check_committed), each key against PB v1.1; 15 per config, 90 in all, or refused.
    base: a folder laid out as the set (the test's mutant); None reads the frozen set."""
    qids, key_sha = i2_key()
    n, dr, files = 0, Counter(), {}
    for c in I2_CONFIGS:
        rid = f"exp_01__{c}__{I2_INDEX}"
        sub = f"sinks/{rid}/answers.jsonl"
        p = fig_repro.check_committed(fig_repro.frozen(I2_SET, sub)) if base is None else base / sub
        k, d = count_jsonl(p, rid, f"{I2_INDEX}|{c}", qids)
        if k != I2_PER_CONFIG:
            raise Refused(f"{rel(p)}: {k} distinct answer keys, want {I2_PER_CONFIG} (5 questions x 3 draws)")
        n += k
        dr += d
        files[rel(p)] = sha(p)
    add("Plant-science reuse demonstration", "I2", n, "committed i2_inputs (frozen by S569, ecf1e368, listed in "
        "SHA256SUMS), distinct answer keys, checked against I2's own key PB v1.1", files, dr,
        note={"key": rel(I2_KEY_PY.parent / "key_v1_1.json"), "key_sha256": key_sha, "questions": sorted(qids)},
        special=I2_SPECIAL)


def status_rows(add):
    """The registry rows of STATUS_ONLY, through registry()'s add(). Audit 27 Oct F5: the status is read from draws.csv
    (its first word, so a count inside the cell does not change this output), not written here: T2 has been running
    since 26 Oct while this said "no run yet"."""
    for exp, plan in STATUS_ONLY:
        word = draws_status(exp, plan)
        if word in NOT_RUN:
            add(exp, plan, 0, f"no run yet (experiments/draws.csv status: {word})", {})
        else:
            add(exp, plan, 0, f"{word} (experiments/draws.csv status), not frozen: its records are in neither the "
                f"repository nor a frozen set, so not counted", {}, counted=False)


def draws_status(exp: str, plan: str) -> str:
    """The first word of experiments/draws.csv's status for this experiment and plan row ("open", "planned",
    "running", "done", ...); refused unless exactly one row matches."""
    rows = [r for r in csv.DictReader(DRAWS.open(newline="", encoding="utf-8"))
            if r["experiment"] == exp and r["plan_row"] == plan]
    if len(rows) != 1:
        raise Refused(f"{rel(DRAWS)}: {len(rows)} rows for {exp} ({plan}), want 1")
    word = re.match(r"[a-z-]*", rows[0]["status"].strip().lower()).group(0)
    if not word:
        raise Refused(f"{rel(DRAWS)}: {exp} ({plan}) has status {rows[0]['status']!r}, not a word")
    return word


def build() -> dict:
    sums = listed_sha()
    anc = anchor()
    qids = key()
    rows = registry(qids, sums)
    new = sum(r["stored"] for r in rows if r["counted"])
    kept = sum(anc["kept"].values())
    not_counted = [r["experiment"] + " (" + r["plan_row"] + ")" for r in rows if not r["counted"]]
    by_exp = {f"{r['experiment']} ({r['plan_row']})": r["stored"] for r in rows}
    compare = {
        "stored_new": {"computed": new, "inventory": INVENTORY_F15["stored_new"],
                       "equal": new == INVENTORY_F15["stored_new"]},
        "kept": {"computed": kept, "inventory": INVENTORY_F15["kept"], "equal": kept == INVENTORY_F15["kept"]},
        "total": {"computed": new + kept, "inventory": INVENTORY_F15["total"],
                  "equal": new + kept == INVENTORY_F15["total"]},
        "count50k_md_F4_stored_today_by_group": COUNT50K_STORED,
        "why_they_differ": "the inventory's 23,062 is experiments/progress.csv's tally (26 Oct 00:20), not a count "
                           "of records; it holds T1 at 320 (25 Oct 21:13), where the frozen fig3_t1.tar holds 360; "
                           "every other experiment's count equals it (G6's depth caps 1,806 included), "
                           "except I2's 90, counted here since D232 (4 Nov), and T3, T2, G10, G11, G17, G19 and S12, "
                           "counted since D281 (6 Nov), none of them in the 26 Oct tally, G5's and G4's draws 2 "
                           "and 3, counted since D287 (1) (7 Nov), where the tally holds their draw 1, and G3's and "
                           "G9's draws 2 and 3 and T2X, counted since 8 Nov (Valerio: a set in a figure or a table "
                           "counts)",
    }
    return {
        "header": {"script": rel(Path(__file__)), "script_sha256": sha(Path(__file__)),
                   "command": "uv run python scripts/S492_answer_registry.py",
                   "anchor_inputs": anc["inputs"], "frozen_sums": {rel(SUMS) + " (entries read)": "see per file",
                                                                   "tars": {s: tar_sha(s, sums) for s in sorted(
                                                                       {k.split(".tar:")[0] for r in rows
                                                                        for k in r["files_sha256"] if ".tar:" in k})}},
                   "unit": "S13: one generation row, one evaluation item under one configuration, counted whether "
                           "or not a judge scored it, the not-answerable half included; not judge calls"},
        "anchor": {k: v for k, v in anc.items() if k != "inputs"},
        "today": {"experiments": rows, "kept_from_april": anc["kept"], "stored_new_counted": new,
                  "total_counted": new + kept, "not_counted": not_counted, "by_experiment": by_exp},
        "inventory_compare": compare,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="compare with the committed output, write nothing")
    a = ap.parse_args(argv)
    try:
        doc = build()
    except (Refused, fig_repro.FrozenInputError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    an = doc["anchor"]
    print(f"reproduced: S13 {an['S13_total']:,} ({', '.join(f'{v:,}' for v in an['S13_groups'].values())}); "
          f"with S141's {an['S141_rows_counted']:,} rows and S187's {an['S187_side_arms_design_arithmetic']} side "
          f"arms, {an['S187_total']:,}")
    text = json.dumps(doc, indent=1) + "\n"
    target = OUT / "registry.json"
    if a.check:
        ok = target.exists() and target.read_text() == text
        print(f"{rel(target)} {'byte-equal' if ok else 'DIFFERS'}")
        return 0 if ok else 1
    OUT.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    t = doc["today"]
    for r in t["experiments"]:
        print(f"  {r['plan_row']:3s} {r['experiment']:40s} {'not counted' if not r['counted'] else format(r['stored'], ',')}")
    print(f"stored new {t['stored_new_counted']:,} + kept {sum(t['kept_from_april'].values()):,} = "
          f"{t['total_counted']:,}; not counted: {', '.join(t['not_counted']) or 'none'}")
    print(f"wrote {rel(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
