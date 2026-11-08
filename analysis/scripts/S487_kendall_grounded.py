#!/usr/bin/env python3
"""S487 - Figure 5's agreement numbers with grounding against the papers (inventory row F10), from committed files.

WHY. experiments/LIST.md:157-163 (Figure 5, Found) states three numbers that a scratch computation of 14 October
gave: Kendall's W falls to 0.44 when grounding is measured against the papers (S19), 269 of 516 answers get a split
verdict, and verified pass is best by grounding (+0.22 over RLM-10). The code that gave them is lost; its text output
is ~/Mentori_scratch_keep/figures_reviewers_2026-10-14/E_signals.txt (lines 62-70, 93-104, 219-221, 258-261), which
this script does not read. D155 Q1 ("rewrite", experiments/README.md, D155) asks for them as a script. This script
computes them from S406's committed per-answer table by the rules of experiments/LIST.md and prints each beside the
value the inventory (findings/audits/scratch_repro_2026-10-26/INVENTORY.md, F10) carries. It rules nothing.

    uv run python scripts/S487_kendall_grounded.py

INPUTS (every one committed; none is opened that git does not hold)
  findings/recompute/S406_exp04_per_answer_v24.csv   one row per exp04 answer on key v2.4, devstral the judge
  findings/recompute/S406_exp04_per_answer_v24.json  S406's provenance: the csv's sha256 (G1)
  data/ground_truth_v2/all_v2_4.json, ground_truth_v2_4_as_v1.json
                                                     the v2.4 key and its v1-format copy: the csv's "# key" line holds
                                                     their sha256 (G1); answer types (G2, Rule 8)
  findings/recompute/S19_minicheck_source_k3.jsonl   S19's MiniCheck against each question's source papers, top 3
                                                     chunks per sentence: the grounding column of the csv is checked
                                                     against it row by row (G3)
  findings/recompute/S26_signal_redundancy.json      the submitted per-configuration means of the three signals
  findings/recompute/S318_statistics_ledger.json     the submitted W and its exact P, as S318 recomputed them (G4)
  S406's csv is read directly, not through phase3_common.exp04_table(): that function and phase3_common.provenance()
  open the merged S388 ledgers, which git does not hold (judged_ledger.py:15-16). The judge scores are therefore the
  ones S406 wrote on 13 October after its own gates; this script does not check them against a ledger.

SIGNALS (per answer, columns of the csv)
  judge         judge_correctness, devstral, 0 to 5
  deterministic det_score_correctness_simfull, the deposited scorer's correctness on v2.4 (S318's
                det_score_correctness_fullsim on v1); det_concept_recall_loose is given as a variant (E_signals line 220
                names "deterministic or loose recall")
  key           mc_key_f1, MiniCheck against the 2.5-sentence answer key: the submitted third signal (S287:133)
  papers        mc_source_k3_precision, MiniCheck against the question's source papers (S19)

METHOD
  Group: the answerable questions of key v2.4 (Rule 8, LIST.md:333-350): 86 questions x 6 configurations, one answer
  each (one draw: the deposited exp04 run).
  W (Rule 7, LIST.md:315-331): a signal's score for a configuration is its mean over the configuration's 86 answers;
    the six means are ranked (scipy rankdata, ties averaged), and W = 12 S / (k^2 (n^3 - n)) with no tie correction,
    as scripts/s318/g3_ranking.py:55-58. Its P is the exact permutation P of g3_ranking.py:61-72 (the first signal's
    ranks fixed, the other two over every untied ordering of 1..6, 720^2 = 518,400 pairs, upper tail). The signals
    enter in S318's order (deterministic, judge, MiniCheck); the configurations in S318's order (g3_ranking.py:40).
  Split verdicts (E_signals F1, lines 62-70): an answer passes the judge at correctness >= T, passes concept recall
    at det_concept_recall_loose >= 0.5, and passes grounding at mc_source_k3_precision >= 0.5. It has a split verdict
    unless all three pass or all three fail. T = 3 is E_signals' threshold (S406's passed column, judged_ledger
    PASS_AT 3) and gives the inventory's number; T = 4 is Rule 5's primary threshold since D154 (LIST.md:291-299),
    given beside it. The 0.5 cut-offs are E_signals'; no rule of LIST.md fixes them.
  Verified pass against RLM-10 (E_signals F7, lines 93-104): the mean over the 86 questions of the per-question
    difference (verified pass minus RLM-10) in MiniCheck-source precision, and in judge pass at T = 3 and T = 4.
  Intervals (Rules 1, 2 and 7): 95% percentile interval (numpy.percentile, linear) over 10,000 question resamples,
    numpy.random.default_rng(20261013).integers(0, 86, size=(10000, 86)) over the 86 sorted question ids, S407's
    method and seed (S407_strategy_contrasts_v24.py:190, :249). E_signals used 2,000 resamples with seed 20261014,
    so its interval is printed beside this one and is not expected to be equal. W gets the same interval.

GATES (one line each; a failed gate stops the run and nothing is written)
  G1 inputs: the csv's sha256 is the one S406's json records for it; its "# key" line names the two key files with
     the sha256 they have.
  G2 table: 807 rows; 516 in the group answerable, on 86 questions x 6 configurations, one row each, status ok, every
     signal a finite number in its range; each answerable row's answer_type is the v2.4 key's (extractive or
     synthesis), and no exp04 question of those types is outside the group; passed is correctness >= 3 on every row.
  G3 grounding: each of the 516 rows has exactly one S19 source top-3 row of its question and configuration, with
     the same precision and the same claim count.
  G4 REPRODUCE: S26's submitted means give W 0.926984126984127 and exact P 0.00018132716049382717 under this
     script's functions, the values S318's ledger holds for kendall_w_three_signals; a script that does not
     reproduce the submitted W writes nothing.

KEY v2.5 (D188, Valerio, 31 October: "every figure using v2.4 needs to move to v2.5"). Once G1 to G4 have passed on
key v2.4, G5 reads S516's table (findings/recompute/S516_exp04_per_answer_v25.csv, scripts/S516_exp04_per_answer_v25.py)
and the same numbers are computed again from it as numbers_v25, with concept recall D181's reading on key v2.5
(concept_recall_d181) in place of det_concept_recall_loose:
  G5 v2.5 table: its sha256 is the one S516's json records; its "# key" line names one file, the v2.5 key, with the
     sha256 it has and S516 pins (a4216184); it holds S406's 516 answerable answers one for one (question, configuration,
     answer type, status) with the columns it carries from S406 equal to S406's (judge correctness, deterministic
     correctness, MiniCheck against the key, MiniCheck against the papers and its claim count, the v2.4 loose recall);
     concept_recall_d181 is d181_found / d181_n_counted to four decimals on every row; every row is in the group
     answerable; S516's json records S516's own sha256 and its matchers' (code_sha256), each equal to the file in the
     repository, so a changed matcher fails G5 until S516 is run again.
  The other signals are S406's key v2.4 values: S516 marks with judge_pending_v25 the answers of the questions whose
  judge fields v2.5 changed (no run has judged exp04 on v2.5), and with answer_key_pending_v25 the answers of the
  question whose expected_answer v2.5 changed (MiniCheck against the key and the deterministic correctness, whose
  bge-m3 similarity reads the expected answer). numbers_v25_status names both counts; numbers_v25 stays provisional
  until those answers are scored on v2.5.

OUTPUT findings/recompute/S487_kendall_grounded/S487_kendall_grounded.json: provenance (script and input sha256,
command, library versions; no time, so two runs give the same bytes), the gates, the anchor, the numbers (key v2.4),
the inventory comparison, and numbers_v25 with its status (key v2.5). Nothing is tuned to an inventory value: a
number that differs is reported with both values.
"""
from __future__ import annotations

import csv
import hashlib
import io
import itertools
import json
import math
import os
import re
import sys
from collections import Counter
from importlib import metadata
from pathlib import Path

import numpy as np
from scipy import stats

ME = "S487"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REC = ROOT / "findings/recompute"
S406_CSV = REC / "S406_exp04_per_answer_v24.csv"
S406_JSON = REC / "S406_exp04_per_answer_v24.json"
KEY = ROOT / "data/ground_truth_v2/all_v2_4.json"
KEY_AS_V1 = ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json"
S19_SOURCE = REC / "S19_minicheck_source_k3.jsonl"
S26 = REC / "S26_signal_redundancy.json"
S318 = REC / "S318_statistics_ledger.json"
S516_CSV = REC / "S516_exp04_per_answer_v25.csv"           # D188: the v2.5 table (scripts/S516_exp04_per_answer_v25.py)
S516_JSON = REC / "S516_exp04_per_answer_v25.json"
KEY25_AS_V1 = ROOT / "data/ground_truth_v2/ground_truth_v2_5_as_v1.json"
KEY25_SHA256 = "a42161841980792f5da521819c97b16dc54999b45838b8eb87cd4315f798270a"   # d181_concept_recall.KEY25_SHA256
OUT_DIR = REC / "S487_kendall_grounded"
OUT = OUT_DIR / "S487_kendall_grounded.json"
COMMAND = "uv run python scripts/S487_kendall_grounded.py"

CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")   # g3_ranking.py:40
S318_ORDER = ("det", "judge", "mc")                                                    # g3_ranking.py:41
COL = {"judge": "judge_correctness", "det": "det_score_correctness_simfull", "loose": "det_concept_recall_loose",
       "key": "mc_key_f1", "papers": "mc_source_k3_precision"}
COL25 = {**COL, "loose": "concept_recall_d181"}             # D188: the concept recall column of S516's table
CARRIED25 = {"answer_type": "answer_type", "status": "status", "judge_correctness": "judge_correctness",
             "det_score_correctness_simfull": "det_score_correctness_simfull", "mc_key_f1": "mc_key_f1",
             "mc_source_k3_precision": "mc_source_k3_precision", "mc_source_k3_n_claims": "mc_source_k3_n_claims",
             "det_concept_recall_loose_v24": "det_concept_recall_loose"}   # S516 column: S406 column, equal on every row
TEXT_COLS = ("question_id", "config", "group", "answer_type", "status", "judge_key_version")
RANGE = {"judge_correctness": (0, 5), "det_score_correctness_simfull": (0, 5), "det_concept_recall_loose": (0, 1),
         "mc_key_f1": (0, 1), "mc_source_k3_precision": (0, 1)}
ANSWERABLE_TYPES = ("extractive", "synthesis")
N_ROWS, N_ANSWERABLE, N_QUESTIONS = 807, 516, 86        # S406 csv's third comment line; Rule 8: 86 x 6
THRESHOLDS = (3, 4)                                     # E_signals F1 (3); Rule 5 primary since D154 (4)
CONCEPT_CUT, GROUND_CUT = 0.5, 0.5                      # E_signals F1, lines 62-63
SEED, N_BOOT, PCT = 20261013, 10000, (2.5, 97.5)        # S407_strategy_contrasts_v24.py:190-191; LIST.md Rule 7
# G4: the submitted W and its exact P (untied null) as S318 holds them (S318_statistics_ledger.json, tests,
# id kendall_w_three_signals, full.W and full.P_untied_null; Figure 5 legend 'Kendall's W over the three rankings is 0.927')
ANCHOR_ID = "kendall_w_three_signals"
ANCHOR_W, ANCHOR_P = 0.926984126984127, 0.00018132716049382717
# the inventory's values (INVENTORY.md F10; experiments/LIST.md:157-163; E_signals.txt lines cited)
INVENTORY = {
    "w_papers": (0.441, 3, "E_signals.txt:221 (0.441); LIST.md:157 and INVENTORY F10 (0.44)"),
    "w_papers_p": (0.28, 2, "E_signals.txt:221 (P 0.28)"),
    "w_key": (0.949, 3, "E_signals.txt:220 (0.949); INVENTORY A11 anchor variant"),
    "w_key_p": (0.0001, 4, "E_signals.txt:220 (exact permutation P 0.0001)"),
    "split_t3": (269, 0, "E_signals.txt:64; LIST.md:159; INVENTORY F10 (269 of 516)"),
    "papers_diff": (0.224, 3, "E_signals.txt:100 (+0.224); LIST.md:163 and INVENTORY F10 (+0.22)"),
    "papers_diff_ci_lo": (0.174, 3, "E_signals.txt:100 (2,000 resamples, seed 20261014)"),
    "papers_diff_ci_hi": (0.278, 3, "E_signals.txt:100 (2,000 resamples, seed 20261014)"),
    "papers_mean_verified_pass": (0.728, 3, "E_signals.txt:102 (answer mean 0.728)"),
    "pass_diff_t3_points": (-31.4, 1, "E_signals.txt:97 (-31.4 points); LIST.md:163 (31 points below RLM-10)"),
}
SPLIT_CELLS_T3 = {"judge and concepts pass, grounding fails": 97, "judge and grounding pass, concepts fail": 67,
                  "judge only": 39, "grounding only": 47, "concepts only": 11, "concepts and grounding, not the judge": 8,
                  "all three pass": 185, "all three fail": 62}          # E_signals.txt:63-70


def refuse(message: str):
    raise SystemExit(f"{ME} REFUSED: {message}")


def rel(p: Path) -> str:
    return Path(p).resolve().relative_to(ROOT).as_posix()


_SEEN: dict = {}


def read(path: Path) -> bytes:
    """The file's bytes; their sha256 is kept for provenance, and a second read that sees other bytes is refused."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        refuse(f"{rel(path)} cannot be read ({type(e).__name__})")
    sha = hashlib.sha256(raw).hexdigest()
    if _SEEN.setdefault(rel(path), sha) != sha:
        refuse(f"{rel(path)} changed during this run")
    return raw


def read_json(path: Path):
    try:
        return json.loads(read(path))
    except ValueError as e:
        refuse(f"{rel(path)} is not JSON ({e})")


class Gates:
    def __init__(self):
        self.records = []

    def gate(self, name: str, ok: bool, message: str) -> bool:
        self.records.append({"name": name, "ok": bool(ok), "message": message})
        print(f"  {'ok  ' if ok else 'FAIL'} {name}  {message}", flush=True)
        return bool(ok)

    def finish(self) -> list:
        bad = [r["name"] for r in self.records if not r["ok"]]
        if bad or not self.records:
            refuse(f"{len(bad)} of {len(self.records)} gates failed ({', '.join(bad)}); nothing is written")
        return [dict(r) for r in self.records]


# ---- statistics -------------------------------------------------------------------------------------------

def kendall_w(R) -> float:
    """W of a k x n rank matrix, no tie correction (scripts/s318/g3_ranking.py:55-58)."""
    R = np.asarray(R, float)
    k, n = R.shape
    s = R.sum(0)
    return 12 * float(((s - s.mean()) ** 2).sum()) / (k * k * (n ** 3 - n))


def w_rows(R) -> np.ndarray:
    """kendall_w of each of many k x n rank matrices, R of shape (m, k, n)."""
    R = np.asarray(R, float)
    _, k, n = R.shape
    s = R.sum(1)
    return 12 * ((s - s.mean(1, keepdims=True)) ** 2).sum(1) / (k * k * (n ** 3 - n))


def w_p_untied_null(R) -> float:
    """The exact P of g3_ranking.py:61-72 for k = 3: the first row fixed, the other two over every untied ordering of
    1..n, the share of the (n!)^2 pairs whose W is at least the observed W (less 1e-12). Vectorized over the pairs."""
    R = np.asarray(R, float)
    k, n = R.shape
    if k != 3:
        refuse(f"w_p_untied_null takes three signals, not {k}")
    obs = kendall_w(R)
    perms = np.array(list(itertools.permutations(range(1, n + 1))), float)
    s = R[0][None, None, :] + perms[:, None, :] + perms[None, :, :]
    w = 12 * ((s - s.mean(2, keepdims=True)) ** 2).sum(2) / (k * k * (n ** 3 - n))
    return int((w >= obs - 1e-12).sum()) / w.size


def ranks(means) -> list:
    return [float(x) for x in stats.rankdata(means)]


def interval(values: np.ndarray) -> list:
    return [float(v) for v in np.percentile(values, PCT)]


# ---- inputs ------------------------------------------------------------------------------------------------

def number(text: str, what: str):
    if text == "":
        return None
    try:
        v = int(text) if re.fullmatch(r"-?\d+", text) else float(text)
    except ValueError:
        return text
    if isinstance(v, float) and not math.isfinite(v):
        refuse(f"{what} is {text!r}")
    return v


def load_table(g: Gates) -> tuple[list, dict]:
    raw = read(S406_CSV)
    text = raw.decode("utf-8")
    comments = [ln for ln in text.splitlines() if ln.startswith("#")]
    body = "\n".join(ln for ln in text.splitlines() if not ln.startswith("#"))
    rows = [{c: number(v, f"{rel(S406_CSV)} {c}") if c not in TEXT_COLS else v
             for c, v in r.items()} for r in csv.DictReader(io.StringIO(body))]
    recorded = read_json(S406_JSON).get("provenance", {}).get("outputs_sha256", {}).get(rel(S406_CSV))
    key_line = [c for c in comments if c.startswith("# key ")]
    named = re.findall(r"(data/\S+\.json) sha256 ([0-9a-f]{64})", key_line[0]) if len(key_line) == 1 else []
    have = {rel(KEY_AS_V1): hashlib.sha256(read(KEY_AS_V1)).hexdigest(), rel(KEY): hashlib.sha256(read(KEY)).hexdigest()}
    key_ok = sorted(p for p, _ in named) == sorted(have) and all(have[p] == h for p, h in named)
    g.gate("G1", recorded == _SEEN[rel(S406_CSV)] and key_ok,
           f"{rel(S406_CSV)} has sha256 {_SEEN[rel(S406_CSV)][:12]}, {rel(S406_JSON)} records {str(recorded)[:12]}; its '# key' "
           f"line names {len(named)} key files" + (", each with the sha256 it has" if key_ok else ", NOT with the sha256 they have"))
    return rows, read_json(KEY)


def check_table(g: Gates, rows: list, key: dict) -> list:
    types = {r["id"]: r.get("answer_type") for r in key.get("records", []) if isinstance(r, dict)}
    A = [r for r in rows if r["group"] == "answerable"]
    cells = Counter((r["question_id"], r["config"]) for r in A)
    qs = sorted({r["question_id"] for r in A})
    problems = []
    if len(rows) != N_ROWS or len(A) != N_ANSWERABLE or len(qs) != N_QUESTIONS:
        problems.append(f"{len(rows)} rows, {len(A)} answerable on {len(qs)} questions")
    if set(cells.values()) != {1} or len(cells) != N_QUESTIONS * len(CONFIGS) or {r["config"] for r in A} != set(CONFIGS):
        problems.append("not one answer per question and configuration")
    for r in A:
        if r["status"] != "ok":
            problems.append(f"{r['question_id']} {r['config']} has status {r['status']!r}")
        for c, (lo, hi) in RANGE.items():
            v = r[c]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
                problems.append(f"{r['question_id']} {r['config']} {c} is {v!r}")
        if types.get(r["question_id"]) not in ANSWERABLE_TYPES or types[r["question_id"]] != r["answer_type"]:
            problems.append(f"{r['question_id']}: answer_type {r['answer_type']!r}, the key's {types.get(r['question_id'])!r}")
        if r["passed"] != int(r["judge_correctness"] >= 3):
            problems.append(f"{r['question_id']} {r['config']}: passed {r['passed']} at correctness {r['judge_correctness']}")
    outside = sorted({r["question_id"] for r in rows if r["group"] != "answerable" and types.get(r["question_id"]) in ANSWERABLE_TYPES})
    if outside:
        problems.append(f"{len(outside)} questions of an answerable type outside the group, the first {outside[0]}")
    g.gate("G2", not problems,
           f"{len(rows)} rows; {len(A)} answerable on {len(qs)} questions x {len(CONFIGS)} configurations, one answer each, status ok, "
           f"every signal a number in its range, answer types as the v2.4 key's (Rule 8), passed = correctness >= 3"
           + (f"; NOT SO ({len(problems)}): {problems[0]}" if problems else ""))
    return A


def load_table_v25(g: Gates, A: list) -> list:
    """G5 (module docstring, KEY v2.5): S516's table, held to its json, the v2.5 key and S406's answerable rows A."""
    raw = read(S516_CSV)
    text = raw.decode("utf-8")
    comments = [ln for ln in text.splitlines() if ln.startswith("#")]
    body = "\n".join(ln for ln in text.splitlines() if not ln.startswith("#"))
    rows = [{c: number(v, f"{rel(S516_CSV)} {c}") if c not in TEXT_COLS else v
             for c, v in r.items()} for r in csv.DictReader(io.StringIO(body))]
    j516 = read_json(S516_JSON)
    recorded = j516.get("outputs_sha256", {}).get(rel(S516_CSV))
    pv = j516.get("provenance") or {}
    code = {pv.get("script"): pv.get("script_sha256"), **(pv.get("code_sha256") or {})}
    key_line = [c for c in comments if c.startswith("# key ")]
    named = re.findall(r"(data/\S+\.json) sha256 ([0-9a-f]{64})", key_line[0]) if len(key_line) == 1 else []
    have = hashlib.sha256(read(KEY25_AS_V1)).hexdigest()
    problems = []
    if recorded != _SEEN[rel(S516_CSV)]:
        problems.append(f"{rel(S516_JSON)} records sha256 {str(recorded)[:12]}, the csv has {_SEEN[rel(S516_CSV)][:12]}")
    if named != [(rel(KEY25_AS_V1), have)] or have != KEY25_SHA256:
        problems.append(f"its '# key' line names {named}, not {rel(KEY25_AS_V1)} at the pinned {KEY25_SHA256[:12]}")
    # the code S516 was built with is the code in the repository (review of build 2, F2): a changed matcher or S516
    # makes the committed table stale, so G5 fails until S516 is run again
    stale = [c for c, h in code.items() if not c or not (ROOT / c).is_file()
             or hashlib.sha256((ROOT / c).read_bytes()).hexdigest() != h]
    if len(code) < 2 or stale:
        problems.append(f"{rel(S516_JSON)} records code that is not the repository's ({stale[:3] or 'no code record'}): "
                        f"run scripts/S516_exp04_per_answer_v25.py again")
    at = {(r["question_id"], r["config"]): r for r in A}
    seen = Counter((r.get("question_id"), r.get("config")) for r in rows)
    if len(rows) != len(A) or set(seen) != set(at) or set(seen.values()) != {1}:
        problems.append(f"{len(rows)} rows, not S406's {len(A)} answerable answers one for one")
    for r in rows:
        a = at.get((r.get("question_id"), r.get("config")))
        if a is None:
            continue                       # counted above: the rows are not S406's answerable answers one for one
        if r.get("group") != "answerable":
            problems.append(f"{r['question_id']} {r['config']}: group {r.get('group')!r}, not answerable")
            continue
        diff = [c for c, c24 in CARRIED25.items() if r.get(c) != a.get(c24)]
        if diff:
            problems.append(f"{r['question_id']} {r['config']}: {', '.join(diff)} differ from S406")
        v, n, f = r.get("concept_recall_d181"), r.get("d181_n_counted"), r.get("d181_found")
        if not isinstance(n, int) or n < 1 or not isinstance(f, int) or v != round(f / n, 4) or not 0 <= v <= 1:
            problems.append(f"{r['question_id']} {r['config']}: concept_recall_d181 {v!r} is not found {f!r} over "
                            f"n_counted {n!r}")
        if r.get("judge_pending_v25") not in (0, 1) or r.get("answer_key_pending_v25") not in (0, 1):
            problems.append(f"{r['question_id']} {r['config']}: a pending flag that is not 0 or 1")
    g.gate("G5", not problems,
           f"v2.5 table {rel(S516_CSV)} (sha256 {_SEEN[rel(S516_CSV)][:12]}, as {rel(S516_JSON)} records), key "
           f"{rel(KEY25_AS_V1)} sha256 {have[:12]}: {len(rows)} rows, S406's answerable answers one for one, each "
           f"in the group answerable, the carried columns equal to S406's, concept_recall_d181 = d181_found / "
           f"d181_n_counted on every row; the {len(code)} code files S516 records equal to the repository's"
           + (f"; NOT SO ({len(problems)}): {problems[0]}" if problems else ""))
    return [r for r in rows if r.get("group") == "answerable"]


def status_v25(A25: list) -> dict:
    """What of numbers_v25 is still on key v2.4 (S516's pending flags), and whether it is provisional."""
    jp = [r for r in A25 if r["judge_pending_v25"]]
    kp = [r for r in A25 if r["answer_key_pending_v25"]]
    return {"provisional": bool(jp or kp),
            "concept_recall": "D181's reading on key v2.5 on every answer (concept_recall_d181)",
            "judge_correctness_on_v24": {"answers": len(jp), "questions": len({r["question_id"] for r in jp}),
                                         "why": "the questions whose judge fields v2.5 changed (S512.changed_ids); "
                                                "no run has judged exp04 on key v2.5"},
            "answer_key_signals_on_v24": {"answers": len(kp), "questions": sorted({r["question_id"] for r in kp}),
                                          "columns": [COL25["key"], COL25["det"]],
                                          "why": "the question whose expected_answer v2.5 changed: MiniCheck against "
                                                 "the key and the bge-m3 similarity in the deterministic correctness "
                                                 "read it"},
            "unchanged_by_v25": [COL25["papers"]]}


def check_grounding(g: Gates, A: list) -> None:
    s19 = Counter()
    by = {}
    for n, ln in enumerate(read(S19_SOURCE).decode("utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            refuse(f"{rel(S19_SOURCE)} line {n} is not JSON")
        if r.get("condition") == "source" and r.get("mode") == "top-3":
            k = (r.get("question_id"), r.get("config"))
            s19[k] += 1
            by[k] = r
    off = [f"{r['question_id']} {r['config']}" for r in A
           if s19[(r["question_id"], r["config"])] != 1
           or by[(r["question_id"], r["config"])].get("precision") != r["mc_source_k3_precision"]
           or by[(r["question_id"], r["config"])].get("n_claims") != r["mc_source_k3_n_claims"]]
    g.gate("G3", not off,
           f"{len(A) - len(off)} of {len(A)} answerable rows have exactly one S19 source top-3 row ({rel(S19_SOURCE)}, "
           f"{sum(s19.values())} rows) with the same precision and claim count" + (f"; NOT SO, the first {off[0]}" if off else ""))


def reproduce(g: Gates) -> dict:
    """G4: the submitted W from S26's means, against S318's ledger and the typed constants."""
    means = read_json(S26).get("per_config_means", {})
    entry = [t for t in read_json(S318).get("tests", []) if isinstance(t, dict) and t.get("id") == ANCHOR_ID]
    full = entry[0].get("full", {}) if len(entry) == 1 else {}
    try:
        R = [ranks([means[s][c] for c in CONFIGS]) for s in S318_ORDER]
    except (KeyError, TypeError):
        refuse(f"{rel(S26)} holds no per_config_means for {', '.join(S318_ORDER)} over the six configurations")
    w, p = kendall_w(R), w_p_untied_null(R)
    ok = (full.get("W"), full.get("P_untied_null")) == (ANCHOR_W, ANCHOR_P) and abs(w - ANCHOR_W) <= 1e-12 and abs(p - ANCHOR_P) <= 1e-15
    g.gate("G4", ok,
           f"REPRODUCE: {rel(S26)}'s submitted means give W {w!r} and exact P {p!r}; {rel(S318)} ({ANCHOR_ID}) holds W "
           f"{full.get('W')!r} and P_untied_null {full.get('P_untied_null')!r}; typed {ANCHOR_W!r} and {ANCHOR_P!r}")
    return {"what": "the submitted Kendall's W (Figure 5d; legend 'Kendall's W over the three rankings is 0.927'), "
                    "recomputed by this script's functions from the submitted per-configuration means",
            "source_means": rel(S26), "source_value": f"{rel(S318)}, tests, id {ANCHOR_ID}, full.W and full.P_untied_null",
            "signals_in_order": list(S318_ORDER), "configs": list(CONFIGS), "ranks": R,
            "W": w, "P_exact_untied_null": p, "W_expected": ANCHOR_W, "P_expected": ANCHOR_P, "equal": ok}


# ---- the numbers -------------------------------------------------------------------------------------------

def compute(A: list, col: dict = COL, recall: str = "loose_recall") -> dict:
    """The numbers (module docstring, METHOD) from the rows A, each signal read from its column in col; recall names
    the two W variants that use the concept recall column (col["loose"])."""
    qs = sorted({r["question_id"] for r in A})
    at = {(r["question_id"], r["config"]): r for r in A}
    X = {name: np.array([[at[(q, c)][cn] for c in CONFIGS] for q in qs], float) for name, cn in col.items()}
    means = {name: [float(v) for v in x.mean(0)] for name, x in X.items()}
    M = np.random.default_rng(SEED).integers(0, len(qs), size=(N_BOOT, len(qs)))
    boot_means = {name: x[M].mean(1) for name, x in X.items()}                     # (N_BOOT, 6) per signal

    def w_block(signals: tuple) -> dict:
        R = [ranks(means[s]) for s in signals]
        Rb = np.stack([stats.rankdata(boot_means[s], axis=1) for s in signals], axis=1)
        wb = w_rows(Rb)
        return {"signals": [f"{s} ({col[s]})" for s in signals], "ranks": dict(zip([col[s] for s in signals], R)),
                "W": kendall_w(R), "P_exact_untied_null": w_p_untied_null(R), "W_interval95": interval(wb)}

    variants = {"key": ("det", "judge", "key"), "papers": ("det", "judge", "papers"),
                f"key_{recall}": ("loose", "judge", "key"), f"papers_{recall}": ("loose", "judge", "papers")}
    W = {name: w_block(sig) for name, sig in variants.items()}
    vp = CONFIGS.index("verified_pass")
    vp_rank = {col[s]: int(len(CONFIGS) + 1 - stats.rankdata(means[s])[vp]) for s in ("judge", "det", "loose", "key", "papers")}

    split = {}
    for t in THRESHOLDS:
        cells = Counter()
        for r in A:
            j, c, gr = r[col["judge"]] >= t, r[col["loose"]] >= CONCEPT_CUT, r[col["papers"]] >= GROUND_CUT
            cells[{(True, True, True): "all three pass", (False, False, False): "all three fail",
                   (True, True, False): "judge and concepts pass, grounding fails",
                   (True, False, True): "judge and grounding pass, concepts fail",
                   (True, False, False): "judge only", (False, False, True): "grounding only",
                   (False, True, False): "concepts only", (False, True, True): "concepts and grounding, not the judge"}[(j, c, gr)]] += 1
        n_split = len(A) - cells["all three pass"] - cells["all three fail"]
        split[f"threshold_{t}"] = {"judge_pass_at": t, "answers": len(A), "split": n_split, "split_share": n_split / len(A),
                                   "cells": dict(sorted(cells.items()))}

    i_vp, i_r10 = CONFIGS.index("verified_pass"), CONFIGS.index("rlm_10")

    def diff(x: np.ndarray, scale: float = 1.0) -> dict:
        d = (x[:, i_vp] - x[:, i_r10]) * scale
        return {"verified_pass": float(x[:, i_vp].mean() * scale), "rlm_10": float(x[:, i_r10].mean() * scale),
                "difference": float(d.mean()), "interval95": interval(d[M].mean(1)), "questions": len(qs)}

    contrasts = {"papers_precision": diff(X["papers"])}
    for t in THRESHOLDS:
        contrasts[f"judge_pass_points_threshold_{t}"] = diff((X["judge"] >= t).astype(float), 100.0)
    return {"questions": len(qs), "answers": len(A), "means": {col[k]: dict(zip(CONFIGS, v)) for k, v in means.items()},
            "kendall_w": W, "verified_pass_rank_high_is_1": vp_rank, "split_verdicts": split,
            "verified_pass_minus_rlm_10": contrasts}


def compare(nums: dict) -> list:
    got = {"w_papers": nums["kendall_w"]["papers"]["W"], "w_papers_p": nums["kendall_w"]["papers"]["P_exact_untied_null"],
           "w_key": nums["kendall_w"]["key"]["W"], "w_key_p": nums["kendall_w"]["key"]["P_exact_untied_null"],
           "split_t3": nums["split_verdicts"]["threshold_3"]["split"],
           "papers_diff": nums["verified_pass_minus_rlm_10"]["papers_precision"]["difference"],
           "papers_diff_ci_lo": nums["verified_pass_minus_rlm_10"]["papers_precision"]["interval95"][0],
           "papers_diff_ci_hi": nums["verified_pass_minus_rlm_10"]["papers_precision"]["interval95"][1],
           "papers_mean_verified_pass": nums["verified_pass_minus_rlm_10"]["papers_precision"]["verified_pass"],
           "pass_diff_t3_points": nums["verified_pass_minus_rlm_10"]["judge_pass_points_threshold_3"]["difference"]}
    out = []
    for name, (value, digits, source) in INVENTORY.items():
        mine = got[name]
        shown = round(mine, digits) if digits else mine
        out.append({"number": name, "inventory": value, "source": source, "this_script": mine,
                    "this_script_at_the_inventory_precision": shown, "equal": shown == value})
    cells = nums["split_verdicts"]["threshold_3"]["cells"]
    out.append({"number": "split_t3_cells", "inventory": SPLIT_CELLS_T3, "source": "E_signals.txt:63-70",
                "this_script": cells, "this_script_at_the_inventory_precision": cells, "equal": cells == SPLIT_CELLS_T3})
    return out


def versions() -> dict:
    return {m: metadata.version(m) for m in ("numpy", "scipy")}


def main() -> int:
    print(f"{ME}: Kendall's W with grounding against the papers, split verdicts, verified pass against RLM-10 (F10)", flush=True)
    g = Gates()
    rows, key = load_table(g)
    A = check_table(g, rows, key)
    check_grounding(g, A)
    anchor = reproduce(g)
    gates = g.finish()                     # G1 to G4 on key v2.4 first; G5 reads the v2.5 table only once they pass
    g5 = Gates()
    A25 = load_table_v25(g5, A)
    gates += g5.finish()
    nums = compute(A)
    inv = compare(nums)
    nums25 = compute(A25, COL25, "d181_recall")
    st25 = status_v25(A25)
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    doc = {"provenance": {"script": rel(Path(__file__)), "script_sha256": script_sha, "command": COMMAND,
                          "inputs_sha256": dict(sorted(_SEEN.items())), "libraries": versions(),
                          "seed": SEED, "resamples": N_BOOT, "no_time": "no time is written, so two runs give the same bytes"},
           "what": "Figure 5's agreement numbers (devstral, the 516 answerable exp04 answers): Kendall's W with "
                   "MiniCheck against the key and against the papers (S19), split verdicts across judge, concept recall and "
                   "grounding, and verified pass against RLM-10; numbers on key v2.4 (the inventory comparison), "
                   "numbers_v25 on key v2.5 (D188; numbers_v25_status says what is still read from v2.4). Method in "
                   "the script's docstring.",
           "gates": gates, "anchor": anchor, "numbers": nums, "inventory_comparison": inv,
           "numbers_v25_status": st25, "numbers_v25": nums25}
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    OUT_DIR.mkdir(exist_ok=True)
    tmp = OUT.with_name(OUT.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, OUT)
    k, p = nums["kendall_w"]["key"], nums["kendall_w"]["papers"]
    s3, s4 = nums["split_verdicts"]["threshold_3"], nums["split_verdicts"]["threshold_4"]
    c = nums["verified_pass_minus_rlm_10"]["papers_precision"]
    print(f"\n{ME}: written {rel(OUT)} (sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]})")
    print(f"{ME}: anchor W {anchor['W']:.6f} (submitted {ANCHOR_W:.6f}); W key {k['W']:.4f} (P {k['P_exact_untied_null']:.6f}), "
          f"W papers {p['W']:.4f} (P {p['P_exact_untied_null']:.4f}); split {s3['split']} of {s3['answers']} at 3, {s4['split']} at 4; "
          f"verified pass minus RLM-10 on grounding {c['difference']:+.4f} ({c['interval95'][0]:+.4f} to {c['interval95'][1]:+.4f})")
    for x in inv:
        if x["number"] != "split_t3_cells":
            print(f"  {x['number']:28s} inventory {x['inventory']!s:>8s}  this script {x['this_script_at_the_inventory_precision']!s:>8s}  "
                  f"{'equal' if x['equal'] else 'DIFFERS'}")
    print(f"  {'split_t3_cells':28s} {'equal' if inv[-1]['equal'] else 'DIFFERS'}")
    k5, p5 = nums25["kendall_w"]["key"], nums25["kendall_w"]["papers"]
    s35, s45 = nums25["split_verdicts"]["threshold_3"], nums25["split_verdicts"]["threshold_4"]
    print(f"{ME}: key v2.5 ({'PROVISIONAL: ' if st25['provisional'] else ''}judge on v2.4 for "
          f"{st25['judge_correctness_on_v24']['answers']} answers, key signals on v2.4 for "
          f"{st25['answer_key_signals_on_v24']['answers']}): W key {k5['W']:.4f}, W papers {p5['W']:.4f}; split "
          f"{s35['split']} of {s35['answers']} at 3, {s45['split']} at 4")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
