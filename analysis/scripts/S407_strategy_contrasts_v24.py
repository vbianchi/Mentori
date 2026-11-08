#!/usr/bin/env python3
"""S407 - pass rates per generation strategy and every pairwise difference between strategies, with intervals, in the
experiments that compare the strategies, on ground truth v2.4: under the main judge and, where the loader holds its
scores (the two replications), under the second judge. It reports numbers. It fits no model, runs no test, adjusts
no interval for multiplicity and orders no strategies.

WHY. R3 of D8 (notes/DECISIONS_2026-10-13.md:59-61): on the 1,500 calibration answers the contrast between
verified_pass and multi_hop changes sign with the judge, each interval including 0, and phase 3 looks at that contrast
in the experiments themselves before a sentence orders the two strategies. Section A of the report is that contrast
in every block; the other sections give every strategy and every pair.

READS
  scripts/judged_ledger.py (imported as jl)   every judge score: jl.reported("exp04"), jl.corpus_scaling_reported(),
                                              jl.reported and jl.paired for rep2 and rep5 with each of the two judges.
                                              This script parses no ledger and no result file. For the provenance block
                                              (inputs()) it hashes the key files, the loader's record, the manifest and
                                              the result files, and takes each merged ledger's sha256 from the loader's
                                              record, which the loader checks against the ledger's bytes
  findings/recompute/S393_early_claims.json   the known numbers of gate G1 (its devstral column on the v2.4 key and,
                                              for the ten, E6's ten_group, which sits beside that column)

DEFINITIONS, the loader's (judged_ledger.py, module docstring) unless stated:
  judges      jl.MAIN_JUDGE (devstral, D8) in every block; jl.SECOND_JUDGE (gptoss) in the blocks of rep2 and rep5,
              whose rows under both judges the script requires (a missing ledger is a refusal; G2 then requires the
              same answers under both), and in the blocks of exp04 or of corpus scaling when jl.judges() lists a
              complete ledger of it there (on 13 October it lists none)
  group       the tables are on the group answerable. The ten false-premise questions (group refutation) are counted
              per block, judge and strategy (answers, passes against the refutation) and enter no rate, difference
              or interval: D11 (notes/DECISIONS_2026-10-13.md:77-82) makes them their own group in the paper,
              reported as passed against the refutation. The rows of the group not_answerable are counted per block
              and enter no table
  pass        the loader's Row.passed: score of 3 or more on the group's dimension (correctness for the groups
              answerable and refutation)
  rows        jl.reported(): the arm reported, in scope under Q55, scored. Corpus scaling's verified_pass rows are
              the S314 rerun's (jl.corpus_scaling_reported()); the six D7 questions are in no ledger
  strategy    Row.config, one of STRATEGIES. A pair is written "first - second" with the first strategy earlier in
              STRATEGIES: the order fixes the sign of a difference and ranks nothing
  unit        the run inside which two strategies are paired on a question: the index (core size and noise ratio) in
              corpus scaling, the generator and draw in the replications, the generator in exp04 (one run)

BLOCKS. exp04; corpus scaling pooled over its indexes, per core size and per index; rep2 pooled and per generator;
rep5 pooled, per generator and per draw. A pooled block holds the answers of the blocks under it.

STATISTICS, per block and judge, on the answers of the group answerable:
  resamples     one resample matrix per number of questions n, numpy.random.default_rng(SEED).integers(0, n,
                size=(N_BOOT, n)), drawn once and used by every block, judge, pair and strategy with that n (the
                matrix that seeding again for each block would give). The n questions are the block's: the distinct
                questions with an answerable row in the block, sorted
  per strategy  questions (distinct questions with an answer of the strategy), answers, passes, pass rate, and two
                95% intervals of the pass rate, both stored. wilson95: the Wilson interval of passes out of answers
                (no continuity correction, z = NormalDist().inv_cdf(0.975)), which treats the answers as independent.
                question_bootstrap95: the PCT percentiles (2.5th and 97.5th; numpy.percentile, linear interpolation)
                of the pass rate over the block's resamples. A question drawn c times brings each of its answers of
                the strategy c times; the pass rate of a resample is the passes drawn divided by the answers drawn. A
                resample that draws no answer of the strategy is left out and counted. The report shows
                question_bootstrap95 in a table whose block holds more than one answer of a strategy on a question
                (several indexes, generators or draws: those answers share questions, of which Wilson takes no
                account) and wilson95 in a table with one answer per question and strategy
                (pass_rate_interval_shown, answers_per_question_and_strategy_max)
  per pair      the paired set is every (unit, question) on which both strategies have a row. Difference: the first
                strategy's pass rate minus the second's over the paired set. Interval: the PCT percentiles
                (numpy.percentile, linear interpolation) of the difference over the block's resamples. A question
                drawn c times brings each of its paired answers c times; the difference of a resample is the sum of
                (first pass - second pass) over the paired answers drawn, divided by their number. A resample that
                draws no paired answer is left out and counted. ci_includes_0 is lower <= 0 <= upper;
                ci_bound_equals_0 marks an interval with a bound equal to 0; ci_bound_within_one_step_of_0 marks one
                with a bound b such that abs(b) <= 1 / n_pairs, a bound equal to 0 included. The bounds are estimates
                from N_BOOT resamples, so the ci_includes_0 of an interval with that mark can change with the seed.
                The mark is no full list of such intervals: in a block with several units, where a question drawn
                brings several pairs, ci_includes_0 can also change when both bounds are farther than one step from
                0, and no field marks that.
                The questions drawn are the block's also when a pair's paired set holds fewer (n_questions_resampled,
                n_questions). For such a pair the JSON also holds ci95_resampling_the_paired_set, the same
                percentiles over resamples of the paired set's own sorted questions (the matrix of that number of
                questions): the other reading of resampling questions, kept beside the first and shown in no table
  two judges    in a block with both judges, per pair: the sign of each judge's difference (-1, 0 or 1), whether the
                two signs are equal, and whether the two judges' paired sets are the same. Refused: a block whose
                two judges do not hold the same strategies and pairs, or whose two tables would show two kinds of
                interval beside a pass rate

GATES (the run stops with one sentence, writing nothing, when one fails)
  G1  from the loader's rows, these fields of S393_early_claims.json (the result of each claim in its column
      S393_COLUMN, the devstral scores on the v2.4 key, and E6's ten_group, which sits beside that column), after
      checking that S393 names this key, these D7 questions and these ten, and that each claim used is at full
      coverage:
        E1          units, n_questions and, per strategy, n and rate (exp04, group answerable)
        E2, E4, E5  n_pairs, rate_a, rate_b, diff, a_only, b_only, discordant, baseline_correct for single_pass with
                    verified_pass, rlm_10 with verified_pass and rlm_10 with single_pass; E3 is E2 with pass at a
                    score of 4 or more
        E6          units, n_questions and, per strategy, n and rate on the group not_answerable; ten_group's new_n and
                    new_passed per strategy
        R1, R2, R3  per generator: the answers of single_pass and rlm_10 (generators), R3's deltas, R2's n_sp, n_rlm,
                    single_pass_pct, rlm_10_pct and delta_pp, and R1's single_pass_pct, rlm_10_pct and delta_pp at the
                    two decimals S393 stores
        S1, S2      per index cell of corpus scaling: n, single_pass, rlm_10, sp_minus_rlm
        J1          the two judges on the answerable rows of both replications: units, n_questions, generators,
                    rate_main, rate_second, gap, main_only, second_only, disagreements, agreement, kappa, and the four
                    values of its printed sentence at their precision
      Counts are compared exactly, rates to TOL; a value that is not a number, on either side, is the gate's refusal,
      and so is an integer too large to subtract from a float (OverflowError).
      Not recomputed: S393's P values and Cohen's h, R1's bootstrap fields (did_pp, ci_pp, verdict), the ranks of E1
      and the fields S393 derives from the counts above (E6's gap, harmful and degraded of E2 to E5, R3's
      two_most_negative). This script runs no test and ranks nothing
  G2  the counts of the loader's rows: KNOWN_COUNTS (typed here; exp04's is also compared with jl.EXPECTED) and, for
      corpus scaling, the count corpus_scaling_expected() derives from jl.EXPECTED; the verified_pass rows of corpus
      scaling are all rows of s314 and no row of exp05; the two judges of each replication hold the same ledger keys
      in the selection. For corpus scaling the gate compares the total with the derived count, which does not
      depend on EXPECTED's out-of-scope rows of s314 (the derivation adds and subtracts them), and each of the two
      parts, the rows of exp05 and of s314, with the number of rows of the loader's own selection: no expected
      count is compared with a part
  G3  the resampling is reproducible: one block (G3_BLOCK, main judge) computed a second time with a resample
      matrix drawn again from the seed gives the same matrix, the same difference and ci95 of every pair and the same
      question_bootstrap95 of every strategy, compared with ==
  G4  the Wilson formula against scipy.stats.binomtest(...).proportion_ci(method="wilson") on every (passes, answers)
      of the tables, to 1e-12
  G5  the interval rule of a difference, in four parts
      (a) every pair, in a block with one unit, whose paired set holds every question of the block (one paired
          answer per question, n of them). The difference of a resample is then the mean of n independent draws of
          +1, 0 and -1 with probabilities first_only / n, (n - first_only - second_only) / n and second_only / n.
          The distribution of that mean is computed by n convolutions, and each bound of ci95 must lie within one
          step 1 / n (plus 1e-12) of its G5_LEVELS quantile, the smallest value whose cumulative probability reaches
          the level (less 1e-12, for the rounding of the sums). G5_LEVELS (0.025, 0.975) is typed apart from PCT.
          This part fails a level whose quantile lies more than one step away, and no closer one: part (c) holds
          the level itself. The gate refuses when no pair meets the condition
      (b) G3_BLOCK under the main judge, every pair: the difference of each of the first GATHERED resamples,
          recomputed from the block's rows by gathering the questions drawn one by one through the index matrix
          (drawn again from the seed), equals (==) the value the percentiles of ci95 were taken over
      (c) the level and the interpolation of percentile_interval, the function every resampling interval of this
          script is taken with, on a statistic with a known answer: the N_BOOT values 0, 1 / (N_BOOT - 1), ..., 1,
          whose quantile at a level is the level under linear interpolation. The two values the function returns
          must be G5_LEVELS to 1e-9
      (d) every pair of every block and judge: ci95 recomputed from the block's rows over all N_BOOT resamples,
          the sums of a resample taken as integers by indexing through the index matrix of the block's questions
          (drawn again from the seed, once per number of questions) and the percentiles by percentile_interval,
          equals (==) the stored ci95. The questions this part draws are the block's also for a pair whose paired
          set holds fewer, so it holds that reading for those pairs (d_pairs_with_fewer_questions_than_the_block)
  G6  the question-bootstrap interval of a pass rate, in the style of G5(b): G3_BLOCK under the main judge, every
      strategy: the pass rate of each of the first GATHERED resamples, recomputed from the block's rows by gathering
      the questions drawn through the index matrix, equals (==) the value the percentiles of question_bootstrap95
      were taken over. Its percentiles come from percentile_interval, the function G5(c) tests. No gate recomputes
      question_bootstrap95 itself: one taken from those resampled pass rates by other code than that function
      would pass
  Read by no gate, besides the two cases stated under G2 and G6: ci_includes_0 and the two marks of an interval,
  which no gate recomputes from ci95, and pass_rate_interval_shown (two_judges() refuses only a block whose two
  judges give two kinds). The report lists these cases; the list is the cases known, not a proof of no other

    uv run python scripts/S407_strategy_contrasts_v24.py
Writes findings/recompute/S407_strategy_contrasts_v24.json and .md: both texts are built first, each is written to
<name>.tmp beside its file, and the two are renamed onto their names after both are written, the JSON first. When
the second rename fails after the first, the run ends with its refusal and the JSON of this run stands beside the
.md of the run before: nothing puts the earlier JSON back. The time stamp is in the JSON's provenance block only.
Changes no answer, no key and no ledger; calls no model and opens no connection.
"""
from __future__ import annotations

import hashlib
import json
import math
import numbers
import os
import platform
import re
import sys
import time
from collections import Counter
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from statistics import NormalDist

import numpy as np
import scipy
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import judged_ledger as jl  # noqa: E402
import key_scope  # noqa: E402
from machine import RECOMPUTE, ROOT, rel  # noqa: E402

OUT_JSON = RECOMPUTE / "S407_strategy_contrasts_v24.json"
OUT_MD = RECOMPUTE / "S407_strategy_contrasts_v24.md"
S393_JSON = RECOMPUTE / "S393_early_claims.json"
S393_COLUMN = "devstral_v22_matched"                 # S393's name for its column of devstral scores on the current key
COMMAND = "uv run python scripts/S407_strategy_contrasts_v24.py"
MAIN, SECOND = jl.MAIN_JUDGE, jl.SECOND_JUDGE
STRATEGIES = ("single_pass", "verified_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20")
FOCUS = ("verified_pass", "multi_hop")               # R3, notes/DECISIONS_2026-10-13.md:59-61
REPLICATIONS = ("rep2", "rep5")
SEED, N_BOOT = 20261013, 10000
PCT = (2.5, 97.5)                                    # the percentiles of every resampling interval (percentile_interval)
Z = NormalDist().inv_cdf(0.975)
TOL = 1e-9
G3_BLOCK = "rep5/pooled"
G5_LEVELS = (0.025, 0.975)                           # the levels of G5(a) and G5(c), typed apart from PCT on purpose
GATHERED = 200                                       # the resamples that G5(b) and G6 recompute by gathering
# G2. 516: typed here and compared with jl.EXPECTED["exp04_groups"] (judged_ledger.py:1154). 515 and 7,672: typed
# here; they are the sums of the generator counts of S393's J1 (258 + 257; 1,525 + 1,536 + 1,545 + 1,535 + 1,531),
# which G1 compares one by one. The count of corpus scaling is no constant of this script: corpus_scaling_expected()
# derives it from jl.EXPECTED (on 13 October it gives 9,552, and the loader's rows are 7,947 of exp05 and 1,605 of s314)
KNOWN_COUNTS = {"exp04_answerable": 516, "rep2_answerable": 515, "rep5_answerable": 7672}
# G1. The loader keeps the generator's name as the result file stores it (judged_ledger.py:87-90); S393's tables use
# S393.TWO_FILES for the two files of rep2 (S393_early_claims.py:171-172) and the campaign's names for rep5
S393_GENERATOR = {"anthropic::claude-haiku-4-5": "claude-haiku-4-5",
                  "gemini::gemini-3-flash-preview": "gemini-3-flash-preview",
                  "ollama::gemma3:27b": "gemma3:27b",
                  "ollama::glm-4.7-flash:latest": "glm-4.7-flash",
                  "ollama::nemotron-3-nano:30b": "nemotron-3-nano:30b",
                  "ollama::qwen3-coder:latest": "qwen3-coder:30b",
                  "ollama::qwen3.5:122b": "qwen3.5:122b"}
S393_J1_TEXT = re.compile(r"second judge passes ([0-9.]+)%, main ([0-9.]+)%; agreement ([0-9.]+)%, kappa ([0-9.]+);")
UNIT_TEXT = {"exp04": "the generator, which has one run", "corpus_scaling": "the index, a core size with a noise ratio",
             "rep2": "the generator and draw", "rep5": "the generator and draw"}
TITLE = {"exp04": "exp04, generation strategies", "corpus_scaling": "Corpus scaling (exp05, with the S314 rerun's "
         "verified_pass rows)", "rep2": "rep2, the two-model replication", "rep5": "rep5, the five-model replication"}


def die(msg: str) -> None:
    raise SystemExit("S407 REFUSED: " + msg)


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ask(what: str, fn, *args):
    """A loader call. The loader's ValueError (an experiment or a judge without a complete ledger) becomes a refusal of
    one sentence; its own refusals are SystemExit and pass through."""
    try:
        return fn(*args)
    except ValueError as e:
        die(f"judged_ledger gave no {what}: {e}")


# ---- statistics --------------------------------------------------------------------------------------------

def wilson(k: int, n: int) -> list[float]:
    """The Wilson 95% interval of k passes out of n answers, no continuity correction."""
    p = k / n
    den = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return [centre - half, centre + half]


def resample_index(n: int) -> np.ndarray:
    """(N_BOOT, n): the question drawn at each of the n places of each resample of n questions with replacement, from
    a generator seeded with SEED. The same n gives the same matrix."""
    return np.random.default_rng(SEED).integers(0, n, size=(N_BOOT, n))


def resample_counts(n: int) -> np.ndarray:
    """(N_BOOT, n): how many times each of n questions is drawn in each resample, counted from resample_index(n)."""
    idx = resample_index(n)
    flat = np.bincount((idx + n * np.arange(N_BOOT)[:, None]).ravel(), minlength=N_BOOT * n)
    return flat.reshape(N_BOOT, n).astype(float)


counts_for = lru_cache(maxsize=None)(resample_counts)    # one matrix per n, drawn once (module docstring, resamples)


def resampled(w: np.ndarray, num: np.ndarray, den: np.ndarray) -> tuple:
    """Per resample of w: the sum of num over the questions drawn, each as many times as it is drawn, divided by the
    same sum of den; NaN where that sum of den is 0. Second value: the mask of the resamples that have a ratio."""
    top, bottom = w @ num, w @ den
    ok = bottom > 0
    stat = np.full(len(w), np.nan)
    stat[ok] = top[ok] / bottom[ok]
    return stat, ok


def percentile_interval(stat: np.ndarray, ok: np.ndarray) -> list[float]:
    """The PCT percentiles of a resampled statistic over the resamples that have one (linear interpolation)."""
    return [float(v) for v in np.percentile(stat[ok], PCT)]


def corpus_scaling_expected() -> int:
    """The rows jl.corpus_scaling_reported() returns when every row in scope is scored, from jl.EXPECTED: exp05's
    rows of the arm reported less that arm's out-of-scope rows, plus s314's rows of the arm reported less its
    out-of-scope rows. EXPECTED["out_of_scope"] counts exp05's out-of-scope rows over its two arms; the arm
    deposit_verified_pass holds as many of them as s314, whose rows of the arm reported are on that arm's
    (index, question) pairs (jl.corpus_scaling_reported refuses otherwise). s314's out-of-scope rows are rows of the
    arm reported: they are at 5 and 10 core papers, its smoke rows at 50 (EXPECTED["smoke_core"]). On 13 October:
    8,067 - (144 - 24) + 1,629 - 24 = 9,552 (judged_ledger.py:1156-1160; :147-148 states the 120 and the 24). The
    sum adds s314's out-of-scope rows in its first part and subtracts them in its second, so the count returned
    does not depend on them: it is 8,067 - 144 + 1,629."""
    try:
        arms, out = jl.EXPECTED["arms"], jl.EXPECTED["out_of_scope"]
        out05, out314 = sum(out["exp05"].values()), sum(out["s314"].values())
        want = arms["exp05"][jl.REPORTED] - (out05 - out314) + arms["s314"][jl.REPORTED] - out314
        smoke_out = sorted(set(out["s314"]) & set(jl.EXPECTED["smoke_core"]))
    except (KeyError, TypeError, AttributeError) as e:
        die(f"G2: jl.EXPECTED of scripts/judged_ledger.py does not hold the arms, the smoke rows and the out-of-scope "
            f"rows of exp05 and s314 that the expected count of corpus scaling is derived from ({type(e).__name__}: {e})")
    if smoke_out:
        die(f"G2: jl.EXPECTED gives s314 out-of-scope rows and smoke rows at the same core size ({smoke_out}), so the "
            "expected count of corpus scaling cannot be derived from it")
    if isinstance(want, bool) or not isinstance(want, int):
        die(f"G2: the expected count of corpus scaling derived from jl.EXPECTED is {want!r}, which is no count")
    return want


def unit_of(r):
    """The run inside which two strategies are paired on a question (module docstring, unit)."""
    if r.experiment in REPLICATIONS:
        return (r.generator, r.draw)
    if r.experiment in jl.WITH_SCOPE:                    # exp05 and s314: the rows of corpus scaling
        return r.index
    return r.generator


def unit_text(u) -> str:
    return f"{u[0]} draw {u[1]}" if isinstance(u, tuple) else str(u)


def cells(rows, flag=None) -> dict:
    """strategy -> {(unit, question): passed} over rows of one group. flag, when given, replaces Row.passed (gate G1
    uses it for E3's pass at 4). Refused: a config outside STRATEGIES, a row without a score, two rows of a strategy
    on one question in one unit."""
    by: dict = {}
    for r in rows:
        if r.config not in STRATEGIES:
            die(f"the row {r.key} has the config {r.config!r}, which is none of {', '.join(STRATEGIES)}")
        if r.passed is None or r.score is None:
            die(f"the row {r.key} has no score (status {r.status!r}), and every table counts a row as a pass or a fail")
        key = (unit_of(r), r.question_id)
        d = by.setdefault(r.config, {})
        if key in d:
            die(f"two rows of {r.config} on {r.question_id} in the unit {unit_text(key[0])} ({r.key} is the second)")
        d[key] = bool(r.passed) if flag is None else bool(flag(r))
    return by


def pair_counts(a: dict, b: dict, pos: dict) -> dict:
    """Two strategies' cells over their paired set, the (unit, question) keys both hold: counts, both pass rates, the
    difference and, per question of pos, the number of paired answers (_m) and the sum of first pass minus second
    pass (_d)."""
    shared = a.keys() & b.keys()
    d, m = np.zeros(len(pos)), np.zeros(len(pos))
    pa = pb = a_only = b_only = 0
    for key in shared:
        x, y = a[key], b[key]
        i = pos[key[1]]
        m[i] += 1
        d[i] += int(x) - int(y)
        pa += x
        pb += y
        a_only += x and not y
        b_only += y and not x
    n = len(shared)
    return {"n_questions": int((m > 0).sum()), "n_pairs": n, "n_pass_first": int(pa), "n_pass_second": int(pb),
            "rate_first": pa / n if n else None, "rate_second": pb / n if n else None,
            "first_only": int(a_only), "second_only": int(b_only), "diff": (pa - pb) / n if n else None,
            "_d": d, "_m": m, "_set": frozenset(shared)}


def interval(c: dict, w: np.ndarray, where: str) -> dict:
    """The 95% percentile interval of a pair's difference over the resample matrix w (module docstring, per pair).
    c: pair_counts of a pair with at least one paired answer. where names the pair and block in a refusal."""
    stat, ok = resampled(w, c["_d"], c["_m"])
    if not ok.any():
        die(f"no resample of the block's questions draws a paired answer of {where}")
    lo, hi = percentile_interval(stat, ok)
    own, other = c["_m"] > 0, None
    if not own.all():                                    # the other reading, for the record: the paired set's own questions
        other = percentile_interval(*resampled(counts_for(int(own.sum())), c["_d"][own], c["_m"][own]))
    step = 1 / c["n_pairs"]
    return {"ci95": [lo, hi], "ci_includes_0": bool(lo <= 0.0 <= hi), "ci_bound_equals_0": bool(lo == 0.0 or hi == 0.0),
            "ci_bound_within_one_step_of_0": bool(abs(lo) <= step or abs(hi) <= step),
            "resamples_undefined": int((~ok).sum()), "ci95_resampling_the_paired_set": other,
            "_stat_head": stat[:GATHERED]}


def block_stats(rows: list, where: str, w: np.ndarray | None = None) -> dict:
    """One block under one judge (module docstring, STATISTICS). rows: the block's Rows of that judge, every group.
    where names the block and judge in a refusal. w: a resample matrix for the block's questions;
    counts_for(number of questions) when not given. Refused: a block with no answerable row, a pair of strategies
    with no paired answer, a strategy or a pair that no resample draws an answer of."""
    ans = [r for r in rows if r.group == jl.ANSWERABLE]
    if not ans:
        die(f"{where} holds no row of the group answerable")
    questions = sorted({r.question_id for r in ans})
    pos = {q: i for i, q in enumerate(questions)}
    if w is None:
        w = counts_for(len(questions))
    by = cells(ans)
    present = [s for s in STRATEGIES if s in by]
    strategies = {}
    for s in present:
        n, k = len(by[s]), sum(by[s].values())
        per_q_answers, per_q_passes = np.zeros(len(questions)), np.zeros(len(questions))
        for (_, q), passed in by[s].items():
            per_q_answers[pos[q]] += 1
            per_q_passes[pos[q]] += passed
        stat, ok = resampled(w, per_q_passes, per_q_answers)
        if not ok.any():
            die(f"no resample of the block's questions draws an answer of {s} in {where}")
        strategies[s] = {"n_questions": len({q for _, q in by[s]}), "n_answers": n, "n_pass": int(k),
                         "pass_rate": k / n, "wilson95": wilson(int(k), n),
                         "answers_per_question_max": int(per_q_answers.max()),
                         "question_bootstrap95": percentile_interval(stat, ok),
                         "question_bootstrap_resamples_undefined": int((~ok).sum()), "_stat_head": stat[:GATHERED]}
    pairs = {}
    for a, b in combinations(present, 2):
        c = pair_counts(by[a], by[b], pos)
        if not c["n_pairs"]:
            die(f"{where} holds no (unit, question) with an answer of both {a} and {b}, a case the tables do not cover")
        pairs[f"{a} - {b}"] = {"first": a, "second": b, "n_questions_resampled": len(questions), **c,
                               **interval(c, w, f"{a} and {b} in {where}")}
    ten = cells([r for r in rows if r.group == jl.REFUTATION])
    most = max(v["answers_per_question_max"] for v in strategies.values())
    return {"n_rows_by_group": dict(sorted(Counter(r.group for r in rows).items())),
            "n_questions": len(questions), "n_answers": len(ans),
            "units": sorted(unit_text(u) for u in {unit_of(r) for r in ans}),
            "answers_per_question_and_strategy_max": most,
            "pass_rate_interval_shown": "question_bootstrap95" if most > 1 else "wilson95",
            "strategies": strategies, "strategies_absent": [s for s in STRATEGIES if s not in by], "pairs": pairs,
            "the_ten": {"n_questions": len({q for d in ten.values() for _, q in d}),
                        "strategies": {s: {"n_answers": len(ten[s]), "n_pass": int(sum(ten[s].values()))}
                                       for s in STRATEGIES if s in ten}}}


def sign(x: float) -> int:
    return (x > 0) - (x < 0)


def two_judges(bid: str, per_judge: dict) -> dict:
    """Per pair of a block with both judges: each judge's difference and its sign, whether the signs are equal and
    whether the two paired sets are the same (unit, question) keys. Refused: two judges whose tables of the block do
    not hold the same strategies and pairs, or would show two kinds of interval beside a pass rate."""
    a, b = per_judge[MAIN], per_judge[SECOND]
    if list(a["strategies"]) != list(b["strategies"]) or list(a["pairs"]) != list(b["pairs"]):
        die(f"the block {bid} holds the strategies {', '.join(a['strategies'])} under {MAIN} and "
            f"{', '.join(b['strategies']) or 'none'} under {SECOND}, and its tables need the same under both")
    if a["pass_rate_interval_shown"] != b["pass_rate_interval_shown"]:
        die(f"the block {bid} holds at most {a['answers_per_question_and_strategy_max']} answers per question and "
            f"strategy under {MAIN} and {b['answers_per_question_and_strategy_max']} under {SECOND}, so its two tables "
            "would show two kinds of interval beside a pass rate")
    out = {}
    for name, x in a["pairs"].items():
        y = b["pairs"][name]
        out[name] = {"diff": {MAIN: x["diff"], SECOND: y["diff"]}, "sign": {MAIN: sign(x["diff"]), SECOND: sign(y["diff"])},
                     "same_sign": sign(x["diff"]) == sign(y["diff"]), "same_paired_set": x["_set"] == y["_set"]}
    return out


# ---- data: the loader's rows and gate G2 -------------------------------------------------------------------

def load() -> dict:
    """name -> {"rows": {judge: rows}, "statements": {what: the loader's sentence}} for exp04, corpus scaling and the
    two replications, plus "_pairs": the loader's pairs of the two judges per replication. Gate G2 runs here."""
    data: dict = {}

    def has_second(*exps: str) -> bool:
        return all(SECOND in ask(f"list of the judges of {e}", jl.judges, e) for e in exps)

    data["exp04"] = {"rows": {}, "statements": {}}
    for judge in (MAIN, SECOND) if has_second("exp04") else (MAIN,):
        sel = ask(f"rows of exp04 under the judge {judge}", jl.reported, "exp04", judge)
        data["exp04"]["rows"][judge], data["exp04"]["statements"][judge] = sel.rows, sel.statement()
    cs = ask("rows of corpus scaling", jl.corpus_scaling_reported, MAIN)
    data["corpus_scaling"] = {"rows": {MAIN: cs.rows}, "statements": {MAIN: cs.statement()}}
    if has_second("exp05", "s314"):
        cs2 = ask(f"rows of corpus scaling under the judge {SECOND}", jl.corpus_scaling_reported, SECOND)
        data["corpus_scaling"]["rows"][SECOND], data["corpus_scaling"]["statements"][SECOND] = cs2.rows, cs2.statement()
    pairs = {}
    for exp in REPLICATIONS:
        data[exp] = {"rows": {}, "statements": {}}
        for judge in (MAIN, SECOND):
            sel = ask(f"rows of {exp} under the judge {judge}", jl.reported, exp, judge)
            data[exp]["rows"][judge] = sel.rows
            data[exp]["statements"][judge] = sel.statement()
        pairs[exp] = ask(f"pairs of the two judges for {exp}", jl.paired, exp, MAIN, SECOND)
        data[exp]["statements"]["the two judges"] = pairs[exp].statement()

    def n_ans(rows) -> int:
        return sum(r.group == jl.ANSWERABLE for r in rows)

    got = {"exp04_answerable": n_ans(data["exp04"]["rows"][MAIN]), "corpus_scaling_rows": len(cs.rows)}
    for exp in REPLICATIONS:
        got[f"{exp}_answerable"] = n_ans(data[exp]["rows"][MAIN])
        if n_ans(data[exp]["rows"][SECOND]) != got[f"{exp}_answerable"] or pairs[exp].only_first or pairs[exp].only_second:
            die(f"G2: the two judges of {exp} do not hold the same answers in the arm reported "
                f"({got[exp + '_answerable']:,} and {n_ans(data[exp]['rows'][SECOND]):,} answerable rows; "
                f"{len(pairs[exp].only_first)} and {len(pairs[exp].only_second)} rows of one judge alone)")
    for name, want in KNOWN_COUNTS.items():
        if got[name] != want:
            die(f"G2: the loader gives {got[name]:,} for {name}, and KNOWN_COUNTS of this script holds {want:,}")
    if got["exp04_answerable"] != jl.EXPECTED["exp04_groups"][jl.ANSWERABLE]:
        die("G2: KNOWN_COUNTS and jl.EXPECTED give two counts of exp04's answerable rows")
    derived = corpus_scaling_expected()
    if got["corpus_scaling_rows"] != derived:
        die(f"G2: the loader gives {got['corpus_scaling_rows']:,} rows of corpus scaling, and the count derived from "
            f"jl.EXPECTED is {derived:,}")
    vp = Counter(r.experiment for r in cs.rows if r.config == jl.S314_CONFIG)
    by_exp = Counter(r.experiment for r in cs.rows)
    if set(vp) != {"s314"} or vp["s314"] != by_exp["s314"] or by_exp["s314"] != len(cs.s314.rows) \
            or by_exp["exp05"] != len(cs.exp05.rows) or set(by_exp) != {"exp05", "s314"}:
        die(f"G2: corpus scaling's {jl.S314_CONFIG} rows are not all rows of the S314 rerun and those alone "
            f"({dict(vp)} of {dict(by_exp)})")
    data["_pairs"] = pairs
    data["_g2"] = {**got, "corpus_scaling_rows_exp05": by_exp["exp05"], "corpus_scaling_rows_s314": by_exp["s314"],
                   "corpus_scaling_rows_derived_from_jl_EXPECTED": derived,
                   "corpus_scaling_verified_pass_rows": dict(vp),
                   "rows_of_one_judge_alone": {exp: [len(pairs[exp].only_first), len(pairs[exp].only_second)]
                                               for exp in REPLICATIONS}, "passed": True}
    return data


def split(name: str, rows: tuple) -> list:
    """(block id, level, title, row filter) of one experiment's blocks, from the main judge's answerable rows."""
    ans = [r for r in rows if r.group == jl.ANSWERABLE]
    if name == "exp04":
        return [("exp04", "experiment", "exp04", lambda r: True)]
    if name == "corpus_scaling":
        idx = sorted({(r.core, r.noise) for r in ans})
        cores = sorted({c for c, _ in idx})
        out = [("corpus_scaling/pooled", "pooled", f"corpus scaling, the {len(idx)} indexes pooled", lambda r: True)]
        out += [(f"corpus_scaling/core={c}", "core size",
                 f"corpus scaling, {c} core papers ({sum(1 for x, _ in idx if x == c)} noise ratios pooled)",
                 lambda r, c=c: r.core == c) for c in cores]
        out += [(f"corpus_scaling/core={c},noise={n}", "index", f"corpus scaling, {c} core papers, noise ratio {n}",
                 lambda r, c=c, n=n: (r.core, r.noise) == (c, n)) for c, n in idx]
        return out
    gens, draws = sorted({r.generator for r in ans}), sorted({r.draw for r in ans})
    out = [(f"{name}/pooled", "pooled", f"{name}, {len(gens)} generators"
            + (f" and {len(draws)} draws" if len(draws) > 1 else "") + " pooled", lambda r: True)]
    out += [(f"{name}/generator={g}", "generator", f"{name}, generator {g}", lambda r, g=g: r.generator == g) for g in gens]
    if len(draws) > 1:
        out += [(f"{name}/draw={d}", "draw", f"{name}, draw {d}", lambda r, d=d: r.draw == d) for d in draws]
    return out


def block_rows(data: dict, bid: str, judge: str) -> list:
    """The Rows of one block under one judge, every group: the experiment's rows that the block's filter keeps."""
    exp = bid.split("/", 1)[0]
    if exp not in data or judge not in data[exp]["rows"]:
        die(f"no rows of the block {bid} under the judge {judge}")
    keep = [k for b, _, _, k in split(exp, data[exp]["rows"][MAIN]) if b == bid]
    if len(keep) != 1:
        die(f"no block {bid}")
    return [r for r in data[exp]["rows"][judge] if keep[0](r)]


def build(data: dict) -> dict:
    """block id -> the block: its experiment, level, title, unit, the loader's statements and, per judge, block_stats;
    for a block with two judges, two_judges too. Refused: a level of an experiment whose blocks do not hold each
    answerable row of the experiment and judge once (the tally per level of section A counts on that)."""
    blocks: dict = {}
    for name in ("exp04", "corpus_scaling", *REPLICATIONS):
        e = data[name]
        held: dict = {}                                  # (level, judge) -> how many blocks of the level hold each row
        for bid, level, title, keep in split(name, e["rows"][MAIN]):
            per = {}
            for judge, rows in e["rows"].items():
                mine = [r for r in rows if keep(r)]
                per[judge] = block_stats(mine, f"the block {bid} under the judge {judge}")
                held.setdefault((level, judge), Counter()).update(r for r in mine if r.group == jl.ANSWERABLE)
            b = {"experiment": name, "level": level, "title": title, "unit": UNIT_TEXT[name],
                 "judge_models": {judge: sorted({r.judge_model for r in rows}) for judge, rows in e["rows"].items()},
                 "loader_statements": e["statements"], "judges": per}
            if SECOND in per:
                b["two_judges"] = two_judges(bid, per)
            blocks[bid] = b
        for (level, judge), seen in held.items():
            n_exp = sum(r.group == jl.ANSWERABLE for r in e["rows"][judge])
            if len(seen) != n_exp or set(seen.values()) != {1}:
                die(f"the blocks of the level {level!r} of {name} under {judge} hold {len(seen):,} of the experiment's "
                    f"{n_exp:,} answerable rows, a row in up to {max(seen.values())} blocks, and each must be in one")
    return blocks


# ---- gates G1, G3, G4 --------------------------------------------------------------------------------------

def j1(pairs: list) -> dict:
    """The two judges on the same answers: pass rates, agreement, Cohen's kappa ((po - pe) / (1 - pe)) and the two
    discordant counts. Refused: a row without a score."""
    for r in (r for pair in pairs for r in pair):
        if r.passed is None:
            die(f"G1: the row {r.key} of the judge {r.judge} has no score (status {r.status!r}), and J1 counts each "
                "answer as a pass or a fail")
    a = np.array([bool(x.passed) for x, _ in pairs])
    b = np.array([bool(y.passed) for _, y in pairs])
    pa, pb, po = float(a.mean()), float(b.mean()), float((a == b).mean())
    pe = pa * pb + (1 - pa) * (1 - pb)
    return {"units": len(pairs), "n_questions": len({x.question_id for x, _ in pairs}), "rate_main": pa, "rate_second": pb,
            "gap": pa - pb, "main_only": int((a & ~b).sum()), "second_only": int((~a & b).sum()),
            "disagreements": int((a != b).sum()), "agreement": po, "kappa": (po - pe) / (1 - pe)}


def gate_g1(data: dict, blocks: dict) -> dict:
    """The devstral values of S393_early_claims.json on the v2.4 key, from the loader's rows (module docstring, G1)."""
    try:
        doc = json.loads(S393_JSON.read_text())
    except (OSError, ValueError, RecursionError) as e:   # RecursionError: brackets nested deeper than the parser goes
        die(f"G1: {rel(S393_JSON)} cannot be read as JSON ({type(e).__name__}: {e})")
    checks: list = []                                    # (what, got, want, tolerance; 0 for a count, beside)

    def num(what: str, got, want, tol: float = TOL, beside: bool = False) -> None:
        """One comparison. beside: the known value is read from E6's ten_group, outside the column S393_COLUMN."""
        checks.append((what, got, want, tol, beside))

    try:
        head = doc["_provenance"]
        if head["key"]["sha256"] != sha_file(jl.S373.KEY) or set(head["d7"]) != set(jl.d7_questions()) \
                or set(head["q51"]) != set(key_scope.Scope().ten):
            die(f"G1: {rel(S393_JSON)} was not computed on the key {jl.S373.KEY.name} the loader reads, or with other "
                f"D7 questions or another ten")
        claims = {c["id"]: c for c in doc["claims"]}
        known = {}
        for cid in ("E1", "E2", "E3", "E4", "E5", "E6", "R1", "R2", "R3", "S1", "S2", "J1"):
            cov = claims[cid]["coverage"]
            if cov["units_matched"] != cov["units_needed"]:
                die(f"G1: S393's devstral column of {cid} is on {cov['units_matched']} of {cov['units_needed']} units")
            known[cid] = claims[cid][S393_COLUMN]["result"]

        e4 = blocks["exp04"]["judges"][MAIN]
        e4_rows = data["exp04"]["rows"][MAIN]
        # E1: every strategy of exp04
        num("E1 units", e4["n_answers"], known["E1"]["units"], 0)
        num("E1 n_questions", e4["n_questions"], known["E1"]["n_questions"], 0)
        for s in STRATEGIES:
            num(f"E1 {s}_n", e4["strategies"][s]["n_answers"], known["E1"][f"{s}_n"], 0)
            num(f"E1 {s}_rate", e4["strategies"][s]["pass_rate"], known["E1"][f"{s}_rate"])

        def paired_claim(cid: str, c: dict, first_is_a: bool) -> None:
            """A pair of this script against S393's result of a claim, whose a is the pair's first or second strategy."""
            k = known[cid]
            a, b = ("first", "second") if first_is_a else ("second", "first")
            num(f"{cid} n_pairs", c["n_pairs"], k["n_pairs"], 0)
            num(f"{cid} rate_a", c[f"rate_{a}"], k["rate_a"])
            num(f"{cid} rate_b", c[f"rate_{b}"], k["rate_b"])
            num(f"{cid} diff", c["diff"] if first_is_a else -c["diff"], k["diff"])
            num(f"{cid} a_only", c[f"{a}_only"], k["a_only"], 0)
            num(f"{cid} b_only", c[f"{b}_only"], k["b_only"], 0)
            num(f"{cid} discordant", c["first_only"] + c["second_only"], k["discordant"], 0)
            num(f"{cid} baseline_correct", c[f"n_pass_{a}"], k["baseline_correct"], 0)

        paired_claim("E2", e4["pairs"]["single_pass - verified_pass"], True)
        paired_claim("E4", e4["pairs"]["verified_pass - rlm_10"], False)
        paired_claim("E5", e4["pairs"]["single_pass - rlm_10"], False)
        # E3: E2 with pass at a score of 4 or more, through the same pair_counts
        at4 = cells([r for r in e4_rows if r.group == jl.ANSWERABLE], flag=lambda r: r.score >= 4)
        pos = {q: i for i, q in enumerate(sorted({q for _, q in at4["single_pass"]} | {q for _, q in at4["verified_pass"]}))}
        paired_claim("E3", pair_counts(at4["single_pass"], at4["verified_pass"], pos), True)
        # E6: the group not_answerable per strategy, and the ten's counts per strategy
        na = cells([r for r in e4_rows if r.group == jl.NOT_ANSWERABLE])
        num("E6 units", sum(len(v) for v in na.values()), known["E6"]["units"], 0)
        num("E6 n_questions", len({q for v in na.values() for _, q in v}), known["E6"]["n_questions"], 0)
        for s in STRATEGIES:
            num(f"E6 {s}_n", len(na[s]), known["E6"][f"{s}_n"], 0)
            num(f"E6 {s}_rate", sum(na[s].values()) / len(na[s]), known["E6"][f"{s}_rate"])
            ten = claims["E6"]["ten_group"]["by_config"][s]
            num(f"E6 the ten, {s} new_n", e4["the_ten"]["strategies"][s]["n_answers"], ten["new_n"], 0, beside=True)
            num(f"E6 the ten, {s} new_passed", e4["the_ten"]["strategies"][s]["n_pass"], ten["new_passed"], 0, beside=True)
        # R1, R2, R3: single_pass and rlm_10 per generator, in the seven per-generator blocks
        per_gen = {}
        for bid, b in blocks.items():
            if b["experiment"] in REPLICATIONS and b["level"] == "generator":
                g = bid.split("generator=", 1)[1]
                if g not in S393_GENERATOR:
                    die(f"G1: the generator {g!r} of {b['experiment']} has no name in S393_GENERATOR")
                per_gen[S393_GENERATOR[g]] = b["judges"][MAIN]["strategies"]
        if set(per_gen) != set(known["R3"]["deltas"]) or set(per_gen) != set(known["R1"]["by_generator"]):
            die(f"G1: the replications hold the generators {sorted(per_gen)}, S393's R3 {sorted(known['R3']['deltas'])}")
        for g, st in per_gen.items():
            sp, rl = st["single_pass"], st["rlm_10"]
            delta = 100 * (rl["pass_rate"] - sp["pass_rate"])
            r1 = known["R1"]["by_generator"][g]
            num(f"R1 generators {g}", sp["n_answers"] + rl["n_answers"], known["R1"]["generators"][g], 0)
            num(f"R1 {g} single_pass_pct", 100 * sp["pass_rate"], r1["single_pass_pct"], 0.005 + TOL)
            num(f"R1 {g} rlm_10_pct", 100 * rl["pass_rate"], r1["rlm_10_pct"], 0.005 + TOL)
            num(f"R1 {g} delta_pp", delta, r1["delta_pp"], 0.005 + TOL)
            num(f"R3 deltas {g}", delta, known["R3"]["deltas"][g])
            num(f"R3 generators {g}", sp["n_answers"] + rl["n_answers"], known["R3"]["generators"][g], 0)
        (g2, n2), = known["R2"]["generators"].items()
        sp, rl = per_gen[g2]["single_pass"], per_gen[g2]["rlm_10"]
        num("R2 units", sp["n_answers"] + rl["n_answers"], n2, 0)
        num("R2 n_sp", sp["n_answers"], known["R2"]["n_sp"], 0)
        num("R2 n_rlm", rl["n_answers"], known["R2"]["n_rlm"], 0)
        num("R2 single_pass_pct", 100 * sp["pass_rate"], known["R2"]["single_pass_pct"])
        num("R2 rlm_10_pct", 100 * rl["pass_rate"], known["R2"]["rlm_10_pct"])
        num("R2 delta_pp", 100 * (rl["pass_rate"] - sp["pass_rate"]), known["R2"]["delta_pp"])
        # S1 and S2: single_pass with rlm_10 in each index of corpus scaling
        index_cells = {**known["S1"]["cells"], **known["S2"]["cells"]}
        idx_blocks = {bid for bid, b in blocks.items() if b["experiment"] == "corpus_scaling" and b["level"] == "index"}
        for name, k in index_cells.items():
            m = re.fullmatch(r"(\d+) core, (\d+)x", name)
            bid = f"corpus_scaling/core={m.group(1)},noise={m.group(2)}" if m else None
            if bid not in idx_blocks:
                die(f"G1: S393's cell {name!r} of corpus scaling is no index of the loader's rows")
            c = blocks[bid]["judges"][MAIN]["pairs"]["single_pass - rlm_10"]
            idx_blocks.discard(bid)
            num(f"S cell {name} n", c["n_pairs"], k["n"], 0)
            num(f"S cell {name} single_pass", c["rate_first"], k["single_pass"])
            num(f"S cell {name} rlm_10", c["rate_second"], k["rlm_10"])
            num(f"S cell {name} sp_minus_rlm", c["diff"], k["sp_minus_rlm"])
        if idx_blocks:
            die(f"G1: S393's S1 and S2 hold no cell for {sorted(idx_blocks)}")
        # J1: the two judges on the answerable rows of both replications
        both = [(x, y) for exp in REPLICATIONS for x, y in data["_pairs"][exp].pairs if x.group == jl.ANSWERABLE]
        mine = j1(both)
        for f in ("units", "n_questions", "main_only", "second_only", "disagreements"):
            num(f"J1 {f}", mine[f], known["J1"][f], 0)
        for f in ("rate_main", "rate_second", "gap", "agreement", "kappa"):
            num(f"J1 {f}", mine[f], known["J1"][f])
        by_gen = Counter(S393_GENERATOR.get(x.generator) for x, _ in both)
        for g, n in known["J1"]["generators"].items():
            num(f"J1 generators {g}", by_gen[g], n, 0)
        text = S393_J1_TEXT.search(claims["J1"][S393_COLUMN]["value"])
        printed = (f"{100 * mine['rate_second']:.1f}", f"{100 * mine['rate_main']:.1f}", f"{100 * mine['agreement']:.1f}",
                   f"{mine['kappa']:.2f}")
        if not text or text.groups() != printed:
            die(f"G1: J1's printed sentence in {rel(S393_JSON)} does not give {printed} for the second judge's pass rate, "
                f"the main judge's, the agreement and kappa")
    except (KeyError, TypeError, AttributeError, ValueError) as e:
        die(f"G1: {rel(S393_JSON)} or a block of this script lacks a field the gate reads ({type(e).__name__}: {e})")

    def number(v) -> bool:
        return isinstance(v, numbers.Real) and not isinstance(v, (bool, np.bool_))

    worst = 0.0
    for what, got, want, tol, _ in checks:
        exact = tol == 0
        try:
            off = not number(got) or not number(want) or (got != want if exact else not abs(got - want) <= tol)
        except OverflowError:                            # an integer of S393's JSON too large to subtract from a float
            off = True
        if off:
            die(f"G1: {what} is {got!r} from the loader's rows and {want!r} in {rel(S393_JSON)}")
        if tol == TOL:
            worst = max(worst, abs(got - want))
    return {"file": rel(S393_JSON), "column": S393_COLUMN, "comparisons": len(checks),
            "comparisons_of_counts": sum(1 for c in checks if c[3] == 0),
            "comparisons_to_1e-9": sum(1 for c in checks if c[3] == TOL),
            "comparisons_at_two_decimals": sum(1 for c in checks if c[3] not in (0, TOL)),
            "comparisons_with_the_column": sum(1 for c in checks if not c[4]),
            "comparisons_with_e6_ten_group": sum(1 for c in checks if c[4]),
            "max_abs_diff_of_the_1e-9_comparisons": worst,
            "j1": {**mine, "printed": {"rate_second_pct": printed[0], "rate_main_pct": printed[1],
                                       "agreement_pct": printed[2], "kappa": printed[3]}},
            "passed": True}


def gate_g3(data: dict, blocks: dict) -> dict:
    """G3_BLOCK under the main judge a second time, with a resample matrix drawn again from the seed."""
    if G3_BLOCK not in blocks:
        die(f"G3: no block {G3_BLOCK}")
    first = blocks[G3_BLOCK]["judges"][MAIN]
    w = resample_counts(first["n_questions"])
    again = block_stats(block_rows(data, G3_BLOCK, MAIN), f"the block {G3_BLOCK} under the judge {MAIN}", w)
    same_w = bool(np.array_equal(w, counts_for(first["n_questions"])))
    off = [name for name, p in first["pairs"].items()
           if p["ci95"] != again["pairs"][name]["ci95"] or p["diff"] != again["pairs"][name]["diff"]]
    off_rates = [s for s, v in first["strategies"].items()
                 if v["question_bootstrap95"] != again["strategies"][s]["question_bootstrap95"]]
    if not same_w or off or off_rates:
        die(f"G3: a second run of {G3_BLOCK} with the seed {SEED} gives another resample matrix or other intervals "
            f"({len(off)} of {len(first['pairs'])} pairs and {len(off_rates)} of {len(first['strategies'])} strategies "
            "differ)")
    return {"block": G3_BLOCK, "judge": MAIN, "pairs_compared": len(first["pairs"]),
            "strategies_compared": len(first["strategies"]), "same_resample_matrix": same_w, "passed": True}


def exact_quantiles(n: int, up: int, down: int) -> list[float]:
    """The G5_LEVELS quantiles of the mean of n independent draws of +1, 0 and -1 with probabilities up / n,
    (n - up - down) / n and down / n. The distribution of the sum comes from n convolutions; a quantile is the
    smallest value whose cumulative probability reaches the level, less 1e-12 for the rounding of the sums."""
    one = np.array([down, n - up - down, up], dtype=float) / n          # the probabilities of -1, 0 and +1
    dist = np.array([1.0])
    for _ in range(n):
        dist = np.convolve(dist, one)                    # after i steps: the sums -i to +i
    cdf = np.cumsum(dist)
    return [(int(np.searchsorted(cdf, level - 1e-12)) - n) / n for level in G5_LEVELS]


def gathered_ratio(questions: list, idx: np.ndarray, num: Counter, den: Counter) -> list:
    """Per resample of idx (rows of places, each holding the position of the question drawn): the sum of num over
    the questions drawn, taken one by one, divided by the same sum of den; None where that sum of den is 0."""
    out = []
    for places in idx:
        drawn = [questions[j] for j in places]
        top, bottom = sum(num[q] for q in drawn), sum(den[q] for q in drawn)
        out.append(top / bottom if bottom else None)
    return out


def same_as_gathered(head: np.ndarray, want: list) -> bool:
    """The first resamples of the matrix form against the gathered values: == where there is a ratio, NaN where
    there is none."""
    return len(head) == len(want) and all(bool(np.isnan(g)) if x is None else bool(g == x) for g, x in zip(head, want))


def g3_block_gathered(data: dict, blocks: dict, gate: str) -> tuple:
    """For G5(b) and G6: the answerable rows of G3_BLOCK under the main judge as cells, the block's sorted questions
    and the first GATHERED rows of the index matrix, drawn again from the seed."""
    if G3_BLOCK not in blocks:
        die(f"{gate}: no block {G3_BLOCK}")
    ans = [r for r in block_rows(data, G3_BLOCK, MAIN) if r.group == jl.ANSWERABLE]
    questions = sorted({r.question_id for r in ans})
    return cells(ans), questions, resample_index(len(questions))[:GATHERED]


def g5_level() -> float:
    """G5(c): percentile_interval on the N_BOOT values 0, 1 / (N_BOOT - 1), ..., 1, every one kept. Under linear
    interpolation their quantile at a level is the level, so the two values returned must be G5_LEVELS to 1e-9.
    Returns the larger of the two distances."""
    got = percentile_interval(np.arange(N_BOOT) / (N_BOOT - 1), np.ones(N_BOOT, dtype=bool))
    off = max(abs(g - level) for g, level in zip(got, G5_LEVELS))
    if len(got) != len(G5_LEVELS) or not off <= 1e-9:
        die(f"G5: on the {N_BOOT:,} values 0 to 1 in equal steps, whose quantile at a level is the level under linear "
            f"interpolation, percentile_interval returns {got!r} and the levels of the gate are {list(G5_LEVELS)!r}, so "
            "its percentiles or its interpolation are not the ones the definitions state")
    return off


def g5_every_interval(data: dict, blocks: dict) -> tuple:
    """G5(d): ci95 of every pair of every block and judge a second time over all N_BOOT resamples. Per block and
    judge: the answerable rows as cells, the block's sorted questions, the index matrix of that number of questions
    (drawn again from the seed, once per number of questions). Per pair and question: the paired answers and the sum
    of first pass minus second pass, as integers. Per resample: the two sums over the questions drawn, by indexing
    through the index matrix. Each interval, taken with percentile_interval over the resamples that draw a paired
    answer, must equal (==) the stored ci95. Returns the number of pairs and how many of them have a paired set with
    fewer questions than the block."""
    drawn: dict = {}
    pairs = fewer = 0
    for bid, b in blocks.items():
        for judge, per in b["judges"].items():
            ans = [r for r in block_rows(data, bid, judge) if r.group == jl.ANSWERABLE]
            questions = sorted({r.question_id for r in ans})
            pos = {q: i for i, q in enumerate(questions)}
            if len(questions) not in drawn:
                drawn[len(questions)] = resample_index(len(questions))
            idx = drawn[len(questions)]
            by = cells(ans)
            for name, p in per["pairs"].items():
                x, y = by[p["first"]], by[p["second"]]
                d, m = np.zeros(len(questions), dtype=np.int64), np.zeros(len(questions), dtype=np.int64)
                for key in x.keys() & y.keys():
                    d[pos[key[1]]] += int(x[key]) - int(y[key])
                    m[pos[key[1]]] += 1
                top, bottom = d[idx].sum(axis=1), m[idx].sum(axis=1)
                ok = bottom > 0
                stat = np.full(N_BOOT, np.nan)
                stat[ok] = top[ok] / bottom[ok]
                again = percentile_interval(stat, ok) if ok.any() else None
                if again != p["ci95"]:
                    die(f"G5: in the block {bid} under {judge}, the interval of {name} is {p['ci95']!r}, and {again!r} when "
                        f"recomputed over the {N_BOOT:,} resamples of the block's {len(questions)} questions by indexing "
                        "through the index matrix")
                pairs += 1
                fewer += int((m > 0).sum()) < len(questions)
    return pairs, fewer


def gate_g5(data: dict, blocks: dict) -> dict:
    """The interval rule of a difference (module docstring, G5): (a) the exact bootstrap quantiles where the paired
    set is one answer per question of the block, (b) the resampled differences of G3_BLOCK by gathering, (c) the
    level and interpolation of percentile_interval on a known answer, (d) every interval a second time over all the
    resamples of the block's questions."""
    tested = equal = 0
    worst = 0.0
    for bid, b in blocks.items():
        for judge, per in b["judges"].items():
            if len(per["units"]) != 1:
                continue
            for name, p in per["pairs"].items():
                n = p["n_pairs"]
                if not n == p["n_questions"] == p["n_questions_resampled"]:
                    continue
                tested += 1
                for got, want, level in zip(p["ci95"], exact_quantiles(n, p["first_only"], p["second_only"]), G5_LEVELS):
                    away = abs(got - want)
                    if not away <= 1 / n + 1e-12:
                        die(f"G5: in the block {bid} under {judge}, the interval of {name} has the bound {got!r}, more "
                            f"than one step 1/{n} from the exact {100 * level:g}% quantile of the resampled difference, "
                            f"{want!r}")
                    equal += away <= 1e-12
                    worst = max(worst, away * n)
    if not tested:
        die("G5: no pair of a block with one unit has a paired set that holds every question of the block, so the "
            "exact quantiles test no interval")
    by, questions, idx = g3_block_gathered(data, blocks, "G5")
    first = blocks[G3_BLOCK]["judges"][MAIN]
    for name, p in first["pairs"].items():
        a, b = by[p["first"]], by[p["second"]]
        d, m = Counter(), Counter()
        for key in a.keys() & b.keys():
            d[key[1]] += int(a[key]) - int(b[key])
            m[key[1]] += 1
        if not same_as_gathered(p["_stat_head"], gathered_ratio(questions, idx, d, m)):
            die(f"G5: in the block {G3_BLOCK} under {MAIN}, the resampled differences of {name} that the interval was "
                f"computed from are not the ones gathered question by question over the first {len(idx)} resamples")
    level_off = g5_level()
    d_pairs, d_fewer = g5_every_interval(data, blocks)
    return {"a_pairs_tested": tested, "a_bounds_tested": 2 * tested, "a_bounds_equal_to_the_exact_quantile": int(equal),
            "a_largest_distance_in_steps": worst, "a_levels": list(G5_LEVELS),
            "b_block": G3_BLOCK, "b_judge": MAIN, "b_pairs": len(first["pairs"]), "b_resamples_per_pair": len(idx),
            "c_values": N_BOOT, "c_levels": list(G5_LEVELS), "c_largest_distance_from_a_level": level_off,
            "d_pairs": d_pairs, "d_resamples_per_pair": N_BOOT,
            "d_pairs_with_fewer_questions_than_the_block": int(d_fewer),
            "passed": True}


def gate_g6(data: dict, blocks: dict) -> dict:
    """The resampled pass rates of G3_BLOCK by gathering (module docstring, G6)."""
    by, questions, idx = g3_block_gathered(data, blocks, "G6")
    first = blocks[G3_BLOCK]["judges"][MAIN]
    if set(first["strategies"]) != set(by):
        die(f"G6: the block {G3_BLOCK} holds other strategies in its table than in its rows")
    for s, v in first["strategies"].items():
        passes, answers = Counter(), Counter()
        for (_, q), passed in by[s].items():
            passes[q] += int(passed)
            answers[q] += 1
        if not same_as_gathered(v["_stat_head"], gathered_ratio(questions, idx, passes, answers)):
            die(f"G6: in the block {G3_BLOCK} under {MAIN}, the resampled pass rates of {s} that the interval was "
                f"computed from are not the ones gathered question by question over the first {len(idx)} resamples")
    return {"block": G3_BLOCK, "judge": MAIN, "strategies": len(first["strategies"]), "resamples_per_strategy": len(idx),
            "passed": True}


def gate_g4(blocks: dict) -> dict:
    """The Wilson formula against scipy's on every (passes, answers) of the tables."""
    seen, worst = set(), 0.0
    for b in blocks.values():
        for per in b["judges"].values():
            for s in per["strategies"].values():
                seen.add((s["n_pass"], s["n_answers"]))
    for k, n in sorted(seen):
        ref = binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
        worst = max(worst, abs(wilson(k, n)[0] - ref.low), abs(wilson(k, n)[1] - ref.high))
    if not worst <= 1e-12:
        die(f"G4: the Wilson interval differs from scipy's by {worst}")
    return {"distinct_passes_and_answers": len(seen), "max_abs_diff": worst, "passed": True}


# ---- the focus table ---------------------------------------------------------------------------------------

def focus_table(blocks: dict) -> dict:
    """verified_pass minus multi_hop in every block and judge that holds both strategies, the blocks that do not, and
    counts of the rows by the sign of the difference and by where the interval lies: per experiment, level and judge
    (tally_by_level, whose blocks share no answer: build() refuses otherwise) and per judge over every row (tally,
    in which an answer is counted once per level of its experiment)."""
    name = f"{FOCUS[0]} - {FOCUS[1]}"
    rows, absent = [], []
    for bid, b in blocks.items():
        for judge, per in b["judges"].items():
            p = per["pairs"].get(name)
            if p is None:
                absent.append({"block": bid, "judge": judge, "strategies_absent": per["strategies_absent"]})
                continue
            two = b["two_judges"][name] if "two_judges" in b else None
            rows.append({"block": bid, "experiment": b["experiment"], "level": b["level"], "judge": judge,
                         "n_questions": p["n_questions"], "n_pairs": p["n_pairs"], "rate_first": p["rate_first"],
                         "rate_second": p["rate_second"], "diff": p["diff"], "ci95": p["ci95"],
                         "ci_includes_0": p["ci_includes_0"], "ci_bound_equals_0": p["ci_bound_equals_0"],
                         "ci_bound_within_one_step_of_0": p["ci_bound_within_one_step_of_0"],
                         "same_sign_under_the_two_judges": None if two is None else two["same_sign"]})

    def tally(sel: list) -> dict:
        return {"rows": len(sel), "diff_above_0": sum(r["diff"] > 0 for r in sel),
                "diff_below_0": sum(r["diff"] < 0 for r in sel), "diff_equal_0": sum(r["diff"] == 0 for r in sel),
                "interval_includes_0": sum(r["ci_includes_0"] for r in sel),
                "interval_above_0": sum(r["ci95"][0] > 0 for r in sel), "interval_below_0": sum(r["ci95"][1] < 0 for r in sel),
                "bound_within_one_step_of_0": sum(r["ci_bound_within_one_step_of_0"] for r in sel)}

    def signs(sel: list) -> dict:
        """Over rows of blocks with two judges; None for rows of blocks with one."""
        flags = [r["same_sign_under_the_two_judges"] for r in sel]
        if any(f is None for f in flags):
            return {"same_sign_under_the_two_judges": None, "other_sign_under_the_two_judges": None}
        return {"same_sign_under_the_two_judges": sum(flags), "other_sign_under_the_two_judges": sum(not f for f in flags)}

    judges = sorted({r["judge"] for r in rows}, key=(MAIN, SECOND).index)
    both = [r for r in rows if r["judge"] == MAIN and r["same_sign_under_the_two_judges"] is not None]
    by_level = []
    for e, lv, j in dict.fromkeys((r["experiment"], r["level"], r["judge"]) for r in rows):
        sel = [r for r in rows if (r["experiment"], r["level"], r["judge"]) == (e, lv, j)]
        by_level.append({"experiment": e, "level": lv, "judge": j, **tally(sel), **signs(sel)})
    return {"pair": name, "rows": rows, "blocks_without_the_pair": absent,
            "tally_by_level": by_level,
            "tally": {j: tally([r for r in rows if r["judge"] == j]) for j in judges},
            "blocks_with_two_judges": {"blocks": len(both), "same_sign": sum(r["same_sign_under_the_two_judges"] for r in both),
                                       "other_sign": sum(not r["same_sign_under_the_two_judges"] for r in both)}}


# ---- provenance --------------------------------------------------------------------------------------------

def inputs(data: dict) -> dict:
    """The files that give a row or a known number to this run, each with its sha256. Hashed here: the two key
    files, S388's record, the manifest, S393's JSON, the result files that hold a row of the selections, and the
    other result files of the same ledger folders (result_files_with_no_row_in_the_selections): the loader reads them
    for its completeness check (jl._check_complete) and joins their ledger rows, which are rows of other experiments
    of the folder or of arms the selections leave out, and they give no row to a table. The merged ledgers are not
    opened by this script: their sha256 is the one S388's record lists, and the loader refuses a ledger whose bytes
    have another (judged_ledger.py:25-28). Not listed: the other merged ledgers of S388's record, which the loader
    hashes in the same check and this run reads no row of."""
    rows = [r for name, e in data.items() if not name.startswith("_") for rs in e["rows"].values() for r in rs]
    used = sorted({(r.slug, r.judge) for r in rows})
    slugs = {slug for slug, _ in used}
    with_rows = {(r.label, r.tag) for r in rows}
    paths = jl._paths()                                  # (S374 label, file tag) -> result file: the loader's own table
    in_tables = sorted(Path(p) for k, p in paths.items() if k in with_rows)
    no_row = sorted(Path(p) for (label, tag), p in paths.items()
                    if jl.S388.LABEL_TO_SLUG[label] in slugs and (label, tag) not in with_rows)
    try:
        record = json.loads(jl.PROVENANCE.read_text())["outputs"]
        ledgers = {rel(jl.TREE / f"{slug}/{judge}.jsonl"): record[f"{slug}/{judge}.jsonl"]["sha256"] for slug, judge in used}
    except (OSError, ValueError, KeyError, TypeError) as e:
        die(f"{rel(jl.PROVENANCE)} does not list the sha256 of a merged ledger this run read ({type(e).__name__}: {e})")
    out = {}
    for group, files in (("keys", [jl.S373.KEY, jl.S373.AS_V1]), ("loader_record_and_manifest", [jl.PROVENANCE, jl.MANIFEST]),
                         ("known_numbers", [S393_JSON]), ("result_files_with_rows_in_the_selections", in_tables),
                         ("result_files_with_no_row_in_the_selections", no_row)):
        out[group] = {rel(p): sha_file(p) for p in files}
    out["merged_ledgers_as_listed_in_the_loaders_record"] = ledgers
    return out


# ---- the report --------------------------------------------------------------------------------------------

def pc(x: float) -> str:
    return f"{100 * x:.1f}%"


def pp(x: float) -> str:
    return f"{100 * x:+.1f}"


def dci(p: dict) -> str:
    return f"{pp(p['diff'])} ({pp(p['ci95'][0])} to {pp(p['ci95'][1])})"


def yes(v) -> str:
    return "n/a" if v is None else ("yes" if v else "no")


def inc(p: dict) -> str:
    """Whether a pair's interval includes 0, with a mark when one of its bounds is 0 or within one step of 0."""
    return yes(p["ci_includes_0"]) + (" (a bound is 0)" if p["ci_bound_equals_0"] else
                                      " (a bound is within one step of 0)" if p["ci_bound_within_one_step_of_0"] else "")


SHOWN = {"wilson95": "Wilson 95% interval", "question_bootstrap95": "Question-bootstrap 95% interval"}
LEVEL_TEXT = {"experiment": "whole experiment", "pooled": "pooled", "core size": "per core size", "index": "per index",
              "generator": "per generator", "draw": "per draw"}


def listed(names) -> str:
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def both(per: dict, get) -> str:
    """One value when every judge of the block gives the same, else each judge's."""
    vals = {j: get(p) for j, p in per.items()}
    if len(set(vals.values())) == 1:
        return f"{next(iter(vals.values())):,}"
    return ", ".join(f"{v:,} ({j})" for j, v in vals.items())


def md_block(head: str, bid: str, b: dict) -> list[str]:
    per = b["judges"]
    judges = list(per)
    first = per[MAIN]
    groups = "; ".join(f"{j}: " + ", ".join(f"{n:,} {g}" for g, n in per[j]["n_rows_by_group"].items()) for j in judges)
    out = [f"### {head} {b['title']}", "",
           f"Block `{bid}`. Rows of the loader's selection in the block, by group ({groups}). The tables are on the "
           f"{both(per, lambda p: p['n_answers'])} answers of the group answerable, on {both(per, lambda p: p['n_questions'])} "
           f"questions. Unit of pairing: {b['unit']}; the block holds {len(first['units'])}."
           + (f" No answer of {', '.join(first['strategies_absent'])}." if first["strategies_absent"] else "")
           + (" A strategy has at most one answer on a question."
              if all(p["answers_per_question_and_strategy_max"] == 1 for p in per.values()) else
              " A strategy has up to " + both(per, lambda p: p["answers_per_question_and_strategy_max"])
              + " answers on a question."), ""]
    kind = first["pass_rate_interval_shown"]             # the same under both judges: two_judges() refuses otherwise
    strategies = list(first["strategies"])               # likewise
    if len(judges) == 1:
        out += [f"| Strategy | Questions | Answers | Passes | Pass rate | {SHOWN[kind]} |", "|---|---:|---:|---:|---:|---|"]
        for s in strategies:
            v = first["strategies"][s]
            out.append(f"| {s} | {v['n_questions']} | {v['n_answers']:,} | {v['n_pass']:,} | {pc(v['pass_rate'])} | "
                       f"{pc(v[kind][0])} to {pc(v[kind][1])} |")
        out += ["", "| Pair (first minus second) | Questions | Pairs | First | Second | Difference, pp (95% interval) | "
                "Interval includes 0 |", "|---|---:|---:|---:|---:|---|---|"]
        for name, p in first["pairs"].items():
            out.append(f"| {p['first']} minus {p['second']} | {p['n_questions']} | {p['n_pairs']:,} | {pc(p['rate_first'])} | "
                       f"{pc(p['rate_second'])} | {dci(p)} | {inc(p)} |")
        return out + [""]
    out += ["| Strategy | Questions | Answers | " + " | ".join(f"{j}: passes | {j}: pass rate ({SHOWN[kind]})" for j in judges)
            + " |", "|---|---:|---:|" + "---:|---|" * len(judges)]
    for s in strategies:
        sub = {j: per[j]["strategies"][s] for j in judges}
        out.append(f"| {s} | {both(sub, lambda v: v['n_questions'])} | {both(sub, lambda v: v['n_answers'])} | "
                   + " | ".join(f"{v['n_pass']:,} | {pc(v['pass_rate'])} ({pc(v[kind][0])} to {pc(v[kind][1])})"
                                for v in sub.values()) + " |")
    out += ["", "| Pair (first minus second) | Questions | Pairs | "
            + " | ".join(f"{j}: first, second | {j}: difference, pp (95% interval) | {j}: 0 in interval" for j in judges)
            + " | Same sign |", "|---|---:|---:|" + "---|---|---|" * len(judges) + "---|"]
    for name in first["pairs"]:
        sub = {j: per[j]["pairs"][name] for j in judges}
        p = first["pairs"][name]
        out.append(f"| {p['first']} minus {p['second']} | {both(sub, lambda v: v['n_questions'])} | "
                   f"{both(sub, lambda v: v['n_pairs'])} | "
                   + " | ".join(f"{pc(v['rate_first'])}, {pc(v['rate_second'])} | {dci(v)} | {inc(v)}"
                                for v in sub.values())
                   + f" | {yes(b['two_judges'][name]['same_sign'])} |")
    return out + [""]


def report(prov: dict, blocks: dict, focus: dict, gates: dict, counts: dict, data: dict) -> list[str]:
    models: dict = {}
    for b in blocks.values():
        for j, ms in b["judge_models"].items():
            models[j] = sorted(set(models.get(j, [])) | set(ms))
    by_exp = {name: [bid for bid, b in blocks.items() if b["experiment"] == name] for name in TITLE}
    strat = {name: blocks[by_exp[name][0]]["judges"][MAIN] for name in TITLE}
    six = [name for name in TITLE if not strat[name]["strategies_absent"]]
    fewer = [name for name in TITLE if strat[name]["strategies_absent"]]
    with_second = [name for name in TITLE if SECOND in blocks[by_exp[name][0]]["judges"]]
    listed_too = [name for name in with_second if name not in REPLICATIONS]     # exp04, corpus scaling: load(), has_second
    alt = counts["resampling_the_paired_set"]
    g1, g2, g3, g4, g5, g6 = (gates[g] for g in ("G1", "G2", "G3", "G4", "G5", "G6"))
    key = prov["key"]
    shown = counts["tables_by_interval_shown_beside_a_pass_rate"]
    md = ["# S407: pass rates per generation strategy and every pairwise difference, ground truth v2.4", "",
          f"Computed by {prov['script']} (sha256 {prov['script_sha256'][:12]}) with `{COMMAND}`. Every judge score is read "
          f"through scripts/judged_ledger.py, on the key {jl.S373.KEY.relative_to(ROOT)} (sha256 {key['sha256'][:12]}; v1-format "
          f"key sha256 {key['v1_format_sha256'][:12]}). The JSON's provenance block lists, with its sha256, every file that "
          "gives a row or a known number to this run; for a merged ledger that sha256 is the one S388's record lists, which "
          "the loader checks against the ledger's bytes. The loader also hashes the other merged ledgers of S388's record in "
          "its own check. "
          "Judges, under the model names the ledgers hold: " + "; ".join(f"{j} = {', '.join(ms)}" for j, ms in models.items())
          + f". {MAIN} is the main judge (D8) and scores every block. {SECOND} is the second judge: the script requires its "
          f"rows for {listed(REPLICATIONS)}, which the loader returns from a complete ledger or not at all"
          + (f", and the loader lists a complete ledger of it for {listed(n.replace('_', ' ') for n in listed_too)} as well"
             if listed_too else "")
          + f". The blocks of {listed(n.replace('_', ' ') for n in with_second)} carry both judges.", "",
          f"A block is a set of answers of one experiment: exp04; corpus scaling pooled over its indexes, per core size and per "
          f"index; rep2 pooled and per generator; rep5 pooled, per generator and per draw. There are {counts['blocks']} blocks "
          f"and {counts['block_and_judge_tables']} block-and-judge tables. The blocks overlap: a pooled block holds the answers "
          "of the blocks under it.", "",
          f"Sections A to E are on the group answerable. An answer passes when its correctness score is {jl.PASS_AT} or more "
          "(the loader's field passed). The ten false-premise questions (group refutation) enter no rate, difference or "
          "interval; section F gives their counts. The rows of the group not_answerable enter no table; each block states "
          "how many it holds.", "",
          f"Resamples. Every interval of the tables that is not a Wilson interval is the {PCT[0]:g}th to {PCT[1]:g}th percentile of a "
          f"statistic over {N_BOOT:,} resamples of the block's questions, drawn with replacement; the block's questions are "
          f"the distinct questions with an answer of the group answerable in the block. The seed is {SEED}: one resample matrix per number "
          f"of questions n, numpy.random.default_rng({SEED}).integers(0, n, size=({N_BOOT}, n)), drawn once and used by every "
          "block, judge, pair and strategy with that n (the matrix that seeding again for each block would give).", "",
          "Per strategy: the distinct questions with an answer of the strategy, its answers, its passes, the pass rate and "
          "a 95% interval of the pass rate. Two intervals are computed for every pass rate, and the JSON holds both. The "
          "Wilson interval of passes out of answers (no continuity correction) treats the answers as independent. The "
          "question-bootstrap interval is over the block's resamples: a question drawn several times brings all its "
          "answers of the strategy that many times, and the pass rate of a resample is the passes drawn divided by the "
          f"answers drawn. The tables show the question-bootstrap interval in the {shown['question_bootstrap95']} "
          "block-and-judge tables whose block holds more than one answer of a strategy on a question (several indexes, "
          "generators or draws), because those answers share questions and the Wilson interval takes no account of that, "
          f"and the Wilson interval in the {shown['wilson95']} tables with at most one answer per question and strategy. "
          "Each block states which of the two cases it is, and the heading of the column names the interval.", "",
          "Per pair of strategies, written first minus second in the order " + ", ".join(STRATEGIES) + " (the order fixes "
          "the sign and ranks nothing): the paired set is every (unit, question) on which both strategies have a scored "
          "answer, the unit being the index in corpus scaling, the generator and draw in the replications and the "
          "generator in exp04 (one run). The difference is the first strategy's pass rate minus the second's over the paired set, in "
          "percentage points. Its interval is over the block's resamples: a question drawn "
          "several times brings all its paired answers that many times. Questions is the number of questions in the "
          "paired set, Pairs the number of (unit, question) in it. The questions drawn are the block's in every case: in "
          f"{counts['pairs_with_fewer_questions_than_the_block']} of the {counts['pair_intervals']:,} pairs the paired set "
          "holds fewer questions than the block, because on some questions the two strategies have no scored answer in "
          "the same unit."
          + (" For those pairs the JSON also holds the interval from resamples of the paired set's own "
             f"questions (same seed): a bound moves by at most {100 * alt['largest_change_of_a_bound']:.1f} percentage points and "
             f"the inclusion of 0 changes for {alt['intervals_whose_inclusion_of_0_changes']} of them." if alt["pairs"] else "")
          + " A resample that draws no paired answer of a pair, or no answer of a strategy, is left out of the percentiles of "
          f"that interval: {counts['resamples_undefined']:,} resamples over the {counts['pair_intervals']:,} pairs and "
          f"{counts['pass_rate_resamples_undefined']:,} over the {counts['pass_rates']:,} pass rates.", "",
          "Interval includes 0 is lower <= 0 <= upper on the unrounded bounds, so a bound equal to 0 counts as including 0. "
          f"The bounds are estimates from the {N_BOOT:,} resamples, so the flag of an interval with a bound at or within one "
          "step of 0 can change with the seed; a step is 1 / Pairs. "
          f"{counts['intervals_with_a_bound_within_one_step_of_0']} intervals have such a bound, "
          f"{counts['intervals_with_a_bound_equal_to_0']} of them a bound equal to 0, and each is marked. The marks are no "
          "full list of the flags that can change: in a block with several units, where a question drawn brings several "
          "pairs, a flag can also change when both bounds are farther than one step from 0, and no field marks such an "
          "interval.", "",
          f"The intervals are not adjusted for multiplicity. {counts['pair_intervals']:,} intervals of a difference are shown: "
          f"15 pairs in each of the {counts['tables_with_15_pairs']} block-and-judge tables of "
          + listed(n.replace("_", " ") for n in six) + " (six strategies)"
          + "".join(f", and {len(strat[name]['pairs'])} pairs in each of the "
                    f"{sum(len(blocks[bid]['judges']) for bid in by_exp[name])} tables of {name}, whose rows hold answers of "
                    f"{listed(strat[name]['strategies'])} and none of {listed(strat[name]['strategies_absent'])}"
                    for name in fewer)
          + ". No model is fitted and no test is run: the paper's model-based statistics are the work of other scripts. This "
          "file states numbers and orders no strategies.", "",
          "The ten false-premise questions are a group of their own, scored for correctness against the refutation (D5): "
          "the group and the scoring that D11 rules for the paper (notes/DECISIONS_2026-10-13.md:77-82). Section F gives "
          "their counts only, with no rate and no interval, and they are in no table of sections A to E. The script uses "
          "no concept recall and no calibration.", "",
          "Gates passed before anything was written. "
          f"G1: {g1['comparisons']} values of {g1['file'].split('/')[-1]} ({g1['comparisons_with_the_column']} from its "
          "devstral column on this key, claims E1 to E6, R1 to R3, S1, S2 and J1, and "
          f"{g1['comparisons_with_e6_ten_group']} from E6's ten_group, which sits beside that column and holds the counts of "
          f"the ten) recomputed from the loader's rows: {g1['comparisons_of_counts']} counts equal, "
          f"{g1['comparisons_to_1e-9']} rates and differences within {g1['max_abs_diff_of_the_1e-9_comparisons']:.1e}, "
          f"{g1['comparisons_at_two_decimals']} percentages of R1 at the two decimals stored; J1 on {g1['j1']['units']:,} "
          f"answerable answers of the two replications: agreement {g1['j1']['printed']['agreement_pct']}%, kappa "
          f"{g1['j1']['printed']['kappa']}, pass rates {g1['j1']['printed']['rate_main_pct']}% ({MAIN}) and "
          f"{g1['j1']['printed']['rate_second_pct']}% ({SECOND}), equal to its printed sentence. "
          f"G2: the counts of the loader's rows equal the expected ones: exp04 {g2['exp04_answerable']:,} answerable rows "
          "(typed in the script and equal to the loader's table EXPECTED); corpus scaling "
          f"{g2['corpus_scaling_rows']:,} rows, equal to the count the script derives from that table, of which "
          f"{g2['corpus_scaling_rows_exp05']:,} are rows of exp05 and {g2['corpus_scaling_rows_s314']:,} rows of the S314 "
          f"rerun, which are all the verified_pass rows; rep2 {g2['rep2_answerable']:,} and rep5 "
          f"{g2['rep5_answerable']:,} answerable rows in the arm reported under each judge (typed in the script), "
          "the two judges on the same ledger keys. "
          f"G3: the block {g3['block']} under {g3['judge']} computed a second time from the seed: the same resample matrix, "
          f"the same {g3['pairs_compared']} intervals of a difference and the same {g3['strategies_compared']} "
          "question-bootstrap intervals of a pass rate. "
          f"G4: the Wilson formula equals scipy's on the {g4['distinct_passes_and_answers']} distinct (passes, answers) of "
          f"the tables, to {g4['max_abs_diff']:.1e}. "
          f"G5, the interval of a difference, in four parts. (a) In the {g5['a_pairs_tested']} pairs of a block with one unit "
          "whose paired set holds every question of the block, the resampled difference is the mean of n independent draws "
          "of +1, 0 and -1, n being the number of pairs, and its exact distribution is computed by convolution: each of the "
          f"{g5['a_bounds_tested']} bounds lies within one step (1 / n) of its exact quantile, {100 * G5_LEVELS[0]:g}% for "
          f"a lower bound and {100 * G5_LEVELS[1]:g}% for an upper one, {g5['a_bounds_equal_to_the_exact_quantile']} of "
          f"them on it; the largest distance is {g5['a_largest_distance_in_steps']:.2f} steps. (b) In the block "
          f"{g5['b_block']} under "
          f"{g5['b_judge']}, the resampled difference of each of the {g5['b_pairs']} pairs over the first "
          f"{g5['b_resamples_per_pair']} resamples, recomputed from the block's rows by gathering the questions drawn one by "
          "one, equals the values the interval was computed from. "
          f"(c) On the {g5['c_values']:,} values 0 to 1 in equal steps, whose quantile at a level is the level under linear "
          "interpolation, the function that takes the percentiles of every resampling interval of the script returns "
          f"{g5['c_levels'][0]:g} and {g5['c_levels'][1]:g} "
          + ("exactly" if g5["c_largest_distance_from_a_level"] == 0
             else f"to within {g5['c_largest_distance_from_a_level']:.1e}") + " (the gate allows a distance of 1e-9). "
          f"(d) Each of the {g5['d_pairs']:,} intervals of a difference, in every block and under every judge, recomputed "
          f"from the block's rows over all {g5['d_resamples_per_pair']:,} resamples by indexing through the index matrix of "
          "the block's questions (drawn again from the seed; the sums of a resample taken as integers), equals the "
          f"stored one. In {g5['d_pairs_with_fewer_questions_than_the_block']} of these pairs the paired set holds fewer "
          "questions than the block, and the questions this part draws are the block's. "
          f"G6: in the block {g6['block']} under {g6['judge']}, the resampled pass rate of each of the {g6['strategies']} "
          f"strategies over the first {g6['resamples_per_strategy']} resamples, recomputed by the gathering of part (b) of "
          "G5, equals the values the question-bootstrap interval was computed from.", "",
          "Not read by a gate. The list holds the cases known when the script was written and is no statement that "
          "there is no other. In G2 the total of corpus scaling is compared with the count derived from the loader's "
          "table, and each of its two parts (the rows of exp05, the rows of the S314 rerun) with the number of rows of "
          "the loader's own selection: no expected count is compared with a part, and the derived count does not depend "
          "on the out-of-scope rows of the S314 rerun that the table lists, which the derivation adds and subtracts. No "
          "gate recomputes the question-bootstrap interval of a pass rate itself: G6 compares the resampled pass rates, "
          "and part (c) of G5 tests the function that takes their percentiles, so an interval taken from those pass "
          "rates by other code would pass. No gate recomputes, from the bounds of an interval, the flag Interval includes "
          "0 or its two marks (a bound equal to 0, a bound within one step of 0), and none reads which of the two "
          "intervals a table shows beside a pass rate; the script refuses only a block whose two judges would show two "
          "kinds.", ""]

    # A
    name = f"{FOCUS[0]} minus {FOCUS[1]}"
    md += [f"## A. {name} in every block", "",
           f"The pair of R3 (notes/DECISIONS_2026-10-13.md:59-61) in each of the {len(focus['rows'])} block-and-judge tables "
           f"that hold both strategies: questions and (unit, question) pairs of the paired set, the two pass rates over it, "
           "the difference in percentage points with its interval, whether the interval includes 0 and, in the blocks "
           "with two judges, whether the two judges' differences have the same sign.", "",
           f"| Block | Judge | Questions | Pairs | {FOCUS[0]} | {FOCUS[1]} | Difference, pp (95% interval) | "
           "Interval includes 0 | Same sign under the two judges |", "|---|---|---:|---:|---:|---:|---|---|---|"]
    for r in focus["rows"]:
        md.append(f"| {r['block']} | {r['judge']} | {r['n_questions']} | {r['n_pairs']:,} | {pc(r['rate_first'])} | "
                  f"{pc(r['rate_second'])} | {dci(r)} | {inc(r)} | "
                  + ("one judge" if r["same_sign_under_the_two_judges"] is None else yes(r["same_sign_under_the_two_judges"])) + " |")
    judges_of: dict = {}                                 # experiment -> the judges with a row in the per-level table
    for t in focus["tally_by_level"]:
        judges_of.setdefault(t["experiment"], set()).add(t["judge"])
    twice = [e.replace("_", " ") for e, js in judges_of.items() if len(js) > 1]
    md += ["", "Counts of the rows above per experiment, level and judge. The blocks of one level of an experiment share no "
           "answer, so no answer is counted twice within a row of the next table. The levels of an experiment hold the same "
           "answers, so a sum over the rows of the next table would count an answer once per level"
           + (f", and for {listed(twice)} once per judge as well" if twice else "")
           + "; the table gives no such sum.", "",
           "| Experiment | Level | Judge | Blocks | Difference above 0 | Difference below 0 | Difference equal to 0 | "
           "Interval includes 0 | Interval above 0 | Interval below 0 | A bound at or within one step of 0 | "
           "Same sign under the two judges |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for t in focus["tally_by_level"]:
        same = t["same_sign_under_the_two_judges"]
        md.append(f"| {t['experiment'].replace('_', ' ')} | {LEVEL_TEXT[t['level']]} | {t['judge']} | {t['rows']} | "
                  f"{t['diff_above_0']} | {t['diff_below_0']} | {t['diff_equal_0']} | {t['interval_includes_0']} | "
                  f"{t['interval_above_0']} | {t['interval_below_0']} | {t['bound_within_one_step_of_0']} | "
                  + ("one judge" if same is None else f"{same} of {t['rows']}") + " |")
    md.append("")
    if focus["blocks_without_the_pair"]:
        ab = focus["blocks_without_the_pair"]
        md += [f"{len(ab)} block-and-judge tables have no row here, because they hold no answer of one of the two "
               "strategies: " + ", ".join(sorted({a["block"] for a in ab})) + ".", ""]

    # B to E
    letters = dict(zip(TITLE, "BCDE"))
    for exp, title in TITLE.items():
        md += [f"## {letters[exp]}. {title}", "",
               "The loader's statement of the rows it kept and left out, which holds for every block of this section "
               "(each block is a part of these rows):", ""]
        md += [f"- {what}: {text}" for what, text in data[exp]["statements"].items()]
        md.append("")
        for i, bid in enumerate(by_exp[exp], 1):
            md += md_block(f"{letters[exp]}{i}.", bid, blocks[bid])

    # F
    md += ["## F. The ten false-premise questions: counts", "",
           f"Per block and judge: how many of the ten (OOD_041 to OOD_050, group refutation) have an answer in the block, and "
           f"per strategy the passes out of the answers (correctness of {jl.PASS_AT} or more against the refutation, D5). In "
           "corpus scaling a row on one of the ten is in the loader's selection only where the question's min_core in the key "
           "is at most the core size of the index (Q55). Counts only: no rate, no interval, and these answers are in no table "
           "of sections A to E.", "",
           "| Block | Judge | Questions of the ten | " + " | ".join(STRATEGIES) + " |", "|---|---|---:|" + "---|" * len(STRATEGIES)]
    for bid, b in blocks.items():
        for j, per in b["judges"].items():
            t = per["the_ten"]
            md.append(f"| {bid} | {j} | {t['n_questions']} | "
                      + " | ".join(f"{t['strategies'][s]['n_pass']} of {t['strategies'][s]['n_answers']}" if s in t["strategies"]
                                   else "no answer" for s in STRATEGIES) + " |")
    return md


def clean(o, where: str = "the output"):
    """JSON without numpy types or the arrays and sets the statistics carry (keys that start with "_"). Refused: a
    number that is NaN or infinite, with the place it sits at."""
    if isinstance(o, dict):
        return {str(k): clean(v, f"{where}[{str(k)!r}]") for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [clean(v, f"{where}[{i}]") for i, v in enumerate(o)]
    if isinstance(o, (np.floating, float)):
        if not math.isfinite(o):
            die(f"{where} is {float(o)!r}, and the outputs hold finite numbers only")
        return float(o)
    if isinstance(o, (np.integer, np.bool_)):
        return o.item()
    return o


def write_outputs(texts: dict) -> None:
    """texts: output path -> its whole text, built before this call. Each text is written to <name>.tmp beside its
    file, and the files are renamed onto their names, in the order of texts, after every one is written. A failure
    is a refusal that names the file; the temporary files still there are removed. A file renamed before the
    failure stays: when a later rename fails, the outputs renamed so far are this run's and the others are the
    earlier ones."""
    tmp = {path: path.with_name(path.name + ".tmp") for path in texts}
    at = next(iter(texts))
    try:
        for path, text in texts.items():
            at = path
            tmp[path].write_text(text, encoding="utf-8")
        for path in texts:
            at = path
            os.replace(tmp[path], path)
    except OSError as e:
        for t in tmp.values():
            try:
                t.unlink(missing_ok=True)
            except OSError:
                pass
        die(f"cannot write {rel(at)} ({type(e).__name__}: {e})")


def main() -> int:
    t0 = time.time()
    script = Path(__file__).resolve()
    script_sha = sha_file(script)                        # the code that computes, read before it runs

    def step(msg: str) -> None:
        print(f"[{time.time() - t0:5.1f} s] {msg}", flush=True)

    if not S393_JSON.is_file():
        die(f"input file not found: {rel(S393_JSON)}")
    data = load()
    g2 = data["_g2"]
    step(f"G2 passed: exp04 {g2['exp04_answerable']:,} answerable rows; corpus scaling {g2['corpus_scaling_rows']:,} rows "
         f"(the count derived from jl.EXPECTED), its {g2['corpus_scaling_rows_s314']:,} verified_pass rows all of the S314 "
         f"rerun; rep2 {g2['rep2_answerable']:,} and rep5 {g2['rep5_answerable']:,} answerable rows under each judge")
    blocks = build(data)
    step(f"{len(blocks)} blocks computed")
    g1 = gate_g1(data, blocks)
    step(f"G1 passed: {g1['comparisons']} values of {S393_JSON.name} reproduced ({g1['comparisons_of_counts']} counts equal, "
         f"{g1['comparisons_to_1e-9']} within {g1['max_abs_diff_of_the_1e-9_comparisons']:.1e}, "
         f"{g1['comparisons_at_two_decimals']} at two decimals); J1 agreement {g1['j1']['printed']['agreement_pct']}%, kappa "
         f"{g1['j1']['printed']['kappa']}, pass rates {g1['j1']['printed']['rate_main_pct']}% and "
         f"{g1['j1']['printed']['rate_second_pct']}% on {g1['j1']['units']:,} answers")
    g3 = gate_g3(data, blocks)
    step(f"G3 passed: {G3_BLOCK} under {MAIN} a second time from the seed {SEED}: the same {g3['pairs_compared']} intervals "
         f"of a difference and the same {g3['strategies_compared']} of a pass rate")
    g4 = gate_g4(blocks)
    step(f"G4 passed: Wilson equals scipy's on {g4['distinct_passes_and_answers']} (passes, answers), to {g4['max_abs_diff']:.1e}")
    g5 = gate_g5(data, blocks)
    step(f"G5 passed: (a) {g5['a_bounds_tested']} bounds of {g5['a_pairs_tested']} pairs within one step of the exact "
         f"bootstrap quantile ({g5['a_bounds_equal_to_the_exact_quantile']} on it, largest distance "
         f"{g5['a_largest_distance_in_steps']:.2f} steps); (b) {G3_BLOCK} under {MAIN}: {g5['b_pairs']} pairs, the first "
         f"{g5['b_resamples_per_pair']} resampled differences equal to the gathered ones; (c) percentile_interval on "
         f"{g5['c_values']:,} values 0 to 1 at a distance of {g5['c_largest_distance_from_a_level']:.1e} from "
         f"{g5['c_levels'][0]:g} and {g5['c_levels'][1]:g}; (d) {g5['d_pairs']:,} intervals equal when recomputed over all "
         f"{g5['d_resamples_per_pair']:,} resamples of the block's questions, "
         f"{g5['d_pairs_with_fewer_questions_than_the_block']} of them of a pair with fewer questions than the block")
    g6 = gate_g6(data, blocks)
    step(f"G6 passed: {G3_BLOCK} under {MAIN}: {g6['strategies']} strategies, the first {g6['resamples_per_strategy']} "
         "resampled pass rates equal to the gathered ones")
    gates = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6}
    focus = focus_table(blocks)
    tables = [(b["experiment"], len(per["pairs"]), per) for b in blocks.values() for per in b["judges"].values()]
    n_pairs = {exp: sorted({n for e, n, _ in tables if e == exp}) for exp in TITLE}
    if any(len(v) != 1 for v in n_pairs.values()):
        die(f"the tables of one experiment hold different numbers of pairs ({n_pairs}), which the report's sentence on "
            "multiplicity does not cover")
    counts = {"blocks": len(blocks), "block_and_judge_tables": len(tables),
              "pair_intervals": sum(n for _, n, _ in tables),
              "tables_with_15_pairs": sum(n == 15 for _, n, _ in tables),
              "tables_with_fewer_pairs": sum(n != 15 for _, n, _ in tables),
              "pairs_per_table": {exp: v[0] for exp, v in n_pairs.items()},
              "tables": {exp: sum(e == exp for e, _, _ in tables) for exp in TITLE}}
    every = [p for _, _, per in tables for p in per["pairs"].values()]
    rates = [v for _, _, per in tables for v in per["strategies"].values()]
    counts.update({"intervals_including_0": sum(p["ci_includes_0"] for p in every),
                   "intervals_with_a_bound_equal_to_0": sum(p["ci_bound_equals_0"] for p in every),
                   "pairs_with_fewer_questions_than_the_block": sum(p["n_questions"] < p["n_questions_resampled"] for p in every),
                   "resamples_undefined": sum(p["resamples_undefined"] for p in every)})
    fewer = [p for p in every if p["ci95_resampling_the_paired_set"] is not None]
    if len(fewer) != counts["pairs_with_fewer_questions_than_the_block"]:
        die("the pairs with a second interval are not the pairs whose paired set holds fewer questions than the block")
    counts["resampling_the_paired_set"] = {
        "pairs": len(fewer),
        "largest_change_of_a_bound": max((abs(a - b) for p in fewer for a, b in zip(p["ci95"], p["ci95_resampling_the_paired_set"])),
                                         default=None),
        "intervals_whose_inclusion_of_0_changes": sum(
            p["ci_includes_0"] != (p["ci95_resampling_the_paired_set"][0] <= 0.0 <= p["ci95_resampling_the_paired_set"][1])
            for p in fewer)}
    counts.update({"intervals_with_a_bound_within_one_step_of_0": sum(p["ci_bound_within_one_step_of_0"] for p in every),
                   "pass_rates": len(rates),
                   "pass_rate_resamples_undefined": sum(v["question_bootstrap_resamples_undefined"] for v in rates),
                   "tables_by_interval_shown_beside_a_pass_rate": {
                       kind: sum(per["pass_rate_interval_shown"] == kind for _, _, per in tables) for kind in SHOWN}})
    modules = sorted({Path(m.__file__).resolve() for m in list(sys.modules.values())
                      if getattr(m, "__file__", None) and HERE in Path(m.__file__).resolve().parents} - {script})
    prov = {"script": str(script.relative_to(ROOT)), "script_sha256": script_sha, "command": COMMAND,
            "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "machine": platform.node(),
            "key": {"file": rel(jl.S373.KEY), "sha256": sha_file(jl.S373.KEY), "v1_format_file": rel(jl.S373.AS_V1),
                    "v1_format_sha256": sha_file(jl.S373.AS_V1), "key_scope_KEY_SHA256": key_scope.KEY_SHA256},
            "inputs_sha256": inputs(data),
            "imported_modules_sha256": {rel(p): sha_file(p) for p in modules},
            "seed": SEED, "resamples": N_BOOT, "percentiles": list(PCT), "tolerance": TOL, "gates": gates}
    resamples = (f"{N_BOOT} resamples of the block's sorted questions, drawn with replacement: one resample matrix per "
                 f"number of questions n, numpy.random.default_rng({SEED}).integers(0, n, size=({N_BOOT}, n)), drawn once "
                 "and used by every block, judge, pair and strategy with that n (the matrix that seeding again for each "
                 "block would give)")
    definitions = {
        "judges": {"main": MAIN, "second": SECOND},
        "group": "tables on the group answerable; the ten (group refutation) as counts under the_ten; not_answerable in no table",
        "pass": f"Row.passed of scripts/judged_ledger.py: score >= {jl.PASS_AT} on the group's dimension",
        "strategies": list(STRATEGIES),
        "pair": "'first - second', first earlier in strategies; diff = rate_first - rate_second over the paired set, the "
                "(unit, question) on which both strategies have a row",
        "unit": UNIT_TEXT,
        "resamples": resamples,
        "wilson95": "Wilson 95% interval of n_pass out of n_answers, no continuity correction; treats answers as independent",
        "question_bootstrap95": f"{PCT[0]:g}th and {PCT[1]:g}th percentiles (numpy.percentile, linear interpolation) of the "
                                "pass rate over the resamples: a question drawn c times brings each of its answers of the "
                                "strategy c times, and the pass rate of a resample is the passes drawn divided by the "
                                "answers drawn; a resample with no answer of the strategy is left out "
                                "(question_bootstrap_resamples_undefined)",
        "pass_rate_interval_shown": "the interval the .md prints beside the pass rates of a table: question_bootstrap95 when "
                                    "answers_per_question_and_strategy_max is above 1, wilson95 when it is 1; both are "
                                    "stored for every strategy. answers_per_question_max, per strategy: the largest number "
                                    "of its answers on one question in the block",
        "ci95": f"{PCT[0]:g}th and {PCT[1]:g}th percentiles (numpy.percentile, linear interpolation) of diff over the "
                "resamples: a question drawn c times brings each of its paired answers c times; a resample with no paired "
                "answer is left out (resamples_undefined)",
        "ci_includes_0": "ci95[0] <= 0 <= ci95[1]; ci_bound_equals_0: ci95[0] == 0 or ci95[1] == 0; "
                         "ci_bound_within_one_step_of_0: abs(ci95[0]) <= 1 / n_pairs or abs(ci95[1]) <= 1 / n_pairs, a "
                         "bound equal to 0 included. The bounds are estimates from the resamples, and ci_includes_0 of an "
                         "interval with that mark can change with the seed. The mark is no full list of such intervals: "
                         "in a block with several units ci_includes_0 can also change when both bounds are farther than "
                         "one step from 0, and no field marks that",
        "n_questions": "of a pair: the questions of its paired set; n_questions_resampled: the block's questions, which the "
                       "resamples draw from",
        "ci95_resampling_the_paired_set": "for a pair whose paired set holds fewer questions than the block: the same "
                                          "percentiles over resamples of the paired set's own sorted questions (the matrix "
                                          "of that number of questions, same seed and call); null for the other pairs, "
                                          "where the two readings are one",
        "two_judges": "per pair of a block with two judges: each judge's diff, its sign (-1, 0, 1), same_sign, same_paired_set",
        "verified_pass_minus_multi_hop": "rows: the pair in every block and judge that holds it. tally_by_level: counts of "
                                         "those rows per experiment, level and judge; the blocks of one level share no "
                                         "answer. tally and blocks_with_two_judges: counts over every row of a judge, in "
                                         "which an answer is counted once per level of its experiment",
        "multiplicity": "no interval is adjusted; no model, no test",
        "rates": "fractions of 1 in this file; the .md prints percentages and percentage points"}
    md = report(prov, blocks, focus, gates, counts, data)
    try:
        json_text = json.dumps(clean({"provenance": prov, "definitions": definitions, "counts": counts,
                                      "verified_pass_minus_multi_hop": focus, "blocks": blocks}),
                               indent=1, allow_nan=False) + "\n"
    except (TypeError, ValueError) as e:
        die(f"the output cannot be written as JSON ({type(e).__name__}: {e})")
    write_outputs({OUT_JSON: json_text, OUT_MD: "\n".join(md).rstrip("\n") + "\n"})
    step(f"written {rel(OUT_JSON)} and {rel(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
