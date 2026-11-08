#!/usr/bin/env python3
"""S382 - exp04 concept recall, number overlap and the deterministic scores on the current answer key
(item 15, 9 October; ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45)).

Why. The answer key was rebuilt as v2.2 (frozen 9 October) and corrected to v2.3 (11 October, Q45) and v2.4 (Q50), so
every printed number that depends on the key is recomputed against the current one. For the 528 answerable answers of the generation-strategy experiment
(exp04: 88 questions x six strategies) the non-LLM signals reach the paper from one place only: the
deposit's analysis_deterministic_latest.json, joined into master_join.csv by S03_master_join.py
(lines 25-27). No script recomputes them, so none can be pointed at a new key. This one can.

    concept recall          fraction of expected_concepts found in the answer      key: concepts
    number overlap          fraction of the expected answer's numbers it contains   key: expected answer
    correctness composite   0.6 x similarity + 0.4 x number overlap                 key: both
    faithfulness proxy      concept recall x similarity (CR x S)                    key: both
    completeness            concept recall, bucketed 0-5                            key: concepts
    citation quality        0.5 source coverage + 0.25 has citations + 0.25 density  source_files only

The scorer is the deposited one, not a re-implementation. score_all and every function it calls are
lifted with ast out of publication/scripts/analysis_deterministic_scorer.py, the deposit's own file,
and executed unchanged (load_ground_truth, which the deposit imports from the harness, is lifted from
recovered_harness/tests/experiments_v4/exp_common.py). Both files are hashed into the provenance. The
one model in that code is the BGE-M3 embedder inside compute_semantic_similarity. It is replaced by a
lookup that hands back a similarity computed elsewhere, as a pair of unit vectors whose dot product is
that value, so score_all's own dispatch (empty answer, error, unanswerable, question absent from the
key) runs exactly as deposited. With no similarity given, score_all falls back to its own neutral 0.5,
and every column that depends on similarity is left blank rather than written from that default.

Reproduce before writing. Before any current-key number is written, the lifted scorer re-scores all 828 exp04
rows on the v1 key (data/replication_inputs/ground_truth.json, the same bytes as the deposit's
publication/data/ground_truth.json) with the deposited similarity, and must reproduce the deposited
analysis_deterministic_latest.json:
  answerable (528)  concept recall, number overlap, completeness, the four citation fields, the
                    citation composite and similarity itself: equal at the deposited four decimals;
                    all four 0-5 scores: equal
                    correctness and faithfulness composites: within one unit of the fourth decimal,
                    because the deposit stores similarity rounded to four decimals and computed the
                    composites from the unrounded value (0.6 x 5e-5 and CR x 5e-5 are both under 1e-4)
  unanswerable (300) every objective metric and score equal (they read the answer alone)
Any mismatch exits non-zero and writes nothing.

The current key: the judge's, in the v1 format, S373_rejudge_v2.AS_V1 (since 11 October
data/ground_truth_v2/ground_truth_v2_4_as_v1.json, S381 --key 2.4), read-only; reports and printed
labels name the version read from S373.KEY's "version" field ("v2.4"), and the provenance records
S373.KEY's path and sha256. Column names keep the suffix _v22 (concept_recall_v22 and the rest hold the
current key's values) and the outputs keep their names, so that downstream readers hold. The six
questions dropped under D7 are absent from it, and score_all skips a row whose question it cannot find
(analysis_deterministic_scorer.py:661-665), so the drop is the deposited code's own path; the skipped
rows are counted and reported.

The answerable flag is the current key's (D5, Valerio, 11 October). score_all takes a row's own
answerable field before the key's (analysis_deterministic_scorer.py:674), so after the gate, which runs
on the deposited rows unchanged, every row on a question the key keeps is given the key's flag. The
rows whose flag that changes must be exactly the exp04 rows on the questions with answer_type
"refutation" in S373.KEY (the ten false-premise questions OOD_041 to OOD_050, each answered by the six
strategies), each changed from unanswerable to answerable; otherwise the run exits before scoring.
score_all then scores those rows as answerable answers, against the key's expected_answer,
expected_concepts and source_files for their questions (S381 --key 2.4 fills the first two from the
v2.4 record's short_answer, with its synthesis_statement where there is one, and its key-concept
phrases; score_all reads source_files from the key, so source files given to the ten there reach
their citation fields with no change here). They are written as their own group (group "refutation"),
after the kept answerable answers (group "answerable"), and no table of the answerable group includes
them. The deposit scored them as refusals, so every v1 column is blank on them.

Loose concept recall (Q26 and O30, Valerio, 10 October). concept_recall_loose_v1 and
concept_recall_loose_v22, the last two columns, are computed on the same answer text score_all reads,
with the v1 and the current key's concepts. Rule 1 of the loose matcher (scripts/concept_match_loose.py) is "a
concept the exact matcher finds is found". The exact column in this file is not the plain substring
rule that concept_match_loose.py takes as the exact matcher: it is the deposited exp04 scorer,
compute_concept_recall (analysis_deterministic_scorer.py:122-160), which after the substring test also
counts a multi-word concept when every whitespace-separated piece of it longer than three characters
occurs in the answer as a substring, and tries hyphen and space variants. Under the loose rule alone a
concept could therefore be lost that the published column counts, in two ways: (a) the scorer does not
check pieces of three characters or fewer, such as "65%" in "65% reduction", while for the loose rule
a number, or a short word not on its stop list, is a content word to match; (b) the scorer finds a
piece inside a longer word of the answer ("high" inside "higher"), while the loose rule needs a whole
token. O30 applies rule 1 with the scorer exp04 used: a concept is found when the deposited
compute_concept_recall finds it OR concept_recall_loose finds it, decided concept by concept, and the
loose value is found concepts / all concepts rounded to four decimals, as both rules round.

The per-concept decision of the deposited scorer is its own code: the lifted compute_concept_recall
called on a list holding that one concept. Its loop decides each concept without reference to the
others and returns found / len(expected_concepts), so on one concept it returns 1.0 when it counts
the concept and 0.0 when it does not (anything else is fatal). Before any loose value is written:
  - the loose rule's own checks (concept_match_loose.spec_failures()) pass;
  - no answer that is answerable on the deposit's flag or on the key's (the refutation group
    included) takes score_all's empty-or-errored branch (none does), since the scorer reads no text
    there, and no question answerable on the deposit's flag has an empty v1 concept list, nor any
    question written in either group an empty current-key one;
  - on every answer and for each key, the per-concept decisions reproduce the scorer: their sum over
    the number of concepts equals compute_concept_recall on the whole list, and rounded to four
    decimals equals the published column (v1: the deposit's concept_recall; current key: score_all's);
  - on every answer and for each key, the loose value is at least the published column, and at least
    the harness's exact substring rule (compute_concept_recall, lifted unchanged from
    recovered_harness/tests/experiments_v4/exp_v4_9_depth_sweep.py:200-210 and hashed into the
    provenance with the other lifted files).
The current-key checks run on the answerable group and on the refutation group, each on its own.
No other column changes. The report counts, for each key, the answers and concepts the scorer's
decision added to the loose rule alone, and the pooled mean of the loose rule alone beside the union;
for the refutation group it gives the same counts in that group's own section.

Outputs, never over a v1 file:
  findings/recompute/S382_exp04_objective_v22.csv   one row per kept answerable answer: first the kept
                                                    answers v1 flagged answerable (516, group "answerable"),
                                                    v1 beside the current key, then the answers on the ten
                                                    (60, group "refutation"), v1 columns blank; group is the
                                                    last column; first line is a "# {provenance}" comment
  findings/recompute/S382_exp04_objective_v22.md    gate evidence, per-strategy means of each group, D7 count

How to run (pure Python, seconds, any CPU; no model, no GPU, no server):

    uv run python scripts/S382_exp04_objective_v22.py

Finishing the similarity-dependent scores once the current-key BGE-M3 similarity exists (T4). Point the
script at T4's per-answer file, a CSV or a JSONL with question_id, config and a similarity column, and
name the column:

    uv run python scripts/S382_exp04_objective_v22.py \\
        --similarity findings/recompute/<T4 output> --sim-column <column>

The similarity file must name the key it was scored against, and that key must be the one this run
scores on. A CSV must open with "#" lines among which is S30's and S07's "# key <path> sha256 <hex>"
line; a JSONL must carry key_sha256 on every row. The run exits, before the gate and before writing
anything, unless every recorded sha256 equals the sha256 of S373.AS_V1. Before that, and in every run,
S373.AS_V1's source_v<version>_sha256 field (S381's name, from S373.KEY's "version") must equal the
sha256 of S373.KEY, as S388 checks; otherwise the run exits.

The similarity file must also hold a value for every answer score_all scores as answerable on the
current key that is neither empty nor errored, the refutation group's included; the run exits after the
gate, before scoring, if any is missing, and says how many of the missing are on the ten.

The gate runs again first, then score_all runs on the current key with that similarity, and the correctness and
faithfulness composites and scores are filled in. That run writes S382_exp04_objective_v22_<column>.csv
and .md beside the base pair, so the deposit's 2,000-character similarity and S30's full-answer one
(the det_*_fullsim columns the revision uses) can both be finished without either overwriting the
other. Use the script rather than the CSV's rounded columns: the scores bucket the unrounded values.

Opt-in, --loose-scores: the completeness and faithfulness scores computed from the loose concept recall (D12,
Valerio, 13 October; notes/DECISIONS_2026-10-13.md). The flag goes with the arguments of a variant (none, or
--similarity with --sim-column). The run then goes through the reproduction gate, the scoring on the current key
and every check of the loose concept recall described above, for that variant, and stops where the published-rule
CSV would be written: it writes neither file of that pair, builds none of that report's tables, and writes a pair
of its own beside it:

    findings/recompute/S382_exp04_objective_v22_loose.csv and .md             no similarity given
    findings/recompute/S382_exp04_objective_v22_loose_<column>.csv and .md    with --similarity and --sim-column

    uv run python scripts/S382_exp04_objective_v22.py --loose-scores \\
        --similarity findings/recompute/S30_baseline_scores_full_v22.csv --sim-column bge_sim_full

Without the flag the run is the one described above. The mode calls no model and no server: its similarity is the
value read from the --similarity file, handed to the scorer by the same lookup.

What the mode computes. score_all is run twice more on the current key, each time from a fresh copy of the
deposited definitions (the same two files lifted again, into a namespace of their own) in which one name is
replaced: compute_concept_recall, which score_all calls once for each answerable answer that is neither empty nor
errored (analysis_deterministic_scorer.py:720). In the first of the two (the check scoring, gate L1) the stand-in
returns the deposited function's own value. In the second (the loose scoring) it returns O30's union unrounded:
found concepts / all concepts, a concept found when the deposited compute_concept_recall called on that concept
alone returns 1.0 or concept_recall_loose finds it. loose_exp04 rounds the same quotient to four decimals for the
concept_recall_loose_v22 column. score_answerable, the thresholds and every other lifted definition run as
deposited, with the similarity lookup of the default run. In score_answerable
(analysis_deterministic_scorer.py:441-498) the concept recall enters two formulas, completeness_metric =
concept_recall (:459) and faithfulness_metric = concept_recall * semantic_similarity (:464), and five stored
outputs take it: the completeness and faithfulness scores (:479, :480; metric_to_score on those two formulas with
the thresholds of :93 and :97), the stored completeness_metric and faithfulness_composite (:489, :490) and the
stored concept_recall itself (:485), the last three rounded to four decimals. The correctness composite and score
and the citation composite and score hold no concept recall. recall_dependents() reads this list, and the line
numbers the report prints, from the syntax tree of the deposited file in every run of the mode.

Rows and columns of the mode's CSV. One row per row of the published-rule file of the variant, in its order (group
"answerable", then group "refutation"; group is the last column). The first line is "# {provenance}": the default
provenance of this run, with loose_matcher's columns replaced by the file's four loose columns and a field
loose_scores added (the published-rule file and its sha256, the stand-in, what recall_dependents read, the counts
of the gates). Columns: question_id, config, category, difficulty, answer_chars, n_concepts_v22;
concept_recall_v22 and concept_recall_loose_v22 (the two concept recalls); det_score_completeness_v22 and
det_score_completeness_loose_v22; semantic_similarity_v22; faithfulness_composite_v22 and
faithfulness_composite_loose_v22; det_score_faithfulness_v22 and det_score_faithfulness_loose_v22; group. The
columns the published-rule file also has are this run's default rows, which gate L0 holds equal to that file. The
three *_loose_v22 score columns are the loose scoring's completeness score, faithfulness composite and
faithfulness score. completeness_metric is the stored concept recall under either rule (checked on every row) and
has no column. Without a similarity semantic_similarity_v22 and the two pairs of faithfulness columns are blank, as
the similarity-dependent columns of the published-rule file are.

Gates of the mode. All run before either file is written; a failure exits non-zero in one sentence and writes
nothing.
  L0  the published-rule file of the variant is this run's default output: its bytes after the first line equal
      the rows the default code built in this run, written as the default writes them, and the provenance of its
      first line equals this run's, field for field and in the same order, with "generated" left out of both. A
      file written from another key, answers file, scorer, matcher or similarity is refused here; the run of the
      variant without the flag then has to come first.
  L1  the check scoring gives, on every row, the 14 current-key cells of the published-rule file as text (concept
      recall, number overlap, the completeness score, the five citation fields, the citation score, and the five
      similarity-dependent cells, blank without a similarity) and every stored metric and score of this run's
      default scoring.
  L2  the loose stand-in's value, as score_answerable rounds it, equals on every row the union loose_exp04
      computed in this run and the published-rule file's concept_recall_loose_v22; in each of the two scorings
      the stand-in is called as many times as there are rows.
  L3  a second code path, which reads the published-rule file's text, ThresholdConfig's two threshold tuples and
      the similarity file's value, and calls neither score_all, score_answerable nor metric_to_score: found =
      round(concept recall x n_concepts_v22), which must give the stored recall back at four decimals;
      completeness score = band(found / n) on the completeness thresholds; faithfulness composite = found / n x
      similarity; faithfulness score = band of that product on the faithfulness thresholds, band() counting the
      boundaries a value reaches. It is run first on concept_recall_v22 against the published-rule file's own
      three score columns and then on concept_recall_loose_v22 against the loose scoring. The completeness score
      must be equal on every row. With the file's four-decimal similarity the composite must be within 1e-4, and
      the faithfulness score equal on every row where the similarity's rounding interval (the stored value plus
      and minus half a unit of its fourth decimal) leaves one band; those rows are counted. With the similarity
      file's value, clamped to 0..1 as the scorer clamps it, the composite and the score must be equal on every
      row.
  L4  what the deposited file computes from concept recall is exactly the five outputs named above
      (recall_dependents), and score_all's one call is the only call of compute_concept_recall in the lifted
      functions. Each of the five is non-decreasing in concept recall (the similarity is clamped to 0..1, round
      and metric_to_score do not decrease) and the union holds every concept the deposited function finds, so on
      every row its value in the loose scoring must be at least its value in the check scoring. Every other stored
      metric and score must be equal between the two scorings on every row, and completeness_metric equal to the
      stored concept recall in each. Without a similarity the similarity-dependent outputs, which are not written,
      are left out of these comparisons.
With --loose-scores a ValueError, KeyError, TypeError, OSError, RecursionError or csv.Error raised anywhere in the
run ends it in one sentence with no traceback (refuse_unreadable), so an input file that cannot be read or parsed
gives a refusal; without the flag such an exception is raised as before.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import logging
import math
import re
import subprocess
import sys
import traceback
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB_SCRIPTS, RECOMPUTE, RESULTS, ROOT, rel, require  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402  (the judge's key: KEY, AS_V1)
import concept_match_loose  # noqa: E402
from concept_match_loose import concept_recall_loose  # noqa: E402

SCRIPT = "scripts/S382_exp04_objective_v22.py"
LOOSE = Path(concept_match_loose.__file__)
GEN = RESULTS / "exp04_generation_latest.json"
DET = RESULTS / "analysis_deterministic_latest.json"
SCORER = PUB_SCRIPTS / "analysis_deterministic_scorer.py"
HARNESS_COMMON = ROOT / "recovered_harness/tests/experiments_v4/exp_common.py"
HARNESS_SWEEP = ROOT / "recovered_harness/tests/experiments_v4/exp_v4_9_depth_sweep.py"   # its exact rule, :200-210
KEY_V1 = ROOT / "data/replication_inputs/ground_truth.json"
KEY_V22 = S373.AS_V1   # the judge's key in the v1 format: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45) (S381 --key 2.4)
OUT = RECOMPUTE / "S382_exp04_objective_v22"

# score_all and everything it calls, in file order (analysis_deterministic_scorer.py:80-765)
LIFT_SCORER = ["ThresholdConfig", "DEFAULT_THRESHOLDS", "compute_concept_recall", "extract_numbers",
               "compute_number_overlap", "compute_citation_metrics", "compute_semantic_similarity",
               "REFUSAL_STRONG", "REFUSAL_WEAK", "EXPLANATION_PHRASES", "score_ood_refusal",
               "metric_to_score", "score_answerable", "score_all"]
LIFT_COMMON = ["load_ground_truth"]                     # exp_common.py:235, imported by the deposit
CUT = 2000                                              # analysis_deterministic_scorer.py:277-278
CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
N_REFUTATION = 60   # D5: the ten refutation questions x the six strategies (notes/DECISIONS_2026-10-11.md:54)

EXACT = ["concept_recall", "number_overlap", "completeness_metric", "semantic_similarity",
         "source_coverage", "has_citations", "citation_density", "total_citations",
         "citation_composite"]
SIM_COMPOSITES = ["correctness_composite", "faithfulness_composite"]
SIM_TOLERANCE = 1e-4 + 1e-12                            # one unit of the deposited fourth decimal
DIMS = ["correctness", "completeness", "faithfulness", "citation_quality"]


def utcnow() -> str:
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                          capture_output=True, text=True).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── the deposited scorer, lifted ──────────────────────────────────────────────────────────────

class _Collect(logging.Handler):
    """Keeps score_all's warnings, so its own "No ground truth for <id>, skipping" can be counted."""

    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def lift(path: Path, names: list[str], ns: dict) -> dict:
    """Execute the named top-level definitions of a deposited file, unchanged, into ns.

    ast selects the nodes (a decorated class keeps its decorator, an assignment its value) and they
    are compiled as one module under the deposited file's own name and line numbers, so a traceback
    points into the deposit. dont_inherit keeps this script's `from __future__ import annotations`
    out of the deposited code, whose dataclass is written for evaluated annotations.
    """
    src = path.read_text()
    tree = ast.parse(src)
    picked, spans = [], {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            continue
        if name in names:
            picked.append(node)
            first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            spans[name] = f"{first}-{node.end_lineno}"
    missing = [n for n in names if n not in spans]
    if missing:
        sys.exit(f"FATAL: {', '.join(missing)} not found in {rel(path)}")
    exec(compile(ast.Module(body=picked, type_ignores=[]), str(path), "exec", dont_inherit=True), ns)  # noqa: S102
    return {"path": rel(path), "sha256": hashlib.sha256(src.encode()).hexdigest(), "lines": spans}


def deposited_scorer() -> tuple[dict, list, _Collect]:
    """The deposited module's namespace: its own imports (analysis_deterministic_scorer.py:44-55),
    its logger name, then the lifted definitions."""
    log = logging.getLogger("det_scorer")
    log.setLevel(logging.WARNING)
    log.propagate = False
    log.handlers.clear()
    sink = _Collect()
    log.addHandler(sink)
    ns = {"__name__": "deposited_analysis_deterministic_scorer",
          "argparse": argparse, "json": json, "logging": logging, "re": re, "sys": sys,
          "defaultdict": defaultdict, "asdict": asdict, "dataclass": dataclass, "field": field,
          "Path": Path, "Any": Any, "Dict": Dict, "List": List, "Optional": Optional, "Set": Set,
          "Tuple": Tuple, "np": np, "logger": log}
    sources = [lift(SCORER, LIFT_SCORER, ns), lift(HARNESS_COMMON, LIFT_COMMON, ns)]
    return ns, sources, sink


class SimilarityLookup:
    """Stands in for the BGE-M3 embedder in compute_semantic_similarity.

    The deposited function embeds [expected[:2000], generated[:2000]] and takes the dot product. This
    returns [1, 0] and [s, sqrt(1 - s^2)] for the similarity s given for that pair, so the dot product
    is s exactly and the clamp after it is the deposited one. A pair it was not given is fatal, and
    so is a given pair that is never asked for.
    """

    def __init__(self, pairs: dict):
        self.pairs = pairs
        self.used: set = set()

    def embed_documents(self, texts):
        key = (texts[0], texts[1])
        if key not in self.pairs:
            raise SystemExit("FATAL: score_all asked for a similarity the lookup was not given")
        self.used.add(key)
        s = float(self.pairs[key])
        return [[1.0, 0.0], [s, math.sqrt(max(0.0, 1.0 - s * s))]]

    def unused(self) -> int:
        return len(set(self.pairs) - self.used)


def answer_of(row: dict) -> str:
    g = row.get("generation")
    return (g.get("answer") or "") if isinstance(g, dict) else (g or "")


# ── loose concept recall for exp04 (Q26, O30) ─────────────────────────────────────────────────

def loose_exp04(scorer_cr, answer: str, concepts: list, published: float) -> dict:
    """Loose concept recall with rule 1 read as the scorer exp04 used (O30), for one answer.

    scorer_cr is the lifted deposited compute_concept_recall. Its decision on one concept is the
    function called on [concept]; loose's is concept_recall_loose's found_by for that concept. A
    concept counts when either finds it. Returns the union recall, the loose rule's recall alone,
    how many concepts the scorer added, and whether the per-concept scorer decisions reproduce the
    scorer on the whole list and the published value. The caller checks those before writing."""
    plain, per = concept_recall_loose(answer, concepts, detail=True)
    if len(per) != len(concepts) or any(p["concept"] != c for p, c in zip(per, concepts)):
        sys.exit("FATAL: concept_recall_loose's per-concept detail does not follow the concept list")
    single = [scorer_cr(answer, [c]) for c in concepts]
    if any(v not in (0.0, 1.0) for v in single):
        sys.exit("FATAL: the deposited compute_concept_recall returned other than 0.0 or 1.0 on one concept")
    by_scorer = [v == 1.0 for v in single]
    by_loose = [p["found_by"] is not None for p in per]
    union = [a or b for a, b in zip(by_scorer, by_loose)]
    whole = scorer_cr(answer, concepts)
    return {"union": round(sum(union) / len(concepts), 4), "plain": plain,
            "scorer_added": sum(a and not b for a, b in zip(by_scorer, by_loose)),
            "reproduces_whole": sum(by_scorer) / len(concepts) == whole,
            "reproduces_published": round(sum(by_scorer) / len(concepts), 4) == published}


def score(ns: dict, rows: list, key_path: Path, sims: dict | None, sink: _Collect) -> tuple[list, int]:
    """Run the deposited score_all over rows on one key. sims maps (question_id, config) to the
    similarity for that answer; None leaves the embedder out, as --skip-embeddings did."""
    embedder = None
    if sims is not None:
        expected = {q["id"]: q.get("expected_answer", "")
                    for q in json.loads(key_path.read_text())["questions"]}
        pairs = {}
        for r in rows:
            k = (r["question_id"], r["config"])
            if k not in sims or r["question_id"] not in expected:
                continue
            pair = (expected[r["question_id"]][:CUT], answer_of(r)[:CUT])
            if pair in pairs and pairs[pair] != sims[k]:
                sys.exit(f"FATAL: two answers to {k[0]} share their first {CUT} characters "
                         "and carry different similarities; the lookup cannot tell them apart")
            pairs[pair] = sims[k]
        embedder = SimilarityLookup(pairs)
    sink.messages.clear()
    scored = ns["score_all"](rows, key_path, embedder, ns["DEFAULT_THRESHOLDS"])
    skipped = sum(m.startswith("No ground truth for ") for m in sink.messages)
    if embedder is not None and embedder.unused():
        sys.exit(f"FATAL: {embedder.unused()} similarities were given and never asked for")
    return scored, skipped


# ── gate: the v1 key must reproduce the deposit ───────────────────────────────────────────────

def gate(ns: dict, rows: list, det: dict, sink: _Collect) -> dict:
    dep = {(r["question_id"], r["config"]): r for r in det["per_result"]}
    sims = {k: r["objective_metrics"]["semantic_similarity"]
            for k, r in dep.items() if r["answerable"] and "semantic_similarity" in r["objective_metrics"]}
    scored, skipped = score(ns, rows, KEY_V1, sims, sink)
    mine = {(r["question_id"], r["config"]): r for r in scored}

    fails: list[str] = []
    if skipped or len(scored) != len(rows) or set(mine) != set(dep):
        fails.append(f"row sets differ: {len(scored)} scored, {skipped} skipped, {len(dep)} deposited")
    ans = [k for k in dep if dep[k]["answerable"]]
    ood = [k for k in dep if not dep[k]["answerable"]]
    if (len(ans), len(ood)) != (528, 300):
        fails.append(f"expected 528 answerable and 300 unanswerable rows, found {len(ans)} and {len(ood)}")

    fields = {}
    for f in EXACT + SIM_COMPOSITES:
        diffs = [abs(float(mine[k]["objective_metrics"][f]) - float(dep[k]["objective_metrics"][f]))
                 for k in ans if k in mine]
        exact = sum(d == 0 for d in diffs)
        fields[f] = {"compared": len(diffs), "equal": exact, "max_abs_diff": max(diffs)}
        bad = [d for d in diffs if d > (SIM_TOLERANCE if f in SIM_COMPOSITES else 0)]
        if bad or len(diffs) != 528:
            fails.append(f"{f}: {len(bad)} of {len(diffs)} outside tolerance, max {max(diffs):.2e}")
    for d in DIMS:
        eq = sum(mine[k]["deterministic_scores"][d] == dep[k]["deterministic_scores"][d] for k in ans if k in mine)
        fields[f"score_{d}"] = {"compared": len(ans), "equal": eq}
        if eq != len(ans):
            fails.append(f"score {d}: {len(ans) - eq} of {len(ans)} differ")
    ood_eq = sum(mine[k]["objective_metrics"] == dep[k]["objective_metrics"]
                 and mine[k]["deterministic_scores"] == dep[k]["deterministic_scores"] for k in ood if k in mine)
    fields["unanswerable_all_fields"] = {"compared": len(ood), "equal": ood_eq}
    if ood_eq != len(ood):
        fails.append(f"unanswerable rows: {len(ood) - ood_eq} of {len(ood)} differ")

    for f in fails:
        print(f"  REFUSED {f}")
    if fails:
        print(f"\nGATE FAILED: {len(fails)} checks; nothing written")
        raise SystemExit(1)
    print(f"  gate passed: the lifted scorer on the v1 key reproduces the deposit on all {len(ans)} "
          f"answerable rows (9 metrics equal at four decimals, 4 scores equal, 2 composites within "
          f"1e-4: {fields['correctness_composite']['equal']} and {fields['faithfulness_composite']['equal']} "
          f"of 528 equal) and all {len(ood)} unanswerable rows")
    return {"answerable": len(ans), "unanswerable": len(ood), "fields": fields}


# ── the current key ──────────────────────────────────────────────────────────────────────────────────────

def require_as_v1_from_key() -> None:
    """S388's check: S373.AS_V1's source_v<version>_sha256 (S381's field for the version in S373.KEY's
    "version") must be the sha256 of S373.KEY. Exits otherwise."""
    key_bytes = S373.KEY.read_bytes()
    kv = str(json.loads(key_bytes)["version"])
    src = f"source_v{kv.replace('.', '')}_sha256"
    got = json.loads(S373.AS_V1.read_text(encoding="utf-8")).get(src)
    if got != hashlib.sha256(key_bytes).hexdigest():
        sys.exit(f"FATAL: {S373.AS_V1.name} was built from another key ({src} {str(got)[:12]}), "
                 f"not {S373.KEY.name} v{kv}")


KEY_LINE = re.compile(r"^# key \S+ sha256 ([0-9a-f]{64})\b")   # S30's and S07's header line


def read_similarity(path: Path, column: str, key_sha: str) -> dict:
    """Per-answer similarity keyed by (question_id, config). Exits unless the file was scored against the key
    whose sha256 is key_sha: a CSV needs a "# key <path> sha256 <hex>" line before its header row, and every
    such line must carry key_sha; a JSONL needs key_sha256 equal to key_sha on every row."""
    text = path.read_text()
    if path.suffix == ".jsonl":
        recs = [json.loads(line) for line in text.splitlines() if line.strip()]
        other = Counter(str(r.get("key_sha256"))[:12] for r in recs if r.get("key_sha256") != key_sha)
        if other:
            sys.exit(f"FATAL: {rel(path)} has {sum(other.values())} rows scored on another key or none "
                     f"(key_sha256 {dict(other)}), not {key_sha[:12]}")
    else:
        lines = text.splitlines()
        head = [l for l in lines if l.startswith("#")]
        recorded = {m.group(1) for m in map(KEY_LINE.match, head) if m}
        if recorded != {key_sha}:
            sys.exit(f"FATAL: {rel(path)} records key sha256 "
                     f"{sorted(s[:12] for s in recorded) or 'none'}, not {key_sha[:12]}")
        recs = list(csv.DictReader([l for l in lines if not l.startswith("#")]))
    if not recs or column not in recs[0]:
        sys.exit(f"FATAL: {rel(path)} has no column {column!r}")
    out = {}
    for r in recs:
        k = (r["question_id"], r["config"])
        if k in out:
            sys.exit(f"FATAL: {rel(path)} carries {k} twice")
        if r[column] in ("", None):
            continue
        out[k] = float(r[column])
    return out


def mean(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


# ── opt-in, --loose-scores (D12): completeness and faithfulness from the loose concept recall ──────────────

LOOSE_MODE = {"on": False}                              # set by main() from --loose-scores
RECALL_METRICS = ["concept_recall", "completeness_metric", "faithfulness_composite"]   # what score_answerable stores
RECALL_SCORES = ["completeness", "faithfulness"]                                       # from its concept_recall
SIM_METRICS = ["semantic_similarity", "correctness_composite", "faithfulness_composite"]   # blank without a similarity,
SIM_SCORES = ["correctness", "faithfulness"]                                               # as main() blanks them
SIM_CELLS = ["semantic_similarity_v22", "correctness_composite_v22", "det_score_correctness_v22",
             "faithfulness_composite_v22", "det_score_faithfulness_v22"]
LOOSE_COLUMNS = ["concept_recall_loose_v22", "det_score_completeness_loose_v22", "faithfulness_composite_loose_v22",
                 "det_score_faithfulness_loose_v22"]
HALF_UNIT = 5e-5 + 1e-12                                # half a unit of a stored fourth decimal
READ_ERRORS = (ValueError, KeyError, TypeError, OSError, RecursionError, csv.Error)


def refuse_unreadable(fn):
    """main() under the loose mode's rule for inputs: with --loose-scores an exception of READ_ERRORS ends the run
    in one sentence that gives the exception and the line of this script it came through, with no traceback. Every
    such exception is raised before the mode writes (loose_scores handles its own writes). Without the flag the
    exception is raised again as it was."""
    def run():
        try:
            return fn()
        except READ_ERRORS as e:
            if not LOOSE_MODE["on"]:
                raise
            mine = [f for f in traceback.extract_tb(e.__traceback__) if Path(f.filename).name == Path(__file__).name]
            at = f" at line {mine[-1].lineno} of {SCRIPT} ({mine[-1].line})" if mine else ""
            sys.exit(f"FATAL (--loose-scores): {type(e).__name__}: {e}{at}, reached while reading or checking the "
                     "inputs; nothing written")
    return run


def recall_dependents(path: Path) -> dict:
    """What the deposited scorer computes from concept recall, read from the file's syntax tree.

    In score_answerable: the assignments whose right side reads the argument concept_recall or a name assigned
    from it (formulas, with line and text), and the entries of the dict literals it assigns whose value reads one
    of those names (outputs: the name the dict is assigned to, the entry's key, its line). Also the lifted
    functions that call compute_concept_recall with the lines of the calls, and the lines of the completeness
    and faithfulness thresholds in ThresholdConfig."""
    src = path.read_text()
    top = {n.name: n for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    absent = [x for x in ("score_answerable", "ThresholdConfig") if x not in top]
    if absent:
        sys.exit(f"FATAL: {', '.join(absent)} not found in {rel(path)}; nothing written")

    def names(node) -> set:
        return {x.id for x in ast.walk(node) if isinstance(x, ast.Name)}

    read, formulas, outputs = {"concept_recall"}, {}, {}
    for st in top["score_answerable"].body:
        if not (isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name)):
            continue
        target = st.targets[0].id
        if isinstance(st.value, ast.Dict):
            for k, v in zip(st.value.keys, st.value.values):
                if isinstance(k, ast.Constant) and names(v) & read:
                    outputs.setdefault(target, {})[k.value] = k.lineno
        elif names(st.value) & read:
            read.add(target)
            formulas[target] = {"line": st.lineno, "code": " ".join((ast.get_source_segment(src, st) or "").split())}
    callers = {}
    for name in LIFT_SCORER:
        if isinstance(top.get(name), ast.FunctionDef):
            at = sorted(c.lineno for c in ast.walk(top[name]) if isinstance(c, ast.Call)
                        and isinstance(c.func, ast.Name) and c.func.id == "compute_concept_recall")
            if at:
                callers[name] = at
    thresholds = {st.target.id: st.lineno for st in top["ThresholdConfig"].body
                  if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)
                  and st.target.id in ("completeness_thresholds", "faithfulness_thresholds")}
    f = top["score_answerable"]
    return {"score_answerable": f"{f.lineno}-{f.end_lineno}", "formulas": formulas, "outputs": outputs,
            "callers": callers, "thresholds": thresholds}


class RecallStandIn:
    """Stands in for compute_concept_recall in a copy of the deposited scorer (second_scoring), as SimilarityLookup
    stands in for the embedder.

    deposited is the lifted compute_concept_recall of the first copy. With loose=False the stand-in returns
    deposited(answer, expected_concepts): the deposited value through the mode's own path, for gate L1. With
    loose=True it returns O30's union unrounded: the number of concepts for which deposited, called on that concept
    alone, returns 1.0 or which concept_recall_loose finds, over the number of concepts. loose_exp04 makes the same
    decision per concept and rounds the quotient; gate L2 compares the two. calls counts the calls."""

    def __init__(self, deposited, loose: bool):
        self.deposited, self.loose, self.calls = deposited, loose, 0

    def __call__(self, answer: str, expected_concepts: list) -> float:
        self.calls += 1
        if not self.loose:
            return self.deposited(answer, expected_concepts)
        if not expected_concepts:               # main() refuses such a question before any loose value is computed
            raise SystemExit("FATAL: the loose stand-in was called with no expected concepts; nothing written")
        _, per = concept_recall_loose(answer, expected_concepts, detail=True)
        found = sum(self.deposited(answer, [c]) == 1.0 or p["found_by"] is not None
                    for c, p in zip(expected_concepts, per))
        return found / len(expected_concepts)


def second_scoring(ns: dict, sink: _Collect, rows: list, sims: dict | None, stand_in: RecallStandIn,
                   lifted: list, keys: list) -> dict:
    """score_all on the current key from a fresh copy of the deposited definitions in which compute_concept_recall
    is stand_in. The copy starts as a copy of ns; the two deposited files are lifted into it again, which replaces
    every lifted definition by one that reads its names from the copy; then the one name is replaced. ns itself
    is not written to. Returns score_all's rows of the answerable answers by (question_id, config). Exits unless
    this lift gives the path, sha256 and lines of the first, score_all reads its names from the copy, the
    answerable rows are exactly keys, and the stand-in was called as many times as there are keys."""
    ns2 = dict(ns)
    again = [lift(SCORER, LIFT_SCORER, ns2), lift(HARNESS_COMMON, LIFT_COMMON, ns2)]
    if again != lifted[:2]:
        sys.exit(f"FATAL: {rel(SCORER)} or {rel(HARNESS_COMMON)} changed between the two times this run read it; "
                 "nothing written")
    ns2["compute_concept_recall"] = stand_in
    if ns2["score_all"].__globals__ is not ns2 or ns2["score_all"] is ns["score_all"] \
            or ns["compute_concept_recall"] is stand_in:
        sys.exit("FATAL: the copy of the deposited scorer made for the stand-in is not apart from the first; nothing "
                 "written")
    out, _ = score(ns2, rows, KEY_V22, sims, sink)
    got = {(r["question_id"], r["config"]): r for r in out if r["answerable"]}
    if set(got) != set(keys) or len(got) != len(keys) or stand_in.calls != len(keys):
        sys.exit(f"FATAL: the scoring with the stand-in gave {len(got)} answerable rows with {stand_in.calls} calls of "
                 f"the stand-in, where the default code built {len(keys)} rows; nothing written")
    return got


def current_key_cells(r: dict, with_sim: bool) -> dict:
    """The 14 current-key cells of one score_all row under the column names of the published-rule file, the five
    similarity-dependent ones blank when no similarity was given (the rule of main()'s row)."""
    o, s = r["objective_metrics"], r["deterministic_scores"]
    cells = {"concept_recall_v22": o["concept_recall"], "number_overlap_v22": o["number_overlap"],
             "det_score_completeness_v22": s["completeness"], "source_coverage": o["source_coverage"],
             "has_citations": o["has_citations"], "citation_density": o["citation_density"],
             "total_citations": o["total_citations"], "citation_composite": o["citation_composite"],
             "det_score_citation_quality": s["citation_quality"],
             "semantic_similarity_v22": o["semantic_similarity"],
             "correctness_composite_v22": o["correctness_composite"], "det_score_correctness_v22": s["correctness"],
             "faithfulness_composite_v22": o["faithfulness_composite"], "det_score_faithfulness_v22": s["faithfulness"]}
    if not with_sim:
        cells.update(dict.fromkeys(SIM_CELLS, ""))
    return cells


def band(value: float, thresholds: tuple) -> int:
    """A 0-5 score as the number of the five boundaries thresholds[1:] that value reaches. Gate L3's own banding,
    written apart from the deposited metric_to_score, which searches from the top boundary down."""
    return sum(value >= t for t in thresholds[1:])


def read_published(path: Path) -> tuple[dict, bytes, dict]:
    """The published-rule file of a variant: the provenance of its first line, its bytes after that line, and its
    rows as text by (question_id, config), in file order. One sentence and no file written when it is absent or
    cannot be read as that."""
    if not path.exists():
        sys.exit(f"FATAL: {rel(path)} is absent; --loose-scores gates on the published-rule file of the variant, so "
                 "the run of this variant without the flag comes first; nothing written")
    try:
        first, _, body = path.read_bytes().partition(b"\n")
        line = first.decode("utf-8")
        if not line.startswith("# {"):
            raise ValueError("the first line is not '# {provenance}'")
        head = json.loads(line[2:])
        rows = {}
        for r in csv.DictReader(io.StringIO(body.decode("utf-8"), newline="")):
            k = (r["question_id"], r["config"])
            if k in rows:
                raise ValueError(f"{k} is there twice")
            rows[k] = r
        if not rows:
            raise ValueError("no row")
    except READ_ERRORS as e:
        sys.exit(f"FATAL: {rel(path)} cannot be read as a published-rule file of this script "
                 f"({type(e).__name__}: {e}); nothing written")
    return head, body, rows


def second_path(pub: Path, pub_rows: dict, recall_column: str, want: dict, sims: dict | None, thr) -> dict:
    """Gate L3 for one concept recall column of the published-rule file. want holds, per answer, the completeness
    score, the faithfulness composite and the faithfulness score the column must give (the last two are not read
    without a similarity). Reads the file's text (n_concepts_v22, the recall column, semantic_similarity_v22), the
    similarity file's value from sims and the two threshold tuples of thr; calls no lifted function. Exits, naming
    the file, when a cell it reads is no number or any row disagrees; returns the counts."""
    ct, ft = thr.completeness_thresholds, thr.faithfulness_thresholds
    bad, fixed = [], 0
    try:
        for k, c in pub_rows.items():
            n, u = int(c["n_concepts_v22"]), float(c[recall_column])
            found = round(u * n)
            if n < 1 or round(found / n, 4) != u:
                raise ValueError(f"{recall_column} {c[recall_column]} of {k} is no count out of {n} concepts at "
                                 "four decimals")
            cr = found / n
            if band(cr, ct) != want[k]["completeness"]:
                bad.append((k, "completeness score"))
            if sims is None:
                continue
            s4 = float(c["semantic_similarity_v22"])
            if abs(cr * s4 - want[k]["composite"]) > SIM_TOLERANCE:
                bad.append((k, "faithfulness composite from the stored similarity"))
            lo, hi = band(cr * max(0.0, s4 - HALF_UNIT), ft), band(cr * min(1.0, s4 + HALF_UNIT), ft)
            if lo == hi:
                fixed += 1
                if lo != want[k]["faithfulness"]:
                    bad.append((k, "faithfulness score from the stored similarity"))
            s = max(0.0, min(float(sims[k]), 1.0))          # the scorer's clamp (compute_semantic_similarity)
            if round(cr * s, 4) != want[k]["composite"]:
                bad.append((k, "faithfulness composite from the similarity file's value"))
            if band(cr * s, ft) != want[k]["faithfulness"]:
                bad.append((k, "faithfulness score from the similarity file's value"))
    except (ValueError, KeyError, TypeError) as e:
        sys.exit(f"FATAL: {rel(pub)} does not hold what the second code path reads ({type(e).__name__}: {e}); "
                 "nothing written")
    if bad:
        sys.exit(f"FATAL (L3): from the columns of {rel(pub)} the second code path does not give the scores built on "
                 f"{recall_column} in {len(bad)} cases, e.g. {bad[0][0]}: {bad[0][1]}; nothing written")
    return {"rows": len(pub_rows), "faithfulness_score_fixed_by_stored_similarity": fixed if sims is not None else None}


def loose_scores(ns: dict, sink: _Collect, rows_v22: list, sims: dict | None, sim_column: str | None, lx: dict,
                 out_rows: list, scored: list, stem: Path, prov: dict, K: str) -> int:
    """--loose-scores, called by main() where the published-rule pair would be written, with what main() built for
    the variant: the deposited namespace and its warning sink, the rows under the key's answerable flag, the
    similarity, loose_exp04's result per answer (lx), the default rows (out_rows) and scoring (scored), the stem of
    the published-rule pair and the default provenance. Runs gates L0 to L4 of the module docstring, then writes
    <OUT>_loose[_<column>].csv and .md, each through a .tmp file beside it that is read back before both are
    renamed into place. Writes no other file."""
    with_sim = bool(sims)
    pub = stem.with_suffix(".csv")
    mine = OUT.with_name(f"{OUT.name}_loose" + (f"_{sim_column}" if with_sim else ""))
    keys = [(r["question_id"], r["config"]) for r in out_rows]
    scorer_cr = ns["compute_concept_recall"]
    sc = prov["lifted"][0]
    print(f"[S382] --loose-scores: gates against {rel(pub)}")

    # L0: the published-rule file of the variant is this run's default output
    head, body, pub_rows = read_published(pub)
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=list(out_rows[0]))
    w.writeheader()
    w.writerows(out_rows)
    default_body = buf.getvalue().encode("utf-8")
    here = json.loads(json.dumps(prov))
    if not isinstance(head, dict):
        sys.exit(f"FATAL: the first line of {rel(pub)} holds no provenance object; nothing written")
    a, b = ({k: v for k, v in d.items() if k != "generated"} for d in (head, here))
    if json.dumps(a) != json.dumps(b):
        differ = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k)) or ["the order of its fields"]
        sys.exit(f"FATAL (L0): the first line of {rel(pub)} does not record this run's inputs (it differs on: "
                 f"{', '.join(differ)}); the run of this variant without the flag comes first; nothing written")
    if body != default_body:
        theirs = list(pub_rows.values())
        ours = list(csv.DictReader(io.StringIO(default_body.decode("utf-8"), newline="")))
        cells = [((o["question_id"], o["config"]), c) for t, o in zip(theirs, ours) for c in o if t.get(c) != o[c]]
        sys.exit(f"FATAL (L0): {rel(pub)} is not this run's default output ({len(theirs)} rows in the file, "
                 f"{len(ours)} here, {len(cells)} cells differ on the rows both hold"
                 + (f", e.g. {cells[0][0]} {cells[0][1]}" if cells else "") + "); nothing written")
    print(f"  L0 passed: the {len(keys)} rows the default code built in this run are the file's bytes after its "
          "first line, and its first line is this run's provenance apart from the time")

    # L4, the structure: what the deposited file computes from concept recall
    takes = recall_dependents(SCORER)
    got = {name: sorted(v) for name, v in takes["outputs"].items()}
    if got != {"scores": sorted(RECALL_SCORES), "metrics": sorted(RECALL_METRICS)} \
            or list(takes["callers"]) != ["score_all"] or len(takes["callers"]["score_all"]) != 1 \
            or sorted(takes["thresholds"]) != ["completeness_thresholds", "faithfulness_thresholds"]:
        sys.exit(f"FATAL (L4): in {rel(SCORER)} score_answerable computes {got} from concept_recall and "
                 f"compute_concept_recall is called in {takes['callers']}; the mode holds scores {RECALL_SCORES}, "
                 f"metrics {RECALL_METRICS} and one call in score_all; nothing written")
    call_line = takes["callers"]["score_all"][0]

    # L1: the check scoring (the mode's path with the deposited concept recall) reproduces the published-rule file
    base = {(r["question_id"], r["config"]): r for r in scored if r["answerable"]}
    if set(base) != set(keys):
        sys.exit("FATAL: the default scoring's answerable rows are not the rows the default code built; nothing written")
    dep = second_scoring(ns, sink, rows_v22, sims, RecallStandIn(scorer_cr, loose=False), prov["lifted"], keys)
    off = [(k, c) for k in keys for c, v in current_key_cells(dep[k], with_sim).items() if str(v) != pub_rows[k][c]]
    off_mem = [k for k in keys if dep[k]["objective_metrics"] != base[k]["objective_metrics"]
               or dep[k]["deterministic_scores"] != base[k]["deterministic_scores"]]
    if off or off_mem:
        sys.exit(f"FATAL (L1): the check scoring (a copy of the scorer with the deposited concept recall as the "
                 f"stand-in) differs from {rel(pub)} on {len(off)} cells"
                 + (f", e.g. {off[0][0]} {off[0][1]}" if off else "")
                 + f", and from this run's default scoring on {len(off_mem)} rows; nothing written")
    n_cells = len(current_key_cells(dep[keys[0]], with_sim))
    print(f"  L1 passed: with the deposited concept recall as the stand-in, {len(keys)} of {len(keys)} rows equal the "
          f"file on its {n_cells} current-key cells, and the default scoring on every stored metric and score")

    # L2: the loose scoring's concept recall is loose_exp04's and the file's
    loose = second_scoring(ns, sink, rows_v22, sims, RecallStandIn(scorer_cr, loose=True), prov["lifted"], keys)
    off = [k for k in keys if loose[k]["objective_metrics"]["concept_recall"] != lx[k]["union"]
           or str(loose[k]["objective_metrics"]["concept_recall"]) != pub_rows[k]["concept_recall_loose_v22"]]
    if off:
        sys.exit(f"FATAL (L2): the loose stand-in's concept recall differs from loose_exp04's union or from "
                 f"concept_recall_loose_v22 of {rel(pub)} on {len(off)} rows, e.g. {off[0]}; nothing written")
    print(f"  L2 passed: the loose stand-in's concept recall at four decimals equals loose_exp04's union and the "
          f"file's concept_recall_loose_v22 on {len(keys)} of {len(keys)} rows")

    # L4, the values: unchanged where no concept recall enters, not lower where it does
    def stored(r: dict) -> dict:
        return ({f"metric {f}": v for f, v in r["objective_metrics"].items() if with_sim or f not in SIM_METRICS}
                | {f"score {d}": v for d, v in r["deterministic_scores"].items() if with_sim or d not in SIM_SCORES})

    on_recall = {f"metric {f}" for f in RECALL_METRICS} | {f"score {d}" for d in RECALL_SCORES}
    fell, moved, not_recall = [], [], []
    for k in keys:
        x, y = stored(dep[k]), stored(loose[k])
        if list(x) != list(y):
            sys.exit(f"FATAL (L4): the two scorings store different fields for {k}; nothing written")
        fell += [(k, f) for f in x if f in on_recall and y[f] < x[f]]
        moved += [(k, f) for f in x if f not in on_recall and y[f] != x[f]]
        not_recall += [(k, rule) for rule, r in (("deposited", dep[k]), ("loose", loose[k]))
                       if r["objective_metrics"]["completeness_metric"] != r["objective_metrics"]["concept_recall"]]
    if fell or moved or not_recall:
        sys.exit(f"FATAL (L4): under the loose rule {len(fell)} values that take concept recall are below the "
                 f"deposited-rule value, {len(moved)} values that take none differ, and completeness_metric is not the "
                 f"stored concept recall in {len(not_recall)} cases, e.g. {(fell + moved + not_recall)[0]}; "
                 "nothing written")
    fields = list(stored(dep[keys[0]]))
    monotone = [f for f in fields if f in on_recall]
    same = [f for f in fields if f not in on_recall]
    print(f"  L4 passed: on {len(keys)} of {len(keys)} rows the loose-rule value is at least the deposited-rule value "
          f"for {', '.join(monotone)}; equal in the two scorings: {', '.join(same)}")

    # L3: the second code path, from the published-rule file's text
    thr = ns["DEFAULT_THRESHOLDS"]
    try:
        want_dep = {k: {"completeness": int(c["det_score_completeness_v22"]),
                        "composite": float(c["faithfulness_composite_v22"]) if with_sim else None,
                        "faithfulness": int(c["det_score_faithfulness_v22"]) if with_sim else None}
                    for k, c in pub_rows.items()}
    except (ValueError, KeyError, TypeError) as e:
        sys.exit(f"FATAL: {rel(pub)} holds a score cell that is no number ({type(e).__name__}: {e}); nothing written")
    want_loose = {k: {"completeness": loose[k]["deterministic_scores"]["completeness"],
                      "composite": loose[k]["objective_metrics"]["faithfulness_composite"],
                      "faithfulness": loose[k]["deterministic_scores"]["faithfulness"]} for k in keys}
    sims2 = sims if with_sim else None
    l3 = {"deposited": second_path(pub, pub_rows, "concept_recall_v22", want_dep, sims2, thr),
          "loose": second_path(pub, pub_rows, "concept_recall_loose_v22", want_loose, sims2, thr)}
    print(f"  L3 passed: the second code path gives the completeness score on {l3['loose']['rows']} of "
          f"{l3['loose']['rows']} rows under each rule"
          + (f", and the faithfulness composite and score from the similarity file's value on every row; the file's "
             f"four-decimal similarity fixes the faithfulness score on "
             f"{l3['deposited']['faithfulness_score_fixed_by_stored_similarity']} (deposited rule) and "
             f"{l3['loose']['faithfulness_score_fixed_by_stored_similarity']} (loose rule) rows" if with_sim else ""))

    # the rows: the published-rule columns are the default rows of this run (L0), the loose columns the loose scoring's
    rows = []
    for r in out_rows:
        o, s = (loose[(r["question_id"], r["config"])][f] for f in ("objective_metrics", "deterministic_scores"))
        rows.append({"question_id": r["question_id"], "config": r["config"], "category": r["category"],
                     "difficulty": r["difficulty"], "answer_chars": r["answer_chars"],
                     "n_concepts_v22": r["n_concepts_v22"],
                     "concept_recall_v22": r["concept_recall_v22"],
                     "concept_recall_loose_v22": r["concept_recall_loose_v22"],
                     "det_score_completeness_v22": r["det_score_completeness_v22"],
                     "det_score_completeness_loose_v22": s["completeness"],
                     "semantic_similarity_v22": r["semantic_similarity_v22"],
                     "faithfulness_composite_v22": r["faithfulness_composite_v22"],
                     "faithfulness_composite_loose_v22": o["faithfulness_composite"] if with_sim else "",
                     "det_score_faithfulness_v22": r["det_score_faithfulness_v22"],
                     "det_score_faithfulness_loose_v22": s["faithfulness"] if with_sim else "",
                     "group": r["group"]})
    cols = list(rows[0])
    groups = list(dict.fromkeys(r["group"] for r in rows))
    n_group = Counter(r["group"] for r in rows)

    gates = {"L0": {"rows": len(keys), "published_rule_file_is_this_runs_default_output": True},
             "L1": {"rows": len(keys), "cells_per_row": n_cells, "equal_rows": len(keys)},
             "L2": {"rows": len(keys), "equal_rows": len(keys)},
             "L3": l3,
             "L4": {"rows": len(keys), "not_below_under_the_loose_rule": monotone, "equal_in_both_scorings": same}}
    prov2 = dict(prov)
    prov2["loose_matcher"] = dict(prov["loose_matcher"], columns=LOOSE_COLUMNS)
    prov2["loose_scores"] = {
        "flag": "--loose-scores", "decision": "D12, notes/DECISIONS_2026-10-13.md",
        "published_rule_file": rel(pub), "published_rule_file_sha256": sha256(pub),
        "stand_in": f"compute_concept_recall, called by score_all at {sc['path']}:{call_line}, is replaced in a copy "
                    "of the lifted scorer by O30's union unrounded (found concepts / all concepts, a concept found "
                    "when the deposited compute_concept_recall called on it alone returns 1.0 or concept_recall_loose "
                    "finds it)",
        "takes_concept_recall": takes, "gates": gates}
    csv_buf = io.StringIO(newline="")
    csv_buf.write(f"# {json.dumps(prov2)}\n")
    w = csv.DictWriter(csv_buf, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

    pairs = [("concept recall", "concept_recall_v22", "concept_recall_loose_v22"),
             ("completeness score (0-5)", "det_score_completeness_v22", "det_score_completeness_loose_v22")]
    if with_sim:
        pairs += [("faithfulness composite", "faithfulness_composite_v22", "faithfulness_composite_loose_v22"),
                  ("faithfulness score (0-5)", "det_score_faithfulness_v22", "det_score_faithfulness_loose_v22")]
    sim = prov["similarity"]
    variant = f"similarity {sim_column}" if with_sim else "no similarity"
    described = {"concept_recall": "the loose concept recall at four decimals: column concept_recall_loose_v22",
                 "completeness_metric": "the same number as concept_recall; it has no column",
                 "faithfulness_composite": "loose concept recall x similarity at four decimals: column "
                                           "faithfulness_composite_loose_v22",
                 "completeness": "the loose concept recall in the completeness bands: column "
                                 "det_score_completeness_loose_v22",
                 "faithfulness": "loose concept recall x similarity in the faithfulness bands: column "
                                 "det_score_faithfulness_loose_v22"}
    inputs = [("loose matcher", prov["loose_matcher"]["path"], prov["loose_matcher"]["sha256"]),
              ("deposited scorer", sc["path"], sc["sha256"]),
              ("load_ground_truth", prov["lifted"][1]["path"], prov["lifted"][1]["sha256"]),
              ("answers", prov["answers"], prov["answers_sha256"]),
              (f"key {K}, v1 format (scored on)", prov["key"], prov["key_sha256"]),
              (f"key {K}, source", prov["key_source"], prov["key_source_sha256"]),
              ("v1 key (reproduction gate)", prov["gate_key"], prov["gate_key_sha256"]),
              ("deposited scores (reproduction gate)", prov["deposited_scores"], prov["deposited_scores_sha256"])]
    if with_sim:
        inputs.append((f"similarity, column {sim_column}", sim["file"], sim["sha256"]))
    inputs.append(("published-rule file (gates L0 to L3)", rel(pub), prov2["loose_scores"]["published_rule_file_sha256"]))

    md = [f"# S382 exp04 completeness and faithfulness from the loose concept recall (D12), ground truth {K}, "
          f"{variant} ({prov2['generated']})", "",
          f"`{json.dumps({'script': SCRIPT, 'flag': '--loose-scores', 'generated': prov2['generated'], 'key': prov2['key'], 'key_sha256': prov2['key_sha256'], 'gate': prov2['gate']})}`", "",
          f"For each of the {len(rows)} answers of {rel(pub)} ("
          + ", ".join(f"{n_group[g]} in group \"{g}\"" for g in groups) + f") this file holds two sets of scores of "
          f"the deposited scorer on ground truth {K}. The published-rule columns are this run's default scoring. The "
          f"loose columns are a further scoring, from a copy of the lifted definitions in which "
          f"compute_concept_recall, which score_all calls at line {call_line}, is replaced by O30's union unrounded: "
          "found concepts over all concepts, a concept found when the deposited compute_concept_recall called on that "
          "concept alone returns 1.0 or concept_recall_loose finds it. No other definition differs between the two "
          "scorings. A third scoring, from another such copy with the deposited compute_concept_recall as the "
          "stand-in (the check scoring), serves the gates only. "
          + (f"Every scoring takes the similarity from column `{sim_column}` of {sim['file']} through a lookup; the "
             "run calls no model." if with_sim else
             "No similarity was given, so the similarity-dependent columns are blank, as in the published-rule file; "
             "the run calls no model."), "",
          "## Inputs and their sha256", "", "| input | file | sha256 |", "|---|---|---|"]
    md += [f"| {what} | {path} | {digest} |" for what, path, digest in inputs]
    md += ["", "## Where concept recall enters the deposited scorer", "",
           f"Read in this run from the syntax tree of {sc['path']}. In score_answerable (lines "
           f"{takes['score_answerable']}) these assignments read concept_recall:", ""]
    md += [f"- line {f['line']}: `{f['code']}`" for f in takes["formulas"].values()]
    md += ["", "| stored output of score_answerable | line | under --loose-scores |", "|---|--:|---|"]
    for name, label in (("scores", "score"), ("metrics", "metric")):
        md += [f"| {label} {key} | {line} | {described[key]} |" for key, line in takes["outputs"][name].items()]
    md += ["",
           f"The bands are ThresholdConfig's: completeness {thr.completeness_thresholds} (line "
           f"{takes['thresholds']['completeness_thresholds']}) and faithfulness {thr.faithfulness_thresholds} (line "
           f"{takes['thresholds']['faithfulness_thresholds']}); a score is the highest position whose boundary the "
           "value reaches. The stored outputs computed without concept recall are equal in the check scoring and the "
           f"loose scoring on every row (gate L4): {', '.join(same)}.", "",
           "## Gates passed before writing", "", "| gate | what was compared | rows | result |", "|---|---|--:|---|",
           f"| L0 | the rows the default code built in this run, written as the default writes them, against the "
           f"bytes of {rel(pub)} after its first line; this run's provenance against its first line, \"generated\" "
           f"left out | {len(keys)} | equal |",
           f"| L1 | the check scoring against the file's {n_cells} current-key cells as text, and against every stored "
           f"metric and score of the default scoring | {len(keys)} | equal on {len(keys)} |",
           f"| L2 | the loose stand-in's concept recall at four decimals against loose_exp04's union of this run and "
           f"the file's concept_recall_loose_v22 | {len(keys)} | equal on {len(keys)} |",
           f"| L3 | second code path, completeness score = band(found / n) with found = round(concept recall x "
           f"n_concepts_v22), under each rule | {l3['loose']['rows']} | equal on {l3['loose']['rows']} under each "
           "rule |"]
    if with_sim:
        md += [f"| L3 | second code path, faithfulness composite = found / n x the file's four-decimal similarity | "
               f"{l3['loose']['rows']} | within 1e-4 on {l3['loose']['rows']} under each rule |",
               f"| L3 | second code path, faithfulness score = band(found / n x similarity) on the rows where the "
               f"file's four-decimal similarity leaves one band | "
               f"{l3['deposited']['faithfulness_score_fixed_by_stored_similarity']} (deposited rule), "
               f"{l3['loose']['faithfulness_score_fixed_by_stored_similarity']} (loose rule) | equal on each |",
               f"| L3 | second code path, faithfulness composite and score from the similarity file's value | "
               f"{l3['loose']['rows']} | equal on {l3['loose']['rows']} under each rule |"]
    md += [f"| L4 | the outputs the deposited file computes from concept recall, read from its syntax tree, against the "
           f"five the mode holds; the calls of compute_concept_recall in the lifted functions | | the same five; one "
           f"call, in score_all at line {call_line} |",
           f"| L4 | the loose scoring against the check scoring for {', '.join(monotone)} | {len(keys)} | not below on "
           f"{len(keys)} |",
           f"| L4 | the loose scoring against the check scoring on every stored output computed without concept recall "
           f"| {len(keys)} | equal on {len(keys)} |",
           f"| L4 | metric completeness_metric against metric concept_recall, in each of the two scorings | {len(keys)} "
           f"| equal on {len(keys)} |", "",
           "The second code path reads the text of the published-rule file and ThresholdConfig's two threshold tuples"
           + (", and for the last L3 row the similarity file's value" if with_sim else "")
           + "; it calls neither score_all, score_answerable nor metric_to_score. The completeness score is a banded "
           "integer: the file's columns with the thresholds give it on every row, since found / n is recovered from "
           "the four-decimal recall and n_concepts_v22."
           + (" The faithfulness composite is a product stored at four decimals: the file's four-decimal similarity "
              "gives it within 1e-4, the similarity file's value exactly. The faithfulness score is a banded integer "
              "of the unrounded product: the file's columns fix it only where the similarity's rounding interval "
              "leaves one band (the counts above), and the similarity file's value gives it on every row."
              if with_sim else ""), "",
           "## Per-strategy means under the deposited rule and under the loose rule", "",
           "Each cell is the mean of a column of the CSV over the answers of the strategy in the group, rounded to four "
           "decimals; \"deposited\" is the column scored with the deposited scorer's own concept recall, \"loose\" the "
           "column scored with O30's union in its place.", ""]
    for g in groups:
        g_rows = [r for r in rows if r["group"] == g]
        md += [f"### Group \"{g}\" ({len(g_rows)} answers)", "",
               "| strategy | answers | " + " | ".join(f"{lab}, deposited | {lab}, loose" for lab, _, _ in pairs) + " |",
               "|---|--:|" + "--:|--:|" * len(pairs)]
        for cfg in CONFIGS + ["pooled"]:
            sel = g_rows if cfg == "pooled" else [r for r in g_rows if r["config"] == cfg]
            md.append(f"| {cfg} | {len(sel)} | "
                      + " | ".join(f"{mean(r[a] for r in sel):.4f} | {mean(r[b] for r in sel):.4f}" for _, a, b in pairs)
                      + " |")
        md.append("")
    md += ["## Answers on which the loose-rule value is above, equal to or below the deposited-rule value", "",
           "| group | value | answers | above | equal | below |", "|---|---|--:|--:|--:|--:|"]
    for g in groups:
        g_rows = [r for r in rows if r["group"] == g]
        for lab, a, b in pairs:
            md.append(f"| {g} | {lab} | {len(g_rows)} | {sum(r[b] > r[a] for r in g_rows)} | "
                      f"{sum(r[b] == r[a] for r in g_rows)} | {sum(r[b] < r[a] for r in g_rows)} |")
    md += ["",
           "## Columns of the CSV", "",
           f"{rel(mine.with_suffix('.csv'))}: first line `# {{provenance}}`, then one row per answer in the order of "
           f"the published-rule file, joined to it on question_id and config. Columns: {', '.join(cols)}. "
           "concept_recall_v22, det_score_completeness_v22, semantic_similarity_v22, faithfulness_composite_v22 and "
           "det_score_faithfulness_v22 are the published-rule file's columns of those names (deposited rule); "
           "concept_recall_loose_v22 is its loose concept recall; det_score_completeness_loose_v22, "
           "faithfulness_composite_loose_v22 and det_score_faithfulness_loose_v22 are the loose scoring's (loose rule)."
           + ("" if with_sim else " Without a similarity semantic_similarity_v22 and the two pairs of faithfulness "
                                   "columns are blank."), ""]

    files = [(mine.with_suffix(".csv"), csv_buf.getvalue().encode("utf-8")),
             (mine.with_suffix(".md"), "\n".join(md).encode("utf-8"))]
    tmps = [Path(f"{p}.tmp") for p, _ in files]
    try:
        for tmp, (p, data) in zip(tmps, files):
            tmp.write_bytes(data)
            if tmp.read_bytes() != data:
                raise OSError(f"{tmp.name} read back differs from what was written")
    except OSError as e:
        for tmp in tmps:
            tmp.unlink(missing_ok=True)
        sys.exit(f"FATAL: {rel(mine.with_suffix('.csv'))} and its report could not be written ({e}); the temporary "
                 "files are removed and no output file was replaced")
    done = []
    try:
        for tmp, (p, _) in zip(tmps, files):
            tmp.replace(p)
            done.append(rel(p))
    except OSError as e:
        for tmp in tmps:
            tmp.unlink(missing_ok=True)
        sys.exit(f"FATAL: a temporary file could not be renamed into place ({e}); in place from this run: "
                 f"{', '.join(done) or 'no file'}")
    print(f"[S382] --loose-scores wrote {rel(files[0][0])} ("
          + " and ".join(f"{n_group[g]} {g}" for g in groups) + f" rows) and {rel(files[1][0])}; the published-rule "
          "pair was not written")
    return 0


@refuse_unreadable
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--similarity", type=Path, help="per-answer similarity against the current key (T4), CSV or JSONL")
    ap.add_argument("--sim-column", help="the similarity column in that file")
    ap.add_argument("--loose-scores", action="store_true",
                    help="opt-in (D12): for the variant the other arguments name, write the completeness and "
                         "faithfulness scores computed from the loose concept recall beside the deposited-rule ones, "
                         "to S382_exp04_objective_v22_loose[_<column>].csv and .md; the published-rule pair is not written")
    args = ap.parse_args()
    LOOSE_MODE["on"] = args.loose_scores
    if bool(args.similarity) != bool(args.sim_column):
        ap.error("--similarity and --sim-column go together")
    require(GEN, DET, SCORER, HARNESS_COMMON, HARNESS_SWEEP, KEY_V1, KEY_V22, S373.KEY)
    require_as_v1_from_key()
    kv = str(json.loads(S373.KEY.read_text())["version"])     # the current key's version, "2.4" since 11 October, Q50
    K = f"v{kv}"                                              # its printed label
    sim_all = read_similarity(args.similarity, args.sim_column, sha256(KEY_V22)) if args.similarity else None

    ns, sources, sink = deposited_scorer()
    gen = json.loads(GEN.read_text())
    rows = gen["per_question_results"]
    det = json.loads(DET.read_text())

    print("[S382] gate: re-score the deposit on the v1 key")
    g = gate(ns, rows, det, sink)

    key = json.loads(KEY_V22.read_text())
    kq = {q["id"]: q for q in key["questions"]}
    v1q = {q["id"]: q for q in json.loads(KEY_V1.read_text())["questions"]}
    dropped = set(key["dropped_d7"])

    # D5: the key's answerable flag, not the deposit's, decides how score_all scores a row on a kept question. The
    # gate above ran on the deposited rows; from here on the rows carry the key's flag. The rows whose flag changes
    # must be exactly the exp04 rows on S373.KEY's answer_type "refutation" ids, each from unanswerable to answerable.
    recs = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    ref_ids = sorted(q for q in recs if S373.refutation(q, recs))
    ref_set = set(ref_ids)
    not_bool = sorted(q for q, x in kq.items() if not isinstance(x["answerable"], bool))
    if not_bool:
        sys.exit(f"FATAL: {len(not_bool)} questions in {KEY_V22.name} carry an answerable flag that is not a boolean, "
                 f"e.g. {not_bool[:3]}")
    rows_v22 = [dict(r, answerable=kq[r["question_id"]]["answerable"]) if r["question_id"] in kq else r for r in rows]
    raw = {(r["question_id"], r["config"]): r for r in rows}
    raw_v22 = {(r["question_id"], r["config"]): r for r in rows_v22}
    flipped = {k for k in raw if raw[k]["answerable"] != raw_v22[k]["answerable"]}
    on_ten = {k for k in raw if k[0] in ref_set}
    n_ref = len(ref_ids) * len(CONFIGS)
    wrong_way = sorted(k for k in flipped if raw[k]["answerable"] or not raw_v22[k]["answerable"])
    if flipped != on_ten or len(on_ten) != n_ref or wrong_way or n_ref != N_REFUTATION \
            or on_ten != {(q, c) for q in ref_ids for c in CONFIGS}:
        sys.exit(f"FATAL (D5): the key's answerable flag differs from the deposit's on {len(flipped)} exp04 rows "
                 f"({len(flipped - on_ten)} of them off the refutation questions, {len(wrong_way)} changed other than "
                 f"from unanswerable to answerable); it must differ on exactly the {len(on_ten)} rows on the "
                 f"{len(ref_ids)} answer_type 'refutation' ids of {S373.KEY.name} ({', '.join(ref_ids)}), which must "
                 f"number {len(ref_ids)} x {len(CONFIGS)} strategies = {N_REFUTATION}, one row per question and strategy, each changed from unanswerable to "
                 f"answerable. {KEY_V22.name} must carry answerable = the v2.4 question_answerable (S381)")
    print(f"  D5: the key's flag replaces the deposit's on {len(flipped)} rows, exactly those on the {len(ref_ids)} "
          f"answer_type 'refutation' questions ({ref_ids[0]} to {ref_ids[-1]}), unanswerable to answerable; "
          "they form their own group")

    d7 = Counter(("answerable" if r["answerable"] else "unanswerable") for r in rows_v22 if r["question_id"] in dropped)
    d7_questions = sorted({r["question_id"] for r in rows_v22 if r["question_id"] in dropped})

    sims = None
    if sim_all is not None:
        sims = sim_all
        need ={(r["question_id"], r["config"]) for r in rows_v22 if r["answerable"] and r["question_id"] in kq
                and answer_of(r) and not (r.get("generation") or {}).get("error")}
        lacking = need - set(sims)
        if lacking:
            on_lacking = sum(k[0] in ref_set for k in lacking)
            sys.exit(f"FATAL: the similarity file lacks {len(lacking)} of the {len(need)} answers it must "
                     f"cover ({on_lacking} of them on the {len(ref_ids)} refutation questions, which D5 scores as "
                     f"answerable), e.g. {sorted(lacking)[:3]}")
        sims = {k: v for k, v in sims.items() if k in need}

    print(f"[S382] {K}: score_all on {rel(KEY_V22)}" + (f" with similarity {args.sim_column}" if sims else ""))
    scored, skipped = score(ns, rows_v22, KEY_V22, sims, sink)
    if skipped != sum(d7.values()) or len(scored) != len(rows) - skipped:
        sys.exit(f"FATAL: score_all skipped {skipped} rows; the D7 questions account for {sum(d7.values())}")
    print(f"  D7: {skipped} rows skipped by score_all ({d7['answerable']} answerable, "
          f"{d7['unanswerable']} unanswerable) for {', '.join(d7_questions)}")

    dep = {(r["question_id"], r["config"]): r for r in det["per_result"]}
    ex_numbers = ns["extract_numbers"]
    out_ans, out_ref = [], []                  # group "answerable" (v1 flagged them answerable) and group "refutation" (D5)
    for r in scored:
        if not r["answerable"]:
            continue
        k = (r["question_id"], r["config"])
        qid = r["question_id"]
        ten = qid in ref_set
        o2, s2 = r["objective_metrics"], r["deterministic_scores"]
        if ten:
            # the deposit scored these as refusals: no v1 value exists for any v1 column
            o1 = s1 = defaultdict(str)
            nc1 = ne1 = ""
        else:
            o1, s1 = dep[k]["objective_metrics"], dep[k]["deterministic_scores"]
            nc1, ne1 = len(v1q[qid]["expected_concepts"]), len(ex_numbers(v1q[qid]["expected_answer"]))
            for f in ("source_coverage", "has_citations", "citation_density", "total_citations", "citation_composite"):
                if o1[f] != o2[f]:
                    sys.exit(f"FATAL: {k} {f} moved with the key, but source_files are v1 in both keys")
        row = {"question_id": qid, "config": r["config"], "category": r["category"],
               "difficulty": r["difficulty"],
               "answer_chars": len(answer_of(raw[k])),
               "n_concepts_v1": nc1,
               "n_concepts_v22": len(kq[qid]["expected_concepts"]),
               "n_expected_numbers_v1": ne1,
               "n_expected_numbers_v22": len(ex_numbers(kq[qid]["expected_answer"])),
               "concept_recall_v1": o1["concept_recall"], "concept_recall_v22": o2["concept_recall"],
               "number_overlap_v1": o1["number_overlap"], "number_overlap_v22": o2["number_overlap"],
               "det_score_completeness_v1": s1["completeness"], "det_score_completeness_v22": s2["completeness"],
               "source_coverage": o2["source_coverage"], "has_citations": o2["has_citations"],
               "citation_density": o2["citation_density"], "total_citations": o2["total_citations"],
               "citation_composite": o2["citation_composite"],
               "det_score_citation_quality": s2["citation_quality"],
               "semantic_similarity_v1": o1["semantic_similarity"],
               "correctness_composite_v1": o1["correctness_composite"],
               "det_score_correctness_v1": s1["correctness"],
               "faithfulness_composite_v1": o1["faithfulness_composite"],
               "det_score_faithfulness_v1": s1["faithfulness"]}
        # without a similarity score_all used its neutral 0.5 for these four; blank, never written
        row.update({"semantic_similarity_v22": o2["semantic_similarity"] if sims else "",
                    "correctness_composite_v22": o2["correctness_composite"] if sims else "",
                    "det_score_correctness_v22": s2["correctness"] if sims else "",
                    "faithfulness_composite_v22": o2["faithfulness_composite"] if sims else "",
                    "det_score_faithfulness_v22": s2["faithfulness"] if sims else ""})
        (out_ref if ten else out_ans).append(row)
    n_ans = g["answerable"] - d7["answerable"]
    if len(out_ans) != n_ans or {(r["question_id"], r["config"]) for r in out_ref} != on_ten:
        sys.exit(f"FATAL: {len(out_ans)} answerable and {len(out_ref)} refutation rows written, expected {n_ans} "
                 f"and {len(on_ten)} (every row on the {len(ref_ids)} refutation questions)")
    out_rows = out_ans + out_ref                # the answerable group first, each group in generation order

    # Q26 with O30: loose concept recall beside the scorer's, on the answer text score_all reads; a
    # concept counts when the deposited scorer or concept_match_loose.py finds it, concept by concept
    bad = concept_match_loose.spec_failures()
    if bad:
        sys.exit("FATAL: the loose rule fails its own cases: " + "; ".join(bad))
    # every answer answerable on the deposit's flag or on the key's (the refutation group's included)
    zero = [k for k in raw if (raw[k]["answerable"] or raw_v22[k]["answerable"])
            and (not answer_of(raw[k]) or (raw[k].get("generation") or {}).get("error"))]
    if zero:
        sys.exit(f"FATAL: {len(zero)} answerable answers take score_all's empty-or-errored branch, e.g. {zero[:3]}; "
                 "the loose value for them is not defined here")
    empty = sorted({k[0] for k, r in raw.items() if r["answerable"] and not v1q[k[0]]["expected_concepts"]}
                   | {r["question_id"] for r in out_rows if not kq[r["question_id"]]["expected_concepts"]})
    if empty:
        sys.exit(f"FATAL: {len(empty)} questions have no expected concepts, e.g. {empty[:3]}; loose recall is not "
                 "defined for them (concept_match_loose.py returns None, the scorer 1.0)")
    scorer_cr = ns["compute_concept_recall"]
    KR = f"{K} refutation"                      # the refutation group on the current key, kept apart from K throughout
    lx = {"v1": {k: loose_exp04(scorer_cr, answer_of(r), v1q[k[0]]["expected_concepts"],
                                dep[k]["objective_metrics"]["concept_recall"])
                 for k, r in raw.items() if r["answerable"]},
          K: {(r["question_id"], r["config"]): loose_exp04(scorer_cr, answer_of(raw[(r["question_id"], r["config"])]),
                                                                  kq[r["question_id"]]["expected_concepts"],
                                                                  r["concept_recall_v22"])
                   for r in out_ans},
          KR: {(r["question_id"], r["config"]): loose_exp04(scorer_cr, answer_of(raw[(r["question_id"], r["config"])]),
                                                            kq[r["question_id"]]["expected_concepts"],
                                                            r["concept_recall_v22"])
               for r in out_ref}}
    # the per-concept scorer decisions must reproduce the scorer before they are used
    off = [(kn, k, f) for kn, recs in lx.items() for k, x in recs.items()
           for f in ("reproduces_whole", "reproduces_published") if not x[f]]
    if off:
        sys.exit(f"FATAL: the deposited scorer's per-concept decisions fail to reproduce it on {len(off)} checks, e.g. "
                 + "; ".join(f"{kn} {k} {f}" for kn, k, f in off[:3]))
    print(f"  per-concept scorer decisions reproduce compute_concept_recall and the published concept recall on "
          f"{len(lx['v1'])} of {len(lx['v1'])} answers (v1) and {len(lx[K])} of {len(lx[K])} ({K})")
    print(f"  and on {len(lx[KR])} of {len(lx[KR])} answers of the refutation group ({KR})")
    loose_v1 = {k: x["union"] for k, x in lx["v1"].items()}
    for row in out_rows:
        k = (row["question_id"], row["config"])
        ten = row["question_id"] in ref_set
        row["concept_recall_loose_v1"] = "" if ten else loose_v1[k]      # the deposit scored the ten as refusals
        row["concept_recall_loose_v22"] = lx[KR if ten else K][k]["union"]
        row["group"] = "refutation" if ten else "answerable"            # the last column
    # loose >= the published column (the deposited scorer's concept recall), answer by answer and key by key
    pub = {"v1": [(k, x, dep[k]["objective_metrics"]["concept_recall"]) for k, x in loose_v1.items()],
           K: [((r["question_id"], r["config"]), r["concept_recall_loose_v22"], r["concept_recall_v22"])
                    for r in out_ans],
           KR: [((r["question_id"], r["config"]), r["concept_recall_loose_v22"], r["concept_recall_v22"])
                for r in out_ref]}
    below = [(kn, k, x, y) for kn, trio in pub.items() for k, x, y in trio
             if not (isinstance(x, (int, float)) and x >= y)]
    if below:
        sys.exit(f"FATAL: loose concept recall is missing or below the published column on {len(below)} answers, e.g. "
                 + "; ".join(f"{kn} {k}: loose {x}, published {y}" for kn, k, x, y in below[:3]))
    print(f"  loose >= the published concept recall on every answer: {len(pub['v1'])} (v1) and {len(pub[K])} ({K})")
    print(f"  and on {len(pub[KR])} ({KR})")
    # loose >= the harness's exact substring rule, answer by answer and key by key (S383's G5)
    exact_ns: dict = {"List": List}
    sources.append(lift(HARNESS_SWEEP, ["compute_concept_recall"], exact_ns))
    exact_rule = exact_ns["compute_concept_recall"]
    floor = {"v1": [(k, x, exact_rule(answer_of(raw[k]), v1q[k[0]]["expected_concepts"]))
                    for k, x in loose_v1.items()],
             K: [((r["question_id"], r["config"]), r["concept_recall_loose_v22"],
                       exact_rule(answer_of(raw[(r["question_id"], r["config"])]), kq[r["question_id"]]["expected_concepts"]))
                      for r in out_ans],
             KR: [((r["question_id"], r["config"]), r["concept_recall_loose_v22"],
                   exact_rule(answer_of(raw[(r["question_id"], r["config"])]), kq[r["question_id"]]["expected_concepts"]))
                  for r in out_ref]}
    under = [(kn, k, x, e) for kn, trio in floor.items() for k, x, e in trio
             if not (isinstance(x, (int, float)) and x >= e)]
    if under:
        sys.exit(f"FATAL: loose concept recall is missing or below the harness's exact rule on {len(under)} answers, e.g. "
                 + "; ".join(f"{kn} {k}: loose {x}, exact {e}" for kn, k, x, e in under[:3]))
    floor_n = {kn: len(trio) for kn, trio in floor.items()}
    print(f"  loose >= the harness's exact rule on every answer: {floor_n['v1']} (v1) and {floor_n[K]} ({K})")
    print(f"  and on {floor_n[KR]} ({KR})")
    vs_scorer = {kn: Counter("above" if x > y else "equal" if x == y else "below" for _, x, y in trio)
                 for kn, trio in pub.items()}
    # the loose rule alone (the column before O30) against the same published values, and what O30 added
    alone_below = {kn: sum(lx[kn][k]["plain"] < y for k, _, y in trio) for kn, trio in pub.items()}
    raised = {kn: sum(x["union"] > x["plain"] for x in recs.values()) for kn, recs in lx.items()}
    added = {kn: sum(x["scorer_added"] for x in recs.values()) for kn, recs in lx.items()}
    pooled = {kn: (mean(x["plain"] for x in recs.values()), mean(x["union"] for x in recs.values()))
              for kn, recs in lx.items()}
    print(f"  loose concept recall against the scorer's: v1 {dict(vs_scorer['v1'])}, {K} {dict(vs_scorer[K])}; "
          f"the loose rule alone was below on {alone_below['v1']} (v1) and {alone_below[K]} ({K}); the scorer's "
          f"decision raised {raised['v1']} and {raised[K]} answers ({added['v1']} and {added[K]} concepts); "
          f"pooled mean, loose alone to O30: v1 {pooled['v1'][0]} to {pooled['v1'][1]}, "
          f"{K} {pooled[K][0]} to {pooled[K][1]}")
    print(f"  {KR}: loose against the scorer's {dict(vs_scorer[KR])}; the loose rule alone was below on "
          f"{alone_below[KR]}; the scorer's decision raised {raised[KR]} answers ({added[KR]} concepts); pooled "
          f"mean, loose alone to O30: {pooled[KR][0]} to {pooled[KR][1]}")

    stem = OUT if not sims else OUT.with_name(f"{OUT.name}_{args.sim_column}")
    prov = {"script": SCRIPT, "generated": utcnow(),
            "key": rel(KEY_V22), "key_sha256": sha256(KEY_V22),
            "key_source": rel(S373.KEY), "key_source_sha256": sha256(S373.KEY), "key_version": kv,
            "gate_key": rel(KEY_V1), "gate_key_sha256": sha256(KEY_V1),
            "answers": rel(GEN), "answers_sha256": sha256(GEN),
            "deposited_scores": rel(DET), "deposited_scores_sha256": sha256(DET),
            "lifted": sources,
            "loose_matcher": {"path": rel(LOOSE), "sha256": sha256(LOOSE),
                              "columns": ["concept_recall_loose_v1", "concept_recall_loose_v22"],
                              "rule": "O30: a concept is found when the deposited compute_concept_recall "
                                      f"({sources[0]['path']}:{sources[0]['lines']['compute_concept_recall']}), "
                                      "called on that concept alone, or concept_recall_loose finds it"},
            "similarity": ({"file": rel(args.similarity), "sha256": sha256(args.similarity),
                            "column": args.sim_column} if sims else None),
            "gate": "passed", "d7_rows_skipped": dict(d7), "d7_questions": d7_questions,
            "groups": {"column": "group", "answerable": len(out_ans), "refutation": len(out_ref)},
            "d5": {"refutation_ids": ref_ids, "from": f"{rel(S373.KEY)} answer_type 'refutation'",
                   "rows_flag_from_key": len(flipped),
                   "rule": "rows on these ids take the key's answerable flag (true) and are scored as answerable "
                           "against the key; written as group 'refutation', v1 columns blank"}}

    if args.loose_scores:                       # opt-in (D12): files of its own, the published-rule pair is not written
        return loose_scores(ns, sink, rows_v22, sims, args.sim_column, lx[K] | lx[KR], out_rows, scored, stem, prov, K)

    cols = list(out_rows[0])
    if cols[-1] != "group" or any(list(r) != cols for r in out_rows):
        sys.exit("FATAL: the rows do not share one column order ending in group")
    with open(stem.with_suffix(".csv"), "w", newline="") as fh:
        fh.write(f"# {json.dumps(prov)}\n")
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)

    kept = {(r["question_id"], r["config"]) for r in out_ans}       # the answerable group: v1 has a value for each
    v1_all = [dep[k] for k in dep if dep[k]["answerable"]]
    v1_kept = [dep[k] for k in dep if k in kept]

    def by_cfg(recs, get):
        groups = defaultdict(list)
        for x in recs:
            groups[x["config"]].append(get(x))
        return {c: mean(groups[c]) for c in CONFIGS} | {"pooled": mean([get(x) for x in recs])}

    om = lambda f: (lambda x: x["objective_metrics"][f])  # noqa: E731
    ds = lambda d: (lambda x: x["deterministic_scores"][d])  # noqa: E731
    v22 = [r for r in scored if r["answerable"] and r["question_id"] not in ref_set]     # the answerable group
    v22_ref = [r for r in scored if r["answerable"] and r["question_id"] in ref_set]    # the refutation group
    tables = {
        "concept recall": (by_cfg(v1_all, om("concept_recall")), by_cfg(v1_kept, om("concept_recall")),
                           by_cfg(v22, om("concept_recall"))),
        "concept recall, loose (Q26 with O30; every column computed here, v1 included: a concept counts "
        "when the deposited scorer or the loose rule finds it)": (
            by_cfg([{"config": k[1], "v": x} for k, x in loose_v1.items()], lambda x: x["v"]),
            by_cfg([{"config": k[1], "v": x} for k, x in loose_v1.items() if k in kept], lambda x: x["v"]),
            by_cfg(out_ans, lambda x: x["concept_recall_loose_v22"])),
        "number overlap": (by_cfg(v1_all, om("number_overlap")), by_cfg(v1_kept, om("number_overlap")),
                           by_cfg(v22, om("number_overlap"))),
        "completeness score (0-5)": (by_cfg(v1_all, ds("completeness")), by_cfg(v1_kept, ds("completeness")),
                                     by_cfg(v22, ds("completeness"))),
        "citation quality score (0-5)": (by_cfg(v1_all, ds("citation_quality")),
                                         by_cfg(v1_kept, ds("citation_quality")),
                                         by_cfg(v22, ds("citation_quality"))),
    }
    if sims:
        for label, f, d in (("correctness score (0-5)", "correctness_composite", "correctness"),
                            ("faithfulness score (0-5)", "faithfulness_composite", "faithfulness")):
            tables[label] = (by_cfg(v1_all, ds(d)), by_cfg(v1_kept, ds(d)), by_cfg(v22, ds(d)))
    # the refutation group: the current key only (the deposit scored these rows as refusals)
    ref_tables = {"concept recall": by_cfg(v22_ref, om("concept_recall")),
                  "concept recall, loose (O30)": by_cfg(out_ref, lambda x: x["concept_recall_loose_v22"]),
                  "number overlap": by_cfg(v22_ref, om("number_overlap")),
                  "completeness score (0-5)": by_cfg(v22_ref, ds("completeness")),
                  "citation quality score (0-5)": by_cfg(v22_ref, ds("citation_quality"))}
    if sims:
        ref_tables["correctness score (0-5)"] = by_cfg(v22_ref, ds("correctness"))
        ref_tables["faithfulness score (0-5)"] = by_cfg(v22_ref, ds("faithfulness"))
    ref_n = Counter(r["config"] for r in v22_ref)

    def moved(a, b):                            # the answerable group only: the refutation group has no v1 value
        up = sum(float(r[b]) > float(r[a]) for r in out_ans)
        down = sum(float(r[b]) < float(r[a]) for r in out_ans)
        return up, down, len(out_ans) - up - down

    qs_kept = sorted({r["question_id"] for r in out_ans})
    no_concepts = (sum(not v1q[q]["expected_concepts"] for q in qs_kept), sum(not kq[q]["expected_concepts"] for q in qs_kept))
    no_numbers = (sum(not ex_numbers(v1q[q]["expected_answer"]) for q in qs_kept),
                  sum(not ex_numbers(kq[q]["expected_answer"]) for q in qs_kept))
    qs_ref = sorted({r["question_id"] for r in out_ref})
    ref_no = {"concepts": sum(not kq[q]["expected_concepts"] for q in qs_ref),
              "numbers": sum(not ex_numbers(kq[q]["expected_answer"]) for q in qs_ref),
              "sources": sum(not kq[q].get("source_files") for q in qs_ref)}

    gf = g["fields"]
    md = [f"# S382 exp04 objective scores on ground truth {K} ({prov['generated']})", "",
          f"`{json.dumps({k: prov[k] for k in ('script', 'generated', 'key', 'key_sha256', 'gate')})}`", "",
          f"Key {prov['key']} sha256 {prov['key_sha256'][:12]}; answers {prov['answers']}; scorer "
          f"{sources[0]['path']} sha256 {sources[0]['sha256'][:12]} (lines "
          f"{', '.join(f'{n} {s}' for n, s in sources[0]['lines'].items())}); load_ground_truth "
          f"{sources[1]['path']} sha256 {sources[1]['sha256'][:12]} (lines {sources[1]['lines']['load_ground_truth']}).", "",
          "## Gate: the lifted scorer on the v1 key reproduces the deposit", "",
          f"Key {prov['gate_key']} sha256 {prov['gate_key_sha256'][:12]}, deposited similarity, all 828 rows "
          f"against {prov['deposited_scores']}.", "",
          "| field (answerable rows) | compared | equal | max abs diff | rule |", "|---|--:|--:|--:|---|"]
    for f in EXACT:
        md.append(f"| {f} | {gf[f]['compared']} | {gf[f]['equal']} | {gf[f]['max_abs_diff']:.1e} | equal |")
    for f in SIM_COMPOSITES:
        md.append(f"| {f} | {gf[f]['compared']} | {gf[f]['equal']} | {gf[f]['max_abs_diff']:.1e} | within 1e-4 |")
    for d in DIMS:
        md.append(f"| {d} score (0-5) | {gf['score_' + d]['compared']} | {gf['score_' + d]['equal']} | | equal |")
    md += [f"| unanswerable rows, every field | {gf['unanswerable_all_fields']['compared']} | "
           f"{gf['unanswerable_all_fields']['equal']} | | equal |", "",
           "The two composites are compared within one unit of the fourth decimal because the deposit "
           "stores similarity rounded to four decimals and built the composites from the unrounded value.", "",
           "## D7: rows skipped", "",
           f"{skipped} exp04 rows skipped by score_all for {', '.join(d7_questions)}: {d7['answerable']} "
           f"answerable and {d7['unanswerable']} unanswerable. {len(out_ans)} of {g['answerable']} answerable "
           f"answers remain ({len(qs_kept)} questions x 6 strategies).", "",
           f"Beside them, {len(out_ref)} answers on the {len(qs_ref)} false-premise questions are scored as answerable "
           f"on {K} (D5) and reported as their own group, in the section on them below.", "",
           "## Per-strategy means", "",
           f"v1 is the deposited value; v1 kept is the same restricted to the answers {K} keeps, so the "
           "effect of D7 and the effect of the new key can be told apart.", "",
           f"These tables, and the per-answer counts after them, are over the answerable group ({len(out_ans)} "
           "answers; the v1 (528) column also the 12 rows D7 drops); the refutation group is in none of them.", ""]
    for label, (a, b, c) in tables.items():
        md += [f"### {label}", "", f"| strategy | v1 (528) | v1 kept | {K} |", "|---|--:|--:|--:|"]
        for cfg in CONFIGS + ["pooled"]:
            md.append(f"| {cfg} | {a[cfg]:.4f} | {b[cfg]:.4f} | {c[cfg]:.4f} |")
        md.append("")
    md += ["## What moved", "",
           f"| per answer, v1 to {K} | up | down | unchanged |", "|---|--:|--:|--:|"]
    for lab, a, b in (("concept recall", "concept_recall_v1", "concept_recall_v22"),
                      ("concept recall, loose", "concept_recall_loose_v1", "concept_recall_loose_v22"),
                      ("number overlap", "number_overlap_v1", "number_overlap_v22"),
                      ("completeness score", "det_score_completeness_v1", "det_score_completeness_v22")):
        md.append(f"| {lab} | " + " | ".join(str(x) for x in moved(a, b)) + " |")
    if sims:
        for lab, a, b in (("correctness score", "det_score_correctness_v1", "det_score_correctness_v22"),
                          ("faithfulness score", "det_score_faithfulness_v1", "det_score_faithfulness_v22")):
            md.append(f"| {lab} | " + " | ".join(str(x) for x in moved(a, b)) + " |")
    md += ["",
           f"Of the {len(qs_kept)} kept answerable questions, {no_concepts[0]} (v1) and {no_concepts[1]} ({K}) have "
           f"no expected concepts, which the scorer counts as recall 1.0; {no_numbers[0]} (v1) and {no_numbers[1]} "
           f"({K}) have no number in the expected answer, which it counts as overlap 1.0 "
           "(analysis_deterministic_scorer.py:132-133, 203-204).", "",
           "In the answerable group, citation quality reads the answer and the source files only; source_files "
           "are v1 in both keys, so it is identical answer by answer (asserted).", "",
           "## Loose concept recall (Q26 with O30) beside the scorer's", "",
           "Rule 1 of the loose matcher is \"a concept the exact matcher finds is found\". In this file the exact "
           "column is the deposited exp04 scorer's concept recall "
           f"({sources[0]['path']}, compute_concept_recall, lines {sources[0]['lines']['compute_concept_recall']}), "
           "not the plain substring rule: after the substring test it also counts a multi-word concept when every "
           "whitespace-separated piece of it longer than three characters occurs in the answer as a substring, "
           "and tries hyphen and space variants. The loose rule alone could therefore miss a concept the published "
           "column counts, in two ways: (a) the scorer does not check pieces of three characters or fewer "
           "(\"65%\" in \"65% reduction\"), while for the loose rule a number, or a short word not on its stop "
           "list, is a content word to match; (b) the scorer finds a piece inside a longer word of the answer "
           "(\"high\" inside \"higher\"), while the loose rule needs a whole token. O30 applies rule 1 with the "
           "scorer exp04 used.", "",
           f"concept_recall_loose_v1 and concept_recall_loose_v22 count a concept as found when the deposited "
           f"compute_concept_recall, called on that concept alone, counts it, or concept_recall_loose ({rel(LOOSE)}, "
           f"sha256 {sha256(LOOSE)[:12]}) finds it, on the answer text score_all reads; recall is found concepts over "
           "all concepts, rounded to four decimals. Before writing, this run checked on every answer, for each key: "
           "the per-concept scorer decisions reproduce compute_concept_recall on the whole concept list and the "
           f"published concept recall ({len(lx['v1'])} of {len(lx['v1'])} on v1, {len(lx[K])} of "
           f"{len(lx[K])} on {K}); loose is at least the published concept recall (below on "
           f"{vs_scorer['v1']['below']} on v1 and {vs_scorer[K]['below']} on {K}, table below); loose is at "
           "least the harness's exact substring rule "
           f"({sources[2]['path']}, compute_concept_recall, lines {sources[2]['lines']['compute_concept_recall']}; "
           f"{floor_n['v1']} of {floor_n['v1']} on v1, {floor_n[K]} of {floor_n[K]} on {K}).", "",
           "| answers, loose against the scorer's concept recall | above | equal | below |", "|---|--:|--:|--:|",
           f"| v1 key, {sum(vs_scorer['v1'].values())} answerable | {vs_scorer['v1']['above']} | "
           f"{vs_scorer['v1']['equal']} | {vs_scorer['v1']['below']} |",
           f"| {K} key, {sum(vs_scorer[K].values())} kept | {vs_scorer[K]['above']} | "
           f"{vs_scorer[K]['equal']} | {vs_scorer[K]['below']} |", "",
           "What O30 changed, measured in this run against the loose rule alone (the column before O30):", "",
           "| key | answers | loose alone below the scorer's | answers raised by the scorer's decision "
           "| concepts added | pooled mean, loose alone | pooled mean, loose (O30) |",
           "|---|--:|--:|--:|--:|--:|--:|",
           f"| v1 | {len(lx['v1'])} | {alone_below['v1']} | {raised['v1']} | {added['v1']} | "
           f"{pooled['v1'][0]:.4f} | {pooled['v1'][1]:.4f} |",
           f"| {K} | {len(lx[K])} | {alone_below[K]} | {raised[K]} | {added[K]} | "
           f"{pooled[K][0]:.4f} | {pooled[K][1]:.4f} |", ""]
    md += ["## The ten false-premise questions (D5), their own group", "",
           f"The {len(qs_ref)} questions with answer_type \"refutation\" in {rel(S373.KEY)} ({', '.join(qs_ref)}) "
           f"are answerable in {prov['key']}, and the deposit's exp04 rows flag them unanswerable. This run gave "
           f"their {len(out_ref)} rows the key's flag, so score_all scored them as answerable answers against the "
           "key's expected_answer, expected_concepts and source_files for them. The deposit scored them as "
           "refusals, so every v1 column is blank on them (group \"refutation\" in the CSV). None of the "
           "per-strategy, what-moved or loose tables above includes them; the gate's 300 unanswerable rows include "
           "their 60, re-scored as refusals on the v1 key, as the deposit scored them.", "",
           "| strategy | answers | " + " | ".join(ref_tables) + " |", "|---|--:|" + "--:|" * len(ref_tables)]
    for cfg in CONFIGS + ["pooled"]:
        md.append(f"| {cfg} | {len(v22_ref) if cfg == 'pooled' else ref_n[cfg]} | "
                  + " | ".join(f"{t[cfg]:.4f}" for t in ref_tables.values()) + " |")
    md += ["",
           f"Of the {len(qs_ref)}, {ref_no['concepts']} have no expected concepts and {ref_no['numbers']} no number "
           f"in the expected answer on {K}, which the scorer counts as recall 1.0 and overlap 1.0; "
           f"{ref_no['sources']} have no source_files in the key"
           + (", so on their rows source coverage is 0 (analysis_deterministic_scorer.py:240-241) and the citation "
              "composite is at most 0.5 (0.25 has citations + 0.25 citation density)." if ref_no["sources"] else
              ", so citation quality reads each one's source files from the key."), "",
           f"Loose concept recall on the refutation group, with the checks the answerable group passes: the "
           f"per-concept scorer decisions reproduce compute_concept_recall and the published concept recall on "
           f"{len(lx[KR])} of {len(lx[KR])} answers; loose is at least the published concept recall (below on "
           f"{vs_scorer[KR]['below']}) and at least the harness's exact substring rule ({floor_n[KR]} of "
           f"{floor_n[KR]}).", "",
           "| answers | loose above the scorer's | equal | below | loose alone below the scorer's | answers raised "
           "by the scorer's decision | concepts added | pooled mean, loose alone | pooled mean, loose (O30) |",
           "|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
           f"| {len(lx[KR])} | {vs_scorer[KR]['above']} | {vs_scorer[KR]['equal']} | {vs_scorer[KR]['below']} | "
           f"{alone_below[KR]} | {raised[KR]} | {added[KR]} | {pooled[KR][0]:.4f} | {pooled[KR][1]:.4f} |", ""]
    if sims:
        md += ["## The similarity input", "", f"Similarity: {prov['similarity']['file']} column `{args.sim_column}` sha256 "
               f"{prov['similarity']['sha256'][:12]}.", "",
               "The v1 correctness and faithfulness columns are the deposited ones, built on similarity over the "
               "first 2,000 characters. If this similarity reads the complete answer, the like-for-like v1 is S30's "
               "det_score_correctness_fullsim and det_score_faithfulness_fullsim "
               "(findings/recompute/S30_baseline_scores_full.csv).", ""]
    else:
        md += ["## Pending: the similarity-dependent scores", "",
               "semantic_similarity_v22, correctness_composite_v22 (0.6 x similarity + 0.4 x number overlap), "
               "faithfulness_composite_v22 (concept recall x similarity) and their 0-5 scores are blank: they need "
               f"the {K} BGE-M3 similarity (T4). When T4's per-answer file exists:", "",
               "    uv run python scripts/S382_exp04_objective_v22.py --similarity <T4 file> --sim-column <column>", "",
               "writes S382_exp04_objective_v22_<column>.{csv,md}. The CSV's first line is a `# {provenance}` "
               "comment; read it with `pd.read_csv(path, comment=\"#\")` or skip one row.", "",
               f"The similarity file must cover both groups: the run exits if it lacks any of the {len(out_ref)} "
               "answers of the refutation group.", ""]
    stem.with_suffix(".md").write_text("\n".join(md))
    print(f"[S382] wrote {rel(stem.with_suffix('.csv'))} ({len(out_ans)} answerable and {len(out_ref)} refutation "
          f"rows) and {rel(stem.with_suffix('.md'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
