#!/usr/bin/env python3
"""S511 - G2, the matched-budget arm, against single pass and the RLMs: does single pass given RLM-10's token budget
close RLM-10's lead on the many-paper questions?

WHY. Valerio approved A1 (30 October): analyse G2's judge rows now. The findings review of 30 October
(findings/recompute/findings_review_2026-10-30/report.json, entries M01 and M02) found that the RLM loses to single
pass on the 60 one-paper questions and wins on the 26 many-paper ones (M01), and that the RLM's many-paper lead may
come from reading more passages, not from searching in turns (M02). M02 could not say whether G2 also closes the
judge's gap: "G2's judge rows are on the Studio, not on this laptop". This script reads them. If single pass given
the RLM's budget (G2) closes most of the many-paper gap between single pass and RLM-10, the lead is a passage-budget
effect. Exploratory phase: the data are reported as they are; no analysis rule is changed or proposed.

G2'S DESIGN, as decided before its data.
  D36 (experiments/README.md:60): "a matched-budget arm joins the Figure 2 re-run".
  D51 (experiments/README.md:90-91): "the matched-budget arm is single pass given more passages until its input
      tokens per question match RLM-10's median; one call, same model."
  D75 Q79 to Q81 (experiments/runner/matched_budget.py:12-40): per question, the target is the median input tokens of
      that question's own RLM-10 answers (its draws); an RLM-10 answer that stores an error (call_error) is not a
      source; top_k is the smallest from 10 up whose single-pass prompt reaches the target; the floor stays at 10.
  The run (findings/recompute/G2_runs/run_g2.sh:1-23): exp_01 --configs matched_budget, gemini-3-flash-preview, the
      20-paper index exp_v4_s20_n0, the 135 questions, draws 1 2 3 (405 answers), no verifier.
The pre-fixed analysis rule for G2 (experiments/LIST.md, "Analysis rules for three draws", approved D78 Q130 before
any G1 answer was scored): Rule 3 (LIST.md:253-275) names "the matched-budget arm (G2) against RLM-10": effect d = the
mean over questions of (p of A minus p of B), the Rule 2 interval (10,000 question resamples, seed 20261013), the
exact two-sided sign-flip test; Rule 5 (LIST.md:277-286): pass = judge correctness 4 or more, primary, 3 or more the
relaxed threshold, both reported; Rule 8 (LIST.md:334-352): the 86 answerable questions; Rule 10 (LIST.md:375-381):
failed answers count as fails, and the sensitivity leaves them out; Rule 6 (LIST.md:310-311): "G2 and G6 enter a
ranking only if the sentence says so". No letter claim names G2 (the letter "currently says none was run",
LIST.md:82-84), so Rule 11's verdict words are not applied. That rule's result is written apart from the exploratory
numbers (results.json "prefixed_rule"). Everything else here (the one-paper and many-paper split, the gap closed, the
per-draw tables, concept recall, key-paper coverage, passage and token counts) is exploratory.

THE QUESTION TYPES. The split the review's agents used (findings_review_2026-10-30/scripts/a02_scripts/g1_extra.py:6,
out/D10_work/qtypes.py:2-6): many-paper = the D5 key's categories cross_document (17) and synthesis (9), 26
questions; one-paper = factual_recall, technical, conceptual, 20 each, 60 questions. Read here from the runner's D5
key (experiments.runner.experiment.questions(), Rule 8) and checked against the key's source_files: every one-paper
question cites 1 paper, every many-paper question 2 to 5.

INPUTS, each checked by sha256 before it is read further:
  G2's judge rows: findings/recompute/S511_g2_budget/inputs/g2_collect.jsonl and its sidecar, the output of
      s3_guard.py collect --out findings/recompute/S3_runs/out_g2 --set G2 run in the Studio's S3 clone
      (~/projects/mentori-runs-s3, HEAD dacef7e, UV_PYTHON=3.13.5, 30 October 21:14), copied here once.
  G1's judge rows: findings/recompute/fig2_inputs/g1_collect.jsonl (the frozen collect Figure 3 reads).
  Both under one judge code and lock: run_sha256 38ae79ab, lock d66daa28, devstral-small-2:24b, key v2.4 (the same
      key_hash per question in both files).
  Generation records (passages read, tokens, answer text for concept recall): G1 from the frozen k1_inputs_runs and
      fig2_g1r15_inputs (the 15 reruns' latest lines over K1's, as S463 rank reads them); G2 from the frozen
      s457_mirror_20261022/matched_budget/answers.jsonl (sha256 6b4c4653, the copy S3 judged, S3_runs/README.md:77),
      with its plan and reached files. All through fig_repro.frozen().
  Concept recall: findings/recompute/L3/concept_recall.jsonl (G1, D12's loose matcher, key v2.4, provisional) and
      S471.score() for G2's answers.
  Passage to paper: the paper store's chroma.sqlite3 (metadata file_name), the copy in ~/l1_inputs/store, sha256
      332a587a (its MANIFEST.sha256 and COPY.json), read only. Env MENTORI_L1_STORE names another folder holding it
      (RELEASE_DESIGN.md Q5 O1, 11 Nov: reproduce.py points it at the data root); the provenance key stays
      STORE_KEY whatever the folder, so no output changes.

REPRODUCE FIRST (README.md:75-79). Before any G2 number is computed, the same code recomputes from the same G1 rows
and refuses (exit 1, nothing written) unless each of these equals its committed value:
  (1) the sign-flip test gives S04a's published P 0.01921 (15 against 4) and 0.00754 (15 against 3) (LIST.md:262-264);
  (2) Figure 3a: every strategy's pass rate, its Rule 2 interval, the rate with failures left out, and each draw's
      rate, at thresholds 4 and 3 (findings/figures_provisional/fig3_strategies/ranking.json, sheet "Fig. 3a");
  (3) Figure 3e: each strategy's exact two-sided sign-flip P against single pass at 4 and 3 (same file, "Fig. 3e");
  (4) the findings review's one-paper / many-paper pass rates at score 4: the 12 rates and the two question counts
      are read from report.json M01's synthesis line ("G1 pass rate at score 4, one-paper (60) / many-paper
      (26): ..."), and each must equal the rate computed here, rounded to 0.1 (D187, S511-O1 O-a);
  (5) concept recall: S471.score() on G1's records gives every answerable L3 row exactly, and the strategy means and
      intervals of L3's loose reading on key v2.4 as ranking.json records them: since D188 under
      concept_recall.anchor_v24_loose (Figure 3b now draws D181's reading on key v2.5), before it the "Fig. 3b" rows.

THE GATE'S FIGURE 3 VALUES ARE PINNED. Parts (2), (3) and (5) compare with key v2.4 numbers. Figure 3 moved to key v2.5
(D186 (3)) and its sheets moved (old e to 3c), so the gate reads the ranking.json of commit RANKING_V24_AT, the last one
on key v2.4 (pinned in the tree, O3, held to its git blob id), in place of the plate's current file. What it compares is unchanged: 120 values, 10
P values, 18 values.

KEY v2.5 (D188-R1, fig3.md R8). The numbers above stay on key v2.4 under the gate. Beside them, results.json "v25" and
results.md's last section hold the pass rates, pairs, gap closed and pre-fixed rule again with each answer read through
scripts/judge_rows_v25.py: its key v2.5 row where one exists, else its key v2.4 row. G1's v2.5 rows and G2's two sources
are findings/recompute/fig3_s6_inputs/ (S528). Concept recall, passages and tokens have no judge row and do not change.
Figure 3 (S463) holds G2's rates to these.

G13 (D236, D237). Five of G2's questions were sized to RLM-10 answers stored again on 18 October; G13 replanned them
and answered their 15 again, judged once on key v2.5 (set S6WG13). The "v25" section reads the arm as it now stands
through scripts/g13_merge.py: G2's 390 answers and G13's 15 (generation records), G13's 15 judge rows in place of G2's
15, and its pass rates, pairs, gap closed, pre-fixed rule, concept recall, passages, tokens and budget all on those 405.
Before the merge, the same code reads G2 unmerged and must give every key v2.5 pass rate the committed results.json
held (REPRODUCE FIRST); "v25_before_g13" keeps those numbers. The key v2.4 sections above read G2's 405 as S3 judged
them: no key v2.4 row exists for G13's 15, so they are not the arm as it now stands.

ONE COMMAND, from the repository root:

    uv run --frozen python scripts/S511_g2_matched_budget.py

Writes findings/recompute/S511_g2_budget/results.json (every number with its n, the gate's results, provenance: this
script's sha256, every input's sha256, git HEAD, the command) and results.md (the same, as tables). Tests:
uv run --frozen python scripts/S511_g2_matched_budget_test.py.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import pinned_history as PH  # noqa: E402

SCRIPT = "scripts/S511_g2_matched_budget.py"
RECOMPUTE = ROOT / "findings" / "recompute"
OUT = RECOMPUTE / "S511_g2_budget"
G2_COLLECT = OUT / "inputs" / "g2_collect.jsonl"
G2_COLLECT_SHA = "b31508d05557290d0791ba686117ea379397deee0a9df7bc5cc04e725c4cc247"      # copied 30 Oct, Studio sha256
G2_SIDE_SHA = "313b947dc7ebcf62da6cbf62742cee932186ef96e812f011e0a1f0d0de23212c"
G1_COLLECT_SHA = "f5ff75bc244cda492a48e7e11f54f2007ed7d586a8f49e78921edd7244b28965"      # figure3_provenance.json
G2_ANSWERS_SHA = "6b4c46531eca233b1bd73a5cb56819874e1807e9ee6c80152e9ce904a2d32728"      # S3_runs/README.md:77
STORE_DIR_DEFAULT = Path.home() / "l1_inputs" / "store"
STORE = Path(os.environ.get("MENTORI_L1_STORE") or STORE_DIR_DEFAULT).expanduser() / "chroma.sqlite3"   # Q5 O1
STORE_KEY = "~/l1_inputs/store/chroma.sqlite3"          # its name in inputs_sha256, the same wherever STORE is
STORE_SHA = "332a587a932d62af5af59497b29dd990d127191b6fe8318b16615cd874937d4b"           # its MANIFEST.sha256
RANKING = ROOT / "findings" / "figures_provisional" / "fig3_strategies" / "ranking.json"
RANKING_V24_AT = "94262a0e"                           # the last commit whose ranking.json is on key v2.4 with old sheets
FROZEN_S6 = RECOMPUTE / "fig3_s6_inputs"              # S528: S6G1, S6G2 and G2 (key v2.5 and v2.4)
REPORT = RECOMPUTE / "findings_review_2026-10-30" / "report.json"
L3 = RECOMPUTE / "L3" / "concept_recall.jsonl"
LOCK_WANT = "d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12"           # D88; S463:252
LOCKS_OK = __import__("lock_equiv").EQUIVALENT   # D205: D88 and the locks lock_equiv proves equal to it in every sent setting
RUN_SHA = "38ae79ab023b97562b69b2875b3c8001b02f887d5578121103b85d4a0b4729da"             # S3 README:77, G1 and G2
INDEX = "exp_v4_s20_n0"
G1 = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
G2 = "matched_budget"
ARMS = ["single_pass", G2, "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
LABEL = {"single_pass": "single pass", G2: "G2 matched budget", "multi_hop": "multi-hop",
         "verified_pass": "verified pass", "rlm_5": "RLM-5", "rlm_10": "RLM-10", "rlm_20": "RLM-20"}
DRAWS = (1, 2, 3)
THRESHOLDS = (4, 3)                                   # Rule 5, D154: 4 the pass rate, 3 relaxed
N_BOOT, SEED, PCT = 10000, 20261013, (2.5, 97.5)      # Rule 2: S407's resamples, seed and percentiles (S463:255-256)
JUDGE_FAILED = {"error", "stalled", "length", "cancelled", "unparseable"}   # S463:258
MANY = ("cross_document", "synthesis")
ONE = ("factual_recall", "technical", "conceptual")
TOL = 1e-6


class Refused(Exception):
    """An input is not the one this script was written for (exit 2, nothing written)."""


class GateFail(Exception):
    """A known value did not reproduce (exit 1, nothing written)."""


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p) -> str:
    p = Path(p)
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p).replace(str(Path.home()), "~")


# ---------------------------------------------------------------------------------------------------------------
# the method: Rule 2's interval and Rule 3's test (S463_fig2_ranking.py:725-770, the same code, reproduced by the gate)
# ---------------------------------------------------------------------------------------------------------------
_COUNTS: dict = {}


def resample_counts(n: int):
    """S407's resample counts (scripts/S407_strategy_contrasts_v24.py:246-257; S463:725-732)."""
    import numpy as np
    if n not in _COUNTS:
        idx = np.random.default_rng(SEED).integers(0, n, size=(N_BOOT, n))
        flat = np.bincount((idx + n * np.arange(N_BOOT)[:, None]).ravel(), minlength=N_BOOT * n)
        _COUNTS[n] = flat.reshape(N_BOOT, n).astype(float)
    return _COUNTS[n]


def interval(num: list, den: list) -> list[float]:
    """Rule 2: per resample sum(num) / sum(den) over the questions drawn; percentiles 2.5 and 97.5 (S463:737-748)."""
    import numpy as np
    w = resample_counts(len(num))
    top, bottom = w @ np.array(num, dtype=float), w @ np.array(den, dtype=float)
    ok = bottom > 0
    return [float(v) for v in np.percentile(top[ok] / bottom[ok], PCT)]


def signflip_p(diffs: list) -> float:
    """Rule 3: the exact two-sided sign-flip test on per-question differences, by convolution (S463:751-768)."""
    nz = [Fraction(x) for x in diffs if x != 0]
    if not nz:
        return 1.0
    L = math.lcm(*[x.denominator for x in nz])
    v = [abs(int(x * L)) for x in nz]
    obs = abs(sum(int(x * L) for x in nz))
    dist = {0: 1}
    for x in v:
        new = defaultdict(int)
        for s, k in dist.items():
            new[s + x] += k
            new[s - x] += k
        dist = new
    return float(Fraction(sum(k for s, k in dist.items() if abs(s) >= obs), 2 ** len(v)))


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar: binomial(b + c, 1/2), P = min(1, 2 P(X <= min(b, c))). Equal to signflip_p on one
    draw's 0/1 differences (LIST.md:262: 'on one draw this test is the exact McNemar test')."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return float(min(Fraction(1), 2 * Fraction(sum(math.comb(n, i) for i in range(k + 1)), 2 ** n)))


# ---------------------------------------------------------------------------------------------------------------
# questions, judge rows, records
# ---------------------------------------------------------------------------------------------------------------
def questions() -> dict:
    """{question id: {"group": Rule 8 group, "category": key category, "kind": one/many/None, "papers": [...]}} from the
    runner's D5 key (experiments.runner.experiment.questions(), KEY_D5 sha256-pinned), checked against Rule 8's
    counts and the source_files rule of the split."""
    from experiments.runner import experiment as ex
    from experiments.scorers.records import GROUP_OF_TYPE
    if sha256_file(ex.KEY_D5) != ex.KEY_D5_SHA256:
        raise Refused(f"{rel(ex.KEY_D5)} is not the runner's pinned D5 key")
    src = {q["id"]: q for q in json.loads(Path(ex.KEY_D5).read_text())["questions"]}
    out = {}
    for q in ex.questions():
        g = GROUP_OF_TYPE[q["answer_type"]]
        cat = q["category"]
        kind = None
        if g == "answerable":
            kind = "many" if cat in MANY else "one" if cat in ONE else "?"
        out[q["id"]] = {"group": g, "category": cat, "kind": kind, "papers": list(src[q["id"]].get("source_files") or [])}
    groups = Counter(v["group"] for v in out.values())
    kinds = Counter(v["kind"] for v in out.values() if v["group"] == "answerable")
    if len(out) != 135 or groups != Counter({"answerable": 86, "false_premise": 10, "not_answerable": 39}) \
            or kinds != Counter({"one": 60, "many": 26}):
        raise Refused(f"the D5 key gives {len(out)} questions, groups {dict(groups)}, kinds {dict(kinds)}")
    bad = [q for q, v in out.items() if v["kind"] == "one" and len(v["papers"]) != 1] + \
          [q for q, v in out.items() if v["kind"] == "many" and not 2 <= len(v["papers"]) <= 5]
    if bad:
        raise Refused(f"source_files break the split (one-paper = 1 paper, many-paper = 2 to 5): {bad[:5]}")
    return out


def read_collect(path: Path, configs: list[str], qs: dict, want_sha: str) -> tuple[dict, dict]:
    """{(config, question, draw): cell} as S463.read_collect makes it (S463:557-575): scored, failed (no_answer) or
    unscored (a judge failure); plus what was read. Refuses another file, a second run_sha256 or lock, a missing or
    doubled answer, and a prompt that is not the question's Rule 8 group's."""
    got = sha256_file(path)
    if got != want_sha:
        raise Refused(f"{rel(path)} sha256 {got[:12]} is not {want_sha[:12]}")
    side = json.loads(path.with_name(path.name + ".json").read_text())
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    if side.get("rows") != len(rows):
        raise Refused(f"{rel(path)}: sidecar {side.get('rows')} rows, file {len(rows)}")
    if {r.get("run_sha256") for r in rows} != {RUN_SHA} or not {r.get("lock_sha256") for r in rows} <= LOCKS_OK:
        raise Refused(f"{rel(path)}: rows not all under run_sha256 {RUN_SHA[:8]} and lock {LOCK_WANT[:8]}")
    metric = {"answerable": "correctness", "false_premise": "correctness", "not_answerable": "refusal_accuracy"}
    cells, key_hash, b_status = {}, {}, {}
    for r in rows:
        c, q, d = r["config"], r["question_id"], r["draw"]
        k = (c, q, d)
        if k in cells or c not in configs or q not in qs or d not in DRAWS \
                or r.get("answer_key") != f"{INDEX}|{c}|{q}|d{d}":
            raise Refused(f"{rel(path)}: row {k} doubled or not an answer of {configs}")
        if bool(r.get("answerable_prompt")) != (qs[q]["group"] != "not_answerable"):
            raise Refused(f"{rel(path)}: {k} judged with the wrong prompt for group {qs[q]['group']}")
        key_hash.setdefault(q, set()).add(r.get("key_hash"))
        st = (r.get("a") or {}).get("status")
        if st == "ok":
            v = (r["a"].get("scores") or {}).get(metric[qs[q]["group"]])
            cells[k] = {"kind": "scored", "score": v} if isinstance(v, (int, float)) and not isinstance(v, bool) \
                else {"kind": "unscored", "why": "ok, no score"}
        elif st == "no_answer":
            cells[k] = {"kind": "failed"}
        elif st in JUDGE_FAILED:
            cells[k] = {"kind": "unscored", "why": st}
        else:
            raise Refused(f"{rel(path)}: {k} (a) status {st!r}")
        b = r.get("b") or {}
        b_status[k] = {"status": b.get("status"), "error": b.get("error")}
    want = {(c, q, d) for c in configs for q in qs for d in DRAWS}
    if set(cells) != want:
        raise Refused(f"{rel(path)}: {len(want - set(cells))} answers have no row")
    read = {"file": rel(path), "sha256": got, "sidecar_sha256": sha256_file(path.with_name(path.name + ".json")),
            "rows": len(rows), "run_sha256": RUN_SHA, "lock_sha256": LOCK_WANT, "collected_at":
            (side.get("_provenance") or {}).get("at"), "status_a": side.get("status_a"), "status_b": side.get("status_b")}
    return cells, {"read": read, "key_hash": key_hash, "b": b_status}


def rec_summary(r: dict, source: str) -> dict:
    g = r.get("generation") or {}
    ans, err = g.get("answer") or "", g.get("error")
    return {"status": "error" if err else ("ok" if ans.strip() else "no_answer"), "answer": ans,
            "answer_sha256": hashlib.sha256(ans.encode("utf-8")).hexdigest(),
            "turn_limit_note": ((g.get("rlm") or {}).get("metadata") or {}).get("turn_limit_note"),
            "passages": list(dict.fromkeys(g.get("passages") or [])),
            "prompt_tokens": g.get("prompt_tokens"), "llm_calls": g.get("llm_calls"),
            "turns": (g.get("rlm") or {}).get("turns"), "mb": g.get("matched_budget"), "source": source}


def read_records_merged(recs: dict, info: dict) -> tuple[dict, dict, dict]:
    """G13 (D236, D237): recs and info with G2's 15 replanned answers replaced by G13's (scripts/g13_merge.py): the
    generation records, and the reached rows (matched_budget.reached on G13's sink). Returns (recs, info, report)."""
    import fig_repro as FR
    import g13_merge as M
    mb = FR.frozen("s457_mirror_20261022", "s457_mirror_20261022/matched_budget")
    try:
        sums = M.check_sums()
        g13 = M.g13_answers()
        _, rep = M.merge_answers(M.last_lines(mb / "answers.jsonl"), g13)
        reached13 = M.g13_reached(g13)
    except M.Refused as e:
        raise Refused(f"g13_merge: {e}") from None
    out = dict(recs)
    for k in rep["replaced_keys"]:
        out[k] = rec_summary(g13[k], f"{rel(M.ANSWERS)}:{k}")
    rr = {x["answer_key"]: x for x in info["reached"]["answers"]}
    if set(rep["replaced_keys"]) - set(rr):
        raise Refused("G2's reached file lacks a replaced key")
    rr.update({x["answer_key"]: x for x in reached13})
    info2 = {"sha256": {**info["sha256"], **sums}, "plan": info["plan"],
             "reached": {**info["reached"], "answers": [rr[k] for k in sorted(rr)]}}
    return out, info2, rep


def read_records() -> tuple[dict, dict]:
    """{answer_key: record summary} for the seven arms: each key's last line; G1R15's copy over K1's (S463:415-475).
    Every file comes through fig_repro.frozen(), checked against its committed member list."""
    import fig_repro as FR
    k1 = FR.frozen("k1_inputs_runs", "k1_inputs_runs")
    g1r15 = FR.frozen("fig2_g1r15_inputs", "fig2_g1r15_inputs") / "runs"
    mb = FR.frozen("s457_mirror_20261022", "s457_mirror_20261022/matched_budget")
    files = [k1 / f"exp_01__{c}__{INDEX}" / "answers.jsonl" for c in G1]
    files += [g1r15 / f"exp_01__{c}__{INDEX}" / "answers.jsonl" for c in G1 if
              (g1r15 / f"exp_01__{c}__{INDEX}" / "answers.jsonl").exists()]
    files.append(mb / "answers.jsonl")
    if sha256_file(mb / "answers.jsonl") != G2_ANSWERS_SHA:
        raise Refused("G2's answers.jsonl is not the copy S3 judged (6b4c4653)")
    out, shas = {}, {}
    for p in files:
        shas[FR.frozen_label(p)] = sha256_file(p)
        last = {}
        for n, raw in enumerate(p.read_text().splitlines(), 1):
            if raw.strip():
                r = json.loads(raw)
                last[r["answer_key"]] = (n, r)
        for k, (n, r) in last.items():
            out[k] = rec_summary(r, f"{FR.frozen_label(p)}:{n}")
    plan = json.loads((mb / "g2_runs" / "g2_matched_budget_plan.json").read_text())
    reached = json.loads((mb / "g2_runs" / "g2_matched_budget_reached.json").read_text())
    for f in ("g2_matched_budget_plan.json", "g2_matched_budget_reached.json"):
        shas[FR.frozen_label(mb / "g2_runs" / f)] = sha256_file(mb / "g2_runs" / f)
    return out, {"sha256": shas, "plan": plan, "reached": reached}


def check_records(cells: dict, recs: dict) -> None:
    """Each judged answer has its record, and the judge's no_answer is the record's failure (S463:615-627)."""
    bad = []
    for (c, q, d), cell in cells.items():
        r = recs.get(f"{INDEX}|{c}|{q}|d{d}")
        if r is None:
            bad.append(f"{c}|{q}|d{d}: no record")
        elif (cell["kind"] == "failed") != (r["status"] != "ok"):
            bad.append(f"{c}|{q}|d{d}: judge {cell['kind']}, record {r['status']}")
    if bad:
        raise Refused(f"{len(bad)} judged answers do not match their records, first: {bad[0]}")


# ---------------------------------------------------------------------------------------------------------------
# the statistics
# ---------------------------------------------------------------------------------------------------------------
def shares(cells, arms, qids, t, failures_as_fail=True):
    """{arm: {q: (Fraction p or None, {draw: 1, 0 or None})}}, S463.shares (S463:789-808)."""
    out = {}
    for c in arms:
        out[c] = {}
        for q in qids:
            k = n = 0
            per = {}
            for d in DRAWS:
                cell = cells[(c, q, d)]
                if cell["kind"] == "scored":
                    hit = int(cell["score"] >= t)
                    k, n, per[d] = k + hit, n + 1, hit
                elif cell["kind"] == "failed" and failures_as_fail:
                    n, per[d] = n + 1, 0
                else:
                    per[d] = None
            out[c][q] = (Fraction(k, n) if n else None, per)
    return out


def summarise(sh, qids) -> dict:
    """Per arm: the mean of p over the questions with one, the Rule 2 interval, n, each draw's rate and n."""
    res = {}
    for c in sh:
        ps = [sh[c][q][0] for q in qids]
        have = [p for p in ps if p is not None]
        num = [float(p) if p is not None else 0.0 for p in ps]
        den = [1.0 if p is not None else 0.0 for p in ps]
        rate = sum(have, Fraction(0)) / len(have) if have else None
        lo, hi = interval(num, den) if have else (None, None)
        per = {}
        for d in DRAWS:
            v = [sh[c][q][1][d] for q in qids if sh[c][q][1][d] is not None]
            per[d] = {"rate": sum(v) / len(v) if v else None, "n": len(v), "passed": sum(v)}
        res[c] = {"rate": None if rate is None else float(rate), "lo": lo, "hi": hi, "questions": len(have),
                  "answers": sum(1 for q in qids for d in DRAWS if sh[c][q][1][d] is not None),
                  "passed": sum(1 for q in qids for d in DRAWS if sh[c][q][1][d] == 1), "per_draw": per}
    return res


def pair(sh, a, b, qids) -> dict:
    """Rule 3, a minus b: d, the Rule 2 interval, the exact sign-flip P, questions where a or b is higher (S463:835-856);
    and the per-draw 2 x 2 tables (draw d against draw d, descriptive, LIST.md:275) with their exact McNemar P."""
    diffs, num, den = [], [], []
    for q in qids:
        pa, pb = sh[a][q][0], sh[b][q][0]
        if pa is None or pb is None:
            num.append(0.0)
            den.append(0.0)
            continue
        diffs.append(pa - pb)
        num.append(float(pa - pb))
        den.append(1.0)
    n = len(diffs)
    dx = sum(diffs, Fraction(0)) / n if n else None
    lo, hi = interval(num, den) if n else (None, None)
    per = {}
    for d in DRAWS:
        both = [(sh[a][q][1][d], sh[b][q][1][d]) for q in qids
                if sh[a][q][1][d] is not None and sh[b][q][1][d] is not None]
        b_, c_ = sum(1 for x, y in both if x == 1 and y == 0), sum(1 for x, y in both if x == 0 and y == 1)
        per[d] = {"questions": len(both), "a_only": b_, "b_only": c_, "both": sum(1 for x, y in both if x == y == 1),
                  "neither": sum(1 for x, y in both if x == y == 0), "p_mcnemar_exact_two_sided": mcnemar_exact(b_, c_)}
    return {"a": a, "b": b, "d": None if dx is None else float(dx), "lo": lo, "hi": hi,
            "p_signflip_exact_two_sided": signflip_p(diffs), "questions": n,
            "a_higher": sum(1 for x in diffs if x > 0), "b_higher": sum(1 for x in diffs if x < 0),
            "equal": sum(1 for x in diffs if x == 0), "per_draw": per}


def gap_closed(sh, qids, mid=G2, low="single_pass", high="rlm_10") -> dict:
    """(mid - low) / (high - low) on the pooled rates, each draw's ratio, and a percentile interval over the same
    10,000 question resamples as Rule 2 (all draws of a question move together; the three arms of a question are drawn
    together, so the ratio is paired by question). A resample whose denominator is 0 or below has no ratio and is
    counted, not used."""
    import numpy as np
    keep = [q for q in qids if all(sh[c][q][0] is not None for c in (mid, low, high))]
    num = np.array([float(sh[mid][q][0] - sh[low][q][0]) for q in keep])
    den = np.array([float(sh[high][q][0] - sh[low][q][0]) for q in keep])
    w = resample_counts(len(keep))
    top, bottom = w @ num, w @ den
    ok = bottom > 0
    ratio = float(num.sum() / den.sum()) if den.sum() > 0 else None
    lo, hi = ([float(v) for v in np.percentile(top[ok] / bottom[ok], PCT)] if ok.any() else (None, None))
    per = {}
    for d in DRAWS:
        r = {}
        for c in (mid, low, high):
            v = [sh[c][q][1][d] for q in keep if sh[c][q][1][d] is not None]
            r[c] = sum(v) / len(v) if v else None
        ok_d = None not in r.values() and r[high] - r[low] > 0
        per[d] = {"mid": r[mid], "low": r[low], "high": r[high],
                  "ratio": (r[mid] - r[low]) / (r[high] - r[low]) if ok_d else None}
    return {"mid": mid, "low": low, "high": high, "questions": len(keep), "ratio": ratio,
            "mid_minus_low": float(num.mean()), "high_minus_low": float(den.mean()), "lo": lo, "hi": hi,
            "resamples_used": int(ok.sum()), "resamples_without_ratio": int((~ok).sum()), "per_draw": per}


# ---------------------------------------------------------------------------------------------------------------
# the gate (README.md:75-79): reproduce before anything new
# ---------------------------------------------------------------------------------------------------------------
def close(a, b, tol=TOL) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def check_equal(label: str, got, want, tol=TOL) -> str:
    """One gate comparison: raises GateFail when got differs from want by more than tol."""
    if not close(got, want, tol):
        raise GateFail(f"{label}: computed {got}, committed {want}")
    return f"{label}: {got:.9g} = {want:.9g}"


M01_HEAD = re.compile(r"G1 pass rate at score 4, one-paper \((\d+)\) / many-paper \((\d+)\): ")
M01_ITEM = re.compile(r"(.+?) (\d+(?:\.\d+)?) / (\d+(?:\.\d+)?)%")


def m01_split(report: dict) -> tuple[dict, dict]:
    """M01's one-paper / many-paper split as report.json's synthesis line prints it: ({"one": n, "many": n},
    {strategy: (one-paper rate, many-paper rate)}). The line is the one key number of finding M01 whose value starts
    with "G1 pass rate at score 4, one-paper (n) / many-paper (n): "; its list runs to the first " (" and holds
    "<label> <one> / <many>%" items separated by ", ", one per G1 strategy, labels as LABEL prints them. Raises
    GateFail when M01, the line, an item, or a strategy is missing, doubled or unknown."""
    m01 = [f for f in report.get("findings", []) if f.get("id") == "M01"]
    if len(m01) != 1:
        raise GateFail(f"report.json has {len(m01)} findings with id M01, want 1")
    hits = [(m, k["value"]) for k in m01[0].get("key_numbers", []) for m in [M01_HEAD.match(k.get("value", ""))] if m]
    if len(hits) != 1:
        raise GateFail(f"report.json M01: {len(hits)} key numbers print the one-paper / many-paper split, want 1")
    m, value = hits[0]
    body = value[m.end():].split(" (", 1)[0]
    by_label = {LABEL[c]: c for c in G1}
    rates = {}
    for item in body.split(", "):
        mi = M01_ITEM.fullmatch(item)
        if not mi or mi.group(1) not in by_label:
            raise GateFail(f"report.json M01: item {item!r} is not '<strategy> <one> / <many>%' for a G1 strategy")
        c = by_label[mi.group(1)]
        if c in rates:
            raise GateFail(f"report.json M01: {mi.group(1)} printed twice")
        rates[c] = (float(mi.group(2)), float(mi.group(3)))
    if set(rates) != set(G1):
        raise GateFail(f"report.json M01: no rate for {sorted(set(G1) - set(rates))}")
    return {"one": int(m.group(1)), "many": int(m.group(2))}, rates


def check_m01(g1: dict, qs: dict, report: dict) -> str:
    """Gate part (4): the G1 pass rate at score 4 of each strategy on the one-paper and the many-paper questions,
    rounded to 0.1, equals the rate report.json M01 prints (m01_split), and each half has the count M01 prints."""
    n_want, want = m01_split(report)
    qa = sorted(q for q, v in qs.items() if v["group"] == "answerable")
    sh = shares(g1, G1, qa, 4)
    n = 0
    for kind, i in (("one", 0), ("many", 1)):
        sub = [q for q in qa if qs[q]["kind"] == kind]
        if len(sub) != n_want[kind]:
            raise GateFail(f"M01 {kind}-paper: {len(sub)} questions, M01 prints {n_want[kind]}")
        s = summarise(sh, sub)
        for c in G1:
            check_equal(f"M01 {c} {kind}-paper", round(100 * s[c]["rate"], 1), want[c][i], 1e-9)
            n += 1
    return (f"findings review M01 (report.json): {n} of 12 one-paper / many-paper pass rates at score 4 equal the "
            f"rates M01 prints (to 0.1), read from its text")


def ranking_v24() -> tuple[dict, str]:
    """ranking.json at RANKING_V24_AT (the module docstring, THE GATE'S FIGURE 3 VALUES ARE PINNED) and its sha256."""
    try:   # O3: ranking.json as committed at RANKING_V24_AT, pinned in the tree, held to its git blob id
        b = PH.show(RANKING_V24_AT, str(RANKING.relative_to(ROOT)))
    except PH.PinError as e:
        raise Refused(f"git show {RANKING_V24_AT} ranking.json: {str(e)[:200]}") from None
    return json.loads(b), hashlib.sha256(b).hexdigest()


def gate(g1: dict, qs: dict, recs: dict) -> dict:
    lines = []
    # (1) the test against S04a's published values (LIST.md:262-264)
    lines.append(check_equal("Rule 3 sign-flip, 15 against 4", round(signflip_p([1] * 15 + [-1] * 4), 5), 0.01921, 0))
    lines.append(check_equal("Rule 3 sign-flip, 15 against 3", round(signflip_p([1] * 15 + [-1] * 3), 5), 0.00754, 0))
    rk, _ = ranking_v24()
    qa = sorted(q for q, v in qs.items() if v["group"] == "answerable")
    # (2) Figure 3a
    n2a = 0
    for t in THRESHOLDS:
        sh, sh_out = shares(g1, G1, qa, t), shares(g1, G1, qa, t, failures_as_fail=False)
        s, s_out = summarise(sh, qa), summarise(sh_out, qa)
        for row in rk["sheets"]["Fig. 3a"]:
            if row.get("threshold") != t:
                continue
            c = row["strategy"]
            if row["row_kind"] == "strategy":
                check_equal(f"3a {c} t{t} rate", 100 * s[c]["rate"], row["pass_rate_pct"])
                check_equal(f"3a {c} t{t} lo", 100 * s[c]["lo"], row["ci95_lo_pct"])
                check_equal(f"3a {c} t{t} hi", 100 * s[c]["hi"], row["ci95_hi_pct"])
                check_equal(f"3a {c} t{t} failures out", 100 * s_out[c]["rate"], row["pass_rate_pct_failures_left_out"])
                n2a += 4
            elif row["row_kind"] == "draw":
                d = row["draw"]
                check_equal(f"3a {c} t{t} d{d}", 100 * s[c]["per_draw"][d]["rate"], row["draw_pass_rate_pct"])
                if s[c]["per_draw"][d]["n"] != row["draw_questions"]:
                    raise GateFail(f"3a {c} t{t} d{d}: n {s[c]['per_draw'][d]['n']} not {row['draw_questions']}")
                n2a += 2
    if n2a != 2 * 6 * (4 + 3 * 2):
        raise GateFail(f"Fig. 3a: {n2a} values compared, want 120")
    lines.append(f"Figure 3a (ranking.json): {n2a} of 120 values equal (pass rate, interval, failures left out, "
                 f"each draw's rate and n; 6 strategies, thresholds 4 and 3)")
    # (3) Figure 3e: Rule 3's P of each strategy against single pass
    n2e = 0
    for t in THRESHOLDS:
        sh = shares(g1, G1, qa, t)
        for row in rk["sheets"]["Fig. 3e"]:
            if row.get("row_kind") == "strategy against single pass" and row.get("threshold") == t:
                c = row["strategy"]
                pr = pair(sh, c, "single_pass", qa)
                check_equal(f"3e {c} t{t} P", pr["p_signflip_exact_two_sided"], row["p_two_sided_exact_sign_flip"], 1e-12)
                n2e += 1
    if n2e != 10:
        raise GateFail(f"Fig. 3e: {n2e} P values compared, want 10")
    lines.append("Figure 3e (ranking.json): 10 of 10 sign-flip P values against single pass equal (thresholds 4, 3)")
    # (4) the review's split, its 12 rates read from report.json M01's text
    lines.append(check_m01(g1, qs, json.loads(REPORT.read_text())))
    # (5) concept recall: S471.score on G1's records gives L3's rows, then Figure 3b
    cr_g1, n_rows = concept_recall_g1(recs, qs)
    s2b = cr_summary(cr_g1, G1, qa)
    # D188: Figure 3b draws D181's reading on key v2.5; S463 keeps L3's loose values on key v2.4, the ones this check
    # computes, under concept_recall.anchor_v24_loose.strategies (same column names). Before D188, the Fig. 3b rows.
    anc = ((rk.get("concept_recall") or {}).get("anchor_v24_loose") or {}).get("strategies")
    if anc is not None:
        where = "Figure 3b's v2.4 anchor (ranking.json concept_recall.anchor_v24_loose, D188)"
        rows_2b = [{"strategy": c, **v} for c, v in anc.items()]
    else:
        where = "Figure 3b (ranking.json)"
        rows_2b = [r for r in rk["sheets"]["Fig. 3b"] if r.get("row_kind") == "strategy"]
    n2b = 0
    for row in rows_2b:
        c = row["strategy"]
        check_equal(f"3b {c} loose", 100 * s2b[c]["rate"], row["concept_recall_loose_pct"])
        check_equal(f"3b {c} lo", 100 * s2b[c]["lo"], row["ci95_lo_pct"])
        check_equal(f"3b {c} hi", 100 * s2b[c]["hi"], row["ci95_hi_pct"])
        n2b += 3
    if n2b != 18:
        raise GateFail(f"Fig. 3b: {n2b} values compared, want 18")
    lines.append(f"concept recall: S471.score() on G1's records reproduces {n_rows} of {n_rows} answerable L3 rows "
                 f"(value, found counts, per-concept matches); {where}: 18 of 18 values equal")
    return {"passed": True, "lines": lines, "cr_g1": cr_g1}


# ---------------------------------------------------------------------------------------------------------------
# concept recall (L3's loose matcher, key v2.4) and key-paper coverage
# ---------------------------------------------------------------------------------------------------------------
CR_FIELDS = ("n_concepts", "found_loose", "found_exact", "concept_recall_loose", "concept_recall_exact", "found_by",
             "note_removed", "scored_text_sha256")


def _s471():
    import S471_l3_concept_recall as S471
    return S471


def concept_recall_g1(recs: dict, qs: dict) -> tuple[dict, int]:
    """{(config, q, d): Fraction} for G1's answerable answers, each L3 row first regenerated from its record by
    S471.score (S463.read_concept_recall, S463:1125-1206, checks (2) and (3)); any difference is a GateFail."""
    S471 = _s471()
    key = S471.S470.the_key()
    rows = {}
    for x in L3.read_text().splitlines():
        if x.strip():
            r = json.loads(x)
            rows[r["answer_key"]] = r
    out, bad = {}, []
    for c in G1:
        for q, v in qs.items():
            if v["group"] != "answerable":
                continue
            for d in DRAWS:
                k = f"{INDEX}|{c}|{q}|d{d}"
                r, a = rows.get(k), recs.get(k)
                if r is None or a is None or (r["answer_sha256"], r["status"]) != (a["answer_sha256"], a["status"]):
                    bad.append(f"{k}: L3 row and record differ or are missing")
                    continue
                got = S471.score(a["answer"], key["questions"][q]["expected_concepts"], a["turn_limit_note"])
                if {f: got[f] for f in CR_FIELDS} != {f: r.get(f) for f in CR_FIELDS}:
                    bad.append(f"{k}: S471.score does not give its L3 row")
                    continue
                out[(c, q, d)] = Fraction(r["found_loose"], r["n_concepts"])
    if bad:
        raise GateFail(f"{len(bad)} L3 rows not reproduced, first: {bad[0]}")
    return out, len(out)


def concept_recall_g2(recs: dict, qs: dict) -> dict:
    """G2's answerable answers scored by the same S471.score (no turn-limit note: G2 is single pass)."""
    S471 = _s471()
    key = S471.S470.the_key()
    out = {}
    for q, v in qs.items():
        if v["group"] != "answerable":
            continue
        for d in DRAWS:
            a = recs[f"{INDEX}|{G2}|{q}|d{d}"]
            got = S471.score(a["answer"], key["questions"][q]["expected_concepts"], None)
            out[(G2, q, d)] = Fraction(got["found_loose"], got["n_concepts"])
    return out


def cr_shares(cr: dict, arms, qids) -> dict:
    return {c: {q: (sum((cr[(c, q, d)] for d in DRAWS), Fraction(0)) / len(DRAWS), {d: cr[(c, q, d)] for d in DRAWS})
                for q in qids} for c in arms}


def cr_summary(cr: dict, arms, qids) -> dict:
    return summarise(cr_shares(cr, arms, qids), qids)


def paper_map(ids: set) -> dict:
    """{passage id: file_name} from the paper store, read only (sha256 checked first)."""
    if not STORE.exists():
        raise Refused(f"the paper store {rel(STORE)} is not here")
    got = sha256_file(STORE)
    if got != STORE_SHA:
        raise Refused(f"{rel(STORE)} sha256 {got[:12]} is not {STORE_SHA[:12]}")
    con = sqlite3.connect(f"file:{STORE}?mode=ro", uri=True)
    m = dict(con.execute("select e.embedding_id, md.string_value from embeddings e join embedding_metadata md "
                         "on md.id = e.id where md.key = 'file_name'").fetchall())
    con.close()
    return {i: m.get(i) for i in ids}


# ---------------------------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------------------------
def med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def sets_of(qs: dict) -> dict:
    qa = sorted(q for q, v in qs.items() if v["group"] == "answerable")
    return {"all answerable": qa, "one-paper": [q for q in qa if qs[q]["kind"] == "one"],
            "many-paper": [q for q in qa if qs[q]["kind"] == "many"]}


def scored(cells, qs) -> dict:
    """The judge's numbers of one reading of the rows: pass rates, pairs, gap closed and the pre-fixed rule."""
    sets = sets_of(qs)
    qa = sets["all answerable"]
    res = {"pass": {}, "pairs": {}, "gap_closed": {}, "prefixed_rule": {}}
    for t in THRESHOLDS:
        sh = shares(cells, ARMS, qa, t)
        sh_out = shares(cells, ARMS, qa, t, failures_as_fail=False)
        res["pass"][t] = {name: summarise(sh, sub) for name, sub in sets.items()}
        res["pairs"][t] = {name: [pair(sh, a, b, sub) for a, b in ((G2, "rlm_10"), (G2, "single_pass"),
                                                                     ("rlm_10", "single_pass"))]
                           for name, sub in sets.items()}
        res["gap_closed"][t] = {name: gap_closed(sh, sub) for name, sub in sets.items() if name == "many-paper"}
        res["prefixed_rule"][t] = {"failures counted as fails (Rule 10)": pair(sh, G2, "rlm_10", qa),
                                   "failures left out (Rule 10 sensitivity)": pair(sh_out, G2, "rlm_10", qa)}
    return res


def cells_v25(cells24: dict, qs: dict, g13: bool = True) -> tuple[dict, dict]:
    """Every answer of the seven arms read through judge_rows_v25 (R1): its key v2.5 row where one exists, else its key
    v2.4 row. G1's v2.4 source is the frozen fig2_inputs collect with its outs; G1's S6 and both of G2's sources are
    fig3_s6_inputs. With g13 (D236, D237), G2's 15 replanned answers take G13's rows (g13_merge.replace_rows). Refuses
    a chosen row that is not an answer of cells24. Returns the cells and JR.report's counts."""
    import judge_rows_v25 as JR
    import g13_merge as M
    fig2 = RECOMPUTE / "fig2_inputs"
    g1v, g1s = JR.sources(fig2, "G1")[0], JR.sources(FROZEN_S6, "G1")[1]
    g2v, g2s = JR.sources(FROZEN_S6, "G2")
    try:
        srcs_g1 = [JR.read_source(g1v, fig2 / "g1_collect.jsonl"), JR.read_source(g1s, FROZEN_S6 / "s6_g1_collect.jsonl")]
        srcs_g2 = [JR.read_source(g2v, FROZEN_S6 / "g2_collect.jsonl"),
                   JR.read_source(g2s, FROZEN_S6 / "s6_g2_collect.jsonl")]
        choice = {}
        rep = {}
        for name, srcs, arms in (("G1", srcs_g1, G1), ("G2", srcs_g2, [G2])):
            ans = [{"run_id": f"exp_01__{c}__{INDEX}", "config": c, "question_id": q, "draw": d,
                    "answer_key": f"{INDEX}|{c}|{q}|d{d}"} for c in arms for q in qs for d in DRAWS]
            ch = JR.choose(ans, srcs, all_draws=True)
            g13rep = None
            if name == "G2" and g13:
                try:
                    ch, g13rep = M.replace_rows(ch)
                except M.Refused as e:
                    raise Refused(f"g13_merge: {e}") from None
            rep[name] = {k: v for k, v in JR.report(ch, all_draws=True).items() if k in ("by_status", "provisional")}
            if g13rep is not None:
                rep[name]["g13"] = g13rep
            choice.update({k: v for k, v in ch.items() if k != "_sources"})
    except JR.Refused as e:
        raise Refused(f"judge_rows_v25: {e}") from None
    metric = {"answerable": "correctness", "false_premise": "correctness", "not_answerable": "refusal_accuracy"}
    out = {}
    for (run, c, q, d), v in choice.items():
        r = v["row"]
        if r is None or (c, q, d) not in cells24:
            raise Refused(f"judge_rows_v25: {c} {q} d{d} has no row chosen ({v['status']})")
        st = (r.get("a") or {}).get("status")
        if st == "ok":
            x = (r["a"].get("scores") or {}).get(metric[qs[q]["group"]])
            out[(c, q, d)] = {"kind": "scored", "score": x} if isinstance(x, (int, float)) and not isinstance(x, bool) \
                else {"kind": "unscored", "why": "ok, no score"}
        elif st == "no_answer":
            out[(c, q, d)] = {"kind": "failed"}
        elif st in JUDGE_FAILED:
            out[(c, q, d)] = {"kind": "unscored", "why": st}
        else:
            raise Refused(f"judge_rows_v25: {c} {q} d{d} (a) status {st!r}")
    return out, rep


def reproduce_v25(res25_0: dict) -> str:
    """The key v2.5 pass rates of every arm, G2 unmerged, must equal those results.json holds at HEAD (git show, read
    only), before G13's 15 are read. A results.json at HEAD with no "v25_before_g13" is the one written before G13, so
    its "v25" is G2 unmerged; one with it holds the unmerged reading there."""
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel(OUT / 'results.json')}"], capture_output=True)
    if r.returncode:
        raise Refused("results.json at HEAD cannot be read, so the key v2.5 rates before G13 cannot be reproduced")
    old = json.loads(r.stdout)
    base = old.get("v25_before_g13") or old.get("v25") or {}
    want, want_pr = base.get("pass"), base.get("prefixed_rule")
    if not want or not want_pr:
        raise Refused("results.json at HEAD holds no key v2.5 pass rates and pre-fixed rule to reproduce")
    n, bad = 0, []

    def cmp(label, s, w, fields):
        nonlocal n
        if w is None:
            bad.append(f"{label}: no entry at HEAD")
            return
        for f in fields:
            n += 1
            if f not in w:
                bad.append(f"{label} {f}: {s.get(f)} here, no entry at HEAD")
            elif not ((s[f] is None and w[f] is None) or close(s[f], w[f])):
                bad.append(f"{label} {f}: {s[f]} here, {w[f]} at HEAD")

    for t, by in res25_0["pass"].items():
        for name, arms in by.items():
            for c, s in arms.items():
                cmp(f"{t} {name} {c}", s, ((want.get(str(t)) or {}).get(name) or {}).get(c),
                    ("rate", "lo", "hi", "questions", "answers"))
    n_pass = n
    for t, by in res25_0["prefixed_rule"].items():
        for how, s in by.items():
            cmp(f"{t} pre-fixed rule {how}", s, (want_pr.get(str(t)) or {}).get(how),
                ("d", "lo", "hi", "p_signflip_exact_two_sided"))
    if bad:
        raise GateFail(f"key v2.5 before G13: {len(bad)} of {n} values differ from results.json at HEAD, first {bad[:2]}")
    return (f"key v2.5 before G13: {n_pass} pass-rate values and {n - n_pass} pre-fixed rule values (d, interval, "
            f"P), {n} of {n} equal results.json at HEAD")


def compute(cells, qs, recs, info, g1_gate) -> dict:
    sets = sets_of(qs)
    qa = sets["all answerable"]
    res = scored(cells, qs)
    # concept recall
    cr = dict(g1_gate["cr_g1"])
    cr.update(concept_recall_g2(recs, qs))
    crs = cr_shares(cr, ARMS, qa)
    res["concept_recall"] = {
        "summary": {name: summarise(crs, sub) for name, sub in sets.items()},
        "pairs": {name: [pair(crs, a, b, sub) for a, b in ((G2, "rlm_10"), (G2, "single_pass"), ("rlm_10", "single_pass"))]
                  for name, sub in sets.items()},
        "gap_closed": {"many-paper": gap_closed(crs, sets["many-paper"])}}
    # passages, tokens, key-paper coverage
    ids = {p for c in ARMS for q in qa for d in DRAWS for p in recs[f"{INDEX}|{c}|{q}|d{d}"]["passages"]}
    pm = paper_map(ids)
    unmapped = sorted(i for i, f in pm.items() if f is None)
    reading = {}
    for name, sub in sets.items():
        reading[name] = {}
        for c in ARMS:
            n_p, toks, chars, cov_all, per_draw_cov = [], [], [], [], {d: [] for d in DRAWS}
            for q in sub:
                for d in DRAWS:
                    r = recs[f"{INDEX}|{c}|{q}|d{d}"]
                    n_p.append(len(r["passages"]))
                    toks.append(r["prompt_tokens"])
                    chars.append(len(r["answer"]))
                    files = {pm[p] for p in r["passages"] if pm.get(p)}
                    full = set(qs[q]["papers"]) <= files
                    cov_all.append(full)
                    per_draw_cov[d].append(full)
            reading[name][c] = {"answers": len(n_p), "passages_median": med(n_p), "passages_min": min(n_p),
                                "passages_max": max(n_p), "prompt_tokens_median": med(toks),
                                "answer_chars_median": med(chars),
                                "every_key_paper_read": sum(cov_all),
                                "every_key_paper_read_share": sum(cov_all) / len(cov_all),
                                "every_key_paper_read_per_draw": {d: [sum(v), len(v)] for d, v in per_draw_cov.items()}}
    res["reading"] = {"by_set": reading, "passage_ids": len(ids), "unmapped_passage_ids": len(unmapped)}
    # the budget as matched: G2's tokens against RLM-10's median over its draws as stored now
    bud = {}
    for name, sub in sets.items():
        ratios, below = [], []
        for q in sub:
            r10 = med([recs[f"{INDEX}|rlm_10|{q}|d{d}"]["prompt_tokens"] for d in DRAWS])
            for d in DRAWS:
                g = recs[f"{INDEX}|{G2}|{q}|d{d}"]["prompt_tokens"]
                ratios.append(g / r10)
                if g < r10:
                    below.append(f"{q} d{d}")
        bud[name] = {"answers": len(ratios), "ratio_median": med(ratios), "ratio_min": min(ratios),
                     "ratio_max": max(ratios), "g2_below_rlm10_median": len(below)}
    plan = info["plan"]
    exc = [{"question_id": e["question_id"], "answer_key": e["answer_key"],
            "kind": qs[e["question_id"]]["kind"] or qs[e["question_id"]]["group"]}
           for e in plan.get("excluded", [])]
    reached = info["reached"]["answers"]
    res["budget"] = {"g2_tokens_over_rlm10_median_now": bud,
                     "plan": {"made": plan.get("made"), "scope": plan.get("scope"), "k_min": plan.get("k_min"),
                              "k_max": plan.get("k_max"), "count_method": plan.get("count_method"),
                              "floor_bound": plan.get("floor_bound"), "no_target": plan.get("no_target"),
                              "excluded": exc},
                     "reached": {"answers": len(reached),
                                 "at_or_above_target": sum(1 for a in reached if a["reached_tokens"] is not None
                                                           and a["reached_tokens"] >= a["target_tokens"]),
                                 "below_target": [{"answer_key": a["answer_key"], "target_tokens": a["target_tokens"],
                                                   "reached_tokens": a["reached_tokens"]} for a in reached
                                                  if a["reached_tokens"] is None
                                                  or a["reached_tokens"] < a["target_tokens"]],
                                 "at_planned_tokens": sum(1 for a in reached if a["reached_tokens"] == a["planned_tokens"])}}
    return res


def b_errors(meta_g2: dict, qs: dict) -> list[dict]:
    out = []
    for (c, q, d), b in sorted(meta_g2["b"].items()):
        if b["status"] not in ("ok", "not_applicable"):
            err = b.get("error") or ""
            kind = "exceed_context_size_error" if "exceed_context_size_error" in err else err[:80]
            ntok = None
            if "n_prompt_tokens" in err:
                try:
                    ntok = json.loads(err.split(":", 1)[1])["error"]["n_prompt_tokens"]
                except (ValueError, KeyError, IndexError):
                    ntok = None
            out.append({"question_id": q, "draw": d, "status": b["status"], "error_type": kind,
                        "n_prompt_tokens": ntok, "category": qs[q]["category"], "kind": qs[q]["kind"]})
    return out


def pct(x, nd=1):
    return "n/a" if x is None else f"{100 * x:.{nd}f}"


def write_md(path: Path, R: dict) -> None:
    L = []
    w = L.append
    v25 = R["v25"]
    w("# S511: G2, the matched-budget arm, against single pass and the RLMs")
    w("")
    w(f"Written by `{SCRIPT}` ({R['_provenance']['at']}, HEAD {R['_provenance']['git_head'][:8]}). Exploratory phase: "
      "the data as they are. Judge: devstral-small-2:24b, plain call (a), key v2.4, run_sha256 38ae79ab, lock "
      "d66daa28; generator gemini-3-flash-preview; draws 1, 2, 3; 86 answerable questions (60 one-paper, 26 "
      "many-paper). Pass = judge correctness 4 or more (primary), 3 or more (relaxed). A pass rate is the mean over "
      "questions of each question's pass share over its draws (Rule 2); its interval is the Rule 2 percentile interval "
      "over 10,000 question resamples (seed 20261013). n is questions (answers in brackets).")
    w("")
    w("## Reproduce gate (README.md:75-79)")
    w("")
    for x in R["gate"]["lines"]:
        w(f"- {x}")
    w("")
    w("## The pre-fixed rule: Rule 3, G2 against RLM-10 on the 86 answerable questions")
    w("")
    w("| Threshold | Failed answers | d (G2 minus RLM-10), points | 95% interval | exact two-sided sign-flip P | "
      "questions G2 higher / RLM-10 higher / equal | n |")
    w("|---|---|---:|---|---:|---|---:|")
    for t in THRESHOLDS:
        for how, p in R["prefixed_rule"][str(t)].items():
            w(f"| {t} | {how} | {100 * p['d']:+.1f} | [{100 * p['lo']:+.1f}, {100 * p['hi']:+.1f}] | "
              f"{p['p_signflip_exact_two_sided']:.4g} | {p['a_higher']} / {p['b_higher']} / {p['equal']} | "
              f"{p['questions']} |")
    w("")
    w("No letter claim names G2, so Rule 11's verdict words are not applied; Rule 6 keeps G2 out of the six-strategy "
      "ranking.")
    w("")
    for t in THRESHOLDS:
        w(f"## Pass rates at score {t} or more (exploratory split)")
        w("")
        w("| Arm | Set | Pooled % (95% interval) | n questions (answers) | Draw 1 % (passed/n) | Draw 2 % | Draw 3 % |")
        w("|---|---|---|---|---|---|---|")
        for name in ("all answerable", "one-paper", "many-paper"):
            for c in ARMS:
                s = R["pass"][str(t)][name][c]
                dd = " | ".join(f"{pct(s['per_draw'][str(d)]['rate'])} ({s['per_draw'][str(d)]['passed']}/"
                                f"{s['per_draw'][str(d)]['n']})" for d in DRAWS)
                w(f"| {LABEL[c]} | {name} | {pct(s['rate'])} [{pct(s['lo'])}, {pct(s['hi'])}] | {s['questions']} "
                  f"({s['answers']}) | {dd} |")
        w("")
        g = R["gap_closed"][str(t)]["many-paper"]
        w(f"Gap closed on the many-paper questions at {t}: (G2 - single pass) / (RLM-10 - single pass) = "
          f"{100 * g['mid_minus_low']:.1f} / {100 * g['high_minus_low']:.1f} points = **{pct(g['ratio'])}%**, 95% "
          f"interval [{pct(g['lo'])}, {pct(g['hi'])}] over {g['resamples_used']} question resamples "
          f"(resamples where RLM-10 is not above single pass have no ratio: {g['resamples_without_ratio']}); n = "
          f"{g['questions']} questions. Per draw: " + "; ".join(
              f"draw {d} {pct(g['per_draw'][str(d)]['ratio'])}%" for d in DRAWS) + ".")
        w("")
        w(f"Paired comparisons at {t} (Rule 3's method; per-draw exact McNemar, descriptive):")
        w("")
        w("| Set | A minus B | d, points (95% interval) | sign-flip P | A higher / B higher / equal | per draw: A only / "
          "B only, McNemar P |")
        w("|---|---|---|---:|---|---|")
        for name in ("all answerable", "one-paper", "many-paper"):
            for p in R["pairs"][str(t)][name]:
                pd = "; ".join(f"d{d} {p['per_draw'][str(d)]['a_only']}/{p['per_draw'][str(d)]['b_only']} P "
                               f"{p['per_draw'][str(d)]['p_mcnemar_exact_two_sided']:.3g}" for d in DRAWS)
                w(f"| {name} | {LABEL[p['a']]} minus {LABEL[p['b']]} | {100 * p['d']:+.1f} ({100 * p['lo']:+.1f}, "
                  f"{100 * p['hi']:+.1f}) | {p['p_signflip_exact_two_sided']:.3g} | {p['a_higher']} / "
                  f"{p['b_higher']} / {p['equal']} (n {p['questions']}) | {pd} |")
        w("")
    cr = R["concept_recall"]
    w("## Concept recall (L3's loose matcher, key v2.4, provisional)")
    w("")
    w("| Arm | Set | Pooled % (95% interval) | n questions (answers) | Draw 1 % | Draw 2 % | Draw 3 % |")
    w("|---|---|---|---|---|---|---|")
    for name in ("all answerable", "one-paper", "many-paper"):
        for c in ARMS:
            s = cr["summary"][name][c]
            dd = " | ".join(pct(s["per_draw"][str(d)]["rate"]) for d in DRAWS)
            w(f"| {LABEL[c]} | {name} | {pct(s['rate'])} [{pct(s['lo'])}, {pct(s['hi'])}] | {s['questions']} "
              f"({s['answers']}) | {dd} |")
    w("")
    g = cr["gap_closed"]["many-paper"]
    w(f"Concept-recall gap closed on the many-paper questions: {pct(g['ratio'])}% [{pct(g['lo'])}, {pct(g['hi'])}] "
      f"(G2 - single pass {100 * g['mid_minus_low']:.1f} of RLM-10 - single pass {100 * g['high_minus_low']:.1f} "
      f"points; n = {g['questions']}).")
    w("")
    w("| Set | A minus B | d, points (95% interval) | sign-flip P | A higher / B higher / equal |")
    w("|---|---|---|---:|---|")
    for name in ("all answerable", "one-paper", "many-paper"):
        for p in cr["pairs"][name]:
            w(f"| {name} | {LABEL[p['a']]} minus {LABEL[p['b']]} | {100 * p['d']:+.1f} ({100 * p['lo']:+.1f}, "
              f"{100 * p['hi']:+.1f}) | {p['p_signflip_exact_two_sided']:.3g} | {p['a_higher']} / {p['b_higher']} / "
              f"{p['equal']} (n {p['questions']}) |")
    w("")
    w("## What each arm read")
    w("")
    w("Passages = distinct passage ids the generator was given (generation.passages; for the RLMs it equals "
      "rlm.passages_seen on all 405 RLM-10 records). Tokens = generation.prompt_tokens (for the RLMs, the sum over "
      "their calls). Every key paper read = all the key's source_files among the passages' papers (store metadata "
      f"file_name; {R['reading']['passage_ids']} passage ids, {R['reading']['unmapped_passage_ids']} unmapped).")
    w("")
    w("| Set | Arm | answers | passages median (min to max) | input tokens median | answer characters median | "
      "every key paper read | per draw |")
    w("|---|---|---:|---|---:|---:|---|---|")
    for name in ("all answerable", "one-paper", "many-paper"):
        for c in ARMS:
            r = R["reading"]["by_set"][name][c]
            pdraw = "; ".join(f"d{d} {v[0]}/{v[1]}" for d, v in r["every_key_paper_read_per_draw"].items())
            w(f"| {name} | {LABEL[c]} | {r['answers']} | {r['passages_median']:g} ({r['passages_min']} to "
              f"{r['passages_max']}) | {r['prompt_tokens_median']:g} | {r['answer_chars_median']:g} | "
              f"{r['every_key_paper_read']} "
              f"({pct(r['every_key_paper_read_share'])}%) | {pdraw} |")
    w("")
    b = R["budget"]
    w("G2's input tokens over RLM-10's median input tokens of the same question (its three draws as stored now): "
      + "; ".join(f"{name}: median {v['ratio_median']:.3f} (range {v['ratio_min']:.3f} to {v['ratio_max']:.3f}), "
                  f"{v['g2_below_rlm10_median']} of {v['answers']} answers below" for name, v in
                  b["g2_tokens_over_rlm10_median_now"].items()) + ".")
    w("")
    w(f"The plan ({b['plan']['made']}, scope {b['plan']['scope']}, top_k {b['plan']['k_min']} to "
      f"{b['plan']['k_max']}, {b['plan']['count_method']}): floor-bound questions {len(b['plan']['floor_bound'])}, "
      f"no target {len(b['plan']['no_target'])}, RLM-10 answers excluded as sources {len(b['plan']['excluded'])}: "
      + ", ".join(f"{e['answer_key'].split('|', 2)[2]} ({e['kind']})" for e in b["plan"]["excluded"])
      + f". Reached: {b['reached']['at_or_above_target']} of {b['reached']['answers']} answers at or above the "
      f"target, {b['reached']['at_planned_tokens']} at the planned tokens; below the target: "
      + ", ".join(f"{x['answer_key'].split('|', 2)[2]} {x['reached_tokens']} of {x['target_tokens']:g}"
                  for x in b["reached"]["below_target"]) + ".")
    w("")
    w("## The 9 answers without a judge-with-passages (b) score")
    w("")
    w("All 405 G2 answers have their plain-call (a) score, which every pass rate here uses; nothing is excluded from "
      "a pass rate or a concept recall. The 9 are (b) calls (the judge with the passages, used for faithfulness, not "
      "read here), each refused by the server as longer than the context:")
    w("")
    w("| Question | Draw | Category | Set | Error | Prompt tokens (num_ctx 131,072) |")
    w("|---|---:|---|---|---|---:|")
    for e in R["unjudged_b"]:
        w(f"| {e['question_id']} | {e['draw']} | {e['category']} | {e['kind']}-paper | {e['error_type']} | "
          f"{e['n_prompt_tokens']:,} |")
    w("")
    w(f"Many-paper: {sum(1 for e in R['unjudged_b'] if e['kind'] == 'many')}; one-paper: "
      f"{sum(1 for e in R['unjudged_b'] if e['kind'] == 'one')}.")
    w("")
    w("## Key v2.5 (D188-R1): each answer's key v2.5 row where one exists, else its key v2.4 row")
    w("")
    w(f"This section reads G2's {v25['merge']['kept']} answers plus G13's {v25['merge']['replaced']} replanned ones "
      "(D236, D237; scripts/g13_merge.py), G13's judge rows in place of G2's for those answers.")
    w("")
    w("Reproduced before the merge, G2 unmerged (REPRODUCE FIRST): "
      + R["v25_before_g13"]["reproduced"].removeprefix("key v2.5 before G13: ") + ".")
    w("")
    w(f"Read through scripts/judge_rows_v25.py: {v25['judge_rows']}. Everything above stays on key v2.4 under the gate.")
    w("")
    w("| Threshold | Failed answers | d (G2 minus RLM-10), points | 95% interval | exact two-sided sign-flip P | "
      "questions G2 higher / RLM-10 higher / equal | n |")
    w("|---|---|---:|---|---:|---|---:|")
    for t in THRESHOLDS:
        for how, p in v25["prefixed_rule"][str(t)].items():
            w(f"| {t} | {how} | {100 * p['d']:+.1f} | [{100 * p['lo']:+.1f}, {100 * p['hi']:+.1f}] | "
              f"{p['p_signflip_exact_two_sided']:.4g} | {p['a_higher']} / {p['b_higher']} / {p['equal']} | "
              f"{p['questions']} |")
    w("")
    w("| Threshold | Arm | Set | Pooled % (95% interval) | n questions (answers) |")
    w("|---:|---|---|---|---|")
    for t in THRESHOLDS:
        for name in ("all answerable", "one-paper", "many-paper"):
            for c in ARMS:
                s = v25["pass"][str(t)][name][c]
                w(f"| {t} | {LABEL[c]} | {name} | {pct(s['rate'])} [{pct(s['lo'])}, {pct(s['hi'])}] | {s['questions']} "
                  f"({s['answers']}) |")
    w("")
    for t in THRESHOLDS:
        g = v25["gap_closed"][str(t)]["many-paper"]
        w(f"Gap closed on the many-paper questions at {t}: {pct(g['ratio'])}%, 95% interval [{pct(g['lo'])}, "
          f"{pct(g['hi'])}]; n = {g['questions']} questions.")
    w("")
    w("## Inputs (sha256)")
    w("")
    for k, v in R["_provenance"]["inputs_sha256"].items():
        w(f"- `{k}` {v}")
    w("")
    w(f"Command: `{R['_provenance']['command']}`")
    path.write_text("\n".join(L) + "\n")


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, Fraction):
        return float(x)
    return x


def main(argv=None) -> int:
    t0 = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        qs = questions()
        g1, meta_g1 = read_collect(RECOMPUTE / "fig2_inputs" / "g1_collect.jsonl", G1, qs, G1_COLLECT_SHA)
        if sha256_file(G2_COLLECT.with_name(G2_COLLECT.name + ".json")) != G2_SIDE_SHA:
            raise Refused("G2's collect sidecar is not the copied one")
        g2, meta_g2 = read_collect(G2_COLLECT, [G2], qs, G2_COLLECT_SHA)
        diff = [q for q in qs if meta_g1["key_hash"][q] != meta_g2["key_hash"][q] or len(meta_g1["key_hash"][q]) != 1]
        if diff:
            raise Refused(f"G1 and G2 were judged on different keys for {len(diff)} questions, first {diff[0]}")
        recs, info = read_records()
        cells = {**g1, **g2}
        check_records(cells, recs)
        gate_res = gate(g1, qs, recs)           # REPRODUCE FIRST: a GateFail stops here, nothing written
        res = compute(cells, qs, recs, info, gate_res)
        c25_0, rep25_0 = cells_v25(cells, qs, g13=False)
        res25_0 = scored(c25_0, qs)
        before = reproduce_v25(res25_0)          # REPRODUCE FIRST: G2 unmerged gives the committed v2.5 rates
        recs_m, info_m, merge_rep = read_records_merged(recs, info)
        c25, rep25 = cells_v25(cells, qs)
        res25 = compute(c25, qs, recs_m, info_m, gate_res)
        import g13_merge as M
        res25["budget"]["plan"] = {      # the merged arm was answered under two plans (D236, D237)
            "g2": {**res25["budget"]["plan"], "answers": merge_rep["kept"]},
            "g13": {"sha256": M.NEW_PLAN_SHA, "answers": merge_rep["replaced"], "file": "not available locally"}}
        _, rk_sha = ranking_v24()
    except Refused as e:
        print(f"REFUSED: {e}")
        return 2
    except GateFail as e:
        print(f"GATE FAILED (nothing written): {e}")
        return 1
    import fig_repro as FR
    inputs = {**info_m["sha256"], rel(G2_COLLECT): G2_COLLECT_SHA, rel(G2_COLLECT) + ".json": G2_SIDE_SHA,
              "findings/recompute/fig2_inputs/g1_collect.jsonl": G1_COLLECT_SHA,
              "findings/recompute/fig2_inputs/g1_collect.jsonl.json":
                  sha256_file(RECOMPUTE / "fig2_inputs" / "g1_collect.jsonl.json"),
              rel(L3): sha256_file(L3), f"{RANKING_V24_AT}:{rel(RANKING)}": rk_sha, rel(REPORT): sha256_file(REPORT),
              "findings/recompute/fig3_s6_inputs/SHA256SUMS": sha256_file(FROZEN_S6 / "SHA256SUMS"),
              "data/ground_truth_v2/ground_truth_v2_4_as_v1.json":
                  sha256_file(ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json"),
              STORE_KEY: STORE_SHA, "experiments/LOCK.toml": sha256_file(ROOT / "experiments/LOCK.toml"),
              **info["sha256"]}
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    R = {"_provenance": {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)), "at": t0, "git_head": head,
                         "command": f"uv run --frozen python {SCRIPT}", "inputs_sha256": inputs,
                         "g2_collect_made_by": "s3_guard.py collect --out findings/recompute/S3_runs/out_g2 --set G2 "
                                               "in the Studio's ~/projects/mentori-runs-s3 at dacef7e, UV_PYTHON=3.13.5",
                         "g2_collect_at": meta_g2["read"]["collected_at"], "phase": "exploratory (no rule changed)"},
         "design": {"D36": "experiments/README.md:60", "D51": "experiments/README.md:90-91",
                    "D75 Q79 to Q81": "experiments/runner/matched_budget.py:12-40",
                    "prefixed_rule": "LIST.md Rule 3 (:253-275), Rule 5 (:277-286), Rule 6 (:310-311), Rule 8, Rule 10",
                    "split": "many-paper = key category cross_document or synthesis (26), one-paper = factual_recall, "
                             "technical, conceptual (60)"},
         "judge_rows": {"G1": meta_g1["read"], "G2": meta_g2["read"]},
         "gate": {"passed": True, "lines": gate_res["lines"]},
         "prefixed_rule": res["prefixed_rule"], "pass": res["pass"], "pairs": res["pairs"],
         "gap_closed": res["gap_closed"], "concept_recall": res["concept_recall"], "reading": res["reading"],
         "budget": res["budget"], "unjudged_b": b_errors(meta_g2, qs),
         "v25": {"arm": "G2's 390 answers and G13's 15 (D236, D237; scripts/g13_merge.py), G13's 15 judge rows in "
                        "place of G2's 15", "merge": merge_rep,
                 "judge_rows": rep25, "pass": res25["pass"], "pairs": res25["pairs"], "gap_closed": res25["gap_closed"],
                 "prefixed_rule": res25["prefixed_rule"], "concept_recall": res25["concept_recall"],
                 "reading": res25["reading"], "budget": res25["budget"]},
         "v25_before_g13": {"reproduced": before, "judge_rows": rep25_0, "pass": res25_0["pass"],
                            "pairs": res25_0["pairs"], "gap_closed": res25_0["gap_closed"],
                            "prefixed_rule": res25_0["prefixed_rule"]}}
    R = jsonable(R)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(R, indent=1, ensure_ascii=False) + "\n")
    write_md(OUT / "results.md", R)
    print("GATE PASSED: " + " | ".join(gate_res["lines"] + [before]))
    print(f"G13: {merge_rep['replaced']} of G2's answers replaced, {merge_rep['kept']} kept; v2.5 judge rows "
          f"{rep25['G2'].get('g13', {}).get('replaced')} replaced (were {rep25['G2'].get('g13', {}).get('replaced_rows_were')})")
    print(f"WROTE {rel(OUT / 'results.json')} and {rel(OUT / 'results.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
