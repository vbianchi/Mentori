#!/usr/bin/env python3
"""
S08 - Human-eval analysis engine (Mentori revision, Wave B).

Unblocks the ~7h human rating of the 50-item / 2-rater blinded instrument.
The RATINGS THEMSELVES ARE NOT PRODUCED HERE - this script (a) reconstructs the
seed-42 stratified sample and verifies the join to the master_join, and (b)
provides the analysis engine that will run once raters fill the CSV, validated
today in --smoke-test mode against synthetic ratings + hand-computable unit tests.

Provenance
----------
script : scripts/S08_human_eval_analysis.py
inputs :
  - <upstream>/publication/results/analysis_human_eval_20260310.csv       (50 blinded items, 2 raters, 0/50 scored)
  - <upstream>/publication/results/analysis_human_eval_20260310.key.json  (blinding key: Strategy_X -> config, seed 42)
  - <repo>/findings/recompute/master_join.csv                             (verified master join, 828 rows)
  - <upstream>/publication/results/exp04_generation_latest.json           (per_question_results, 828 rows; base for seed-42 reconstruction)
  - <upstream>/publication/results/exp04_minicheck_latest.json            (per_result, 528 rows; per-claim MiniCheck details)
outputs:
  - stdout report + findings/recompute/S08_join_verification.json

The seed-42 sampling logic is REIMPLEMENTED here from the read-only
publication sampler (analysis_human_eval_sampler.py:stratified_sample) - the
publication script is NOT imported or executed (trust boundary). Reading it to
learn the sampling definition is permitted.

Statistics implemented (per dimension, ordinal 0-5):
  - Quadratic-weighted Cohen's kappa   (via sklearn)
  - Ordinal Krippendorff's alpha        (via krippendorff pkg)
  - ICC(2,1)                            (via pingouin)
  - Gwet's AC2                          (implemented manually, weighted)
  - Bootstrap 95% CIs (item resampling) for each
  - Raw exact + adjacent (+/-1) % agreement
Then: human-vs-judge and human-vs-MiniCheck (weighted kappa + Spearman);
judge & MiniCheck as hallucination detectors (precision/recall) vs human gold.

v2.2 MODE (--v22; added 10 October 2026, before any v2.2 rating exists)
------------------------------------------------------------------------
WHY. The approved protocol findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md (9 October) withdraws the
4 August round and fixes a new one: 49 items (the seed-42 50 less E038, SY_010, dropped by D7),
expert answers from ground truth v2.2, v2.3 since 11 October (protocol amendment 6, Q45; v2.4, Q50, changes none of
the 36 rated questions), key points from v2.5 since 31 October (amendment 9; D190: G2 checks the master against
ground_truth_v2_5_as_v1.json, and the judge values are S508's lock-judge rows on it, D183 FD11 c), the judge
devstral-small-2:24b, any number of raters
(every complete packet counted, every incomplete one excluded), five computations and the
decision rule. Its last section asks for this engine to be extended to any number of raters, to
49 items and to the devstral and v2.2 inputs, and validated again on synthetic ratings. Without
--v22 nothing above changes: same functions, same output, same files.

HOW. Items 1 to 5 of the protocol, nothing else (S08's detector and per-dimension analyses are
not in the protocol and are not computed in this mode). Scale 1 to 5, q = 5 categories.
  1  faithfulness, included raters: ordinal Krippendorff's alpha (krippendorff package, value
     domain 1..5), ICC(2,1) (two-way random, absolute agreement, single rater, from the ANOVA mean
     squares), Gwet's AC2 with quadratic weights (Gwet's multi-rater formula), the mean of the
     pairwise quadratic-weighted Cohen's kappas, exact and adjacent (+/-1) agreement both as the
     mean over rater pairs and as the share of items on which every rater agrees
  2  Spearman(mean human faithfulness, the judge's faithfulness on key v2.5, S508's rows (D190))
  3  Spearman(mean human faithfulness, MiniCheck claim precision)
  4  D = rho2 - rho3; 95% percentile interval over 2,000 resamples of the analysis items (the 49,
     less any Q40 removes, below), np.random.default_rng(42), the same draws for every statistic (paired)
  5  descriptive: Spearman(mean human, judge) for correctness and completeness, each with its
     interval. The protocol's item 5 also names overall, but the judge gives no overall score (it
     emits correctness, completeness, faithfulness and citation_quality, S141_runner/judge.py
     ANSWERABLE_DIMS). The overall comparison is therefore not computed and the results say so:
     a departure decided by Valerio Bianchi on 10 October 2026, before any rating (Q35; the
     protocol's "Amendments before any rating"). No option chooses a comparator for it.
  then the decision rule, its sentences checked verbatim against the protocol file.

The join (no rating is read). Gates, any failure refuses and writes nothing:
  G1  the seed-42 reconstruction reproduces findings/recompute/S08_join_verification.json: the
      same 50 (eval_id, question_id, config), all_50_reproduce true
  G2  the v2.2 master's 49 rows are those 50 less E038 (S385's record), in order; each row's
      question, generated answer and category equal the reconstruction's, its strategy decodes
      to the reconstruction's config through the blinding key, its question_id is S385's, its
      expected answer and key points are key v2.5's (V22_KEY25, ground_truth_v2_5_as_v1.json, whose sha256
      must be V22_KEY25_SHA256, the pin S508 judges under, and whose "version" must be 2.5; D190), and
      that key is the one the judge was given (S508.KEY25 and its pin are the same file and sha256; per item,
      S508.items_49 names the same question and strategy with the key_hash of this key's expected answer and
      key points, s508_key_hash; the judge reader then requires each S508 row to carry it). Until D190 G2
      read key v2.4 (S373.AS_V1 built from S373.KEY, S373.key_of): v22_join(key_version="2.4") keeps that
      path, and v22_reproduce_v24 runs it on the 12 October master (from git, V22_V24_MASTER) and requires
      the join stored that day (from git, V22_V24_JOIN) before --verify-join, --smoke-test or the analysis
      writes anything (README.md:75-79)
  G3  S373's own reader (S373.source_files) gives the 807 exp04 answers left after D7 (S388
      KNOWN_LABEL), and each master row's (question, generated answer) names exactly one of them,
      the same (question_id, config) as the reconstruction: that row's S373 key is the item's key
  G4  S08's MiniCheck value for the item (master_join mc_precision) equals the deposited
      exp04_minicheck_latest.json precision, and S384's v1_deposited precision when S384 has the row
Judge value (D190; D183 FD11 c): S508's rows on key v2.5, findings/recompute/S508_judge_49_v25/ or --judge-dir,
read with S508's own functions (items_49, latest, recheck_state, recheck_valid). The reader refuses unless
summary.json names the v2.5 pin, S508's 49 items are the join's, rows.jsonl holds every item under summary.json's
run_sha256 with status ok and the join's question_id, config, answer_chars and v2.5 key_hash, judged by the lock's
judge (model_digest = LOCK.toml [models] digest of [judge] model) under the lock summary.json names for the run, and
recheck_summary.json is a passed recheck of that run made after all 49 were judged. --ledger (S373 ledgers, the
judge values until D190) is refused with --v22.
MiniCheck value: "MiniCheck claim precision, as defined in S08" is master_join mc_precision, the
deposited exp04 run, which asks whether each answer sentence is entailed by the key's expected
answer (S384 docstring, analysis_minicheck.py:131-175). With the key replaced by the current one that
is S384's minicheck.precision (findings/recompute/S384_exp04_minicheck_key_v22.jsonl, or its
shards), every session and row under the sha256 of V22_MC_KEY (S373.AS_V1, ground_truth_v2_4_as_v1.json). D190
leaves it on key v2.4: amendment 9 says MiniCheck "reads the expected answer, which did not change". What is checked:
S508.items_49 (run by the v2.5 join and the judge reader) refuses unless v2.5's expected answers equal v2.3's on the
49 items. What is not: no line here compares v2.5's expected answers with v2.4's directly (open point R1; on the
files of 31 October they differ on 0 of the 36 questions). S19's source
and decoy runs measure grounding in the papers, a different quantity, and are not used.

Refusals on real ratings (--v22 [--analyze PATH]): unless the known-answer tests (v22_unit_tests,
the same as --unit-tests) all pass, run first on every analysis run (O20, 10 October 2026); before
the protocol's deadline (Wed 4 November 2026 15:30 CET since its amendment of 4 November, D244; --deadline may move it later, never
earlier); unless the reproduction of the stored v2.4 join passes (v22_reproduce_v24); unless every one of the 49
items has a judge faithfulness, correctness and completeness score (S508, key v2.5) and a MiniCheck precision
(checked before any rating cell is read); unless the
ratings file carries, row for row and in order, the current master's seven content columns (V22_CONTENT,
eval_id to expected_concepts) with the same values, so that ratings collected on an older master (another
key's expected answers) are not analysed against the current judge key (v22_require_same_content, content
columns only, before any rating cell is read); with fewer than two included packets, or with --one-rater anything but
exactly one included packet, r1 (below). A packet is included when none of its 196 score cells (49 items x four
scales) is blank and its invalid cells (below) on correctness, completeness and faithfulness sit on
10 items or fewer; one with any blank score cell, overall included, is excluded whole (Q36; Valerio
confirmed on 10 October 2026 that a blank overall cell excludes it too, Q43). Every packet is reported
by a status and its counts of rated, invalid and blank cells and of the items its invalid cells on
those three scales sit on, never by a value. The statuses: "complete" (every score cell a whole number
from 1 to 5), "included, with invalid cells" (none blank, at least one invalid, those on the three
scales on 10 items or fewer), "invalid on more than 10 items, excluded" (none blank, invalid cells on
the three scales on more than 10 items), "no ratings" (every score cell blank), "incomplete, excluded"
(some blank, not all).

The analysis item set (Q40, Valerio Bianchi, 10 October 2026, before any rating): a rating cell that
is not blank and not a whole number from 1 to 5 no longer refuses the run. In an included packet it
takes its item out of the analysis for every rater, and the packet still counts; in an excluded
packet it removes nothing. Two such cells on one item remove it once. Items 1 to 5 and D, with its
bootstrap (2,000 resamples of the items left, seed 42), run on the 49 items less the removed ones;
results and report give the set's size, each removed item with the packet and scale of its cells
(never the value), and name any statistic the set is too small to define as undefined (Spearman and
ICC(2,1) need two items). S354 --round v22 writes the word "invalid" in place of such a cell, so its
value never reaches the CSV, and this rule reads it as invalid. Nothing is kept between runs: a
corrected packet collected again has no invalid cell, and its item is back.
O28 and O29 (Valerio Bianchi, 10 October 2026, before any rating; protocol amendment 5) refine it.
Only correctness, completeness and faithfulness, the scales a statistic reads (V22_STAT_SCALES),
count. A packet with no blank score cell whose invalid cells on those scales sit on more than 10
distinct items (V22_MAX_INVALID_ITEMS; items are counted, not cells) is excluded whole, as not
completed, and removes no item; its cells are listed with those of the other excluded packets. At 10
or fewer the rule above applies. An invalid overall cell neither removes its item nor counts toward
the 10; results and report list it. Overall enters no statistic: its cells count only for the blank
rule, the per-packet counts and that listing.

The one-rater mode (--v22 --one-rater --on-word D<nnn>; protocol amendment 8; FP r1 2.14 a, D193 (1)). It runs on
Valerio's word, with no fixed date, so it skips the deadline check and asks instead that D<nnn> stands as a decision line
of experiments/README.md (v22_on_word). Every other refusal above stands. Exactly one packet must be included and it must
be r1 (v22_parse_ratings with min_included=1, then v22_analyze). It computes items 2, 3, 5 and D with r1 as the mean. It
skips v22_irr and v22_decide: with one rater item 1 and the gate cannot be computed, and no decision is taken, so
item1_reliability_faithfulness is null, decision.outcome is "descriptive" and the report says every number is
descriptive (S08b, amendment 8). It writes S08_v22_results_one_rater.{json,md}, git-ignored, and never
S08_v22_results.{json,md}.

    uv run python scripts/S08_human_eval_analysis.py --v22 --unit-tests     # known answers only
    uv run python scripts/S08_human_eval_analysis.py --v22 --smoke-test     # + synthetic scenarios
    uv run python scripts/S08_human_eval_analysis.py --v22 --verify-join    # join + input coverage
    uv run python scripts/S08_human_eval_analysis.py --v22 [--analyze CSV]  # after the deadline
    uv run python scripts/S08_human_eval_analysis.py --v22 --one-rater --on-word D<nnn>   # on Valerio's word only
Writes findings/recompute/S08_v22_smoke_test.json (synthetic ratings only), S08_v22_join.json
(join and coverage, no rating) and S08_v22_results.{json,md} (the protocol's analysis).
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RECOMPUTE, RESULTS, ROOT, rel  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402  (the judge's key: KEY, AS_V1; a 0.1 s import)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PAPER = RESULTS
HUMAN_CSV = PAPER / "analysis_human_eval_20260310.csv"
KEY_JSON = PAPER / "analysis_human_eval_20260310.key.json"
MASTER_JOIN = RECOMPUTE / "master_join.csv"
GEN_JSON = PAPER / "exp04_generation_latest.json"
MINICHECK_JSON = PAPER / "exp04_minicheck_latest.json"
JOIN_OUT = RECOMPUTE / "S08_join_verification.json"

DIMENSIONS = ["correctness", "completeness", "faithfulness", "overall"]
# Human dims that map onto a judge dimension of the same name:
JUDGE_SHARED = ["correctness", "completeness", "faithfulness"]

# Sampler constants (mirror analysis_human_eval_sampler.py; NOT imported)
ALL_CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
ANSWERABLE_CATEGORIES = ["factual_recall", "conceptual", "technical", "cross_document", "synthesis"]
SEED = 42
SCALE_MAX = 5  # ordinal 0..5


# ===========================================================================
# 1. Seed-42 sample reconstruction
# ===========================================================================
def _stratified_sample(results, n=50, seed=SEED):
    """Reimplementation of the publication sampler's stratified_sample().

    Deterministic given the ordering of `results`; uses random.Random(seed)
    which is unaffected by PYTHONHASHSEED.
    """
    rng = random.Random(seed)
    pool = [
        r for r in results
        if r.get("answerable", True)
        and r.get("config") in ALL_CONFIGS
        and r.get("category") in ANSWERABLE_CATEGORIES
    ]
    groups = defaultdict(list)
    for r in pool:
        groups[(r["config"], r["category"])].append(r)
    total = len(pool)
    sampled = []
    remaining = n
    for key in sorted(groups.keys()):
        group = groups[key]
        alloc = max(1, round(len(group) / total * n))
        alloc = min(alloc, remaining, len(group))
        if alloc > 0:
            sampled.extend(rng.sample(group, alloc))
            remaining -= alloc
        if remaining <= 0:
            break
    if remaining > 0:
        used = {r["question_id"] + "|" + r["config"] for r in sampled}
        extras = [r for r in pool if r["question_id"] + "|" + r["config"] not in used]
        rng.shuffle(extras)
        sampled.extend(extras[:remaining])
    rng.shuffle(sampled)
    return sampled[:n]


def reconstruct_sample():
    """Return ordered list of dicts (E001..E050) with question_id/config/etc."""
    data = json.loads(GEN_JSON.read_text())
    results = data["per_question_results"]
    # Enrich generated_answer exactly as the sampler did (ordering unaffected).
    for r in results:
        if not r.get("generated_answer"):
            gen = r.get("generation", {})
            r["generated_answer"] = gen.get("answer", "") if isinstance(gen, dict) else ""
    sampled = _stratified_sample(results, n=50, seed=SEED)
    out = []
    for i, s in enumerate(sampled, 1):
        out.append({
            "eval_id": f"E{i:03d}",
            "question_id": s["question_id"],
            "config": s["config"],
            "category": s.get("category", ""),
            "question": (s.get("question", "") or "").strip(),
            "generated_answer": s.get("generated_answer", "") or "",
            "expected_answer": s.get("expected_answer", "") or "",
        })
    return out


def verify_join():
    """Decode key -> (question_id, config) for all 50; verify master_join rows.

    Cross-checks the reconstruction against the CSV (question text + de-anon
    config) and confirms each item maps to an answerable master_join row that
    carries judge + MiniCheck scores.
    """
    import pandas as pd

    key = json.loads(KEY_JSON.read_text())
    anon = key["anonymization"]  # Strategy_X -> config
    csv_rows = list(csv.DictReader(HUMAN_CSV.open(encoding="utf-8")))
    sample = reconstruct_sample()

    master = pd.read_csv(MASTER_JOIN)
    midx = master.set_index(["question_id", "config"])

    per_item = []
    csv_match = 0
    join_ok = 0
    for row, s in zip(csv_rows, sample):
        csv_cfg = anon.get(row["strategy"], row["strategy"])
        csv_q = row["question"].strip()
        cfg_match = (csv_cfg == s["config"])
        q_match = (csv_q == s["question"])
        if cfg_match and q_match:
            csv_match += 1
        qid, cfg = s["question_id"], s["config"]
        has_row = (qid, cfg) in midx.index
        judge_ok = mc_ok = answerable = False
        if has_row:
            mr = midx.loc[(qid, cfg)]
            answerable = bool(mr["answerable"])
            judge_ok = bool(pd.notna(mr["judge_faithfulness"]))
            mc_ok = bool(pd.notna(mr["mc_precision"]))
        item_join_ok = has_row and answerable and judge_ok and mc_ok
        if item_join_ok:
            join_ok += 1
        per_item.append({
            "eval_id": s["eval_id"], "question_id": qid, "config": cfg,
            "csv_strategy": row["strategy"], "csv_cfg_match": cfg_match,
            "csv_question_match": q_match, "master_row_present": has_row,
            "answerable": answerable, "judge_present": judge_ok,
            "minicheck_present": mc_ok, "join_ok": item_join_ok,
        })

    from subprocess import run
    ts = run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()
    report = {
        "_provenance": {
            "script": "scripts/S08_human_eval_analysis.py",
            "generated": ts,
            "inputs": [rel(GEN_JSON), rel(KEY_JSON), rel(HUMAN_CSV), rel(MASTER_JOIN)],
            "notes": "seed-42 stratified sample reconstructed from exp04 generation "
                     "records; publication sampler NOT imported (reimplemented).",
        },
        "seed": SEED,
        "n_items": len(sample),
        "csv_reconstruction_exact_matches": csv_match,
        "join_ok_count": join_ok,
        "all_50_reproduce": csv_match == 50 and join_ok == 50,
        "blinding_key": anon,
        "per_item": per_item,
    }
    JOIN_OUT.write_text(json.dumps(report, indent=2))
    return report


# ===========================================================================
# 2. Statistics
# ===========================================================================
def quadratic_weighted_kappa(r1, r2):
    """Cohen's kappa with quadratic weights over the ordinal 0..SCALE_MAX scale."""
    from sklearn.metrics import cohen_kappa_score
    labels = list(range(SCALE_MAX + 1))
    return float(cohen_kappa_score(r1, r2, weights="quadratic", labels=labels))


def krippendorff_ordinal(r1, r2):
    """Ordinal Krippendorff's alpha for two coders."""
    import krippendorff
    data = np.array([r1, r2], dtype=float)
    return float(krippendorff.alpha(reliability_data=data, level_of_measurement="ordinal"))


def icc_2_1(r1, r2):
    """ICC(2,1) - two-way random, single measures, absolute agreement."""
    import pandas as pd
    r1 = list(r1); r2 = list(r2)
    # Degenerate cases: pingouin divides by zero error variance.
    if np.array_equal(r1, r2):
        return 1.0
    if np.var(r1 + r2) == 0:
        return 1.0
    n = len(r1)
    df = pd.DataFrame({
        "target": list(range(n)) * 2,
        "rater": ["r1"] * n + ["r2"] * n,
        "score": list(r1) + list(r2),
    })
    import pingouin as pg
    res = pg.intraclass_corr(data=df, targets="target", raters="rater", ratings="score")
    # ICC(2,1) = two-way random, absolute agreement, single measures.
    # pingouin labels it "ICC2" (older) or "ICC(A,1)" (newer). Accept both.
    types = set(res["Type"])
    label = "ICC2" if "ICC2" in types else ("ICC(A,1)" if "ICC(A,1)" in types else None)
    if label is None:
        return float("nan")
    row = res[res["Type"] == label]
    if row.empty or not np.isfinite(row["ICC"].iloc[0]):
        return float("nan")
    return float(row["ICC"].iloc[0])


def _quadratic_weight_matrix(k):
    """Agreement weights w_ij = 1 - (i-j)^2/(k-1)^2 for k categories."""
    idx = np.arange(k)
    diff = idx[:, None] - idx[None, :]
    return 1.0 - (diff ** 2) / ((k - 1) ** 2)


def gwet_ac2(r1, r2, weights="quadratic"):
    """Gwet's AC2 (weighted) - paradox-resistant agreement coefficient.

    Manual implementation. With identity weights this reduces to Gwet's AC1.
      p_a = sum_ij w_ij p_ij                          (weighted observed agreement)
      pi_k = (p_{k+} + p_{+k}) / 2                     (mean marginal for category k)
      T_w = sum_ij w_ij
      p_e = T_w / (q(q-1)) * sum_k pi_k (1 - pi_k)
      AC2 = (p_a - p_e) / (1 - p_e)
    """
    cats = list(range(SCALE_MAX + 1))
    q = len(cats)
    idx = {c: i for i, c in enumerate(cats)}
    O = np.zeros((q, q))
    for a, b in zip(r1, r2):
        O[idx[int(a)], idx[int(b)]] += 1
    N = O.sum()
    P = O / N
    if weights == "quadratic":
        W = _quadratic_weight_matrix(q)
    elif weights == "identity":
        W = np.eye(q)
    else:
        raise ValueError(weights)
    p_a = float((W * P).sum())
    row_marg = P.sum(axis=1)
    col_marg = P.sum(axis=0)
    pi = (row_marg + col_marg) / 2.0
    T_w = float(W.sum())
    p_e = (T_w / (q * (q - 1))) * float((pi * (1 - pi)).sum())
    if abs(1 - p_e) < 1e-12:
        return 1.0
    return float((p_a - p_e) / (1 - p_e))


def pct_agreement(r1, r2):
    r1 = np.asarray(r1); r2 = np.asarray(r2)
    exact = float(np.mean(r1 == r2) * 100)
    adjacent = float(np.mean(np.abs(r1 - r2) <= 1) * 100)
    return exact, adjacent


def bootstrap_ci(func, r1, r2, n_boot=2000, seed=SEED, alpha=0.05):
    """Item-level bootstrap 95% CI for a two-rater statistic."""
    rng = np.random.default_rng(seed)
    r1 = np.asarray(r1); r2 = np.asarray(r2)
    n = len(r1)
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        try:
            v = func(r1[idx].tolist(), r2[idx].tolist())
            if v is not None and np.isfinite(v):
                stats.append(v)
        except Exception:
            continue
    if not stats:
        return (float("nan"), float("nan"))
    lo = float(np.percentile(stats, 100 * alpha / 2))
    hi = float(np.percentile(stats, 100 * (1 - alpha / 2)))
    return lo, hi


# ===========================================================================
# 3. Unit tests (hand-computable)
# ===========================================================================
def run_unit_tests():
    print("\n=== UNIT TESTS (hand-computable) ===")
    ok = True

    def check(name, got, expected, tol=1e-6):
        nonlocal ok
        passed = abs(got - expected) <= tol
        ok = ok and passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: got={got:.6f} expected={expected:.6f}")

    # --- Perfect agreement -> 1.0 for all statistics
    a = [0, 1, 2, 3, 4, 5, 5, 4, 3, 2]
    check("QWK identical", quadratic_weighted_kappa(a, a), 1.0)
    check("Krippendorff identical", krippendorff_ordinal(a, a), 1.0)
    check("ICC(2,1) identical", icc_2_1(a, a), 1.0, tol=1e-4)
    check("Gwet AC2 identical", gwet_ac2(a, a), 1.0)

    # --- QWK == 0 for the balanced 2x2 case (hand-derived: Do=De=0.5 -> kappa=0)
    #     r1=[1,1,2,2], r2=[1,2,1,2]; symmetric marginals, chance-level.
    check("QWK balanced-2x2 == 0", quadratic_weighted_kappa([1, 1, 2, 2], [1, 2, 1, 2]), 0.0, tol=1e-9)

    # --- Kappa paradox demonstration (skewed marginals), unweighted:
    #     r1 = eight 1s + two 2s ; r2 = nine 1s + one 2  (one disagreement)
    #     Hand (Cohen, category count irrelevant): kappa = 0.16/0.26 = 0.615385
    #     Hand (Gwet AC1 over the full q=6 rating scale, the instrument's scale):
    #       p_a=0.9; pi_1=0.85, pi_2=0.15 -> sum pi(1-pi)=0.255;
    #       T_w=trace(I_6)=6, q(q-1)=30 -> p_e=(6/30)*0.255=0.051;
    #       AC1=(0.9-0.051)/(1-0.051)=0.849/0.949=0.894626.
    from sklearn.metrics import cohen_kappa_score
    r1 = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2]
    r2 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 2]
    kappa_unw = float(cohen_kappa_score(r1, r2))
    ac1 = gwet_ac2(r1, r2, weights="identity")
    check("Cohen kappa skewed (paradox)", kappa_unw, 0.615385, tol=1e-4)
    check("Gwet AC1 skewed (paradox), q=6 scale", ac1, 0.894626, tol=1e-4)
    paradox = ac1 > kappa_unw
    ok = ok and paradox
    print(f"  [{'PASS' if paradox else 'FAIL'}] paradox: AC1 ({ac1:.3f}) > kappa ({kappa_unw:.3f})")

    # --- Krippendorff ordinal against an independent hand/pkg check on a tiny case
    #     Known: two coders [1,2,3,3,2,1] vs [1,2,3,3,2,1] already tested (=1).
    #     Perfect disagreement flip on symmetric ordinal -> alpha negative.
    flip = krippendorff_ordinal([0, 1, 2, 3], [3, 2, 1, 0])
    neg = flip < 0
    ok = ok and neg
    print(f"  [{'PASS' if neg else 'FAIL'}] Krippendorff anti-correlated < 0: {flip:.3f}")

    print(f"\n  ALL UNIT TESTS {'PASSED' if ok else 'FAILED'}")
    if not ok:
        raise AssertionError("Unit tests failed")
    return ok


# ===========================================================================
# 4. Full analysis (runs on rated data)
# ===========================================================================
def _read_ratings(csv_path):
    rows = list(csv.DictReader(Path(csv_path).open(encoding="utf-8")))
    data = {d: {"r1": [], "r2": [], "eval_id": []} for d in DIMENSIONS}
    for row in rows:
        for d in DIMENSIONS:
            v1 = row.get(f"r1_{d}", "").strip()
            v2 = row.get(f"r2_{d}", "").strip()
            if v1 != "" and v2 != "":
                try:
                    data[d]["r1"].append(int(round(float(v1))))
                    data[d]["r2"].append(int(round(float(v2))))
                    data[d]["eval_id"].append(row.get("eval_id", ""))
                except ValueError:
                    pass
    n_rated = max(len(data[d]["r1"]) for d in DIMENSIONS)
    return rows, data, n_rated


def _consensus(r1, r2):
    """Consensus human score = mean of the two raters (kept continuous)."""
    return [(a + b) / 2.0 for a, b in zip(r1, r2)]


def analyze(csv_path, rows_source=None, n_boot=2000):
    """Full IRR + human-vs-metric analysis. Exits gracefully if unrated."""
    import pandas as pd
    from scipy.stats import spearmanr
    from sklearn.metrics import precision_score, recall_score, f1_score

    if rows_source is None:
        rows, data, n_rated = _read_ratings(csv_path)
    else:
        rows, data, n_rated = rows_source

    print(f"\n=== HUMAN-EVAL ANALYSIS ===")
    total = len(rows)
    if n_rated == 0:
        print(f"  0/{total} items rated. Nothing to analyze.")
        print("  -> Raters must fill r1_*/r2_* columns before this engine produces statistics.")
        print("  -> See S08_RATING_README.md for the blinding protocol.")
        return {"n_rated": 0, "n_total": total, "status": "unrated"}

    print(f"  {n_rated}/{total} items rated.\n")
    result = {"n_rated": n_rated, "n_total": total, "status": "rated", "per_dimension": {}}

    # --- Inter-rater reliability, per dimension
    print("--- Inter-rater reliability (per dimension) ---")
    for d in DIMENSIONS:
        r1, r2 = data[d]["r1"], data[d]["r2"]
        if len(r1) < 3:
            print(f"  {d}: n={len(r1)} too few to score")
            continue
        qwk = quadratic_weighted_kappa(r1, r2)
        alpha = krippendorff_ordinal(r1, r2)
        icc = icc_2_1(r1, r2)
        ac2 = gwet_ac2(r1, r2)
        exact, adj = pct_agreement(r1, r2)
        ci_qwk = bootstrap_ci(quadratic_weighted_kappa, r1, r2, n_boot)
        ci_ac2 = bootstrap_ci(lambda a, b: gwet_ac2(a, b), r1, r2, n_boot)
        ci_alpha = bootstrap_ci(krippendorff_ordinal, r1, r2, n_boot)
        result["per_dimension"][d] = {
            "n": len(r1), "qwk": qwk, "qwk_ci95": ci_qwk,
            "krippendorff_ordinal": alpha, "alpha_ci95": ci_alpha,
            "icc_2_1": icc, "gwet_ac2": ac2, "ac2_ci95": ci_ac2,
            "pct_exact": exact, "pct_adjacent": adj,
            "r1_mean": float(np.mean(r1)), "r2_mean": float(np.mean(r2)),
        }
        print(f"  {d} (n={len(r1)}):")
        print(f"    QWK={qwk:.3f} [{ci_qwk[0]:.3f},{ci_qwk[1]:.3f}]  "
              f"alpha_ord={alpha:.3f} [{ci_alpha[0]:.3f},{ci_alpha[1]:.3f}]")
        print(f"    ICC(2,1)={icc:.3f}  Gwet AC2={ac2:.3f} [{ci_ac2[0]:.3f},{ci_ac2[1]:.3f}]")
        print(f"    exact={exact:.1f}%  adjacent(+/-1)={adj:.1f}%")

    # --- Human vs judge / MiniCheck: join by eval_id -> (question_id, config)
    sample = reconstruct_sample()
    by_eval = {s["eval_id"]: s for s in sample}
    master = pd.read_csv(MASTER_JOIN).set_index(["question_id", "config"])

    def metric_lookup(eval_id, col):
        s = by_eval.get(eval_id)
        if s is None:
            return None
        key = (s["question_id"], s["config"])
        if key in master.index:
            v = master.loc[key, col]
            return float(v) if pd.notna(v) else None
        return None

    print("\n--- Human (consensus) vs judge & MiniCheck ---")
    result["human_vs_metric"] = {}
    for d in DIMENSIONS:
        r1, r2 = data[d]["r1"], data[d]["r2"]
        eids = data[d]["eval_id"]
        if len(r1) < 3:
            continue
        cons = _consensus(r1, r2)
        entry = {}
        # Human vs judge (shared ordinal dims only)
        if d in JUDGE_SHARED:
            jvals, hvals = [], []
            for e, h in zip(eids, cons):
                jv = metric_lookup(e, f"judge_{d}")
                if jv is not None:
                    jvals.append(jv); hvals.append(h)
            if len(jvals) >= 3:
                rho, p = spearmanr(hvals, jvals)
                # weighted kappa needs int ordinal on both sides
                qwk_hj = quadratic_weighted_kappa(
                    [int(round(x)) for x in hvals], [int(round(x)) for x in jvals])
                entry["judge"] = {"n": len(jvals), "spearman_rho": float(rho),
                                  "spearman_p": float(p), "qwk": qwk_hj}
                print(f"  {d} human-vs-judge (n={len(jvals)}): "
                      f"rho={rho:.3f} (p={p:.3f}) QWK={qwk_hj:.3f}")
        # Human faithfulness vs MiniCheck precision (continuous -> Spearman)
        if d == "faithfulness":
            mvals, hvals = [], []
            for e, h in zip(eids, cons):
                mv = metric_lookup(e, "mc_precision")
                if mv is not None:
                    mvals.append(mv); hvals.append(h)
            if len(mvals) >= 3:
                rho, p = spearmanr(hvals, mvals)
                # coarse ordinal kappa: map precision to 0..5 (documented as coarse)
                qwk_hm = quadratic_weighted_kappa(
                    [int(round(x)) for x in hvals],
                    [int(round(x * SCALE_MAX)) for x in mvals])
                entry["minicheck"] = {"n": len(mvals), "spearman_rho": float(rho),
                                      "spearman_p": float(p),
                                      "qwk_coarse": qwk_hm,
                                      "note": "MiniCheck precision is continuous; "
                                              "QWK uses round(5*precision), coarse."}
                print(f"  faithfulness human-vs-MiniCheck (n={len(mvals)}): "
                      f"rho={rho:.3f} (p={p:.3f}) QWK_coarse={qwk_hm:.3f}")
        if entry:
            result["human_vs_metric"][d] = entry

    # --- Judge & MiniCheck as hallucination detectors vs human gold
    #     Gold: human consensus faithfulness < 4 => UNFAITHFUL (positive class).
    print("\n--- Hallucination detectors vs human gold (faithful>=4) ---")
    r1, r2 = data["faithfulness"]["r1"], data["faithfulness"]["r2"]
    eids = data["faithfulness"]["eval_id"]
    if len(r1) >= 3:
        cons = _consensus(r1, r2)
        gold_unfaithful = [1 if c < 4 else 0 for c in cons]
        # Judge flags unfaithful if judge_faithfulness < 4
        jt, gt = [], []
        for e, g in zip(eids, gold_unfaithful):
            jv = metric_lookup(e, "judge_faithfulness")
            if jv is not None:
                jt.append(1 if jv < 4 else 0); gt.append(g)
        # MiniCheck flags unfaithful if mc_precision < threshold (0.5 default)
        MC_THR = 0.5
        mt, gtm = [], []
        for e, g in zip(eids, gold_unfaithful):
            mv = metric_lookup(e, "mc_precision")
            if mv is not None:
                mt.append(1 if mv < MC_THR else 0); gtm.append(g)
        result["detectors"] = {"gold_positive_rule": "human consensus faithfulness < 4",
                               "mc_threshold": MC_THR}
        for name, pred, gold in [("judge", jt, gt), ("minicheck", mt, gtm)]:
            if sum(gold) == 0:
                print(f"  {name}: no positive (unfaithful) gold cases in synthetic/real set; "
                      f"precision/recall undefined")
                result["detectors"][name] = {"n": len(gold), "note": "no positive gold"}
                continue
            prec = float(precision_score(gold, pred, zero_division=0))
            rec = float(recall_score(gold, pred, zero_division=0))
            f1 = float(f1_score(gold, pred, zero_division=0))
            result["detectors"][name] = {"n": len(gold), "precision": prec,
                                         "recall": rec, "f1": f1,
                                         "n_gold_positive": int(sum(gold))}
            print(f"  {name}: precision={prec:.3f} recall={rec:.3f} f1={f1:.3f} "
                  f"(n={len(gold)}, gold-positive={int(sum(gold))})")

    return result


# ===========================================================================
# 5. Smoke test (synthetic ratings)
# ===========================================================================
def _synthetic_ratings(sample, seed=SEED):
    """Build synthetic r1/r2 rows keyed to the real eval_ids, correlated with
    the judge scores so downstream joins exercise real code paths."""
    import pandas as pd
    rng = np.random.default_rng(seed)
    master = pd.read_csv(MASTER_JOIN).set_index(["question_id", "config"])
    rows = []
    for s in sample:
        key = (s["question_id"], s["config"])
        base = {}
        for d in DIMENSIONS:
            jcol = f"judge_{d}" if d != "overall" else "judge_correctness"
            anchor = 4.0
            if key in master.index and pd.notna(master.loc[key, jcol]):
                anchor = float(master.loc[key, jcol])
            v1 = int(np.clip(round(anchor + rng.normal(0, 0.7)), 0, 5))
            v2 = int(np.clip(round(anchor + rng.normal(0, 0.7)), 0, 5))
            base[f"r1_{d}"] = v1
            base[f"r2_{d}"] = v2
        base["eval_id"] = s["eval_id"]
        rows.append(base)
    # Assemble same structure as _read_ratings
    data = {d: {"r1": [], "r2": [], "eval_id": []} for d in DIMENSIONS}
    for row in rows:
        for d in DIMENSIONS:
            data[d]["r1"].append(row[f"r1_{d}"])
            data[d]["r2"].append(row[f"r2_{d}"])
            data[d]["eval_id"].append(row["eval_id"])
    return rows, data, len(rows)


def smoke_test():
    print("#" * 70)
    print("# S08 SMOKE TEST - synthetic ratings + unit tests")
    print("#" * 70)
    run_unit_tests()
    sample = reconstruct_sample()
    rows, data, n = _synthetic_ratings(sample)
    print(f"\nGenerated {n} synthetic rated rows (judge-anchored). Running full engine...")
    res = analyze(None, rows_source=(rows, data, n), n_boot=500)
    print("\nSMOKE TEST COMPLETE: engine ran end-to-end on synthetic ratings.")
    return res


# ===========================================================================
# 6. v2.2 mode: the approved protocol findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md
# ===========================================================================
V22_PROTOCOL = ROOT / "findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md"
V22_MASTER = ROOT / "response/human_eval_v22/human_eval_master_v22.csv"
V22_MASTER_RECORD = RECOMPUTE / "S385_human_eval_master_v22.json"
# D190 (Valerio, 31 October 2026, H2 O-a): the key moves to v2.5 (amendment 9). G2 compares the master's expected answers
# and key points with this file, pinned as S508 pins it (S508_judge_49_v25.py:78), and the judge values are S508's
# lock-judge rows on it (D183 FD11 c)
V22_KEY_VERSION = "2.5"
V22_KEY25 = ROOT / "data/ground_truth_v2/ground_truth_v2_5_as_v1.json"
V22_KEY25_SHA256 = "a42161841980792f5da521819c97b16dc54999b45838b8eb87cd4315f798270a"   # amendment 9; S504 --final
V22_LOCK = ROOT / "experiments/LOCK.toml"            # its [judge] model and that model's digest name the judge
V22_JUDGE_DIR = RECOMPUTE / "S508_judge_49_v25"   # S508's folder: rows.jsonl, summary.json, recheck_summary.json
# Key v2.4 in the v1 format (S373.AS_V1), the key until D190. Two readers keep it: v22_join(key_version="2.4"), the
# path that reproduces the stored join of 12 October before anything new is written (README.md:75-79), and MiniCheck:
# S384's rows were computed against this file's expected answers and are keyed on its sha256 (V22_MC_KEY). Amendment 9
# states that the expected answers did not change in v2.5. S508.items_49 (run by the v2.5 join) checks v2.5's against
# v2.3's; nothing here compares v2.5's with v2.4's directly (open point R1 of D190; 0 of 36 differ on 31 October).
V22_KEY24 = S373.AS_V1
V22_MC_KEY = S373.AS_V1
# The reproduction anchor (README.md:75-79): the join --verify-join wrote on 12 October (commit 98592027) on key v2.4,
# from the master S385 wrote with key v2.3 (sha256 7b50a9b1, S211's source_sha256 and S515's master_sha256_before;
# its last commit before S515 moved it to v2.5 is 80a8e200). Each is read from git and checked against its sha256.
V22_V24_JOIN = {"commit": "9859202730509001c87622c4437f83827baffd80", "path": "findings/recompute/S08_v22_join.json",
                "sha256": "a2f22e9f422ea40b1dc7110627cf50341ff3c1e57e83eb973cdfb7ce188864d3"}
V22_V24_MASTER = {"commit": "80a8e2008b72f65951133011c07feb562f8727f4",
                  "path": "response/human_eval_v22/human_eval_master_v22.csv",
                  "sha256": "7b50a9b1a7d7a4094ac833fcdd4cff9fe2f520313b97a404c0cdca48ae2d3cae"}
V22_MINICHECK = RECOMPUTE / "S384_exp04_minicheck_key_v22.jsonl"
V22_MINICHECK_SHARDS = RECOMPUTE / "S384_shards"
V22_JOIN_OUT = RECOMPUTE / "S08_v22_join.json"
V22_RESULTS_OUT = RECOMPUTE / "S08_v22_results.json"
V22_ONE_RATER_OUT = RECOMPUTE / "S08_v22_results_one_rater.json"   # git-ignored; amendment 8, on Valerio's word
V22_DECISIONS = ROOT / "experiments/README.md"       # a one-rater run names its decision line here (v22_on_word)
V22_ONE_RATER_WORDS = ("One rater: item 1, the gate and the decision rule cannot be computed, every number is "
                       "descriptive and no decision is taken (S08b, amendment 8)")


def _json_safe(o):
    """An undefined statistic (NaN or an infinity) written as null: bare NaN is not JSON (RFC 8259), and these files go
    to the deposit (10 October review of the Q40 change, which made small item sets possible)."""
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return None
    if isinstance(o, dict):
        return {k: _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    return o
V22_SMOKE_OUT = RECOMPUTE / "S08_v22_smoke_test.json"
V22_CONTENT = ["eval_id", "strategy", "category", "question", "generated_answer", "expected_answer",
               "expected_concepts"]
V22_SCALE = [1, 2, 3, 4, 5]
V22_N_ITEMS = 49
V22_WITHDRAWN = {"E038": "SY_010"}           # D7, 9 October (S385 record)
V22_EXP04_LABEL = "Generation strategies (exp04)"
V22_EXP04_KNOWN = 807                        # S388 KNOWN_LABEL; S390 experiment 3
V22_JUDGE_DIMS = ["correctness", "completeness", "faithfulness"]
V22_ALPHA_GATE = 0.667
V22_N_BOOT = 2000
# The protocol's amendment of 16 October 2026 (findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md, "the deadline after the
# editor's extension"; D76): Saturday 14 November 2026, 23:59 CET, moved "by this rule, not by a choice". Was 17 October
# 23:59 CEST until 31 October (D190 review: before D190 G2's master pin refused every run, which hid the stale date)
# The amendment of 4 November 2026 (D207, D244: both packets are in) moved it to Wednesday 4 November 2026, 15:30 CET
V22_DEADLINE = "2026-11-04T15:30:00+01:00"   # Wed 4 November 2026, 15:30 CET
# Protocol item 5 without overall (Q35, Valerio Bianchi, 10 October 2026, before any rating)
V22_ITEM5_SCALES = ("correctness", "completeness")
V22_ITEM5_OVERALL = ("not computed: the judge gives no overall score (it emits correctness, completeness, "
                     "faithfulness and citation_quality), so item 5 compares correctness and completeness only; "
                     "a departure decided on 10 October 2026, before any rating (protocol, 'Amendments before "
                     "any rating (10 October 2026)')")
# O29 (Valerio Bianchi, 10 October 2026, before any rating): the scales a statistic reads, faithfulness (items 1 to
# 4) and item 5's, are the only ones the invalid-cell rule counts; S354's V22_STAT_SCALES
V22_STAT_SCALES = tuple(d for d in DIMENSIONS if d == "faithfulness" or d in V22_ITEM5_SCALES)
# O28 (same day): a packet whose invalid cells on V22_STAT_SCALES sit on more than this many distinct items is
# excluded whole and removes no item; S354's V22_MAX_INVALID_ITEMS
V22_MAX_INVALID_ITEMS = 10
V22_ST_COMPLETE, V22_ST_INVALID, V22_ST_TOO_MANY = ("complete", "included, with invalid cells",
                                                    f"invalid on more than {V22_MAX_INVALID_ITEMS} items, excluded")
V22_ST_EMPTY, V22_ST_INCOMPLETE = "no ratings", "incomplete, excluded"   # S354's V22_STATUS carries the same words
V22_INCLUDED = (V22_ST_COMPLETE, V22_ST_INVALID)
# Q40 (Valerio Bianchi, 10 October 2026, before any rating): an invalid cell removes its item, not its packet;
# O28 and O29 (same day) refine it
V22_INVALID_RULE = ("a rating cell that is not blank and not a whole number from 1 to 5, on correctness, completeness "
                    "or faithfulness, takes its item out of the analysis for every rater when it sits in an included "
                    "packet. A packet with a blank score cell, on any of the four scales, overall included, is "
                    "excluded whole (Q36; Q43). A packet with no blank score cell counts while its invalid cells on "
                    f"those three scales sit on {V22_MAX_INVALID_ITEMS} items or fewer, and is excluded whole above "
                    "that, removing no item; items are counted, not cells (O28). An invalid overall cell neither "
                    f"removes its item nor counts toward the {V22_MAX_INVALID_ITEMS}, and is listed (O29). Every "
                    "statistic runs on the items left (Q40, O28, O29, decided 10 October 2026, before any rating; "
                    "protocol, amendments 4 and 5)")
# The decision rule, quoted. v22_rule_text() refuses unless each string stands verbatim in the
# protocol file (whitespace and the ** bold markers normalised).
V22_RULE = {
    "gate_condition": "If ordinal Krippendorff's alpha for faithfulness is below 0.667,",
    "gate_text": "the raters do not agree well enough for their labels to adjudicate anything. We report "
                 "the reliability figures and D as descriptive, state that the human validation is "
                 "inconclusive, and make no claim in either direction.",
    "A_condition": "If D <= 0, or its 95% interval includes zero:",
    "A_text": "the judge's faithfulness scores do not track human judgement better than the NLI signal "
              "does. We say so, and that the construct-validity finding holds on human data as well as "
              "on MiniCheck.",
    "B_condition": "If D > 0 and its 95% interval excludes zero:",
    "B_text": "the judge's faithfulness scores track human judgement better than MiniCheck does. We say "
              "so, and temper the construct-validity claim in the abstract, Results and Discussion, "
              "stating how far the human data support the judge and on what sample.",
    "both": "Both correlations and D are reported with their intervals in either case.",
}


class V22Refused(Exception):
    """A v2.2 gate refused. Nothing is written."""


def _v22_key_version() -> str:
    """The current key's version as its file states it (V22_KEY25 "version", "2.5" since D190)."""
    return str(json.loads(V22_KEY25.read_text(encoding="utf-8"))["version"])


def _sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def _sha256(p) -> str:
    return _sha256_bytes(Path(p).read_bytes())


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finite(v) -> bool:
    try:
        return v is not None and bool(np.isfinite(float(v)))
    except (TypeError, ValueError):
        return False


def _norm_ws(s: str) -> str:
    return " ".join(s.replace("**", "").split())


def v22_rule_text() -> dict:
    text = _norm_ws(V22_PROTOCOL.read_text(encoding="utf-8"))
    missing = [k for k, s in V22_RULE.items() if _norm_ws(s) not in text]
    if missing:
        raise V22Refused(f"decision-rule text {missing} is not verbatim in {rel(V22_PROTOCOL)}: the "
                         f"protocol changed, so this engine no longer applies it")
    return dict(V22_RULE)


# ---- statistics, any number of raters; X is raters x items ------------------------------------
def v22_alpha_ordinal(X) -> float:
    """Ordinal Krippendorff's alpha (krippendorff package), value domain 1..5; NaN marks a missing value."""
    import krippendorff
    X = np.asarray(X, dtype=float)
    try:
        return float(krippendorff.alpha(reliability_data=X, level_of_measurement="ordinal",
                                         value_domain=V22_SCALE))
    except (ValueError, ZeroDivisionError):
        return float("nan")


def _alpha_ordinal_reference(X) -> float:
    """Krippendorff (2011) by hand: coincidence matrix, ordinal metric. Used only to test the package."""
    X = np.asarray(X, dtype=float)
    vals = np.unique(X[~np.isnan(X)])
    idx = {v: i for i, v in enumerate(vals)}
    o = np.zeros((len(vals), len(vals)))
    for u in range(X.shape[1]):
        col = X[:, u][~np.isnan(X[:, u])]
        m = len(col)
        if m < 2:
            continue
        for a in range(m):
            for b in range(m):
                if a != b:
                    o[idx[col[a]], idx[col[b]]] += 1.0 / (m - 1)
    nc = o.sum(axis=1)
    n = nc.sum()
    d = np.zeros_like(o)
    for c in range(len(vals)):
        for k in range(len(vals)):
            lo, hi = min(c, k), max(c, k)
            d[c, k] = (nc[lo:hi + 1].sum() - (nc[c] + nc[k]) / 2.0) ** 2
    return float(1 - ((o * d).sum() / n) / ((np.outer(nc, nc) * d).sum() / (n * (n - 1))))


def v22_icc_2_1(X) -> float:
    """ICC(2,1), Shrout and Fleiss (1979): two-way random, absolute agreement, single rater.
    (BMS - EMS) / (BMS + (k-1) EMS + k (JMS - EMS) / n), items as targets, raters as judges."""
    Y = np.asarray(X, dtype=float).T
    n, k = Y.shape
    if n < 2 or k < 2:   # BMS divides by n - 1 and JMS by k - 1: undefined below two items or two raters
        return float("nan")
    g, r, c = Y.mean(), Y.mean(axis=1), Y.mean(axis=0)
    bms = k * ((r - g) ** 2).sum() / (n - 1)
    jms = n * ((c - g) ** 2).sum() / (k - 1)
    ems = ((Y - r[:, None] - c[None, :] + g) ** 2).sum() / ((n - 1) * (k - 1))
    den = bms + (k - 1) * ems + k * (jms - ems) / n
    if np.isclose(den, 0.0):
        return float("nan")
    return float((bms - ems) / den)


def v22_gwet_ac2(X, cats=None, weights: str = "quadratic") -> tuple[float, float, float]:
    """Gwet's AC2 for any number of raters, NaN = missing (Gwet 2014; irrCAC gwet.ac1.raw).
    r_ik raters putting item i in category k, r*_ik = sum_l w_kl r_il, r_i raters of item i;
    p_a = mean over items with r_i >= 2 of sum_k r_ik (r*_ik - 1) / (r_i (r_i - 1));
    pi_k = mean over items with r_i >= 1 of r_ik / r_i; p_e = T_w / (q (q-1)) sum_k pi_k (1 - pi_k).
    Returns (AC2, p_a, p_e). Identity weights give AC1."""
    cats = list(V22_SCALE if cats is None else cats)
    q = len(cats)
    pos = {c: i for i, c in enumerate(cats)}
    k = np.arange(q)
    W = 1.0 - (k[:, None] - k[None, :]) ** 2 / (q - 1) ** 2 if weights == "quadratic" else np.eye(q)
    X = np.asarray(X, dtype=float)
    R = np.zeros((X.shape[1], q))
    for u in range(X.shape[1]):
        for v in X[:, u]:
            if not np.isnan(v):
                R[u, pos[v]] += 1
    ri = R.sum(axis=1)
    rs = R @ W.T
    two = ri >= 2
    pa = float(np.mean((R[two] * (rs[two] - 1)).sum(axis=1) / (ri[two] * (ri[two] - 1))))
    one = ri >= 1
    pi = (R[one] / ri[one, None]).mean(axis=0)
    pe = float(W.sum() / (q * (q - 1)) * (pi * (1 - pi)).sum())
    if np.isclose(1 - pe, 0.0):
        return float("nan"), pa, pe
    return float((pa - pe) / (1 - pe)), pa, pe


def v22_qwk(a, b) -> float:
    """Cohen's kappa with quadratic weights over 1..5: 1 - sum(w O) / sum(w E), w = (i-j)^2."""
    a = np.asarray(a, dtype=int) - 1
    b = np.asarray(b, dtype=int) - 1
    q = len(V22_SCALE)
    O = np.zeros((q, q))
    np.add.at(O, (a, b), 1)
    E = np.outer(O.sum(axis=1), O.sum(axis=0)) / O.sum()
    k = np.arange(q)
    w = (k[:, None] - k[None, :]) ** 2
    den = (w * E).sum()
    if np.isclose(den, 0.0):
        return float("nan")
    return float(1 - (w * O).sum() / den)


def v22_mean_pairwise_qwk(X) -> tuple[float, list[float]]:
    X = np.asarray(X)
    vals = [v22_qwk(X[i], X[j]) for i in range(len(X)) for j in range(i + 1, len(X))]
    return (float(np.mean(vals)) if vals else float("nan")), vals


def v22_agreement(X) -> dict:
    """Exact and adjacent (+/-1) agreement in %, as the mean over rater pairs and as the share of
    items on which all raters agree (identical when there are two raters)."""
    X = np.asarray(X)
    m = len(X)
    pe, pa = [], []
    for i in range(m):
        for j in range(i + 1, m):
            pe.append(np.mean(X[i] == X[j]))
            pa.append(np.mean(np.abs(X[i] - X[j]) <= 1))
    spread = X.max(axis=0) - X.min(axis=0)
    return {"exact_pct_mean_pairwise": float(100 * np.mean(pe)),
            "adjacent_pct_mean_pairwise": float(100 * np.mean(pa)),
            "exact_pct_all_raters": float(100 * np.mean(spread == 0)),
            "adjacent_pct_all_raters": float(100 * np.mean(spread <= 1))}


def v22_spearman(a, b) -> float:
    from scipy.stats import spearmanr
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size < 2 or np.ptp(a) == 0 or np.ptp(b) == 0:   # undefined on fewer than two items (Q40 item set)
        return float("nan")
    return float(spearmanr(a, b).statistic)


def v22_draws(n: int, n_boot: int = V22_N_BOOT, seed: int = SEED) -> list[np.ndarray]:
    """The protocol's resamples of the items: n_boot draws of n indices with replacement, seed 42.
    Every statistic is bootstrapped on these same draws."""
    rng = np.random.default_rng(seed)
    return [rng.integers(0, n, n) for _ in range(n_boot)]


def _ci95(vals) -> list[float]:
    if not vals:
        return [float("nan"), float("nan")]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def v22_irr(X, draws, labels) -> dict:
    """Protocol item 1 on one dimension; X raters x items, complete."""
    import warnings
    X = np.asarray(X, dtype=int)
    funcs = {"krippendorff_alpha_ordinal": v22_alpha_ordinal,
             "icc_2_1": v22_icc_2_1,
             "gwet_ac2_quadratic": lambda Z: v22_gwet_ac2(Z)[0],
             "mean_pairwise_qwk": lambda Z: v22_mean_pairwise_qwk(Z)[0]}
    names = [f"{labels[i]}-{labels[j]}" for i in range(len(labels)) for j in range(i + 1, len(labels))]
    boot = {k: [] for k in funcs}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")      # on a very small item set a statistic is NaN, with a warning
        point = {k: f(X) for k, f in funcs.items()}
        _, pairs = v22_mean_pairwise_qwk(X)
        agreement = v22_agreement(X)
        for idx in draws:
            Z = X[:, idx]
            for k, f in funcs.items():
                v = f(Z)
                if _finite(v):
                    boot[k].append(v)
    return {"n_items": int(X.shape[1]), "n_raters": int(X.shape[0]), "raters": list(labels),
            **point, "ci95": {k: _ci95(v) for k, v in boot.items()},
            "bootstrap_resamples_used": {k: len(v) for k, v in boot.items()},
            "pairwise_qwk": dict(zip(names, pairs)), **agreement}


def v22_correlations(h, j, m, draws) -> dict:
    """Protocol items 2 to 4: rho(h, j), rho(h, m), D = rho(h, j) - rho(h, m), paired bootstrap."""
    import warnings
    h, j, m = (np.asarray(x, dtype=float) for x in (h, j, m))
    rj, rm = v22_spearman(h, j), v22_spearman(h, m)
    bj, bm, bd = [], [], []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for idx in draws:
            a, b = v22_spearman(h[idx], j[idx]), v22_spearman(h[idx], m[idx])
            if _finite(a):
                bj.append(a)
            if _finite(b):
                bm.append(b)
            if _finite(a) and _finite(b):
                bd.append(a - b)
    return {"rho_human_judge": rj, "rho_human_judge_ci95": _ci95(bj),
            "rho_human_minicheck": rm, "rho_human_minicheck_ci95": _ci95(bm),
            "D": rj - rm, "D_ci95": _ci95(bd),
            "bootstrap": {"draws": len(draws), "seed": SEED, "used_judge": len(bj),
                          "used_minicheck": len(bm), "used_D": len(bd)}}


def v22_decide(alpha: float, D: float, ci) -> dict:
    """The protocol's decision rule, verbatim."""
    rule = v22_rule_text()
    lo, hi = ci
    excludes_zero = bool(_finite(lo) and _finite(hi) and (lo > 0 or hi < 0))
    gate = bool(_finite(alpha) and alpha >= V22_ALPHA_GATE)
    out = {"label_gate": {"krippendorff_alpha_ordinal_faithfulness": alpha, "threshold": V22_ALPHA_GATE,
                          "passed": gate},
           "D": D, "D_ci95": list(ci), "D_interval_excludes_zero": excludes_zero,
           "reported_in_every_case": rule["both"]}
    if not gate:
        out.update(outcome="inconclusive", protocol_condition=rule["gate_condition"],
                   protocol_text=rule["gate_text"], D_status="descriptive")
    elif not _finite(D):
        out.update(outcome="undefined", protocol_condition=None,
                   protocol_text="D is undefined (a Spearman correlation has a constant input, or fewer than "
                                 "two items in the analysis set); the protocol has no branch for this. Reported "
                                 "as a departure.",
                   D_status="undefined")
    elif D <= 0 or not excludes_zero:
        out.update(outcome="judge_not_better", protocol_condition=rule["A_condition"],
                   protocol_text=rule["A_text"], D_status="decision")
    else:
        out.update(outcome="judge_better", protocol_condition=rule["B_condition"],
                   protocol_text=rule["B_text"], D_status="decision")
        if not (lo <= D <= hi):
            out["note"] = "the percentile interval does not contain the point estimate"
    return out


# ---- reading: the content and the ratings ------------------------------------------------------
def _v22_slots(header) -> dict:
    import re
    slots: dict = {}
    for h in header:
        m = re.fullmatch(r"(r\d+)_(correctness|completeness|faithfulness|overall|notes)", h or "")
        if m:
            slots.setdefault(m.group(1), set()).add(m.group(2))
    return dict(sorted(slots.items(), key=lambda kv: int(kv[0][1:])))


def v22_read_content(path=V22_MASTER) -> tuple[list[str], list[dict]]:
    """The header and the seven content columns of each row. No rating cell is taken."""
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        header = list(rd.fieldnames or [])
        rows = [{k: r.get(k) for k in V22_CONTENT} for r in rd]
    return header, rows


def v22_require_same_content(path, master=V22_MASTER) -> None:
    """Refuses unless the ratings file at path carries the master's content: the same header-named content
    columns (V22_CONTENT) with the same values, row for row and in order, as the current master. Ratings
    collected on an older master (another key's expected answers, for one) cannot then be analysed against the
    current judge key. Only content columns are read (v22_read_content); the refusal names eval_ids and column
    names, never a cell value."""
    _, got = v22_read_content(path)
    _, want = v22_read_content(master)
    if len(got) != len(want):
        raise V22Refused(f"{rel(Path(path))} has {len(got)} rows, the current master {rel(Path(master))} {len(want)}; "
                         "the ratings were not collected on this master")
    diff = [(w.get("eval_id"), [k for k in V22_CONTENT if g.get(k) != w.get(k)]) for g, w in zip(got, want)]
    diff = [(e, cols) for e, cols in diff if cols]
    if diff:
        cols = sorted({c for _, cs in diff for c in cs})
        raise V22Refused(f"{rel(Path(path))} differs from the current master {rel(Path(master))} on {len(diff)} of "
                         f"{len(want)} rows (columns {', '.join(cols)}; first eval_id {diff[0][0]}): the ratings were "
                         "collected on another master and are not analysed against the current judge key")


def v22_read_rating_rows(path) -> list[dict]:
    """eval_id and the r<k>_<scale> cells of the four scales; the notes columns are never taken."""
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        keep = ["eval_id"] + [h for h in (rd.fieldnames or [])
                              if any(h.endswith("_" + d) for d in DIMENSIONS) and h[:1] == "r" and h[1:2].isdigit()]
        return [{k: r.get(k) for k in keep} for r in rd]


def v22_parse_ratings(rows, eval_ids, min_included: int = 2) -> tuple[list[str], dict, dict, dict]:
    """Rater inclusion by the protocol (Q36, Q43, O28), then the analysis item set (Q40, O29).
    A cell that is not blank and not a whole number from 1 to 5 is invalid. A packet with any blank score
    cell (the items x the four scales, overall included) is excluded whole. A packet with none is excluded
    whole too when its invalid cells on V22_STAT_SCALES (correctness, completeness, faithfulness) sit on more
    than V22_MAX_INVALID_ITEMS distinct items, and counts otherwise. In an included packet an invalid cell on
    V22_STAT_SCALES takes its item out of the analysis set for every rater (two invalid cells on one item take
    it out once); an invalid overall cell removes nothing and is listed. In an excluded packet an invalid cell
    changes nothing. Returns (included slots, status per slot, slot -> scale of V22_STAT_SCALES -> int array
    over the analysis items in eval_ids order, the item set). Statuses and the item set carry counts and
    (packet, item, scale), never a value. min_included: fewer included packets than this refuse; 2, the protocol's
    reliability statistics, unless the one-rater mode asks for 1."""
    if [r.get("eval_id") for r in rows] != list(eval_ids):
        raise V22Refused(f"the ratings sheet's eval_ids are not the {len(eval_ids)} items of the join, in order")
    header = list(rows[0].keys()) if rows else []
    slots = [s for s, dims in _v22_slots(header).items() if set(DIMENSIONS) & dims]
    total = len(rows) * len(DIMENSIONS)
    status, cells, invalid = {}, {}, {}
    for s in slots:
        if not all(f"{s}_{d}" in header for d in DIMENSIONS):
            raise V22Refused(f"rater {s} lacks a column for one of the four scales")
        c = {d: [] for d in DIMENSIONS}
        filled, blank, bad = 0, 0, []
        for r in rows:
            for d in DIMENSIONS:
                v = (r.get(f"{s}_{d}") or "").strip()
                if not v:
                    c[d].append(None)
                    blank += 1
                    continue
                try:
                    f = float(v)
                except ValueError:
                    f = float("nan")
                if not (np.isfinite(f) and f == int(f) and 1 <= f <= 5):
                    bad.append((r.get("eval_id"), d))
                    c[d].append(None)
                    continue
                c[d].append(int(f))
                filled += 1
        # Q36: any blank cell, on any of the four scales, excludes the packet whole (Q43 confirms overall counts);
        # Q40: an invalid cell does not, but such a packet is not called complete; O28 and O29: a packet whose
        # invalid cells on V22_STAT_SCALES sit on more than V22_MAX_INVALID_ITEMS distinct items is excluded whole
        counted = {e for e, d in bad if d in V22_STAT_SCALES}
        st = ((V22_ST_TOO_MANY if len(counted) > V22_MAX_INVALID_ITEMS else V22_ST_INVALID if bad
               else V22_ST_COMPLETE) if blank == 0
              else V22_ST_EMPTY if blank == total else V22_ST_INCOMPLETE)
        status[s] = {"status": st, "cells_rated": filled, "cells_invalid": len(bad), "items_invalid": len(counted),
                     "cells_blank": blank, "cells": total}
        cells[s], invalid[s] = c, bad
    included = [s for s in slots if status[s]["status"] in V22_INCLUDED]
    if len(included) < min_included:
        need = "the reliability statistics need two" if min_included == 2 else f"this run needs {min_included}"
        raise V22Refused(f"{len(included)} included packet(s) of {len(slots)} (a packet is included when no score "
                         f"cell of it is blank and its invalid cells on {', '.join(V22_STAT_SCALES)} sit on "
                         f"{V22_MAX_INVALID_ITEMS} items or fewer); {need}")
    hit = defaultdict(list)
    for s in included:
        for e, d in invalid[s]:
            if d in V22_STAT_SCALES:
                hit[e].append({"packet": s, "scale": d})
    keep = [i for i, e in enumerate(eval_ids) if e not in hit]
    # only the scales a statistic reads: an included packet's overall cell may be invalid on a kept item (O29)
    mats = {s: {d: np.array([cells[s][d][i] for i in keep], dtype=int) for d in V22_STAT_SCALES} for s in included}
    items = {"n_items": len(eval_ids), "n_analysed": len(keep), "analysed": [eval_ids[i] for i in keep],
             "scales_counted": list(V22_STAT_SCALES), "max_invalid_items_per_packet": V22_MAX_INVALID_ITEMS,
             "removed": [{"eval_id": e, "cells": hit[e]} for e in eval_ids if e in hit],
             "invalid_overall_cells_in_included_packets": [{"packet": s, "eval_id": e, "scale": d}
                                                           for s in included for e, d in invalid[s]
                                                           if d not in V22_STAT_SCALES],
             "packets_excluded_for_invalid_items": [s for s in slots if status[s]["status"] == V22_ST_TOO_MANY],
             "invalid_cells_in_excluded_packets": [{"packet": s, "eval_id": e, "scale": d}
                                                   for s in slots if s not in included for e, d in invalid[s]],
             "rule": V22_INVALID_RULE}
    return included, status, mats, items


# ---- the join and the two machine scores -------------------------------------------------------
def _s508_key_hash(q: dict) -> str:
    """S508's key_hash of a key question, computed as S508.items_49 computes it (S508_judge_49_v25.py:129): the expected
    answer, the key points and answerable True (all 49 items are answerable in v2.5, which items_49 checks)."""
    return _sha256_bytes(json.dumps([q["expected_answer"], list(q["expected_concepts"]), True],
                                    ensure_ascii=False).encode("utf-8"))[:16]


def v22_join(master_path=None, key_version: str = V22_KEY_VERSION) -> dict:
    """G1 to G4 (module docstring). Reads no rating: the master's content columns and header only.
    master_path: the master to join (default V22_MASTER). key_version "2.5" (D190, the default): G2 against V22_KEY25,
    sha256-pinned as S508 pins it. "2.4": G2 against S373.AS_V1 and S373.KEY as before D190, the path
    v22_reproduce_v24 runs on the 12 October master to reproduce the stored join (README.md:75-79)."""
    import S373_rejudge_v2 as S373
    import pandas as pd

    master_path = Path(master_path) if master_path is not None else V22_MASTER
    known = json.loads(JOIN_OUT.read_text())
    sample = reconstruct_sample()
    got = [(s["eval_id"], s["question_id"], s["config"]) for s in sample]
    want = [(p["eval_id"], p["question_id"], p["config"]) for p in known["per_item"]]
    if known.get("all_50_reproduce") is not True or got != want:
        raise V22Refused(f"G1: the seed-42 reconstruction does not reproduce {rel(JOIN_OUT)}")
    by_eval = {s["eval_id"]: s for s in sample}

    header, master = v22_read_content(master_path)
    slots = _v22_slots(header)
    if list(slots) != [f"r{k}" for k in range(1, 8)] or any(v != set(DIMENSIONS) | {"notes"} for v in slots.values()):
        raise V22Refused(f"G2: {rel(master_path)} does not carry r1_* to r7_* on the four scales and notes")
    record = json.loads(V22_MASTER_RECORD.read_text())
    if {e["eval_id"]: e["question_id"] for e in record["excluded"]} != V22_WITHDRAWN:
        raise V22Refused(f"G2: {rel(V22_MASTER_RECORD)} does not exclude exactly {V22_WITHDRAWN}")
    ids = [e for e, *_ in got if e not in V22_WITHDRAWN]
    if [m["eval_id"] for m in master] != ids or len(ids) != V22_N_ITEMS:
        raise V22Refused(f"G2: the master's eval_ids are not the {V22_N_ITEMS} of the reconstruction less E038")
    blind = json.loads(KEY_JSON.read_text())["anonymization"]
    # S373's all_v2_4 records name the exp04 answers for G3 (S373.source_files) on either key (D190 open point R2)
    s373_bytes = S373.KEY.read_bytes()
    s373_sha = _sha256_bytes(s373_bytes)
    s373_doc = json.loads(s373_bytes)
    v2 = {r["id"]: r for r in s373_doc["records"]}
    if key_version == "2.4":
        key_file = V22_KEY24
        as_v1 = json.loads(V22_KEY24.read_text())
        kv = str(s373_doc["version"])
        src = f"source_v{kv.replace('.', '')}_sha256"        # the field S381 writes for this key version
        if as_v1.get(src) != s373_sha:
            raise V22Refused(f"G2: {V22_KEY24.name} was built from another key than {S373.KEY.name} "
                             f"(its {src} is not the sha256 of that v{kv} file)")
        key_ref, key_sha = S373.KEY, s373_sha
    elif key_version == "2.5":
        import S508_judge_49_v25 as S508
        key_file = V22_KEY25
        key_bytes = V22_KEY25.read_bytes()
        key_sha = _sha256_bytes(key_bytes)
        if key_sha != V22_KEY25_SHA256:
            raise V22Refused(f"G2: {rel(V22_KEY25)} sha256 {key_sha[:12]} is not amendment 9's v2.5 "
                             f"{V22_KEY25_SHA256[:12]}")
        as_v1 = json.loads(key_bytes)
        kv = str(as_v1.get("version"))
        if kv != "2.5":
            raise V22Refused(f"G2: {rel(V22_KEY25)} states version {kv}, not 2.5")
        # the judge's key is the rater's: S508 judged on this same file under this same pin (FD11 c); per item, S508's
        # own items_49() names the item's question and strategy and its key_hash, which must be the hash of this
        # file's expected answer and key points for that question (below); v22_judge_values then requires each S508
        # row to carry that key_hash
        if Path(S508.KEY25).resolve() != V22_KEY25.resolve() or S508.KEY25_SHA256 != V22_KEY25_SHA256:
            raise V22Refused(f"G2: S508 judges on {S508.KEY25} {S508.KEY25_SHA256[:12]}, not {rel(V22_KEY25)} "
                             f"{V22_KEY25_SHA256[:12]}")
        try:
            s508_items = {x["eval_id"]: x for x in S508.items_49()[0]}
        except S508.Refused as e:
            raise V22Refused(f"G2: S508.items_49() refuses: {e}")
        key_ref = V22_KEY25
    else:
        raise V22Refused(f"G2: key version {key_version!r}: only 2.5 (D190) and 2.4 (the reproduction) are joined")
    d7 = set(as_v1["dropped_d7"])
    if not set(V22_WITHDRAWN.values()) <= d7:
        raise V22Refused("G2: SY_010 is not in dropped_d7")
    gt = {q["id"]: q for q in as_v1["questions"]}
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}

    def judge_key_is_rater_key(e, qid, cfg):
        if qid not in gt:
            return False
        if key_version == "2.4":
            return S373.key_of(qid, v2) == (gt[qid]["expected_answer"], gt[qid]["expected_concepts"])
        x = s508_items.get(e)              # 2.5: the item as S508 judges it, with S508's key_hash (review F6, D190)
        return x is not None and (x["question_id"], x["config"]) == (qid, cfg) and x["key_hash"] == _s508_key_hash(gt[qid])

    items = [x for x in S373.source_files((V22_EXP04_LABEL,))(v1, v2) if x["question_id"] not in d7]
    if len(items) != V22_EXP04_KNOWN:
        raise V22Refused(f"G3: S373's reader gives {len(items)} exp04 answers after D7, known {V22_EXP04_KNOWN}")
    by_qa = defaultdict(list)
    for x in items:
        by_qa[(x["question"], x["answer"])].append(x)

    mj = pd.read_csv(MASTER_JOIN).set_index(["question_id", "config"])
    dep = {(r["question_id"], r["config"]): r for r in json.loads(MINICHECK_JSON.read_text())["per_result"]}
    per, fails = [], []
    for m in master:
        e = m["eval_id"]
        s = by_eval[e]
        qid, cfg = s["question_id"], s["config"]
        hits = by_qa.get((m["question"], m["generated_answer"]), [])
        hit = hits[0] if len(hits) == 1 else None
        mc_s08 = float(mj.loc[(qid, cfg), "mc_precision"]) if (qid, cfg) in mj.index else float("nan")
        mc_dep = (dep.get((qid, cfg)) or {}).get("minicheck", {}).get("precision")
        checks = {
            "G2 question": m["question"] == s["question"],
            "G2 generated_answer": m["generated_answer"] == s["generated_answer"],
            "G2 category": m["category"] == s["category"],
            "G2 strategy decodes to config": blind.get(m["strategy"]) == cfg,
            "G2 S385 question_id": record["question_ids"].get(e) == qid,
            f"G2 expected_answer is v{kv}": qid in gt and m["expected_answer"] == gt[qid]["expected_answer"],
            f"G2 key points are v{kv}": qid in gt and m["expected_concepts"] == "; ".join(gt[qid]["expected_concepts"]),
            "G2 judge key = rater key": judge_key_is_rater_key(e, qid, cfg),
            "G3 one S373 answer": hit is not None,
            "G3 same answer as reconstruction": hit is not None and (hit["question_id"], hit["config"]) == (qid, cfg),
            "G4 S08 MiniCheck = deposited": _finite(mc_s08) and _finite(mc_dep) and abs(mc_s08 - mc_dep) < 1e-9,
        }
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            fails.append(f"{e} ({qid}, {cfg}): {bad}")
            continue
        it = {"eval_id": e, "question_id": qid, "config": cfg, "category": s["category"],
              "s373_key": hit["key"], "answer_chars": len(hit["answer"]),
              "key_hash": S373.key_hash(qid, v2), "mc_precision_s08_v1_key": mc_s08}
        if key_version == "2.5":
            it["s508_key_hash"] = _s508_key_hash(gt[qid])
        per.append(it)
    if fails:
        raise V22Refused("join gates failed: " + "; ".join(fails[:10]))
    inputs = {rel(p): _sha256(p) for p in (V22_PROTOCOL, master_path, V22_MASTER_RECORD, KEY_JSON, GEN_JSON,
                                           MASTER_JOIN, MINICHECK_JSON, key_file, S373.KEY, S373.V1, JOIN_OUT)}
    built = (f"built from {rel(S373.KEY)}" if key_version == "2.4" else
             f"sha256 {V22_KEY25_SHA256[:8]} as S508 pins it; S508 judged on the same file")
    jk = ("judge key = rater key" if key_version == "2.4" else
          "judge key = rater key (each item's key_hash as S508.items_49 gives it = the hash of this key's expected "
          "answer and key points)")
    return {"items": per, "key": rel(key_ref), "key_version": kv, "key_sha256": key_sha, "d7": sorted(d7),
            "inputs": inputs,
            "gates": {"G1": f"seed-42 reconstruction = {rel(JOIN_OUT)} (50 of 50)",
                      "G2": f"{V22_N_ITEMS} master rows = reconstruction less E038; question, answer, category, "
                            f"strategy, question_id, v{kv} expected answer and key points ({rel(key_file)}, "
                            f"{built}), {jk}",
                      "G3": f"S373 reader: {len(items)} exp04 answers after D7; each item names exactly one",
                      "G4": "master_join mc_precision = deposited exp04 MiniCheck precision for every item"}}


def _v22_git_blob(pin: dict, dst: Path) -> Path:
    """One file of a pinned commit, written to dst and checked against its pinned sha256 (README.md:75-79 anchors)."""
    import subprocess
    try:
        b = subprocess.run(["git", "-C", str(ROOT), "show", f"{pin['commit']}:{pin['path']}"], capture_output=True,
                           check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        raise V22Refused(f"reproduction: {pin['path']} at commit {pin['commit'][:8]} cannot be read from git ({e})")
    if _sha256_bytes(b) != pin["sha256"]:
        raise V22Refused(f"reproduction: {pin['path']} at commit {pin['commit'][:8]} has sha256 "
                         f"{_sha256_bytes(b)[:12]}, not the pinned {pin['sha256'][:12]}")
    dst.write_bytes(b)
    return dst


V22_REPRODUCED_FIELDS = ("eval_id", "question_id", "config", "category", "s373_key", "answer_chars", "key_hash",
                         "mc_precision_s08_v1_key")


def v22_reproduce_v24(minicheck=()) -> dict:
    """README.md:75-79, before the v2.5 join writes anything: the v2.4 path of v22_join, on the master as it stood
    on 12 October (V22_V24_MASTER, from git, read for its content columns and header only), gives the stored join of
    that day (V22_V24_JOIN, from git): the same 49 items with the same fields (V22_REPRODUCED_FIELDS: eval_id,
    question_id, config, category, S373 key and key hash, answer_chars, MiniCheck precision), the same gates, the
    same key version and key sha256, the same master sha256, and MiniCheck (v22_minicheck_values, unchanged by D190)
    scored on 49 of 49 as stored. The stored join's devstral coverage came from S373's reader, which D190 replaced,
    so it is required as stored (49 of 49) and not recomputed. Refuses on any difference."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        anchor = json.loads(_v22_git_blob(V22_V24_JOIN, Path(td) / "join_v24.json").read_text(encoding="utf-8"))
        master = _v22_git_blob(V22_V24_MASTER, Path(td) / "human_eval_master_v22.csv")
        join = v22_join(master, key_version="2.4")
        master_sha = _sha256(master)
    diffs = []
    got = [{k: it[k] for k in V22_REPRODUCED_FIELDS} for it in join["items"]]
    want = [{k: it.get(k) for k in V22_REPRODUCED_FIELDS} for it in anchor["per_item"]]
    if got != want:
        bad = [g["eval_id"] for g, w in zip(got, want) if g != w] if len(got) == len(want) else ["(item count)"]
        diffs.append(f"items differ ({len(got)} reproduced, {len(want)} stored; first {bad[:5]})")
    for k in ("gates", "key_version", "key_sha256", "d7"):
        if join[k] != anchor[k]:
            diffs.append(k)
    stored_master = anchor["_provenance"]["inputs"].get(rel(V22_MASTER))
    if master_sha != stored_master:
        diffs.append(f"master sha256 {master_sha[:12]}, stored {str(stored_master)[:12]}")
    _, mcov, _ = v22_minicheck_values(join, minicheck)
    mc_scored = sum(v == "scored" for v in mcov.values())
    if (mc_scored, anchor.get("minicheck_scored")) != (V22_N_ITEMS, V22_N_ITEMS):
        diffs.append(f"MiniCheck scored on {mc_scored}, stored {anchor.get('minicheck_scored')}, of {V22_N_ITEMS}")
    if anchor.get("judge_scored") != V22_N_ITEMS or anchor.get("inputs_complete") is not True:
        diffs.append(f"the stored join's devstral coverage is {anchor.get('judge_scored')} of {V22_N_ITEMS}")
    if diffs:
        raise V22Refused(f"reproduction: the v2.4 path on the 12 October master does not give the stored join "
                         f"{V22_V24_JOIN['path']} at {V22_V24_JOIN['commit'][:8]}: " + "; ".join(diffs))
    return {"anchor": {**V22_V24_JOIN}, "master": {**V22_V24_MASTER}, "items": len(got),
            "fields": list(V22_REPRODUCED_FIELDS), "gates": "equal", "key_version": join["key_version"],
            "minicheck_scored": mc_scored, "judge_scored_as_stored": anchor["judge_scored"]}


def v22_lock_judge(which: str = "main") -> tuple[str, str]:
    """The lock's judge: LOCK.toml [judge] model (which "main") or second_model (which "second", D274) and its [models]
    digest (the one set of settings, CLAUDE.md section 0)."""
    import tomllib
    lock = tomllib.loads(V22_LOCK.read_text(encoding="utf-8"))
    model = lock["judge"][{"main": "model", "second": "second_model"}[which]]
    digest = (lock.get("models", {}).get(model) or {}).get("digest")
    if not digest:
        raise V22Refused(f"{rel(V22_LOCK)}: the judge {model} has no digest in [models]")
    return model, digest


V22_SECOND_JUDGE_DIR = RECOMPUTE / "S508_judge_49_v25_second"   # S508 --judge second (D273, SUPP3-B O1, D274)


def v22_judge_values(join: dict, judge_dir=None, which: str = "main") -> tuple[dict, dict, dict]:
    """eval_id -> the lock judge's scores on key v2.5 (S508, D183 FD11 c; D190); coverage per eval_id; files read.
    Reads judge_dir (default V22_JUDGE_DIR, S508's folder) with S508's own functions, and refuses unless: the join is
    on key v2.5; summary.json names the pinned v2.5 key; S508.items_49() gives the join's items (eval_id, question_id,
    config, in order); S508.latest() reads rows.jsonl under summary.json's run_sha256 (it refuses a row of another
    item text, key, lock or code); recheck_summary.json is a passed recheck of that run made after all 49 were judged
    (S508.recheck_valid); and each of the 49 items has a row with status ok (S508.FINAL) whose question_id, config,
    answer_chars and key_hash are the join's (key_hash: v22_join's s508_key_hash, S508's formula), whose model_digest
    is the lock's judge (LOCK.toml [models] digest of [judge] model; before D190 the reader required S373's devstral
    and options, review F1) and whose lock_sha256 is the one summary.json names for the run. which "second" (D274) reads
    S508 --judge second's folder (default V22_SECOND_JUDGE_DIR) the same way, against [judge] second_model's digest."""
    import S508_judge_49_v25 as S508
    d = Path(judge_dir) if judge_dir is not None else (V22_JUDGE_DIR if which == "main" else V22_SECOND_JUDGE_DIR)
    if join.get("key_version") != "2.5":
        raise V22Refused(f"judge values are S508's on key v2.5 (FD11 c); this join is on key v{join.get('key_version')}")
    rows_f, summ_f, rck_f = d / "rows.jsonl", d / "summary.json", d / "recheck_summary.json"
    missing = [f.name for f in (rows_f, summ_f, rck_f) if not f.is_file()]
    if missing:
        raise V22Refused(f"{rel(d)}: {', '.join(missing)} missing; S508 has not finished there")
    summary = json.loads(summ_f.read_text(encoding="utf-8"))
    if (summary.get("key") or {}).get("sha256") != V22_KEY25_SHA256:
        raise V22Refused(f"{rel(summ_f)}: judged on key sha256 {str((summary.get('key') or {}).get('sha256'))[:12]}, "
                         f"not v2.5 {V22_KEY25_SHA256[:12]}")
    run_sha = (summary.get("judge") or {}).get("run_sha256")
    if not run_sha:
        raise V22Refused(f"{rel(summ_f)} names no run_sha256")
    run_lock = (summary.get("judge") or {}).get("lock_sha256")
    if not run_lock:
        raise V22Refused(f"{rel(summ_f)} names no lock_sha256 for the run")
    judge_model, judge_digest = v22_lock_judge(which)
    try:
        items, _ = S508.items_49()
        if [(x["eval_id"], x["question_id"], x["config"]) for x in items] != \
                [(it["eval_id"], it["question_id"], it["config"]) for it in join["items"]]:
            raise V22Refused("S508.items_49() does not give the join's 49 items (eval_id, question_id, config), in order")
        rows = S508.latest(rows_f, items, run_sha)
        rck = S508.recheck_state(d, run_sha)
    except S508.Refused as e:
        raise V22Refused(f"S508's rows: {e}")
    if not S508.recheck_valid(rck):
        raise V22Refused(f"{rel(rck_f)}: no passed recheck of run {run_sha[:12]} made after all 49 were judged "
                         f"(S508.recheck_valid)")
    values, coverage, prov, bad = {}, {}, {}, []
    for it in join["items"]:
        e = it["eval_id"]
        r = rows.get(e)
        if r is None:
            bad.append(f"{e}: no row")
            continue
        if r.get("status") not in S508.FINAL:
            bad.append(f"{e}: status {r.get('status')}")
            continue
        named = (r.get("question_id"), r.get("config"), r.get("answer_chars"), r.get("key_hash"))
        joined = (it["question_id"], it["config"], it["answer_chars"], it["s508_key_hash"])
        if named != joined:
            bad.append(f"{e}: the row names {named}, the join {joined}")
            continue
        if r.get("model_digest") != judge_digest:
            bad.append(f"{e}: judged by model digest {str(r.get('model_digest'))[:12]}, not the lock's judge "
                       f"{judge_model} {judge_digest[:12]}")
            continue
        if r.get("lock_sha256") != run_lock:
            bad.append(f"{e}: judged under lock {str(r.get('lock_sha256'))[:12]}, not the run's {run_lock[:12]}")
            continue
        sc = r.get("scores") or {}
        values[e] = {k: sc.get(k) for k in V22_JUDGE_DIMS + ["citation_quality"]}
        coverage[e] = "scored" if all(_finite(sc.get(k)) for k in V22_JUDGE_DIMS) else "scored, a dimension missing"
        prov[e] = {"file": rel(rows_f), "at": r.get("at"), "status": r.get("status"),
                   "model_digest": r.get("model_digest"), "ollama": r.get("ollama_version")}
    if bad:
        raise V22Refused(f"{rel(rows_f)}: {len(bad)} of {len(join['items'])} items are not judged ok on this join's "
                         f"item: " + "; ".join(bad[:5]))
    files = {rel(f): {"sha256_of_bytes_read": _sha256(f)} for f in (rows_f, summ_f, rck_f)}
    return values, coverage, {"files": files, "rows_dropped": {}, "row_per_item": prov,
                              "judge": "S508 (D183 FD11 c): the lock's judge call on key v2.5",
                              "key_sha256": V22_KEY25_SHA256, "run_sha256": run_sha, "lock_sha256": run_lock,
                              "model": judge_model, "model_digest": judge_digest,
                              "recheck": {k: (rck or {}).get(k) for k in ("n", "equal", "passed", "after_complete", "at")}}


def v22_minicheck_values(join: dict, paths=()) -> tuple[dict, dict, dict]:
    """eval_id -> S384 MiniCheck precision (rows under V22_MC_KEY's sha256, key v2.4's expected answers; D190 keeps
    it there, amendment 9: "reads the expected answer, which did not change"); coverage; files read."""
    files = [Path(p) for p in paths]
    if not files:
        files = ([V22_MINICHECK] if V22_MINICHECK.exists() else []) + \
                (sorted(V22_MINICHECK_SHARDS.glob(f"{V22_MINICHECK.stem}.shard*.jsonl"))
                 if V22_MINICHECK_SHARDS.is_dir() else [])
    key_sha = _sha256(V22_MC_KEY)
    rows, read = {}, {}
    for p in files:
        b = p.read_bytes()
        parts = b.split(b"\n")
        read[rel(p)] = {"sha256_of_bytes_read": _sha256_bytes(b), "partial_final_line_skipped": parts[-1] != b""}
        for raw in (x for x in parts[:-1] if x.strip()):
            d = json.loads(raw)
            if "_session" in d:
                if d["_session"].get("key_sha256") != key_sha:
                    raise V22Refused(f"{p.name}: a session was run against key sha256 "
                                     f"{d['_session'].get('key_sha256')}, not {V22_MC_KEY.name} {key_sha}")
                continue
            if d.get("key_sha256") != key_sha:
                raise V22Refused(f"{p.name}: row {(d.get('question_id'), d.get('config'))} is not under {V22_MC_KEY.name}")
            k = (d["question_id"], d["config"])
            if k in rows and rows[k] != d:
                raise V22Refused(f"{k} is scored twice, differently, across {[rel(f) for f in files]}")
            rows[k] = d
    values, coverage = {}, {}
    for it in join["items"]:
        e, d = it["eval_id"], rows.get((it["question_id"], it["config"]))
        if d is None:
            coverage[e] = "no row"
            continue
        v1 = (d.get("v1_deposited") or {}).get("precision")
        if not (_finite(v1) and abs(float(v1) - it["mc_precision_s08_v1_key"]) < 1e-9):
            raise V22Refused(f"G4: S384's v1_deposited precision for {e} is {v1}, S08's is {it['mc_precision_s08_v1_key']}")
        p = (d.get("minicheck") or {}).get("precision")
        values[e] = p
        coverage[e] = "scored" if _finite(p) else "precision missing"
    return values, coverage, {"files": read, "rows_read": len(rows)}


def v22_require_inputs(eval_ids, judge: dict, mc: dict) -> None:
    """Refuses unless every item has a judge score on the three shared scales and a MiniCheck precision."""
    mj = [e for e in eval_ids if e not in judge or not all(_finite(judge[e].get(d)) for d in V22_JUDGE_DIMS)]
    mm = [e for e in eval_ids if not _finite(mc.get(e))]
    if mj or mm:
        kv = _v22_key_version()
        raise V22Refused(f"inputs incomplete: S508's judge scores on key v{kv} missing for {len(mj)} of "
                         f"{len(eval_ids)} items {mj}; MiniCheck precision (S384, against key v2.4's expected "
                         f"answers) missing for {len(mm)} {mm}")


def v22_deadline_check(deadline: str = V22_DEADLINE, now=None) -> None:
    from datetime import datetime, timezone
    d, d0 = datetime.fromisoformat(deadline), datetime.fromisoformat(V22_DEADLINE)
    if d.tzinfo is None:
        raise V22Refused(f"--deadline {deadline}: give a time zone")
    if d < d0:
        raise V22Refused(f"--deadline {deadline} is earlier than the protocol's {V22_DEADLINE}; it may only move later")
    now = now or datetime.now(timezone.utc)
    if now < d:
        raise V22Refused(f"the protocol forbids computing any agreement, correlation or summary of the ratings "
                         f"before the deadline {deadline}; it is now {now.isoformat(timespec='seconds')}")


# ---- the analysis ----------------------------------------------------------------------------
def v22_undefined(res: dict) -> dict:
    """Every statistic of the result whose point estimate is not a finite number, with why, in words.
    Used by the report so that a statistic the analysis set is too small for is said to be undefined."""
    n = res["analysis_items"]["n_analysed"]
    irr, c = res["item1_reliability_faithfulness"] or {}, res["items2to4"]   # one rater: no item 1
    if n == 0:
        why = "no item is left in the analysis set"
    elif n == 1:
        why = "one item is left in the analysis set"
    else:
        why = f"undefined on these ratings ({n} items; for example a constant input)"
    size = {"icc_2_1": "ICC(2,1) needs at least two items (its between-items mean square divides by n - 1)",
            "rho_human_judge": "a Spearman correlation needs at least two items",
            "rho_human_minicheck": "a Spearman correlation needs at least two items",
            "D": "D needs both Spearman correlations"}
    out = {}
    for k in ("krippendorff_alpha_ordinal", "icc_2_1", "gwet_ac2_quadratic", "mean_pairwise_qwk",
              "exact_pct_mean_pairwise", "adjacent_pct_mean_pairwise", "exact_pct_all_raters",
              "adjacent_pct_all_raters"):
        if irr and not _finite(irr[k]):
            out[f"item 1 {k}"] = why + (f"; {size[k]}" if k in size and n < 2 else "")
    for k in ("rho_human_judge", "rho_human_minicheck", "D"):
        if not _finite(c[k]):
            out[f"items 2 to 4 {k}"] = why + (f"; {size[k]}" if n < 2 else "")
    for d, v in res["item5_descriptive"].items():
        if not _finite(v["rho_human_judge"]):
            out[f"item 5 {d}"] = why + (f"; {size['rho_human_judge']}" if n < 2 else "")
    return out


def v22_analyze(rows, eval_ids, judge: dict, mc: dict, n_boot: int = V22_N_BOOT, one_rater: bool = False) -> dict:
    """Protocol items 1 to 5 and the decision, on the analysis item set (Q40, O28, O29: the items less every
    item with an invalid cell on correctness, completeness or faithfulness in an included packet). The input
    gate runs before any rating cell is parsed.
    Item 5 compares correctness and completeness only; its overall comparison is stated as not computed.
    one_rater (S08b, amendment 8): exactly one included packet, r1, or a refusal; items 2, 3, 5 and D with r1 as the
    mean; item 1 and the decision are skipped, so item1_reliability_faithfulness is None and decision.outcome is
    "descriptive"."""
    eval_ids = list(eval_ids)
    v22_require_inputs(eval_ids, judge, mc)
    included, status, mats, items = v22_parse_ratings(rows, eval_ids, min_included=1 if one_rater else 2)
    if one_rater and included != ["r1"]:
        raise V22Refused(f"the one-rater mode needs exactly one included packet and it must be r1; included: "
                         f"{', '.join(included)}")
    kept = items["analysed"]
    draws = v22_draws(len(kept), n_boot)
    F = np.array([mats[s]["faithfulness"] for s in included])
    irr = None if one_rater else v22_irr(F, draws, included)
    h = F.mean(axis=0) if F.shape[1] else np.zeros(0)
    jf = np.array([judge[e]["faithfulness"] for e in kept], dtype=float)
    mcv = np.array([mc[e] for e in kept], dtype=float)
    corr = v22_correlations(h, jf, mcv, draws)
    decision = ({"outcome": "descriptive", "D": corr["D"], "D_ci95": corr["D_ci95"], "D_status": "descriptive",
                 "label_gate": None, "protocol_condition": None, "protocol_text": V22_ONE_RATER_WORDS}
                if one_rater else v22_decide(irr["krippendorff_alpha_ordinal"], corr["D"], corr["D_ci95"]))
    desc = {}
    for d in V22_ITEM5_SCALES:
        Hd = np.array([mats[s][d] for s in included])
        hd = Hd.mean(axis=0) if Hd.shape[1] else np.zeros(0)
        jd = np.array([judge[e][d] for e in kept], dtype=float)
        bs = []
        for idx in draws:
            v = v22_spearman(hd[idx], jd[idx])
            if _finite(v):
                bs.append(v)
        desc[d] = {"judge_score": f"the judge's {d}",
                   "rho_human_judge": v22_spearman(hd, jd), "ci95": _ci95(bs), "bootstrap_used": len(bs)}
    res = {"n_items": len(eval_ids), "n_items_analysed": len(kept), "analysis_items": items,
           "one_rater": bool(one_rater), "raters": status, "included": included,
           "item1_reliability_faithfulness": irr, "items2to4": corr, "decision": decision,
           "item5_descriptive": desc, "item5_overall": V22_ITEM5_OVERALL, "n_boot": n_boot, "seed": SEED}
    res["undefined"] = v22_undefined(res)
    return res


def _fx(v, spec: str = ".3f") -> str:
    """A number as text, or "undefined" when it is not finite (a statistic the item set is too small for)."""
    return format(float(v), spec) if _finite(v) else "undefined"


def _fmt_ci(ci) -> str:
    if not (_finite(ci[0]) and _finite(ci[1])):
        return "[undefined]"
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def v22_report_md(res: dict, prov: dict) -> str:
    irr, c, dec = res["item1_reliability_faithfulness"], res["items2to4"], res["decision"]
    it = res.get("analysis_items") or {"n_items": res["n_items"], "n_analysed": res["n_items"], "removed": [],
                                       "invalid_cells_in_excluded_packets": [], "rule": V22_INVALID_RULE}
    lines = [f"# S08 v2.2: human validation of the judge ({prov['generated']})", "",
             f"Protocol `{rel(V22_PROTOCOL)}`; {it['n_analysed']} of {it['n_items']} items analysed; "
             f"{len(res['included'])} raters included "
             f"({', '.join(res['included'])}); {res['n_boot']:,} resamples of the items, seed {res['seed']}.", "",
             "## Raters", "",
             "| Slot | Packet | Cells rated | Cells invalid | Items with an invalid cell on correctness, "
             "completeness or faithfulness |", "|---|---|---:|---:|---:|"]
    lines += [f"| {s} | {v['status']} | {v['cells_rated']} of {v['cells']} | {v.get('cells_invalid', 0)} | "
              f"{v.get('items_invalid', 0)} |" for s, v in res["raters"].items()]
    lines += ["", "## The analysis item set", "",
              f"{it['n_analysed']} of {it['n_items']} items. Rule: {it['rule']}.", ""]
    if it["removed"]:
        lines += [f"{len(it['removed'])} item(s) left the set, each for a cell that is not blank and not a whole "
                  f"number from 1 to 5, on correctness, completeness or faithfulness, in an included packet "
                  f"(value not shown):", ""]
        lines += [f"- {r['eval_id']}: " + "; ".join(f"packet {x['packet']}, {x['scale']}" for x in r["cells"])
                  for r in it["removed"]]
    else:
        lines.append("No item left the set: no included packet has a cell that is not blank and not a whole "
                     "number from 1 to 5 on correctness, completeness or faithfulness.")
    if it.get("packets_excluded_for_invalid_items"):
        lines += ["", f"Packet(s) excluded whole for invalid cells on more than {V22_MAX_INVALID_ITEMS} items of "
                      f"correctness, completeness and faithfulness, which remove no item (O28): "
                  + "; ".join(f"{s} ({res['raters'][s]['items_invalid']} items)"
                              for s in it["packets_excluded_for_invalid_items"]) + "."]
    if it.get("invalid_overall_cells_in_included_packets"):
        lines += ["", "Overall cells that are not blank and not a whole number from 1 to 5, in included packets, "
                      "which remove no item because overall enters no statistic (O29; value not shown): "
                  + "; ".join(f"packet {x['packet']}, {x['eval_id']}, {x['scale']}"
                              for x in it["invalid_overall_cells_in_included_packets"]) + "."]
    if it["invalid_cells_in_excluded_packets"]:
        lines += ["", "Cells of the same kind in excluded packets, which remove no item (value not shown): "
                  + "; ".join(f"packet {x['packet']}, {x['eval_id']}, {x['scale']}"
                              for x in it["invalid_cells_in_excluded_packets"]) + "."]
    if res.get("undefined"):
        lines += ["", f"Undefined on this set of {it['n_analysed']} item(s), reported as undefined and not as a "
                      f"number:", ""] + [f"- {k}: {v}" for k, v in res["undefined"].items()]
    if irr is None:
        lines += ["", "## 1. Reliability of faithfulness", "", V22_ONE_RATER_WORDS + ".", ""]
    else:
        lines += ["", "## 1. Reliability of faithfulness", "", "| Statistic | Value | 95% interval |", "|---|---:|---|"]
        for k, lab in (("krippendorff_alpha_ordinal", "Krippendorff's alpha, ordinal"), ("icc_2_1", "ICC(2,1)"),
                       ("gwet_ac2_quadratic", "Gwet's AC2, quadratic weights"),
                       ("mean_pairwise_qwk", "Mean pairwise quadratic-weighted kappa")):
            lines.append(f"| {lab} | {_fx(irr[k])} | {_fmt_ci(irr['ci95'][k])} |")
        lines += [f"| Exact agreement, mean over pairs | {_fx(irr['exact_pct_mean_pairwise'], '.1f')}% | |",
                  f"| Adjacent (+/-1) agreement, mean over pairs | {_fx(irr['adjacent_pct_mean_pairwise'], '.1f')}% | |",
                  f"| Exact agreement, all raters | {_fx(irr['exact_pct_all_raters'], '.1f')}% | |",
                  f"| Adjacent (+/-1) agreement, all raters | {_fx(irr['adjacent_pct_all_raters'], '.1f')}% | |", ""]
    lines += ["## 2 to 4. Human against judge and MiniCheck (Spearman, mean human faithfulness)", "",
              f"- rho(human, devstral faithfulness) = {_fx(c['rho_human_judge'])} {_fmt_ci(c['rho_human_judge_ci95'])}",
              f"- rho(human, MiniCheck precision) = {_fx(c['rho_human_minicheck'])} "
              f"{_fmt_ci(c['rho_human_minicheck_ci95'])}",
              f"- D = {_fx(c['D'])} {_fmt_ci(c['D_ci95'])}", "", "## Decision", ""]
    if irr is None:
        lines += [f"None. {V22_ONE_RATER_WORDS}.", ""]
    else:
        lines += [f"Label gate: alpha {_fx(dec['label_gate']['krippendorff_alpha_ordinal_faithfulness'])} against "
                  f"{V22_ALPHA_GATE}: {'passed' if dec['label_gate']['passed'] else 'not passed'}. "
                  f"D's interval excludes zero: {dec['D_interval_excludes_zero']}.", "",
                  f"Outcome: **{dec['outcome']}**. Protocol: \"{dec['protocol_condition'] or ''} "
                  f"{dec['protocol_text']}\"", "", dec["reported_in_every_case"], ""]
    lines += ["## 5. Descriptive (not part of the decision)", "", "| Scale | Judge score | rho | 95% interval |",
              "|---|---|---:|---|"]
    for d, v in res["item5_descriptive"].items():
        lines.append(f"| {d} | {v['judge_score']} | {_fx(v['rho_human_judge'])} | {_fmt_ci(v['ci95'])} |")
    lines += ["", f"Overall comparison {res['item5_overall']}."]
    lines += ["", "## Inputs", ""] + [f"- `{k}` sha256 {v[:12]}" for k, v in prov["inputs"].items()]
    return "\n".join(lines) + "\n"


# ---- tests and the smoke test ----------------------------------------------------------------
# Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability", the 4 observers x 12 units
# example with 7 missing values (fetched 10 October 2026 from
# https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff%27s%20Alpha-Reliability.pdf):
# alpha nominal .743, ordinal .815, interval .849, ratio .797. irrCAC uses the same data as
# cac.raw4raters and prints, for it, AC1 .77544 (pa .8181818, pe .1903212) and quadratic AC2 .914
# (pa .9753788, pe .7137044) (https://cran.r-project.org/web/packages/irrCAC/vignettes/overview.html
# and weighting.html, fetched 10 October 2026).
_K2011 = [[1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
          [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
          [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None],
          [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None]]
# Shrout and Fleiss (1979), Psychological Bulletin 86:420-428, Table 2 (four judges, six targets);
# Table 4 prints ICC(1,1) .17, ICC(2,1) .29, ICC(3,1) .71, ICC(1,4) .44, ICC(2,4) .62, ICC(3,4) .91
# (values read from https://www.aliquote.org/cours/2012_biomed/biblio/Shrout1979.pdf, fetched
# 10 October 2026; the table's ratings are an image there, and these are checked by reproducing all
# six printed values through pingouin).
_SF1979 = [[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]]


def v22_unit_tests() -> list[dict]:
    """Known answers. Raises AssertionError on any failure, so nothing downstream runs."""
    import warnings
    import krippendorff
    import pandas as pd
    import pingouin as pg
    from datetime import datetime, timezone
    out = []

    def check(name, got, expected, tol=1e-6, source=""):
        ok = _finite(got) and abs(got - expected) <= tol
        out.append({"test": name, "got": float(got), "expected": float(expected), "tol": tol,
                    "source": source, "pass": bool(ok)})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got:.6f}, expected {expected:.6f} (tol {tol:g})")

    def truth(name, cond, source=""):
        out.append({"test": name, "pass": bool(cond), "source": source})
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    print("\n=== v2.2 UNIT TESTS (known answers) ===")
    K = np.array([[np.nan if v is None else v for v in row] for row in _K2011], dtype=float)
    lit = "Krippendorff 2011, 4 x 12 example"
    for lvl, exp in (("nominal", 0.743), ("ordinal", 0.815), ("interval", 0.849), ("ratio", 0.797)):
        check(f"krippendorff package {lvl} alpha", krippendorff.alpha(reliability_data=K, level_of_measurement=lvl),
              exp, 5e-4, lit)
    check("v22_alpha_ordinal (engine)", v22_alpha_ordinal(K), 0.815, 5e-4, lit)
    check("hand coincidence-matrix ordinal alpha", _alpha_ordinal_reference(K), 0.815, 5e-4, lit)
    # hand: units (1,1), (2,2), (1,2): o11 = o22 = 2, o12 = o21 = 1, n1 = n2 = 3, delta^2 = 9,
    # D_o = 18/6 = 3, D_e = 162/30 = 5.4, alpha = 1 - 3/5.4 = 4/9
    check("ordinal alpha, two raters, three units, by hand", v22_alpha_ordinal([[1, 2, 1], [1, 2, 2]]), 4 / 9, 1e-9,
          "hand")
    check("ordinal alpha, identical raters", v22_alpha_ordinal([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]]), 1.0, 1e-12)
    rng = np.random.default_rng(7)
    for m in (2, 3, 5, 7):
        X = np.clip(rng.integers(1, 6, 49)[None, :] + rng.integers(-1, 2, (m, 49)), 1, 5)
        check(f"ordinal alpha: package = hand coincidence matrix, {m} raters", v22_alpha_ordinal(X),
              _alpha_ordinal_reference(X), 1e-9)

    SF = np.array(_SF1979, dtype=float).T  # raters x targets
    sf = "Shrout and Fleiss 1979, Tables 2 and 4"
    check("ICC(2,1) engine, Shrout-Fleiss", v22_icc_2_1(SF), 0.29, 5e-3, sf)
    df = pd.DataFrame([(t, j, _SF1979[t][j]) for t in range(6) for j in range(4)], columns=["t", "j", "s"])
    pgr = pg.intraclass_corr(data=df, targets="t", raters="j", ratings="s").set_index("Type")["ICC"]
    for lab, exp in (("ICC(1,1)", 0.17), ("ICC(A,1)", 0.29), ("ICC(C,1)", 0.71), ("ICC(1,k)", 0.44),
                     ("ICC(A,k)", 0.62), ("ICC(C,k)", 0.91)):
        check(f"pingouin {lab}, Shrout-Fleiss data", pgr[lab], exp, 5e-3, sf)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for m in (2, 3, 5):
            X = np.clip(rng.integers(1, 6, 49)[None, :] + rng.integers(-1, 2, (m, 49)), 1, 5)
            d = pd.DataFrame([(i, r, X[r, i]) for r in range(m) for i in range(49)], columns=["t", "j", "s"])
            ref = pg.intraclass_corr(data=d, targets="t", raters="j", ratings="s").set_index("Type")["ICC"]["ICC(A,1)"]
            check(f"ICC(2,1) engine = pingouin ICC(A,1), {m} raters", v22_icc_2_1(X), ref, 1e-9)
    check("ICC(2,1), identical raters", v22_icc_2_1([[1, 2, 3, 4, 5]] * 3), 1.0, 1e-12)

    irr = "irrCAC vignettes, cac.raw4raters"
    ac1, pa1, pe1 = v22_gwet_ac2(K, weights="identity")
    check("Gwet AC1 p_a", pa1, 0.8181818, 1e-7, irr)
    check("Gwet AC1 p_e", pe1, 0.1903212, 1e-7, irr)
    check("Gwet AC1", ac1, 0.77544, 1e-5, irr)
    ac2, pa2, pe2 = v22_gwet_ac2(K)
    check("Gwet AC2 quadratic p_a", pa2, 0.9753788, 1e-7, irr)
    check("Gwet AC2 quadratic p_e", pe2, 0.7137044, 1e-7, irr)
    check("Gwet AC2 quadratic", ac2, 0.914, 5e-4, irr)
    # hand, q = 5, quadratic weights w = 1 - d^2/16, T_w = 25 - 100/16 = 75/4; items (1,1,2), (3,3,3):
    # p_a = (23/24 + 1)/2 = 47/48; pi = (1/3, 1/6, 1/2, 0, 0), sum pi(1-pi) = 11/18;
    # p_e = (75/4)/20 * 11/18 = 55/96; AC2 = (47/48 - 55/96)/(41/96) = 39/41
    g = v22_gwet_ac2([[1, 3], [1, 3], [2, 3]])
    check("Gwet AC2, three raters by hand: p_a", g[1], 47 / 48, 1e-12, "hand")
    check("Gwet AC2, three raters by hand: p_e", g[2], 55 / 96, 1e-12, "hand")
    check("Gwet AC2, three raters by hand", g[0], 39 / 41, 1e-12, "hand")
    for _ in range(3):
        a = rng.integers(0, 6, 49)
        b = np.clip(a + rng.integers(-2, 3, 49), 0, 5)
        check("Gwet AC2 multi-rater = S08 two-rater gwet_ac2 (0..5 scale)",
              v22_gwet_ac2(np.array([a, b]), cats=range(6))[0], gwet_ac2(a.tolist(), b.tolist()), 1e-12, "S08")

    # QWK by hand: (1,1), (2,2), (3,4): sum w O = 1; E = 1/3 on {1,2,3} x {1,2,4}, sum w E = 21/3 = 7
    check("QWK by hand", v22_qwk([1, 2, 3], [1, 2, 4]), 6 / 7, 1e-12, "hand")
    check("mean pairwise QWK by hand: (6/7 + 1 + 6/7)/3", v22_mean_pairwise_qwk([[1, 2, 3], [1, 2, 4], [1, 2, 3]])[0],
          19 / 21, 1e-12, "hand")
    check("QWK balanced 2x2 = 0", v22_qwk([1, 1, 2, 2], [1, 2, 1, 2]), 0.0, 1e-12, "S08 unit test")
    from sklearn.metrics import cohen_kappa_score
    for _ in range(3):
        a = rng.integers(1, 6, 49)
        b = np.clip(a + rng.integers(-2, 3, 49), 1, 5)
        check("QWK engine = sklearn quadratic", v22_qwk(a, b),
              cohen_kappa_score(a, b, weights="quadratic", labels=V22_SCALE), 1e-12)
        check("QWK on 1..5 = S08 quadratic_weighted_kappa on 0..5", v22_qwk(a, b),
              quadratic_weighted_kappa(a.tolist(), b.tolist()), 1e-12, "S08")

    ag = v22_agreement([[1, 2, 3, 4], [1, 3, 3, 5], [2, 2, 3, 1]])
    for k, exp in (("exact_pct_mean_pairwise", 125 / 3), ("adjacent_pct_mean_pairwise", 250 / 3),
                   ("exact_pct_all_raters", 25.0), ("adjacent_pct_all_raters", 75.0)):
        check(f"agreement by hand: {k}", ag[k], exp, 1e-9, "hand")

    hh = np.arange(1, 11, dtype=float)
    c = v22_correlations(hh, hh.copy(), hh[::-1].copy(), v22_draws(10))
    check("rho(h, j) = 1", c["rho_human_judge"], 1.0, 1e-12, "hand")
    check("rho(h, m) = -1", c["rho_human_minicheck"], -1.0, 1e-12, "hand")
    check("D = 2", c["D"], 2.0, 1e-12, "hand")
    check("D interval low = 2", c["D_ci95"][0], 2.0, 1e-12, "hand")
    check("D interval high = 2", c["D_ci95"][1], 2.0, 1e-12, "hand")
    # undefined below two items (Q40 can shrink the item set): NaN, never an exception
    truth("Spearman on one item: undefined", not _finite(v22_spearman([3], [4])), "definition")
    truth("Spearman on no item: undefined", not _finite(v22_spearman([], [])), "definition")
    truth("ICC(2,1) on one item: undefined", not _finite(v22_icc_2_1([[3], [4], [5]])), "definition (n - 1 = 0)")
    d1, d2 = v22_draws(49), v22_draws(49)
    truth("draws: 2,000 resamples, seed 42, repeatable", len(d1) == 2000 and all((x == y).all() for x, y in zip(d1, d2)))

    for name, (a, D, ci), want in (
            ("alpha below 0.667: inconclusive, whatever D", (0.60, 0.4, (0.2, 0.6)), "inconclusive"),
            ("alpha exactly 0.667 passes the gate", (0.667, 0.4, (0.2, 0.6)), "judge_better"),
            ("D > 0, interval excludes zero", (0.80, 0.3, (0.1, 0.5)), "judge_better"),
            ("D > 0, interval includes zero", (0.80, 0.3, (-0.1, 0.5)), "judge_not_better"),
            ("D > 0, interval touches zero", (0.80, 0.3, (0.0, 0.5)), "judge_not_better"),
            ("D = 0", (0.80, 0.0, (-0.2, 0.2)), "judge_not_better"),
            ("D < 0, interval excludes zero", (0.80, -0.3, (-0.5, -0.1)), "judge_not_better"),
            ("alpha undefined: gate not passed", (float("nan"), 0.4, (0.2, 0.6)), "inconclusive"),
            ("D undefined", (0.80, float("nan"), (float("nan"), float("nan"))), "undefined")):
        truth(f"decision: {name}", v22_decide(a, D, ci)["outcome"] == want, "protocol, decision rule")

    # The deadline is 4 November 2026 15:30 CET since the protocol's amendment of 4 November (D244; it was 14 November
    # 23:59 CET from 16 October, and 17 October before that); these cases test the same rule on the current date. The
    # first is 31 October, the day D190 removed the other refusal that had stopped every run before the deadline (review
    # F2); the second is one second before the deadline (D244 review F1)
    t0 = datetime(2026, 10, 31, 22, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 11, 4, 14, 30, tzinfo=timezone.utc)   # 15:30 CET, the amendment of 4 November (D244)
    for name, kw, refused in (("before the deadline (31 October 2026): refused", {"now": t0}, True),
                              ("one second before the deadline: refused",
                               {"now": datetime(2026, 11, 4, 14, 29, 59, tzinfo=timezone.utc)}, True),
                              ("at the deadline: allowed", {"now": t1}, False),
                              ("an earlier --deadline (the original 17 October): refused",
                               {"deadline": "2026-10-17T23:59:00+02:00", "now": t1}, True),
                              ("a later --deadline, before it: refused", {"deadline": "2026-11-21T23:59:00+01:00", "now": t1}, True)):
        try:
            v22_deadline_check(**kw)
            r = False
        except V22Refused:
            r = True
        truth(f"deadline: {name}", r == refused, "protocol, deadline")
    ok = all(t["pass"] for t in out)
    print(f"\n  v2.2 UNIT TESTS: {sum(t['pass'] for t in out)} of {len(out)} passed")
    if not ok:
        raise AssertionError("v2.2 unit tests failed")
    return out


def _v22_synthetic_rows(eval_ids, raters: dict, slots=7, notes=False) -> list[dict]:
    """CSV-like rows (strings) with r1..r<slots>; raters: slot -> scale -> list (None = blank)."""
    rows = []
    for i, e in enumerate(eval_ids):
        r = {"eval_id": e}
        for k in range(1, slots + 1):
            s = f"r{k}"
            for d in DIMENSIONS:
                v = raters.get(s, {}).get(d)
                r[f"{s}_{d}"] = "" if v is None or v[i] is None else str(int(v[i]))
            if notes:
                r[f"{s}_notes"] = "SYNTHETIC NOTE, never read"
        rows.append(r)
    return rows


def _v22_scenario(eval_ids, rng, n_raters, rater_sd, judge_mode, mc_mode, independent=False):
    """Synthetic ratings: one latent per item and scale, raters = latent + noise, rounded into 1..5.
    judge: 'track' (latent + 0.3 noise), 'random', 'shared' (rounded from a signal MiniCheck shares);
    MiniCheck: 'track', 'random', 'shared'."""
    n = len(eval_ids)
    lat = {d: rng.uniform(1, 5, n) for d in DIMENSIONS}
    raters = {}
    for k in range(1, n_raters + 1):
        raters[f"r{k}"] = {d: (rng.integers(1, 6, n) if independent else
                               np.clip(np.rint(lat[d] + rng.normal(0, rater_sd, n)), 1, 5)).astype(int).tolist()
                           for d in DIMENSIONS}
    shared = lat["faithfulness"] + rng.normal(0, 0.8, n)
    judge = {}
    for i, e in enumerate(eval_ids):
        jd = {}
        for d in V22_JUDGE_DIMS:
            if judge_mode == "random":
                jd[d] = int(rng.integers(1, 6))
            elif judge_mode == "shared" and d == "faithfulness":
                jd[d] = int(np.clip(np.rint(shared[i]), 1, 5))
            else:
                jd[d] = int(np.clip(np.rint(lat[d][i] + rng.normal(0, 0.3)), 1, 5))
        jd["citation_quality"] = None
        judge[e] = jd
    t = lat["faithfulness"]
    m = {"track": np.clip((t - 1) / 4 + rng.normal(0, 0.05, n), 0, 1), "random": rng.uniform(0, 1, n),
         "shared": np.clip((shared - 1) / 4, 0, 1)}[mc_mode]
    return raters, judge, {e: float(m[i]) for i, e in enumerate(eval_ids)}


def v22_one_packet_scenario(ids, rng) -> dict:
    """The one-rater mode on synthetic ratings: {check: (got, wanted)}. One packet in r1 runs with items 2, 3, 5 and D
    equal to the same ratings with r1 alone as the mean, and no item 1 or decision. The default parser refuses that sheet,
    a single packet in r2 refuses, and two packets refuse. Reads no file. v22_smoke_test records it; S530's test calls
    it on made-up ids, since the smoke test itself reads the master."""
    R, J, M = _v22_scenario(ids, rng, 2, 0.35, "track", "random")
    one = _v22_synthetic_rows(ids, {"r1": R["r1"]})
    res = v22_analyze(one, ids, J, M, one_rater=True)
    h = np.array(R["r1"]["faithfulness"], float)
    jf = np.array([J[e]["faithfulness"] for e in ids], float)
    mcv = np.array([M[e] for e in ids], float)
    same = v22_correlations(h, jf, mcv, v22_draws(len(ids)))

    def refused(fn) -> bool:
        try:
            fn()
        except V22Refused:
            return True
        return False
    report = v22_report_md(res, {"generated": "synthetic", "inputs": {}})
    return {"one packet, r1: item 1 skipped": (res["item1_reliability_faithfulness"], None),
            "one packet, r1: no decision": (res["decision"]["outcome"], "descriptive"),
            "one packet, r1: D as r1 alone": (res["items2to4"]["D"], same["D"]),
            "one packet, r1: D's interval as r1 alone": (res["items2to4"]["D_ci95"], same["D_ci95"]),
            "item 5 stays": (list(res["item5_descriptive"]), list(V22_ITEM5_SCALES)),
            "the report says descriptive": (V22_ONE_RATER_WORDS in report, True),
            "without the flag one packet refuses": (refused(lambda: v22_analyze(one, ids, J, M)), True),
            "one packet in r2 refuses": (refused(lambda: v22_analyze(_v22_synthetic_rows(ids, {"r2": R["r2"]}), ids, J, M,
                                                                     one_rater=True)), True),
            "two packets refuse": (refused(lambda: v22_analyze(_v22_synthetic_rows(ids, R), ids, J, M, one_rater=True)),
                                   True)}


def v22_smoke_test(judge_dir=None, minicheck=()) -> int:
    """Known answers, then synthetic scenarios through the same parse, gate and analysis code as the
    real run. No human rating is read. Writes S08_v22_smoke_test.json only when everything passes."""
    import tempfile
    print("#" * 70)
    print("# S08 v2.2 SMOKE TEST - known answers + SYNTHETIC ratings (no human rating is read)")
    print("#" * 70)
    unit = v22_unit_tests()
    v22_rule_text()
    print("\n=== reproduction (README.md:75-79): the v2.4 path on the 12 October master gives the stored join ===")
    rep = v22_reproduce_v24(minicheck)
    print(f"  reproduced: {rep['items']} items, fields {', '.join(rep['fields'])}; gates equal; MiniCheck "
          f"{rep['minicheck_scored']} of {rep['items']}")
    print("\n=== join (G1 to G4) on key v2.5 (D190), no rating read ===")
    join = v22_join()
    ids = [it["eval_id"] for it in join["items"]]
    print(f"  {len(ids)} items joined; " + "; ".join(f"{k}: {v}" for k, v in join["gates"].items()))
    rng = np.random.default_rng(SEED)
    scen, failed = [], []

    def record(name, expect, res=None, refused=None, extra=None):
        rec = {"scenario": name, "expected": expect}
        if refused is not None:
            rec.update(outcome="refused", message=str(refused)[:400])
            ok = expect == "refused"
        else:
            dec, irr, c = res["decision"], res["item1_reliability_faithfulness"], res["items2to4"]
            rec.update(outcome=dec["outcome"], included=res["included"], raters=res["raters"],
                       alpha=irr["krippendorff_alpha_ordinal"], icc_2_1=irr["icc_2_1"],
                       gwet_ac2=irr["gwet_ac2_quadratic"], mean_pairwise_qwk=irr["mean_pairwise_qwk"],
                       exact_pct_mean_pairwise=irr["exact_pct_mean_pairwise"],
                       adjacent_pct_mean_pairwise=irr["adjacent_pct_mean_pairwise"],
                       rho_judge=c["rho_human_judge"], rho_judge_ci95=c["rho_human_judge_ci95"],
                       rho_minicheck=c["rho_human_minicheck"], rho_minicheck_ci95=c["rho_human_minicheck_ci95"],
                       D=c["D"], D_ci95=c["D_ci95"], decision=dec,
                       item5={d: v.get("rho_human_judge") for d, v in res["item5_descriptive"].items()},
                       items_analysed=res["n_items_analysed"],
                       items_removed=res["analysis_items"]["removed"], undefined=res["undefined"])
            ok = dec["outcome"] == expect
        if extra:
            for k, (got, want) in extra.items():
                rec.setdefault("checks", {})[k] = {"got": got, "expected": want, "pass": got == want}
                ok = ok and got == want
        rec["pass"] = bool(ok)
        scen.append(rec)
        if not ok:
            failed.append(name)
        line = (f"  [{'PASS' if ok else 'FAIL'}] {name}: {rec['outcome']}")
        if refused is None:
            line += (f" | items {rec['items_analysed']} | raters {','.join(res['included'])} alpha {rec['alpha']:.3f} "
                     f"ICC {rec['icc_2_1']:.3f} "
                     f"AC2 {rec['gwet_ac2']:.3f} QWK {rec['mean_pairwise_qwk']:.3f} | rho_j {rec['rho_judge']:.3f} "
                     f"rho_mc {rec['rho_minicheck']:.3f} D {rec['D']:.3f} {_fmt_ci(rec['D_ci95'])}")
        else:
            line += f" | {rec['message'][:150]}"
        print(line)

    def run(name, expect, raters, judge, mc, slots=7, extra_fn=None, rows=None):
        rows = rows if rows is not None else _v22_synthetic_rows(ids, raters, slots)
        try:
            res = v22_analyze(rows, ids, judge, mc)
        except V22Refused as e:
            record(name, expect, refused=e)
            return None
        record(name, expect, res, extra=extra_fn(res) if extra_fn else None)
        return res

    print("\n=== synthetic scenarios (2,000 resamples, seed 42, as the protocol) ===")
    R, J, M = _v22_scenario(ids, rng, 2, 0.35, "track", "random")
    r1 = run("2 raters agree; judge tracks them, MiniCheck does not", "judge_better", R, J, M,
             extra_fn=lambda res: {
                 "item 5: correctness and completeness only (Q35)":
                     (list(res["item5_descriptive"]), ["correctness", "completeness"]),
                 "item 5: overall stated as not computed (Q35)": (res["item5_overall"], V22_ITEM5_OVERALL),
                 "report states the overall comparison as not computed":
                     ("\nOverall comparison not computed: the judge gives no overall score"
                      in v22_report_md(res, {"generated": "synthetic", "inputs": {}}), True)})
    r1b = v22_analyze(_v22_synthetic_rows(ids, R), ids, J, M)
    record("the same scenario again: identical result (determinism)", "judge_better", r1b,
           extra={"identical JSON": (json.dumps(r1b, sort_keys=True, default=str) ==
                                     json.dumps(r1, sort_keys=True, default=str), True)})

    R, J, M = _v22_scenario(ids, rng, 3, 0.35, "random", "track")
    run("3 raters agree; MiniCheck tracks them, judge does not", "judge_not_better", R, J, M)

    R, J, M = _v22_scenario(ids, rng, 5, 0.35, "track", "random")
    run("5 raters agree; judge tracks them, MiniCheck does not", "judge_better", R, J, M,
        extra_fn=lambda res: {"5 raters included": (len(res["included"]), 5)})

    R, J, M = _v22_scenario(ids, rng, 5, 0.35, "track", "random", independent=True)
    run("5 raters who rate independently, so they do not agree (the label gate fails)", "inconclusive",
        R, J, M, extra_fn=lambda res: {"alpha below 0.667": (res["item1_reliability_faithfulness"]
                                                             ["krippendorff_alpha_ordinal"] < V22_ALPHA_GATE, True)})

    R, J, M = _v22_scenario(ids, rng, 7, 0.35, "shared", "shared")
    R["r5"]["faithfulness"] = [None, None, None] + R["r5"]["faithfulness"][3:]   # 3 items unrated
    R["r6"] = {}                                                                 # packet not returned
    R["r7"]["overall"] = [None] * len(ids)                                       # one scale left blank
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "synthetic_ratings.csv"
        rows = _v22_synthetic_rows(ids, R, notes=True)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        back = v22_read_rating_rows(p)
    run("7 packets, 4 complete, 2 incomplete and 1 empty; judge and MiniCheck share one signal (CSV round trip)",
        "judge_not_better", R, J, M, rows=back,
        extra_fn=lambda res: {"included": (res["included"], ["r1", "r2", "r3", "r4"]),
                              "statuses": ([res["raters"][s]["status"] for s in ("r5", "r6", "r7")],
                                           ["incomplete, excluded", "no ratings", "incomplete, excluded"]),
                              "notes columns not read": (any(k.endswith("_notes") for k in back[0]), False)})

    R, J, M = _v22_scenario(ids, rng, 3, 0.35, "track", "random")
    R["r2"], R["r3"] = R["r1"], R["r1"]
    run("3 identical raters: every reliability statistic is 1, agreement 100%", "judge_better", R, J, M,
        extra_fn=lambda res: {k: (round(res["item1_reliability_faithfulness"][k], 12), v) for k, v in
                              (("krippendorff_alpha_ordinal", 1.0), ("icc_2_1", 1.0), ("gwet_ac2_quadratic", 1.0),
                               ("mean_pairwise_qwk", 1.0), ("exact_pct_all_raters", 100.0))})

    print("\n=== synthetic refusals ===")
    R, J, M = _v22_scenario(ids, rng, 3, 0.35, "track", "random")
    J2 = dict(J)
    J2[ids[10]] = {**J[ids[10]], "faithfulness": None}
    run("a judge faithfulness score missing for one item", "refused", R, J2, M)
    M2 = dict(M)
    del M2[ids[20]]
    run("a MiniCheck precision missing for one item", "refused", R, J, M2)
    run("one complete packet only", "refused", {"r1": R["r1"], "r2": {**R["r2"], "overall": [None] * len(ids)}}, J, M)
    run("a ratings sheet missing one item", "refused", R, J, M, rows=_v22_synthetic_rows(ids, R)[:-1])

    # Q40 (Valerio Bianchi, 10 October 2026, before any rating): a cell that is not blank and not a whole
    # number from 1 to 5 takes its item out of the analysis for every rater; the packet stays if no score
    # cell is blank. Until then such a cell refused the whole run (the two scenarios below expected "refused").
    print("\n=== Q40: an invalid cell removes its item for every rater, not its packet ===")

    def on_set(res, raters, judge, mc, removed, extra=None):
        """The removed items, and every statistic recomputed here directly on the items left: the same
        functions on the subset matrices, with v22_draws over the subset's size."""
        keep = [e for e in ids if e not in removed]
        pos = [ids.index(e) for e in keep]
        inc = res["included"]
        F = np.array([[raters[s]["faithfulness"][i] for i in pos] for s in inc], dtype=int).reshape(len(inc), len(pos))
        dr = v22_draws(len(keep))
        irr = v22_irr(F, dr, inc)
        h = F.mean(axis=0) if len(pos) else np.zeros(0)
        corr = v22_correlations(h, [judge[e]["faithfulness"] for e in keep], [mc[e] for e in keep], dr)
        Hc = np.array([[raters[s]["correctness"][i] for i in pos] for s in inc], dtype=float).reshape(len(inc), len(pos))
        rc = v22_spearman(Hc.mean(axis=0) if len(pos) else np.zeros(0), [judge[e]["correctness"] for e in keep])
        same = lambda a, b: json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)
        out = {"items removed": ([r["eval_id"] for r in res["analysis_items"]["removed"]], list(removed)),
               "items analysed": (res["n_items_analysed"], len(keep)),
               "item 1 equals the statistics computed directly on the items left":
                   (same(res["item1_reliability_faithfulness"], irr), True),
               "items 2 to 4 equal the statistics computed directly on the items left":
                   (same(res["items2to4"], corr), True),
               "item 5 correctness equals the Spearman computed directly on the items left":
                   (same(res["item5_descriptive"]["correctness"]["rho_human_judge"], rc), True)}
        out.update(extra or {})
        return out

    bad = {s: {d: list(v) for d, v in R[s].items()} for s in R}
    bad["r2"]["faithfulness"][5], bad["r3"]["completeness"][9] = 6, 0
    run("cells outside 1 to 5 (a 6 and a 0, two packets): their two items leave the set for every rater",
        "judge_better", bad, J, M,
        extra_fn=lambda res: on_set(res, R, J, M, [ids[5], ids[9]], {
            "packets stay included": (res["included"], ["r1", "r2", "r3"]),
            "cells listed by packet and scale": ([r["cells"] for r in res["analysis_items"]["removed"]],
                                                 [[{"packet": "r2", "scale": "faithfulness"}],
                                                  [{"packet": "r3", "scale": "completeness"}]]),
            "invalid cells counted per packet": ([res["raters"][s]["cells_invalid"] for s in ("r1", "r2", "r3")],
                                                 [0, 1, 1]),
            "a packet with an invalid cell is not called complete": (
                [res["raters"][s]["status"] for s in ("r1", "r2", "r3")],
                ["complete", "included, with invalid cells", "included, with invalid cells"])}))
    rows = _v22_synthetic_rows(ids, R)
    rows[4]["r1_correctness"] = "3.5"
    run("a cell that is not a whole number (3.5): its item leaves the set", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: on_set(res, R, J, M, [ids[4]]))

    R, J, M = _v22_scenario(ids, rng, 3, 0.35, "track", "random")
    clean = v22_analyze(_v22_synthetic_rows(ids, R), ids, J, M)
    rows = _v22_synthetic_rows(ids, R)
    # S354's marker sits on correctness: since O29 an invalid overall cell removes no item (scenarios below)
    rows[17]["r2_faithfulness"], rows[30]["r1_correctness"] = "n/a", "invalid"   # text; S354's marker
    run("text in a cell, and S354's marker 'invalid' in another: both items leave the set, every packet stays",
        "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: on_set(res, R, J, M, [ids[17], ids[30]], {
            "packets stay included": (res["included"], ["r1", "r2", "r3"]),
            "report states the set": (f"{len(ids) - 2} of {len(ids)} items analysed"
                                      in v22_report_md(res, {"generated": "synthetic", "inputs": {}}), True),
            "report lists the item, packet and scale": (f"- {ids[17]}: packet r2, faithfulness"
                                                        in v22_report_md(res, {"generated": "synthetic",
                                                                               "inputs": {}}), True),
            "the result differs from the clean run": (res["items2to4"] != clean["items2to4"], True)}))
    rows[17]["r2_faithfulness"], rows[30]["r1_correctness"] = (str(R["r2"]["faithfulness"][17]),
                                                               str(R["r1"]["correctness"][30]))
    run("the same packets with both cells corrected: both items are back, the result is the clean run's",
        "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {"items analysed": (res["n_items_analysed"], len(ids)),
                              "identical to the run that never had the invalid cells":
                                  (json.dumps(res, sort_keys=True, default=str) ==
                                   json.dumps(clean, sort_keys=True, default=str), True)})
    rows = _v22_synthetic_rows(ids, R)
    rows[22]["r1_faithfulness"], rows[22]["r3_completeness"], rows[22]["r3_overall"] = "0", "9", "x"
    run("three invalid cells on one item, in two packets and on three scales: the item leaves once, for its two "
        "cells on scales a statistic reads; the overall cell is listed and removes nothing (O29)",
        "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: on_set(res, R, J, M, [ids[22]], {
            "one item, its two cells on the scales counted": ([r["cells"] for r in res["analysis_items"]["removed"]],
                                                              [[{"packet": "r1", "scale": "faithfulness"},
                                                                {"packet": "r3", "scale": "completeness"}]]),
            "the overall cell listed apart": (res["analysis_items"]["invalid_overall_cells_in_included_packets"],
                                              [{"packet": "r3", "eval_id": ids[22], "scale": "overall"}]),
            "r3's two invalid cells sit on one item": ((res["raters"]["r3"]["cells_invalid"],
                                                        res["raters"]["r3"]["items_invalid"]), (2, 1))}))

    R, J, M = _v22_scenario(ids, rng, 4, 0.35, "track", "random")
    R["r4"]["overall"][3] = None                                                 # one blank: r4 excluded whole
    rows = _v22_synthetic_rows(ids, R)
    rows[12]["r4_faithfulness"] = "7"                                            # an invalid cell in r4 too
    run("a blank cell still excludes its packet whole (Q36); an invalid cell in that excluded packet removes "
        "no item", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: on_set(res, R, J, M, [], {
            "included": (res["included"], ["r1", "r2", "r3"]),
            "r4 excluded, its cells counted": ((res["raters"]["r4"]["status"], res["raters"]["r4"]["cells_blank"],
                                                res["raters"]["r4"]["cells_invalid"]),
                                               ("incomplete, excluded", 1, 1)),
            "listed as removing no item": (res["analysis_items"]["invalid_cells_in_excluded_packets"],
                                           [{"packet": "r4", "eval_id": ids[12], "scale": "faithfulness"}])}))

    def tiny(res, n):
        md = v22_report_md(res, {"generated": "synthetic", "inputs": {}})
        und = res["undefined"]
        return {"items analysed": (res["n_items_analysed"], n),
                "ICC(2,1) undefined": ("item 1 icc_2_1" in und, True),
                "both Spearman correlations and D undefined": (all(f"items 2 to 4 {k}" in und for k in
                                                                    ("rho_human_judge", "rho_human_minicheck", "D")),
                                                               True),
                "report says undefined": (f"Undefined on this set of {n} item(s)" in md
                                          and "| ICC(2,1) | undefined |" in md and "D = undefined" in md, True)}
    # Since O28 one packet removes at most 10 items, so a set of one item, or none, takes five packets: each
    # carries invalid faithfulness cells on its own block of 10 items or fewer and stays included
    R5, J5, M5 = _v22_scenario(ids, rng, 5, 0.35, "track", "random")
    rows = _v22_synthetic_rows(ids, R5)
    for i in range(len(ids) - 1):
        rows[i][f"r{i // V22_MAX_INVALID_ITEMS + 1}_faithfulness"] = "invalid"
    run("invalid cells on all items but one, spread over five packets of 10 items or fewer each: one item left, "
        "the statistics it cannot define are said undefined", "inconclusive", R5, J5, M5, rows=rows,
        extra_fn=lambda res: {**tiny(res, 1),
                              "all five packets included": (res["included"], ["r1", "r2", "r3", "r4", "r5"]),
                              "items with an invalid cell, per packet": (
                                  [res["raters"][f"r{k}"]["items_invalid"] for k in range(1, 6)], [10, 10, 10, 10, 8])})
    rows[-1]["r5_faithfulness"] = "invalid"
    run("invalid cells on every item, five packets of 10 items or fewer each: no item left, every statistic "
        "undefined, no crash", "inconclusive", R5, J5, M5, rows=rows,
        extra_fn=lambda res: {**tiny(res, 0), "alpha undefined": ("item 1 krippendorff_alpha_ordinal"
                                                                  in res["undefined"], True)})

    def same_stats(a, b):
        """Items 1 to 5 and the decision of two results, compared as JSON."""
        keys = ("item1_reliability_faithfulness", "items2to4", "item5_descriptive", "decision", "n_items_analysed")
        return json.dumps({k: a[k] for k in keys}, sort_keys=True, default=str) == \
            json.dumps({k: b[k] for k in keys}, sort_keys=True, default=str)

    without_r2 = v22_analyze(_v22_synthetic_rows(ids, {s: v for s, v in R.items() if s != "r2"}), ids, J, M)
    rows = _v22_synthetic_rows(ids, R)
    for r in rows:
        for d in DIMENSIONS:
            r[f"r2_{d}"] = "invalid"                                             # S354's marker in every cell
    run("a packet whose every score cell is invalid: no cell blank, but invalid on 49 items, more than 10, so it is "
        "excluded whole as 'invalid on more than 10 items, excluded' and removes no item (O28; until O28 it took "
        "every item out)", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {
            "r2 excluded": (res["included"], ["r1", "r3"]),
            "r2's status and counts": ((res["raters"]["r2"]["status"], res["raters"]["r2"]["cells_rated"],
                                        res["raters"]["r2"]["cells_invalid"], res["raters"]["r2"]["items_invalid"],
                                        res["raters"]["r2"]["cells_blank"]),
                                       (V22_ST_TOO_MANY, 0, len(DIMENSIONS) * len(ids), len(ids), 0)),
            "no item removed": ((res["n_items_analysed"], res["analysis_items"]["removed"]), (len(ids), [])),
            "listed as excluded for invalid items": (res["analysis_items"]["packets_excluded_for_invalid_items"],
                                                     ["r2"]),
            "the statistics are those of the run where r2 returned nothing": (same_stats(res, without_r2), True)})

    # O28 and O29 (Valerio Bianchi, 10 October 2026, before any rating; protocol amendment 5): only correctness,
    # completeness and faithfulness count; a packet whose invalid cells on them sit on more than 10 distinct items
    # is excluded whole and removes no item; an invalid overall cell removes nothing and is listed. Q43 (same day):
    # a blank overall cell still excludes its packet whole.
    print("\n=== O28, O29, Q43: more than 10 invalid items exclude the packet; overall does not count; "
          "a blank overall cell still excludes ===")
    R, J, M = _v22_scenario(ids, rng, 3, 0.35, "track", "random")
    clean = v22_analyze(_v22_synthetic_rows(ids, R), ids, J, M)
    without_r2 = v22_analyze(_v22_synthetic_rows(ids, {s: v for s, v in R.items() if s != "r2"}), ids, J, M)
    without_r3 = v22_analyze(_v22_synthetic_rows(ids, {s: v for s, v in R.items() if s != "r3"}), ids, J, M)
    ten = list(range(3, 3 + V22_MAX_INVALID_ITEMS))                              # 10 distinct items
    rows = _v22_synthetic_rows(ids, R)
    for n, i in enumerate(ten):
        for d in V22_STAT_SCALES:
            rows[i][f"r2_{d}"] = ("invalid", "0", "6", "2.5", "n/a")[(n + len(d)) % 5]
    run("O28: invalid cells on exactly 10 items (30 cells, every scale counted on each): the packet stays and the "
        "10 items leave the set; items are counted, not cells", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: on_set(res, R, J, M, [ids[i] for i in ten], {
            "packets stay included": (res["included"], ["r1", "r2", "r3"]),
            "r2's status and counts": ((res["raters"]["r2"]["status"], res["raters"]["r2"]["cells_invalid"],
                                        res["raters"]["r2"]["items_invalid"]),
                                       (V22_ST_INVALID, 3 * V22_MAX_INVALID_ITEMS, V22_MAX_INVALID_ITEMS)),
            "no packet excluded for invalid items": (res["analysis_items"]["packets_excluded_for_invalid_items"], [])}))
    eleven = ten + [30]                                                          # 11 distinct items
    rows = _v22_synthetic_rows(ids, R)
    for i, d in zip(eleven, (V22_STAT_SCALES * 4)[:len(eleven)]):
        rows[i][f"r2_{d}"] = "invalid"
    run("O28: invalid cells on 11 items (11 cells, fewer than the 30 above): the packet is excluded whole and "
        "removes no item; its cells are listed", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {
            "r2 excluded": (res["included"], ["r1", "r3"]),
            "r2's status and counts": ((res["raters"]["r2"]["status"], res["raters"]["r2"]["cells_invalid"],
                                        res["raters"]["r2"]["items_invalid"], res["raters"]["r2"]["cells_blank"]),
                                       (V22_ST_TOO_MANY, 11, 11, 0)),
            "no item removed": ((res["n_items_analysed"], res["analysis_items"]["removed"]), (len(ids), [])),
            "listed as excluded for invalid items": (res["analysis_items"]["packets_excluded_for_invalid_items"],
                                                     ["r2"]),
            "its 11 cells listed as removing nothing": (
                [(x["packet"], x["eval_id"]) for x in res["analysis_items"]["invalid_cells_in_excluded_packets"]],
                [("r2", ids[i]) for i in eleven]),
            "the statistics are those of the run where r2 returned nothing": (same_stats(res, without_r2), True),
            "report names the exclusion": (f"{V22_ST_TOO_MANY}" in v22_report_md(res, {"generated": "synthetic",
                                                                                     "inputs": {}})
                                           and "r2 (11 items)" in v22_report_md(res, {"generated": "synthetic",
                                                                                     "inputs": {}}), True)})
    rows = _v22_synthetic_rows(ids, R)
    rows[7]["r1_overall"] = "invalid"
    run("O29: an invalid overall cell: the item stays, the packet stays, the cell is listed; the statistics are "
        "the clean run's", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {
            "packets stay included": (res["included"], ["r1", "r2", "r3"]),
            "no item removed": ((res["n_items_analysed"], res["analysis_items"]["removed"]), (len(ids), [])),
            "r1 not called complete; its cell counted, no item counted": (
                (res["raters"]["r1"]["status"], res["raters"]["r1"]["cells_invalid"],
                 res["raters"]["r1"]["items_invalid"]), (V22_ST_INVALID, 1, 0)),
            "the overall cell listed": (res["analysis_items"]["invalid_overall_cells_in_included_packets"],
                                        [{"packet": "r1", "eval_id": ids[7], "scale": "overall"}]),
            "report lists it": (f"packet r1, {ids[7]}, overall" in v22_report_md(res, {"generated": "synthetic",
                                                                                    "inputs": {}}), True),
            "the statistics are the clean run's": (same_stats(res, clean), True)})
    rows = _v22_synthetic_rows(ids, R)
    for i in ten:
        rows[i]["r2_completeness"] = "invalid"
    for r in rows:
        r["r2_overall"] = "invalid"                                              # all 49 overall cells
    run("O29 and O28: invalid on 10 items of the three scales and on every overall cell (49 items with an invalid "
        "cell, 59 cells): overall does not count toward the 10, so the packet stays; the 10 items leave, the 49 "
        "overall cells are listed", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: on_set(res, R, J, M, [ids[i] for i in ten], {
            "packets stay included": (res["included"], ["r1", "r2", "r3"]),
            "r2's counts": ((res["raters"]["r2"]["status"], res["raters"]["r2"]["cells_invalid"],
                             res["raters"]["r2"]["items_invalid"]),
                            (V22_ST_INVALID, V22_MAX_INVALID_ITEMS + len(ids), V22_MAX_INVALID_ITEMS)),
            "49 overall cells listed": (len(res["analysis_items"]["invalid_overall_cells_in_included_packets"]),
                                        len(ids))}))
    rows = _v22_synthetic_rows(ids, R)
    rows[40]["r3_overall"] = ""
    run("Q43: one blank overall cell in a packet otherwise complete excludes it whole, though overall enters no "
        "statistic", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {
            "r3 excluded": (res["included"], ["r1", "r2"]),
            "r3's status and counts": ((res["raters"]["r3"]["status"], res["raters"]["r3"]["cells_blank"],
                                        res["raters"]["r3"]["cells_rated"]),
                                       (V22_ST_INCOMPLETE, 1, len(DIMENSIONS) * len(ids) - 1)),
            "the statistics are those of the run where r3 returned nothing": (same_stats(res, without_r3), True)})
    rows[7]["r3_overall"] = "invalid"
    rows[7]["r2_overall"] = "invalid"
    run("Q43 and O29 together: r3 blank on overall and invalid on overall, r2 invalid on overall: r3 excluded "
        "whole for the blank, r2 stays, no item removed", "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {
            "included": (res["included"], ["r1", "r2"]),
            "r2's overall cell listed apart; r3's with the excluded packets": (
                (res["analysis_items"]["invalid_overall_cells_in_included_packets"],
                 res["analysis_items"]["invalid_cells_in_excluded_packets"]),
                ([{"packet": "r2", "eval_id": ids[7], "scale": "overall"}],
                 [{"packet": "r3", "eval_id": ids[7], "scale": "overall"}])),
            "no item removed": (res["n_items_analysed"], len(ids)),
            "the statistics are those of the run where r3 returned nothing": (same_stats(res, without_r3), True)})

    # D190 (Valerio, 31 October 2026, H2 O-a): the judge values are S508's lock-judge rows on key v2.5 (D183 FD11 c).
    # The cases of S373's ledger reader, which D190 replaced, are replaced by S508-shaped folders here; MiniCheck keeps
    # key v2.4's sha256 (V22_MC_KEY). Each mutant is this file's source with one check changed, imported from a temp
    # copy: a case that refuses must then read (or the reverse), or the case does not test that check.
    print("\n=== the judge reader on SYNTHETIC S508 folders, MiniCheck on SYNTHETIC rows (the real join's items) ===")
    import importlib.util
    import S508_judge_49_v25 as S508
    its = join["items"]
    mc_sha = _sha256(V22_MC_KEY)
    s508_items, _ = S508.items_49()
    RUN, LOCKSHA = "f" * 64, "e" * 64
    JMODEL, JDIGEST = v22_lock_judge()

    def jrow(x, **kw):
        r = {"eval_id": x["eval_id"], "question_id": x["question_id"], "config": x["config"],
             "key_hash": x["key_hash"], "item_sha256": x["item_sha256"], "answer_chars": len(x["answer"]),
             "status": "ok", "scores": {"correctness": 4, "completeness": 3, "faithfulness": 5, "citation_quality": 4},
             "run_sha256": RUN, "lock_sha256": LOCKSHA, "at": "2026-10-30T20:30:00", "model_digest": JDIGEST,
             "ollama_version": "synthetic"}
        r.update(kw)
        return r

    def s508_folder(td, name, rows=None, summary=None, recheck=None):
        d = Path(td) / name
        d.mkdir()
        rows = [jrow(x) for x in s508_items] if rows is None else rows
        (d / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        (d / "summary.json").write_text(json.dumps(summary or {"key": {"sha256": V22_KEY25_SHA256},
                                                               "judge": {"run_sha256": RUN, "lock_sha256": LOCKSHA}}))
        (d / "recheck_summary.json").write_text(json.dumps(recheck or {"n": 10, "equal": 10, "passed": True,
                                                                       "run_sha256": RUN, "after_complete": True}))
        return d

    def mrow(it, **kw):
        r = {"question_id": it["question_id"], "config": it["config"], "key_sha256": mc_sha,
             "minicheck": {"precision": 0.5}, "v1_deposited": {"precision": it["mc_precision_s08_v1_key"]}}
        r.update(kw)
        return r

    def write(td, name, rows, tail=""):
        p = Path(td) / name
        p.write_text("".join(json.dumps(r) + "\n" for r in rows) + tail)
        return p

    def reader_case(name, expect, fn, checks=None):
        try:
            got = fn()
        except V22Refused as e:
            record(name, expect, refused=e)
            return
        rec = {"scenario": name, "expected": expect, "outcome": "read", "checks": {}}
        ok = expect == "read"
        for k, want in (checks or {}).items():
            g = got.get(k) if isinstance(got, dict) else None
            rec["checks"][k] = {"got": g, "expected": want, "pass": g == want}
            ok = ok and g == want
        rec["pass"] = bool(ok)
        scen.append(rec)
        if not ok:
            failed.append(name)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {rec['checks']}")

    def mutant(td, label, old, new):
        """This file's source with `old` (exactly once) replaced by `new`, imported from a temp copy."""
        src = Path(__file__).read_text(encoding="utf-8")
        if src.count(old) != 1:
            raise AssertionError(f"mutant {label}: the text to change occurs {src.count(old)} times, not once")
        f = Path(td) / f"S08_mutant_{label}.py"
        f.write_text(src.replace(old, new), encoding="utf-8")
        spec = importlib.util.spec_from_file_location(f"S08_mutant_{label}", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def killed(name, fn, exc, expected):
        """Runs a case under a mutant. The mutant is killed when the outcome is `expected`, the opposite of the
        outcome the same case has under the real code (recorded by its own case above)."""
        try:
            fn()
            verdict = "read"
        except exc:
            verdict = "refused"
        rec = {"scenario": name, "expected": expected, "outcome": verdict, "pass": verdict == expected}
        scen.append(rec)
        if not rec["pass"]:
            failed.append(name)
        print(f"  [{'PASS' if rec['pass'] else 'FAIL'}] {name}: {verdict} (mutant killed: {rec['pass']})")

    with tempfile.TemporaryDirectory() as td:
        sys.path.insert(0, td)
        try:
            good = s508_folder(td, "good")

            def jgood(d=good, mod=None):
                v, cov, pr = (mod or sys.modules[__name__]).v22_judge_values(join, d)
                return {"items scored": sum(c == "scored" for c in cov.values()),
                        "faithfulness, first three": [v[it["eval_id"]]["faithfulness"] for it in its[:3]],
                        "files": sorted(Path(k).name for k in pr["files"]), "run": pr["run_sha256"]}
            reader_case("judge: an S508 folder, 49 rows ok, a passed recheck of the run after all 49", "read", jgood,
                        {"items scored": len(its), "faithfulness, first three": [5, 5, 5],
                         "files": ["recheck_summary.json", "rows.jsonl", "summary.json"], "run": RUN})
            reader_case("judge: S508's key_hash of every item equals the join's s508_key_hash (the formula agrees)",
                        "read", lambda: {"equal": [x["key_hash"] for x in s508_items] ==
                                                  [it["s508_key_hash"] for it in its]}, {"equal": True})
            rows = [jrow(x) for x in s508_items]
            rows[4] = jrow(s508_items[4], status="error", scores=None)
            reader_case("judge: one row not ok", "refused", lambda: v22_judge_values(join, s508_folder(td, "err", rows)))
            reader_case("judge: 48 rows, one item never judged", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "short", [jrow(x) for x in s508_items[:-1]])))
            rows = [jrow(x) for x in s508_items]
            rows[7] = jrow(s508_items[7], run_sha256="0" * 64)
            reader_case("judge: a row of another run (S508.latest refuses it)", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "run", rows)))
            other_run = s508_folder(td, "recheck_run", recheck={"n": 10, "equal": 10, "passed": True,
                                                                "run_sha256": "0" * 64, "after_complete": True})
            reader_case("judge: the recheck is of another run", "refused", lambda: v22_judge_values(join, other_run))
            reader_case("judge: the recheck did not pass", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "recheck_fail", recheck={
                            "n": 10, "equal": 9, "passed": False, "run_sha256": RUN, "after_complete": True})))
            reader_case("judge: the recheck was made before all 49 were judged", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "recheck_early", recheck={
                            "n": 10, "equal": 10, "passed": True, "run_sha256": RUN, "after_complete": False})))
            reader_case("judge: summary.json names a key other than the v2.5 pin", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "key", summary={
                            "key": {"sha256": "0" * 64}, "judge": {"run_sha256": RUN, "lock_sha256": LOCKSHA}})))
            # review F1 (D190): before D190 the reader refused a row judged by another model or options; S508's rows
            # name the model by digest and the lock by sha256, so the reader requires the lock's judge digest and the
            # run's lock on every row
            rows = [jrow(x) for x in s508_items]
            rows[5] = jrow(s508_items[5], model_digest="0" * 64)
            other_model = s508_folder(td, "model", rows)
            reader_case("judge: a row judged by another model (its digest is not the lock's judge)", "refused",
                        lambda: v22_judge_values(join, other_model))
            rows = [jrow(x) for x in s508_items]
            rows[6] = jrow(s508_items[6], lock_sha256="0" * 64)
            reader_case("judge: a row judged under another lock than the run's", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "lock", rows)))
            reader_case("judge: summary.json names no lock for the run", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "nolock", summary={
                            "key": {"sha256": V22_KEY25_SHA256}, "judge": {"run_sha256": RUN}})))
            rows = [jrow(x) for x in s508_items]
            rows[2] = jrow(s508_items[2], answer_chars=1)
            reader_case("judge: a row whose answer length is not the join's", "refused",
                        lambda: v22_judge_values(join, s508_folder(td, "chars", rows)))
            rows = [jrow(x) for x in s508_items]
            rows[3] = jrow(s508_items[3], key_hash="0" * 16)
            bad_hash = s508_folder(td, "hash", rows)
            reader_case("judge: a row whose key_hash is not the join's v2.5 key hash", "refused",
                        lambda: v22_judge_values(join, bad_hash))
            reader_case("judge: a join on key v2.4 takes no S508 value", "refused",
                        lambda: v22_judge_values({**join, "key_version": "2.4"}, good))

            m_rck = mutant(td, "no_recheck", "    if not S508.recheck_valid(rck):\n", "    if False:\n")
            killed("mutant 'the recheck is not checked': the recheck of another run is read",
                   lambda: m_rck.v22_judge_values(join, other_run), m_rck.V22Refused, "read")
            # the old text is split so that this line does not contain it (mutant() requires one occurrence)
            m_hash = mutant(td, "no_key_hash", '        joined = (it["question_id"], it["config"], it["answer_chars"], '
                            'it["s508_key_hash"])\n',
                            '        joined = (it["question_id"], it["config"], it["answer_chars"], r.get("key_hash"))\n')
            killed("mutant 'the key_hash is not checked': the row with another key_hash is read",
                   lambda: m_hash.v22_judge_values(join, bad_hash), m_hash.V22Refused, "read")
            m_model = mutant(td, "no_model", "        if r.get(\"model_digest\") != judge_digest:\n",
                             "        if False:\n")
            killed("mutant 'the judge model is not checked': the row judged by another model is read",
                   lambda: m_model.v22_judge_values(join, other_model), m_model.V22Refused, "read")

            sess = {"_session": {"key_sha256": mc_sha}}
            m1 = write(td, "S384_a.jsonl", [sess, mrow(its[0]), mrow(its[1], minicheck={"precision": None})])

            def mgood(mod=None):
                v, cov, _ = (mod or sys.modules[__name__]).v22_minicheck_values(join, [m1])
                e = [it["eval_id"] for it in its[:3]]
                return {"coverage": [cov[x] for x in e], "precision": [v.get(x) for x in e]}
            reader_case("MiniCheck rows under key v2.4's sha256 (V22_MC_KEY), on the v2.5 join: scored, precision "
                        "missing, absent", "read", mgood,
                        {"coverage": ["scored", "precision missing", "no row"], "precision": [0.5, None, None]})
            m_mc = mutant(td, "mc_on_v25", "    key_sha = _sha256(V22_MC_KEY)\n", "    key_sha = _sha256(V22_KEY25)\n")
            killed("mutant 'MiniCheck keyed on V22_KEY25': the v2.4 rows are refused",
                   lambda: mgood(m_mc), m_mc.V22Refused, "refused")
            m2 = write(td, "S384_b.jsonl", [sess, mrow(its[0], v1_deposited={"precision": -1.0})])
            reader_case("MiniCheck: v1_deposited precision is not S08's (G4)", "refused",
                        lambda: v22_minicheck_values(join, [m2]))
            m3 = write(td, "S384_c.jsonl", [{"_session": {"key_sha256": "0" * 64}}, mrow(its[0])])
            reader_case("MiniCheck: a session run against another key", "refused",
                        lambda: v22_minicheck_values(join, [m3]))
            m4 = write(td, "S384_d.jsonl", [sess, mrow(its[0], minicheck={"precision": 0.9})])
            reader_case("MiniCheck: one answer scored differently in two files", "refused",
                        lambda: v22_minicheck_values(join, [m1, m4]))

            # G2 on key v2.5 and the content rule, on copies of the master's CONTENT columns (rating columns blank)
            print("\n=== G2 on key v2.5 and the content rule, on content-only copies of the master ===")
            header, content = v22_read_content(V22_MASTER)
            k24 = {q["id"]: q for q in json.loads(V22_KEY24.read_text())["questions"]}
            k25 = {q["id"]: q for q in json.loads(V22_KEY25.read_text())["questions"]}
            qid_of = {it["eval_id"]: it["question_id"] for it in its}
            changed = [e for e in ids if k24[qid_of[e]]["expected_concepts"] != k25[qid_of[e]]["expected_concepts"]]

            def content_copy(name, swap=(), cols=None):
                f = Path(td) / name
                cols = header if cols is None else cols
                with open(f, "w", encoding="utf-8", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=cols)
                    w.writeheader()
                    for r in content:
                        row = {c: "" for c in cols}
                        row.update(r)
                        if r["eval_id"] in swap:
                            row["expected_concepts"] = "; ".join(k24[qid_of[r["eval_id"]]]["expected_concepts"])
                        w.writerow(row)
                return f
            reader_case("G2: a content-only copy of the master joins on key v2.5", "read",
                        lambda: {"items": len(v22_join(content_copy("m25.csv"))["items"])}, {"items": len(ids)})
            print(f"  {len(changed)} items whose key points differ between v2.4 and v2.5")
            reader_case(f"G2: the same copy with the v2.4 key points of one changed item ({changed[0]}) is refused "
                        f"on key v2.5", "refused", lambda: v22_join(content_copy("m24one.csv", [changed[0]])))
            cols = V22_CONTENT + [f"r{k}_{d}" for k in (1, 2) for d in DIMENSIONS]
            reader_case("content rule: a ratings CSV carrying the master's v2.5 content is accepted", "read",
                        lambda: v22_require_same_content(content_copy("r25.csv", cols=cols)) or {"accepted": True},
                        {"accepted": True})
            reader_case("content rule: a ratings CSV with v2.4 key points on one changed item (collected from a v2.4 "
                        "packet) is refused", "refused",
                        lambda: v22_require_same_content(content_copy("r24.csv", [changed[-1]], cols=cols)))
        finally:
            sys.path.remove(td)

    # Amendment 9: rater 1's completeness is his v2.5 score on the 36 changed items and as given on the 13 others,
    # the r1_completeness column S354 copies from packet r1_v25; one blank cell on a changed item excludes the packet
    # (the blank rule, amendment 2). SYNTHETIC ratings.
    print("\n=== amendment 9: a blank completeness cell on a changed item excludes rater 1 (SYNTHETIC ratings) ===")
    R, J, M = _v22_scenario(ids, rng, 3, 0.35, "track", "random")
    rows = _v22_synthetic_rows(ids, R)
    rows[ids.index(changed[0])]["r1_completeness"] = ""
    run(f"rater 1 leaves the completeness of a changed item ({changed[0]}) blank: his packet is excluded whole",
        "judge_better", R, J, M, rows=rows,
        extra_fn=lambda res: {"r1's status": (res["raters"]["r1"]["status"], V22_ST_INCOMPLETE),
                              "included": (res["included"], ["r2", "r3"]),
                              "one blank cell": (res["raters"]["r1"]["cells_blank"], 1)})

    print("\n=== the one-rater mode (S08b, amendment 8), synthetic ===")
    checks = v22_one_packet_scenario(ids, rng)
    wrong = [k for k, (got, want) in checks.items() if got != want]
    scen.append({"scenario": "one packet, r1: items 2, 3, 5 and D, no item 1, no decision", "expected": "descriptive",
                 "checks": {k: {"got": got, "expected": want, "pass": got == want} for k, (got, want) in checks.items()},
                 "pass": not wrong})
    if wrong:
        failed.append("one packet")
    print(f"  [{'FAIL' if wrong else 'PASS'}] one packet: {len(checks) - len(wrong)} of {len(checks)} checks")

    print("\n=== the input gate on the REAL judge and MiniCheck inputs (no rating read) ===")
    jv, jcov, jprov = v22_judge_values(join, judge_dir)
    mv, mcov, mprov = v22_minicheck_values(join, minicheck)
    try:
        v22_require_inputs(ids, jv, mv)
        real_gate = {"refused": False}
    except V22Refused as e:
        real_gate = {"refused": True, "message": str(e)}
    real_gate.update(judge_scored=sum(v == "scored" for v in jcov.values()),
                     minicheck_scored=sum(v == "scored" for v in mcov.values()),
                     judge_coverage=jcov, minicheck_coverage=mcov,
                     judge_files=list(jprov["files"]), minicheck_files=list(mprov["files"]))
    print(f"  S508 judge scores on key v{join['key_version']}: {real_gate['judge_scored']} of {len(ids)}; MiniCheck: "
          f"{real_gate['minicheck_scored']} of {len(ids)}; gate {'REFUSES' if real_gate['refused'] else 'passes'}")

    n_unit = sum(t["pass"] for t in unit)
    print(f"\n  scenarios: {sum(s['pass'] for s in scen)} of {len(scen)} as designed")
    if failed:
        print(f"SMOKE TEST FAILED: {failed}; nothing written")
        return 1
    prov = {"script": "scripts/S08_human_eval_analysis.py", "script_sha256": _sha256(Path(__file__)),
            "command": "uv run python scripts/S08_human_eval_analysis.py --v22 --smoke-test",
            "generated": _utc_now(), "inputs": join["inputs"],
            "ratings": "SYNTHETIC only; no human rating column of any file was read"}
    V22_SMOKE_OUT.write_text(json.dumps(_json_safe(json.loads(json.dumps(
        {"_provenance": prov, "unit_tests": {"passed": n_unit, "of": len(unit), "tests": unit},
         "reproduction": rep, "join_key_version": join["key_version"], "join_gates": join["gates"],
         "scenarios": scen, "real_input_gate": real_gate}, default=str))),
        indent=1, allow_nan=False) + "\n")
    print(f"SMOKE TEST PASSED: {n_unit} known answers, {len(scen)} scenarios. Wrote {rel(V22_SMOKE_OUT)}")
    return 0


def v22_verify_join(judge_dir=None, minicheck=()) -> dict:
    rep = v22_reproduce_v24(minicheck)           # README.md:75-79: the stored v2.4 join first, then the v2.5 one
    join = v22_join()
    jv, jcov, jprov = v22_judge_values(join, judge_dir)
    mv, mcov, mprov = v22_minicheck_values(join, minicheck)
    ids = [it["eval_id"] for it in join["items"]]
    missing_j = [e for e in ids if jcov.get(e) != "scored"]
    missing_m = [e for e in ids if mcov.get(e) != "scored"]
    out = {"_provenance": {"script": "scripts/S08_human_eval_analysis.py",
                           "command": "uv run python scripts/S08_human_eval_analysis.py --v22 --verify-join",
                           "generated": _utc_now(), "inputs": join["inputs"],
                           "judge_files": jprov["files"], "minicheck_files": mprov["files"],
                           "reproduced_before_writing": rep, "ratings": "none read"},
           "gates": join["gates"], "n_items": len(ids), "key": join["key"], "key_version": join["key_version"],
           "key_sha256": join["key_sha256"], "d7": join["d7"],
           "judge_definition": "S508 (D183 FD11 c): the lock's judge call on key v2.5, one row per item, status ok, "
                               "with a passed recheck of the run",
           "minicheck_definition": "S384 minicheck.precision: each answer sentence checked against the v2.4 expected "
                                   "answer (ground_truth_v2_4_as_v1.json), the deposited exp04 definition S08 used "
                                   "(master_join mc_precision); amendment 9 states that v2.5 left the expected "
                                   "answers unchanged; S508.items_49 checks v2.5's against v2.3's, and no line "
                                   "compares v2.5's with v2.4's directly",
           "inputs_complete": not missing_j and not missing_m,
           "judge_scored": len(ids) - len(missing_j), "minicheck_scored": len(ids) - len(missing_m),
           "judge_missing": {e: jcov.get(e) for e in missing_j},
           "minicheck_missing": {e: mcov.get(e) for e in missing_m},
           "judge_rows_dropped": jprov["rows_dropped"],
           "per_item": [{**it, "judge": jcov.get(it["eval_id"]), "judge_row": jprov["row_per_item"].get(it["eval_id"]),
                         "minicheck": mcov.get(it["eval_id"])} for it in join["items"]]}
    V22_JOIN_OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"join: {len(ids)} items, gates G1 to G4 passed")
    print(f"reproduced first: the v2.4 path on the 12 October master gives {V22_V24_JOIN['path']} at "
          f"{V22_V24_JOIN['commit'][:8]} ({rep['items']} items, gates equal)")
    print(f"S508 judge scores on key v{join['key_version']} present: {out['judge_scored']} of {len(ids)}; "
          f"missing {missing_j}")
    print(f"MiniCheck precision (against key v2.4's expected answers) present: {out['minicheck_scored']} of "
          f"{len(ids)}; missing {missing_m}")
    print(f"Wrote {rel(V22_JOIN_OUT)}")
    return out


def v22_on_word(decision, readme=None) -> str:
    """The one-rater mode's word: decision must read D<nnn> and stand as a decision line, "- **D<nnn>** ...", in
    experiments/README.md. Returns that line. FP r1 2.14 a (D193 (1)): it runs on Valerio's word, with no fixed date."""
    import re
    if not re.fullmatch(r"D\d{1,4}", decision or ""):
        raise V22Refused(f"--one-rater needs --on-word D<nnn>, the decision that records Valerio's word; got {decision!r}")
    path = Path(readme) if readme is not None else V22_DECISIONS
    hit = [x for x in path.read_text(encoding="utf-8").splitlines() if re.match(rf"\s*- \*\*{decision}\*\*", x)]
    if len(hit) != 1:
        raise V22Refused(f"{rel(path)} holds {len(hit)} decision lines for {decision}, not one: a one-rater run needs "
                         f"the dated decision")
    return hit[0]


def v22_run(args) -> int:
    # O20 (Valerio Bianchi, 10 October 2026): the known-answer tests first, on every real analysis run;
    # any failure refuses before the deadline check, the join or any rating cell
    try:
        unit = v22_unit_tests()
    except Exception as e:                      # AssertionError on a failed check; anything else is a failure too
        raise V22Refused(f"the known-answer tests did not all pass ({type(e).__name__}: {e}); the analysis "
                         f"does not run on an engine that fails them")
    one = bool(getattr(args, "one_rater", False))
    word = v22_on_word(args.on_word) if one else None     # the one-rater mode replaces the deadline by his word
    if not one:
        v22_deadline_check(args.deadline)        # before any rating cell is opened
    rep = v22_reproduce_v24(args.minicheck)      # README.md:75-79, before any rating cell is opened
    join = v22_join()
    ids = [it["eval_id"] for it in join["items"]]
    judge, jcov, jprov = v22_judge_values(join, args.judge_dir)
    mc, mcov, mprov = v22_minicheck_values(join, args.minicheck)
    v22_require_inputs(ids, judge, mc)           # before any rating cell is opened
    path = Path(args.analyze) if args.analyze else V22_MASTER
    v22_require_same_content(path)               # content columns only, before any rating cell is opened
    res = v22_analyze(v22_read_rating_rows(path), ids, judge, mc, one_rater=one)
    prov = {"script": "scripts/S08_human_eval_analysis.py", "script_sha256": _sha256(Path(__file__)),
            "command": "uv run python " + " ".join(sys.argv), "generated": _utc_now(),
            "protocol": rel(V22_PROTOCOL), "deadline": None if one else args.deadline,
            "on_word": (args.on_word if one else None),
            "key": join["key"], "key_version": join["key_version"], "key_sha256": join["key_sha256"],
            "unit_tests": {"passed": sum(t["pass"] for t in unit), "of": len(unit), "run": "first, O20"},
            "inputs": {**join["inputs"], rel(path): _sha256(path)},
            "judge_files": jprov["files"], "judge_row_per_item": jprov["row_per_item"],
            "judge_run_sha256": jprov["run_sha256"], "minicheck_files": mprov["files"],
            "reproduced_before_writing": rep}
    out = V22_ONE_RATER_OUT if one else V22_RESULTS_OUT
    out.write_text(json.dumps(_json_safe(json.loads(json.dumps({"_provenance": prov, **res}, default=str))),
                              indent=1, allow_nan=False) + "\n")
    md = out.with_suffix(".md")
    md.write_text(v22_report_md(res, prov))
    print(f"Decision line for this run: {word[:120]}" if one else md.read_text())
    print(f"Wrote {rel(out)} and {rel(md)}")
    return 0


def v22_main(args) -> int:
    try:
        if args.unit_tests:
            v22_unit_tests()
            return 0
        if args.smoke_test:
            return v22_smoke_test(args.judge_dir, args.minicheck)
        if args.verify_join:
            v22_verify_join(args.judge_dir, args.minicheck)
            return 0
        return v22_run(args)
    except V22Refused as e:
        print(f"REFUSED, nothing written: {e}")
        return 1


# ===========================================================================
# CLI
# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description="S08 human-eval analysis engine")
    ap.add_argument("--smoke-test", action="store_true",
                    help="Run unit tests + full engine on synthetic ratings")
    ap.add_argument("--verify-join", action="store_true",
                    help="Reconstruct seed-42 sample and verify master_join join")
    ap.add_argument("--analyze", type=str, default=None,
                    help="Analyze a completed rating CSV (defaults to the real CSV)")
    ap.add_argument("--unit-tests", action="store_true", help="Run unit tests only")
    ap.add_argument("--v22", action="store_true",
                    help="the v2.2 protocol (findings/S08b_PROTOCOL_HUMAN_EVAL_V22.md); with --unit-tests, "
                         "--smoke-test, --verify-join, or alone (with --analyze CSV) for the analysis")
    ap.add_argument("--ledger", action="append", default=[],
                    help="refused with --v22 since D190: the judge values are S508's on key v2.5 (FD11 c), not "
                         "S373 ledgers; use --judge-dir")
    ap.add_argument("--judge-dir", default=None,
                    help=f"v2.2: S508's folder to read the judge values from (default {rel(V22_JUDGE_DIR)}), e.g. "
                         f"a copy from another machine")
    ap.add_argument("--minicheck", action="append", default=[],
                    help="v2.2: S384 output file(s) to read instead of the default ones")
    ap.add_argument("--deadline", default=V22_DEADLINE,
                    help="v2.2: the ratings deadline, if the editor moves it later (ISO, with zone)")
    ap.add_argument("--one-rater", action="store_true",
                    help="v2.2: the one-rater mode (S08b, amendment 8), on Valerio's word; needs --on-word D<nnn>")
    ap.add_argument("--on-word", default=None, help="v2.2 --one-rater: the decision line that records his word")
    ap.add_argument("--overall-judge", choices=["none"], default="none",
                    help="none is the only value (Q35, 10 October 2026): the judge gives no overall score, so "
                         "item 5 has no overall comparison. Kept so that earlier command lines still parse; it "
                         "changes nothing")
    args = ap.parse_args()

    if args.v22:
        if args.ledger:
            ap.error("--ledger: since D190 the judge values are S508's lock-judge rows on key v2.5 (D183 FD11 c), "
                     "read from --judge-dir; S373 ledgers are not read")
        raise SystemExit(v22_main(args))
    if args.ledger or args.minicheck or args.judge_dir or args.deadline != V22_DEADLINE or args.one_rater \
            or args.on_word:
        ap.error("--ledger, --judge-dir, --minicheck, --deadline, --one-rater and --on-word apply only with --v22")

    if args.unit_tests:
        run_unit_tests()
        return
    if args.smoke_test:
        smoke_test()
        return
    if args.verify_join:
        rep = verify_join()
        print(json.dumps({k: rep[k] for k in
                          ["seed", "n_items", "csv_reconstruction_exact_matches",
                           "join_ok_count", "all_50_reproduce"]}, indent=2))
        print(f"Wrote {JOIN_OUT}")
        return

    # Default: verify join THEN analyze the real (empty) CSV -> graceful exit.
    rep = verify_join()
    print(f"Join verification: {rep['csv_reconstruction_exact_matches']}/50 CSV-reproduced, "
          f"{rep['join_ok_count']}/50 join-OK. Wrote {JOIN_OUT}")
    path = args.analyze or str(HUMAN_CSV)
    analyze(path)


if __name__ == "__main__":
    main()
