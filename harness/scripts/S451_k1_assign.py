#!/usr/bin/env python3
"""S451: K1's assignment of Figure 5's questions to two stages and three machines (D83 Q142, D86), written before
scoring, with the stage 1 sizing and the G1 gate the launchers check.

    uv run python scripts/S451_k1_assign.py size --runs <six G1 sinks> --store <chroma dir> [--immutable]
                [--target-end ISO] [--start studio=ISO beelink=ISO laptop=ISO] [--rc-factor m=x ...]
                [--ragas-factor m=x ...] [--confidence 0.95] [--s2-laptop <clone>] [--stage-1 m=n ...]
                                                      # the sizing table; writes findings/recompute/K1/sizing.json
    uv run python scripts/S451_k1_assign.py write     # findings/recompute/K1/assignment.json from sizing.json
                                                      # (refuses to change an existing file)
    uv run python scripts/S451_k1_assign.py check     # recompute and compare; exit 1 on any difference; prints
                                                      # each machine's stage 1 and stage 2 hours and end times
    uv run python scripts/S451_k1_assign.py gate --records <dir>
                                                      # G1's draw 1 is final (Q151 rerun ended after it started)
    uv run python scripts/S451_k1_assign.py plan --runs <dir> --store <dir> [--immutable]
                                                      # hours per machine and stage; no model call, no write
  helpers (Valerio, 17 October; findings/recompute/K1/README.md "Helping K1" gives the commands in order)
    ... genesis                                       # amendments.json's genesis (refuses to change an existing one)
    ... estimates --runs <dir> --store <dir> --immutable
                                                      # estimates.json: per answer, the RAGChecker and RAGAS seconds the
                                                      # sizing used; refused unless they give question_cost_h again
    ... worker --worker W [--fields]                  # the launcher's lookup: machine, port, clone, head, fence state
    ... fence --worker W                              # in W's clone, W stopped: lock, hash, questions begun
    ... move --from W --to T [--new] --questions N [--stage 1|2] --fence-from <dir> [--fence-to <dir>]
             [--progress <dir>] --reason "..."        # on the coordinator: appends a move to amendments.json
    ... abandon --worker W --fence <dir> --reason "..."   # on the coordinator: a fence no move will use
    ... release --worker W [--abandon]                # in W's clone, after the amended file is checked out there
    ... progress --worker W                           # in W's clone: JSON for suggest
    ... suggest --progress <dir> [--free studio:11451 ...] [--min-gain-h 12]
                                                      # on the coordinator: proposed moves; writes nothing

HELPERS. A worker is a name bound to (machine, port, clone): the three machines are the first three workers, a helper is
<machine>_<port> on the Studio (the only machine with several Ollama servers). assignment.json is never edited; the
moves are records of findings/recompute/K1/amendments.json, signed and chained (experiments/scorers/assignment.py
load_chain), each made from a fence of its source (and of its target when that exists): a question moves only if its
source has not begun it (no row, no call record naming it, not the next question after a call record naming none), the
last N in the source's order of work, a stage 1 question only to end stage 1 sooner (project(), the same projection
suggest uses: the sizing's per-answer estimates, estimates.json, times each worker's measured rate). MOVE_RULE below is
the rule's text, signed into the genesis. CHECK also verifies the chain, the genesis (registry, move rule, lock) and the
estimates, and prints each worker's effective hours once a move exists.

THE DECISIONS. D83 (Q142): split by question, a rule written before scoring, all six strategies' answers to a question
on one machine one after another, the machine in every record. D86 (Q183, 17 October): two stages. Stage 1 is a subset
of the 96 questions drawn at random before any scoring (seeded, balanced across categories), sized so it surely ends
by the target; stage 2, the rest, runs after it. Three machines: Studio, Beelink, and the laptop once its S2 variant
ends.

THE RULE (RULE below, hashed into the file; compute()). The 96 are the questions Rule 8 applies RAGAS and RAGChecker
to, in the answer key's order.
  stage draw   Each question is ranked by sha256("<SEED>|<question id>") (hex, lowest first): the seeded random
               order, the same in any language. Stage 1 takes, from each category, its quota of lowest ranks; the
               quotas are the stage 1 size split over the categories in proportion to their sizes (largest remainder,
               ties to the category first in the key). Stage 2 is the rest.
  stage 1      The stage 1 questions are listed by category (in the key's order of categories), then in the key's
  machines     order, and dealt to the machines one by one: each goes to the machine furthest behind its share (its
               stage 1 size times the position over the stage's length, less what it holds; ties in MACHINES order),
               so every category is split over the machines in proportion to their stage 1 sizes. compute() refuses
               unless every (stage 1, category, machine) count is within one question of that proportion (|count -
               proportion| <= 1).
  stage 2      Dealt so the machines END stage 2 as close together as the questions allow (D86 review D1, 17 October;
  machines     the first D86 file split stage 2 by questions per hour, which left the ends 2.9 days apart). A
               machine's projected end starts at its start plus the estimated hours of its stage 1 questions. The
               stage 2 questions are taken largest first (a question's cost here is the largest of its three machine
               costs c_qm, SIZE below; ties in the key's order), and each goes to the machine whose projected end is
               then the earliest (ties in MACHINES order), whose projected end grows by c_qm. A question is one unit:
               its six answers go to one machine (Q142). The guarantee: the machine that ends last took its last
               question when it was the earliest, so the latest end exceeds every other end by at most that
               question's cost; compute() refuses unless the spread of the stage 2 ends is at most the largest cost
               of a stage 2 question on the machine it went to (it can fail only if a machine's stage 1 alone ends
               after every other machine's whole stage 2). Stage 2 is not balanced by category: a question's six
               strategies are compared on one machine whatever its category.
  order        Each machine scores its stage 1 questions, then its stage 2 questions, each stage in the key's order,
               the six configs in G1's order inside a question (single_pass, multi_hop, verified_pass, rlm_5, rlm_10,
               rlm_20).
The stage 1 sizes and the deal's inputs (each machine's start, each question's estimated hours per machine, the factors
and the answers' sha256 they came from) come from SIZE (sizing.json); the seed is SEED. All are signed into the file
with the questions (stage_2_inputs), so CHECK recomputes the whole file from the pinned key, the seed, the stage 1
sizes and those inputs. SIZE does not read any score: it reads the answers' lengths and passage counts, and the
timings below.

SIZE: STAGE 1 SIZE PER MACHINE. A machine m starts at start_m and must end stage 1 by the target, so it has
H_m = target - start_m hours. A question costs it c_qm = sum over the question's six answers of
(RAGChecker seconds x RC_FACTOR[m] + RAGAS seconds x RAGAS_FACTOR[m]). Its stage 1 count n_m is the largest n for which
the CONFIDENCE quantile (default 0.95) of the cost of n questions drawn at random from the 96 (MC_DRAWS draws, seed
MC_SEED) is at most H_m; the size rounds down. --stage-1 gives the counts instead (the fitted n is still printed),
so a sizing on new answers can keep a stage 1 already drawn. Stage 1 is the sum. Stage 2 is the other questions,
dealt by the stage 2 rule above from c_qm and the starts; SIZE prints each machine's stage 1 and stage 2 hours and
ends for the questions actually dealt (point estimates at the upper end per answer; the p50 and p95 SIZE prints are
of random draws of n questions, the sizing's, not of the drawn ones).
  per answer (the upper end, as D86 asks: "surely finish")
    RAGChecker  checking calls = (answer characters / 64 + reference characters / 43) x (passages + 1), RefChecker's
                four steps (K0 timing: 1,045 = 95 x 11 for single_pass 01_sarek_CO2); 64 characters per response
                claim is the K0 timing answers' figure (G1-style answers; the upper end of the two observed, R0's
                S357 answers give 125). Seconds per checking call 1.868, claims order (D86, Q143): R0's Beelink rows
                90 to 179 (57 rows, 56 of them RLM answers; 29.5 passages of 1,818 characters on average; read 17 October 15:08):
                wall over checking calls, so the extraction calls are inside it, and higher than K0's 1.789 on
                whole-passage single-pass answers. Plus 200 s per answer (K0 timing: answer wall less checking calls x
                seconds per call, 177 to 283 s). 0 for an answer stored as an error (not scored).
    RAGAS       seconds = 52.2 + 10.13 x context kchars + 41.2 x answer kchars on the Studio (least squares over the 100
                R0 Studio rows, R^2 0.55).
  per machine (RC_FACTOR on RAGChecker seconds, RAGAS_FACTOR on RAGAS seconds; both settable)
    beelink   1.0 and 3.0. RAGAS: the K1 note of plan.csv, "RAGAS 3x faster on the Studio"; measured 2.30 (ratio of
              sums) on the 62 R0 rows the Beelink (attempts 3 and 4, 15 October) and the Studio both scored, so 3.0
              is the upper end.
    studio    1.06 and 1.0. RAGChecker: R0, 15 October, 1.018 s per checking call on the Studio against 0.96 on the
              Beelink (short passages), measured while the Studio GPU was shared with R0's RAGAS and S2. ASSUMPTION:
              the same ratio holds with three S2 variants on the GPU (11451, 11452, 11454) and whole passages;
              UNVERIFIED. RAGAS: the fit is the Studio's own rows (shared GPU then too).
    laptop    1.0 and 3.0: UNVERIFIED, assumed the Beelink's. The laptop has no R0 history. Its S2 devstral calls give
              prompt rates from 349 to 1,058 tokens per second depending on the strategy (cache and context
              effects), against the Beelink's 875 on checking calls, too mixed to stand for a checking call.
  starts    studio and beelink: the time SIZE runs plus SETUP_H (2 h: the Q151 rerun's end, the copy, R0's stop on the
            Beelink, the dry runs), unless --start gives one. laptop: when its S2 variant is expected to end
            (laptop_s2_end(), the later of exp05's own ETA and the per-strategy estimate) plus LAPTOP_SETUP_H.
  target    26 October 2026 18:00 CEST as given (16:00 UTC). Summer time ends on 25 October, so the clocks then show
            17:00 CET: the earlier of the two readings.

GATE. G1's draw 1 is final when, in the records directory (the Studio's findings/recompute/G1_runs, or the copy the
inputs carry in g1_records/): every config's g1_<config>.end.json has rc 0 and ends after its g1_<config>.start.json;
and g1_multi_hop's start and end are both after the Q151 rerun's start (rerun.json "q151_rerun", written by
rerun_q151.sh into q151_before_rerun_<UTC>/; the copy names it q151_rerun.json). Exit 1 otherwise.

PLAN. As before (the 17 October K1 README's table), per machine and stage, with the D83 constants (claims order low
and high, passage order) for comparison.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.runner import experiment as ex  # noqa: E402
from experiments.scorers import assignment as A  # noqa: E402
from experiments.scorers import records as R  # noqa: E402

K1 = ROOT / "findings" / "recompute" / "K1"
OUT = K1 / "assignment.json"
SIZING = K1 / "sizing.json"
MACHINES = ["studio", "beelink", "laptop"]       # tie order when dealing
CONFIGS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]   # G1's six, exp_01 order
DRAWS = [1]                                      # D80 V10: draw 1 only
INDEX = "exp_v4_s20_n0"
SEED = "K1 D86 stage draw, 17 October 2026"
RULE = (
    "K1 (D83 Q142, D86). The questions are the 135 of answer key v2.4 (experiments/runner/experiment.py questions(), "
    "in the key's order) to which Rule 8 applies RAGAS and RAGChecker (experiments/scorers/records.py APPLIES: "
    "answerable and false_premise): 96. The other 39 are listed as not scored, with the reason. Stage draw: each "
    "question is ranked by the sha256 hex of the seed, a '|' and its id, lowest first; stage 1 takes from each "
    "category its quota of lowest ranks, the quotas being the stage 1 size split over the categories in proportion "
    "to their sizes (largest remainder, ties to the category first in the key); stage 2 is the rest. Stage 1 "
    "machines: the stage 1 questions are listed by category (the key's order of categories), then in the key's order, "
    "and each goes to the machine furthest behind its share (its stage 1 size times the position over the stage's "
    "length, less what it holds; ties in the order studio, beelink, laptop); every (stage 1, category, machine) count "
    "must be within one question of its proportion, or nothing is written. Stage 2 machines: each machine's projected "
    "end starts at its start (stage_2_inputs) plus the estimated hours of its stage 1 questions; the stage 2 questions "
    "are taken largest first (a question's cost the largest of its estimated hours on the three machines; ties in the "
    "key's order) and each goes to the machine whose projected end is then the earliest (ties in the order studio, "
    "beelink, laptop), whose end grows by the question's estimated hours on it; the spread of the stage 2 ends must be "
    "at most the largest estimated hours of a stage 2 question on the machine it went to, or nothing is written. The "
    "estimates are stage_2_inputs' question_cost_h. Every answer of draw 1 to a question, in the six "
    "configs single_pass, multi_hop, verified_pass, rlm_5, rlm_10 and rlm_20, is scored on that question's machine, "
    "one after another in that config order; each machine takes its stage 1 questions, then its stage 2 questions, "
    "each stage in the key's order.")

# D83 planning constants (PLAN; the 17 October README's table)
RC_CHARS_PER_CLAIM = {"low": 125.0, "high": 64.0}
GT_CHARS_PER_CLAIM = 43.0
RC_S_PER_CHECK = {"claims": 1.789, "passage": 0.530}
RC_OVERHEAD_S = 200.0
RAGAS_FIT = (52.2, 10.13, 41.2)                   # s = a + b * context kchars + c * answer kchars (Studio)
RAGAS_BEELINK_FACTOR = 3.0
# D86 sizing (SIZE in the docstring): the upper end per answer, factors per machine
RC_UPPER_CHARS_PER_CLAIM = 64.0
RC_UPPER_S_PER_CHECK = 1.868
RC_FACTOR = {"studio": 1.06, "beelink": 1.0, "laptop": 1.0}
RAGAS_FACTOR = {"studio": 1.0, "beelink": 3.0, "laptop": 3.0}
CONFIDENCE = 0.95
MC_DRAWS, MC_SEED = 20000, 86
TARGET_END = "2026-10-26T18:00:00+02:00"
SETUP_H, LAPTOP_SETUP_H = 2.0, 0.5
S2_LAPTOP = Path.home() / "projects" / "mentori-runs-s2-laptop-d75"
S2_TAG, S2_REF_TAG = "devstral-small-2-24b+default", "gpt-oss-20b+medium"   # the variant, and the one it is scaled from
TZ = ZoneInfo("Europe/Amsterdam")                # the clock end times are reported in (CEST, then CET from 25 October)
S2_TASKS = 20                                    # 220 attempts = 11 strategies x 20 tasks (exp_05, draw 1)


# ---------------------------------------------------------------- the rule

def rank(qid: str, seed: str = SEED) -> str:
    return hashlib.sha256(f"{seed}|{qid}".encode("utf-8")).hexdigest()


def apportion(total: int, weights: dict, order: list) -> dict:
    """total split over the keys of weights in proportion (largest remainder; ties to the key first in order)."""
    w = sum(weights.values())
    exact = {k: total * weights[k] / w for k in order}
    out = {k: int(exact[k]) for k in order}
    for k in sorted(order, key=lambda k: (-(exact[k] - out[k]), order.index(k)))[: total - sum(out.values())]:
        out[k] += 1
    return out


def deal(qs: list[dict], sizes: dict) -> dict:
    """question id -> machine: each question, in the given order, to the machine furthest behind its share."""
    n, held, out = len(qs), {m: 0 for m in MACHINES}, {}
    for i, q in enumerate(qs, 1):
        open_ = [m for m in MACHINES if held[m] < sizes[m]]
        m = max(open_, key=lambda m: (sizes[m] * i / n - held[m], -MACHINES.index(m)))
        held[m] += 1
        out[q["id"]] = m
    return out


def start_hours(starts: dict) -> dict:
    """Each machine's start in hours after the earliest start (the starts are ISO times with a UTC offset)."""
    t = {m: dt.datetime.fromisoformat(starts[m]) for m in MACHINES}
    if any(v.tzinfo is None for v in t.values()):
        raise SystemExit(f"REFUSED: every start needs a UTC offset ({starts})")
    t0 = min(t.values())
    return {m: (t[m] - t0).total_seconds() / 3600 for m in MACHINES}


def deal_stage_2(stage_1: dict, stage_2: list[str], inputs: dict, order: list[str]) -> tuple[dict, dict]:
    """The stage 2 rule (docstring): stage_1 {question id: machine}, stage_2 the stage 2 question ids, order the key's
    order of every question. Returns ({question id: machine} for stage 2, {"stage_1_end_h", "end_h", "bound_h"}),
    the ends in hours after the earliest start."""
    cost = inputs["question_cost_h"]
    end = start_hours(inputs["starts"])
    for q, m in stage_1.items():
        end[m] += cost[m][q]
    end1 = dict(end)
    pos = {q: i for i, q in enumerate(order)}
    out, bound = {}, 0.0
    for q in sorted(stage_2, key=lambda q: (-max(cost[m][q] for m in MACHINES), pos[q])):
        m = min(MACHINES, key=lambda m: (end[m], MACHINES.index(m)))
        out[q] = m
        end[m] += cost[m][q]
        bound = max(bound, cost[m][q])
    return out, {"stage_1_end_h": end1, "end_h": end, "bound_h": bound}


def compute(stage_sizes: dict, inputs: dict, seed: str = SEED) -> dict:
    """The signed content of the assignment, from the pinned key (experiment.py checks both key files' sha256), the
    seed, the stage 1 sizes (stage_sizes["1"], {machine: n}; a "2" given is not read: the deal gives it) and the
    deal's inputs ({"starts": {machine: ISO}, "question_cost_h": {machine: {question id: hours}}, ...})."""
    if R.APPLIES["ragas"] != R.APPLIES["ragchecker"]:
        raise SystemExit("REFUSED: Rule 8 applies RAGAS and RAGChecker to different groups; one assignment cannot serve both")
    qs = [q for q in ex.questions() if R.applies("ragchecker", q["id"])]
    s1 = {m: int(stage_sizes["1"][m]) for m in MACHINES}
    if sum(s1.values()) > len(qs) or any(n < 0 for n in s1.values()):
        raise SystemExit(f"REFUSED: the stage 1 sizes {s1} are not a part of the {len(qs)} questions")
    cost = inputs.get("question_cost_h") or {}
    lacking = [(m, q["id"]) for m in MACHINES for q in qs if not isinstance(cost.get(m, {}).get(q["id"]), (int, float))]
    if lacking or sorted(inputs.get("starts") or {}) != sorted(MACHINES):
        raise SystemExit(f"REFUSED: the deal's inputs lack {len(lacking)} (machine, question) costs (first "
                         f"{lacking[:1]}) or a machine's start ({inputs.get('starts')})")
    cats = list(dict.fromkeys(q["category"] for q in qs))
    n1 = sum(s1.values())
    quota = apportion(n1, Counter(q["category"] for q in qs), cats)
    stage = {}
    for c in cats:
        ranked = sorted((q for q in qs if q["category"] == c), key=lambda q: rank(q["id"], seed))
        for i, q in enumerate(ranked):
            stage[q["id"]] = 1 if i < quota[c] else 2
    inside = sorted((q for q in qs if stage[q["id"]] == 1), key=lambda q: cats.index(q["category"]))  # stable
    machine = deal(inside, s1)
    off = []
    for c in cats:
        in_c = [q for q in qs if q["category"] == c and stage[q["id"]] == 1]
        for m in MACHINES:
            want = len(in_c) * s1[m] / n1 if n1 else 0
            got = sum(machine[q["id"]] == m for q in in_c)
            if abs(got - want) > 1:
                off.append(f"stage 1 {c} {m}: {got}, proportion {want:.2f}")
    if off:
        raise SystemExit(f"REFUSED: the deal leaves {off} a question or more from the proportion; the rule needs "
                         f"Valerio's call")
    two, ends = deal_stage_2(dict(machine), [q["id"] for q in qs if stage[q["id"]] == 2], inputs, [q["id"] for q in qs])
    machine.update(two)
    spread = max(ends["end_h"].values()) - min(ends["end_h"].values())
    if two and spread > ends["bound_h"] + 1e-9:
        raise SystemExit(f"REFUSED: the stage 2 ends are {spread:.1f} h apart, more than the largest question dealt "
                         f"({ends['bound_h']:.1f} h): a machine's stage 1 ends after every other machine's stage 2; "
                         f"the rule needs Valerio's call")
    sizes = {"1": s1, "2": {m: sum(machine[q] == m for q in two) for m in MACHINES}}
    questions = [{"id": q["id"], "category": q["category"], "group": R.group_of(q["id"]), "stage": stage[q["id"]],
                  "machine": machine[q["id"]]} for q in qs]           # the key's order
    not_scored = [{"id": q["id"], "group": R.group_of(q["id"]), "reason": R.NOT_APPLICABLE + " (Rule 8)"}
                  for q in ex.questions() if not R.applies("ragchecker", q["id"])]
    asg = {"rule": RULE, "rule_sha256": A.sha256(RULE), "draws": DRAWS, "configs": CONFIGS, "machines": MACHINES,
           "questions": questions, "not_scored": not_scored, "seed": seed, "stage_sizes": sizes,
           "stage_2_inputs": inputs}
    asg["assignment_sha256"] = A.sha256(A.canonical(asg))
    return asg


def ends(asg: dict) -> dict:
    """Per machine, from the file's own stage_2_inputs: each stage's questions, estimated hours and end (the hours
    are the point estimates of SIZE, upper end per answer)."""
    inp = asg["stage_2_inputs"]
    cost = inp["question_cost_h"]
    out = {}
    for m in asg["machines"]:
        t = dt.datetime.fromisoformat(inp["starts"][m])
        row = {"start": t}
        for k in A.STAGES:
            qs = [q["id"] for q in asg["questions"] if q["stage"] == k and q["machine"] == m]
            h = sum(cost[m][q] for q in qs)
            t = t + dt.timedelta(hours=h)
            row[k] = {"questions": len(qs), "hours": h, "end": t}
        out[m] = row
    return out


def local(t: dt.datetime) -> str:
    """The time on the Dutch clock, with its zone's name (CEST until 25 October 03:00, CET after)."""
    return t.astimezone(TZ).strftime("%a %d %b %H:%M %Z")


def print_ends(asg: dict, sizing: dict | None = None) -> None:
    """Each machine's stage 1 and stage 2 from the written assignment (a report: the file is fixed whatever it says).
    With the sizing, stage 1 also shows the p50 and p95 of n questions drawn at random (the sizing's quantiles)."""
    e = ends(asg)
    print(f"  {'machine':8s} {'start':>20s} | {'stage 1':>3s} {'hours':>6s} {'end':>20s} | {'stage 2':>3s} {'hours':>6s} "
          f"{'end':>20s}")
    for m, r in e.items():
        print(f"  {m:8s} {local(r['start']):>20s} | {r[1]['questions']:7d} {r[1]['hours']:6.1f} {local(r[1]['end']):>20s} | "
              f"{r[2]['questions']:7d} {r[2]['hours']:6.1f} {local(r[2]['end']):>20s}")
    last = [r[2]["end"] for r in e.values()]
    print(f"  stage 2 ends {(max(last) - min(last)).total_seconds() / 3600:.1f} h apart (the deal's guarantee: at most "
          f"the largest stage 2 question on its machine, {deal_bound(asg):.1f} h)")
    for m, r in (e.items() if sizing else ()):
        sm = sizing["machines"][m]
        p = lambda h: local(r["start"] + dt.timedelta(hours=h))                                  # noqa: E731
        print(f"  {m}: sizing, {sm['stage_1']} questions drawn at random: p50 {sm['stage_1_h_p50']} h (ends "
              f"{p(sm['stage_1_h_p50'])}), p{sizing['confidence'] * 100:g} {sm['stage_1_h_quantile']} h (ends "
              f"{p(sm['stage_1_h_quantile'])}); target "
              f"{local(dt.datetime.fromisoformat(sizing['target_end']))}")


def deal_bound(asg: dict) -> float:
    cost = asg["stage_2_inputs"]["question_cost_h"]
    return max((cost[q["machine"]][q["id"]] for q in asg["questions"] if q["stage"] == 2), default=0.0)


def counts(asg: dict) -> dict:
    qs, ms = asg["questions"], asg["machines"]
    cats = list(dict.fromkeys(q["category"] for q in qs))
    out = {"questions": len(qs), "not_scored": len(asg["not_scored"])}
    for k in A.STAGES:
        sq = [q for q in qs if q.get("stage") == k]
        out[f"stage_{k}"] = {"questions": len(sq), "per_machine": {m: sum(q["machine"] == m for q in sq) for m in ms},
                             "answers_per_machine": {m: sum(q["machine"] == m for q in sq) * len(asg["configs"])
                                                     * len(asg["draws"]) for m in ms},
                             "per_category": {c: {m: sum(q["category"] == c and q["machine"] == m for q in sq)
                                                  for m in ms} for c in cats},
                             "per_group": {g: sum(q["group"] == g for q in sq) for g in dict.fromkeys(q["group"] for q in qs)}}
    return out


def rel(p: Path) -> str:
    p = p.resolve()
    return str(p.relative_to(ROOT)) if ROOT in p.parents else str(p)


def cmd_write(a) -> int:
    try:
        sizing = json.loads(Path(a.sizing).read_text())
    except (OSError, ValueError) as e:
        print(f"REFUSED: cannot read the sizing ({e}); run `S451 size` first")
        return 1
    if "stage_2_inputs" not in sizing:
        print("REFUSED: the sizing has no stage_2_inputs (written before the stage 2 deal, D86 review D1); run "
              "`S451 size` again")
        return 1
    asg = compute(sizing["stage_sizes"], sizing["stage_2_inputs"])
    if asg["stage_sizes"] != sizing["stage_sizes"]:
        print(f"REFUSED: the deal gives stage sizes {asg['stage_sizes']}, the sizing says {sizing['stage_sizes']}")
        return 1
    if OUT.exists():
        old = A.load(OUT)
        if old["assignment_sha256"] == asg["assignment_sha256"]:
            print(f"unchanged: {OUT.relative_to(ROOT)} already holds assignment {asg['assignment_sha256'][:12]}")
            return 0
        print(f"REFUSED: {OUT.relative_to(ROOT)} holds assignment {old['assignment_sha256'][:12]}, this script now "
              f"computes {asg['assignment_sha256'][:12]}; the rule is fixed before scoring, so it is not overwritten")
        return 1
    doc = {"_provenance": {"script": "scripts/S451_k1_assign.py", "script_sha256": A.sha256(Path(__file__).read_bytes()),
                           "written": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                           "decision": "D83 (Q142), D86 (Q183), experiments/README.md",
                           "inputs": {"key_v24": [str(ex.KEY_V24.relative_to(ROOT)), ex.KEY_V24_SHA256],
                                      "key_d5": [str(ex.KEY_D5.relative_to(ROOT)), ex.KEY_D5_SHA256],
                                      "sizing": [rel(Path(a.sizing)), A.sha256(Path(a.sizing).read_bytes())]},
                           "sizing_summary": {k: sizing.get(k) for k in ("computed", "target_end", "starts",
                                                                         "confidence", "stage_1_size")}},
           **asg, "counts": counts(asg)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    A.load(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}: assignment {asg['assignment_sha256'][:12]}, rule {asg['rule_sha256'][:12]}, "
          f"seed {asg['seed']!r}")
    print(json.dumps(counts(asg)))
    print_ends(asg, sizing)
    return 0


def cmd_check(a) -> int:
    try:
        old = A.load(OUT)
        if not A.staged(old) or "stage_2_inputs" not in old:
            raise A.AssignmentError(f"{OUT} has no stages or no stage_2_inputs (a D83 file, or D86's first form); "
                                    f"D86 needs the stage 2 deal's")
    except (A.AssignmentError, FileNotFoundError) as e:
        print(f"CHECK FAILED: {e}")
        return 1
    asg = compute(old["stage_sizes"], old["stage_2_inputs"])
    ok = old["assignment_sha256"] == asg["assignment_sha256"] and all(old[k] == asg[k] for k in A.SIGNED + A.STAGED)
    print(f"{OUT.relative_to(ROOT)}: assignment {old['assignment_sha256'][:12]}, recomputed {asg['assignment_sha256'][:12]}"
          f", rule {old['rule_sha256'][:12]}, seed {old['seed']!r}")
    print(json.dumps(counts(old)))
    print_ends(old)
    why = check_chain(old)
    for w in why:
        print(f"  {w}")
    print("CHECK PASSED" if ok and not why else "CHECK FAILED: the file is not what the rule gives now" if not ok
          else "CHECK FAILED: the amendment chain or the estimates")
    return 0 if ok and not why else 1


# ---------------------------------------------------------------- per answer estimates

def estimate(x: dict, ref: str) -> dict:
    """Planning estimate for one answer: the D83 constants (PLAN) and the D86 upper end (SIZE)."""
    scored = x["status"] == "ok" and x["passages_kind"] in ("ids", "none") and bool(ref.strip())
    p = len(x["passages"] or [])
    ctx = sum(len(q["text"] or "") for q in x["passages"] or [])
    out = {"question_id": x["question_id"], "config": x["config"], "status": x["status"], "passages": p,
           "context_chars": ctx, "answer_chars": len(x["answer"] or ""), "scored": scored,
           "k1_stage": x.get("k1_stage")}
    if not scored:
        return {**out, "checks": {"low": 0, "high": 0}, "rc_s": {}, "rc_upper_s": 0.0, "ragas_s": 0.0}
    gc = len(ref) / GT_CHARS_PER_CLAIM
    checks = {k: (len(x["answer"]) / v + gc) * (p + 1) for k, v in RC_CHARS_PER_CLAIM.items()}
    rc_s = {f"{o}_{k}": checks[k] * s + RC_OVERHEAD_S for o, s in RC_S_PER_CHECK.items() for k in checks}
    upper = (len(x["answer"]) / RC_UPPER_CHARS_PER_CLAIM + gc) * (p + 1) * RC_UPPER_S_PER_CHECK + RC_OVERHEAD_S
    a0, b, c = RAGAS_FIT
    return {**out, "checks": checks, "rc_s": rc_s, "rc_upper_s": upper,
            "ragas_s": a0 + b * ctx / 1000 + c * len(x["answer"]) / 1000}


def read_estimates(runs: str, store: str | None, immutable: bool) -> list[dict]:
    refs = {q["id"]: q.get("expected_answer", "") for q in json.loads(ex.KEY_D5.read_text())["questions"]}
    keep = {q["id"] for q in ex.questions() if R.applies("ragchecker", q["id"])}
    est = []
    for c in CONFIGS:
        for x in R.read_run(Path(runs) / f"exp_01__{c}__{INDEX}", store=Path(store) if store else None,
                            immutable=immutable):
            if x["draw"] in DRAWS and x["question_id"] in keep:
                est.append(estimate(x, refs.get(x["question_id"], "")))
    got = Counter((e["question_id"], e["config"]) for e in est)
    if len(got) != len(keep) * len(CONFIGS) or any(n != 1 for n in got.values()):
        raise SystemExit(f"REFUSED: the runs hold {len(got)} (question, config) answers of draw 1, not "
                         f"{len(keep) * len(CONFIGS)} each once")
    return est


# ---------------------------------------------------------------- the laptop's S2 variant

def _s2_answers(clone: Path, strategy: str, tag: str) -> list[dict]:
    f = clone / "findings" / "runs" / f"exp_05__{strategy}__{tag}" / "answers.json"
    try:
        return [x for x in json.loads(f.read_text())["results"] if x.get("latency_s") is not None and x.get("draw") == 1]
    except (OSError, ValueError, KeyError):
        return []


def laptop_s2_end(clone: Path, now: dt.datetime) -> dict:
    """When the laptop's S2 variant (S2_TAG) is expected to end, two ways; start = the later.
    exp05     its own ETA on the last progress line of exp05.log, from the log's last write.
    strategy  sum over the 11 strategies of (20 - attempts stored) x a time per attempt: the variant's own mean in a
              strategy with at least 10 stored attempts, else S2_REF_TAG's mean there (laptop, full run) times R, the
              variant's latency over S2_REF_TAG's on the attempts both stored. From now: the running attempt's elapsed
              time is not subtracted."""
    log = clone / "findings" / "recompute" / "S2_launch_laptop" / f"ollama--{S2_TAG}" / "exp05.log"
    out: dict = {"log": str(log)}
    try:
        lines = [ln for ln in log.read_text(errors="replace").splitlines() if re.search(r"\[\d+/\d+\]", ln)]
        m = re.search(r"\[(\d+)/(\d+)\] (\S+) .*ETA: ([\d.]+)h", lines[-1])
        t = dt.datetime.fromtimestamp(log.stat().st_mtime).astimezone()
        out.update(progress=f"{m.group(1)}/{m.group(2)}", last_line_strategy=m.group(3),
                   exp05_eta_end=(t + dt.timedelta(hours=float(m.group(4)))).isoformat(timespec="minutes"))
    except (OSError, IndexError, AttributeError) as e:
        out["exp05_error"] = f"{type(e).__name__}: {e}"
    runs = sorted((clone / "findings" / "runs").glob(f"exp_05__*__{S2_TAG}"))
    strategies = [p.name.split("__")[1] for p in runs]
    own = {s: _s2_answers(clone, s, S2_TAG) for s in strategies}
    ref = {s: _s2_answers(clone, s, S2_REF_TAG) for s in strategies}
    pairs = [(a["latency_s"], b["latency_s"]) for s in strategies for a in own[s] for b in ref[s]
             if a.get("op_id") == b.get("op_id")]
    ratio = sum(a for a, _ in pairs) / sum(b for _, b in pairs) if pairs else None
    rem_s, per = 0.0, {}
    for s in strategies:
        n_rem = max(0, S2_TASKS - len(own[s]))
        if len(own[s]) >= 10:
            t_s, how = sum(x["latency_s"] for x in own[s]) / len(own[s]), "own mean"
        elif ref[s] and ratio:
            t_s, how = ratio * sum(x["latency_s"] for x in ref[s]) / len(ref[s]), f"{S2_REF_TAG} mean x {ratio:.2f}"
        else:
            t_s, how = None, "no timing"
        per[s] = {"stored": len(own[s]), "remaining": n_rem, "s_per_attempt": None if t_s is None else round(t_s),
                  "how": how}
        if n_rem and t_s is None:
            out["strategy_error"] = f"no timing for {s}"
        rem_s += n_rem * (t_s or 0)
    out.update(strategies=per, ratio_to_ref=None if ratio is None else round(ratio, 2), pairs=len(pairs),
               strategy_remaining_h=round(rem_s / 3600, 1),
               strategy_end=(now + dt.timedelta(seconds=rem_s)).isoformat(timespec="minutes"))
    ends = [dt.datetime.fromisoformat(out[k]) for k in ("exp05_eta_end", "strategy_end") if k in out]
    if not ends or "strategy_error" in out:
        out["end"] = None
    else:
        out["end"] = max(ends).isoformat(timespec="minutes")
    return out


# ---------------------------------------------------------------- SIZE

def quantile_cost(costs: list[float], n: int, q: float, draws: int, seed: int) -> float:
    """The q quantile of the summed cost of n questions drawn at random without replacement (seeded)."""
    if n == 0:
        return 0.0
    rng = random.Random(seed)
    sums = sorted(sum(rng.sample(costs, n)) for _ in range(draws))
    return sums[min(len(sums) - 1, int(q * len(sums)))]


def parse_kv(pairs: list | None, kind) -> dict:
    out = {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        if k not in MACHINES or not v:
            raise SystemExit(f"REFUSED: '{p}' is not machine=value with a machine of {MACHINES}")
        out[k] = kind(v)
    return out


def cmd_size(a) -> int:
    now = dt.datetime.now().astimezone().replace(second=0, microsecond=0)
    target = dt.datetime.fromisoformat(a.target_end)
    if target.tzinfo is None:
        raise SystemExit("REFUSED: --target-end needs a UTC offset (e.g. +02:00)")
    rc_f = {**RC_FACTOR, **parse_kv(a.rc_factor, float)}
    rg_f = {**RAGAS_FACTOR, **parse_kv(a.ragas_factor, float)}
    given = parse_kv(a.start, dt.datetime.fromisoformat)
    if any(t.tzinfo is None for t in given.values()):
        raise SystemExit("REFUSED: every --start needs a UTC offset (e.g. laptop=2026-10-18T14:00+02:00)")
    starts, why = {}, {}
    for m in ("studio", "beelink"):
        starts[m] = given.get(m) or now + dt.timedelta(hours=SETUP_H)
        why[m] = "--start" if m in given else f"now + {SETUP_H:g} h (setup)"
    s2 = laptop_s2_end(Path(a.s2_laptop), now)
    if "laptop" in given:
        starts["laptop"], why["laptop"] = given["laptop"], "--start"
    elif s2.get("end"):
        starts["laptop"] = dt.datetime.fromisoformat(s2["end"]) + dt.timedelta(hours=LAPTOP_SETUP_H)
        why["laptop"] = f"S2 {S2_TAG} expected end (the later estimate) + {LAPTOP_SETUP_H:g} h"
    else:
        raise SystemExit(f"REFUSED: the laptop's S2 end cannot be estimated ({s2}); give --start laptop=ISO")

    est = read_estimates(a.runs, a.store, a.immutable)
    qids = list(dict.fromkeys(e["question_id"] for e in est))
    cost = {m: {q: 0.0 for q in qids} for m in MACHINES}
    for e in est:
        for m in MACHINES:
            cost[m][e["question_id"]] += (e["rc_upper_s"] * rc_f[m] + e["ragas_s"] * rg_f[m]) / 3600

    # the per-strategy table (per answer, scored answers only, hours on the Beelink and the Studio's RAGAS seconds)
    print(f"K1 stage 1 sizing (D86), {now.isoformat(timespec='minutes')}: {len(est)} answers of draw 1, "
          f"{len(qids)} questions\n")
    print("Per answer, by strategy (upper end; RAGChecker hours at the Beelink's speed, claims order; RAGAS minutes "
          "on the Studio)")
    print(f"  {'strategy':14s} {'scored':>6s} {'passages':>8s} {'answer ch':>9s} {'RC h mean':>9s} {'RC h p90':>8s} "
          f"{'RC h max':>8s} {'RAGAS min':>9s}")
    table = {}
    for c in CONFIGS:
        es = [e for e in est if e["config"] == c and e["scored"]]
        rc = sorted(e["rc_upper_s"] / 3600 for e in es)
        row = {"answers": sum(e["config"] == c for e in est), "scored": len(es),
               "passages_mean": round(sum(e["passages"] for e in es) / max(1, len(es)), 1),
               "answer_chars_mean": round(sum(e["answer_chars"] for e in es) / max(1, len(es))),
               "rc_h_mean": round(sum(rc) / max(1, len(rc)), 2), "rc_h_p90": round(rc[int(0.9 * (len(rc) - 1))], 2),
               "rc_h_max": round(rc[-1], 2), "ragas_min_mean": round(sum(e["ragas_s"] for e in es) / max(1, len(es)) / 60, 1)}
        table[c] = row
        print(f"  {c:14s} {row['scored']:6d} {row['passages_mean']:8.1f} {row['answer_chars_mean']:9d} "
              f"{row['rc_h_mean']:9.2f} {row['rc_h_p90']:8.2f} {row['rc_h_max']:8.2f} {row['ragas_min_mean']:9.1f}")

    print(f"\nPer machine (cost of a question = its six answers; stage 1 count n = the largest n whose "
          f"{a.confidence:.0%} quantile over {MC_DRAWS:,} random draws of n questions fits the hours)")
    print(f"  {'machine':8s} {'RC x':>5s} {'RAGAS x':>7s} {'start':>17s} {'hours':>6s} {'q h mean':>8s} {'q h max':>7s} "
          f"{'n@50%':>5s} {'n@80%':>5s} {'n':>3s} {'n: h p50':>8s} {'h p' + format(a.confidence * 100, 'g'):>7s}  start from")
    machines = {}

    def fit(cs, hours, q, i):
        n = 0
        while n < len(cs) and quantile_cost(cs, n + 1, q, MC_DRAWS, MC_SEED + i) <= hours:
            n += 1
        return n
    for i, m in enumerate(MACHINES):
        cs = list(cost[m].values())
        hours = max(0.0, (target - starts[m]).total_seconds() / 3600)
        mean = sum(cs) / len(cs)
        n = fit(cs, hours, a.confidence, i)
        machines[m] = {"rc_factor": rc_f[m], "ragas_factor": rg_f[m], "start": starts[m].isoformat(timespec="minutes"),
                       "start_from": why[m], "hours": round(hours, 1), "question_h_mean": round(mean, 2),
                       "question_h_max": round(max(cs), 2), "n_at_50": fit(cs, hours, 0.5, i),
                       "n_at_80": fit(cs, hours, 0.8, i), "n": n,
                       "n_h_p50": round(quantile_cost(cs, n, 0.5, MC_DRAWS, MC_SEED + i), 1),
                       "n_h_quantile": round(quantile_cost(cs, n, a.confidence, MC_DRAWS, MC_SEED + i), 1)}
        r = machines[m]
        print(f"  {m:8s} {r['rc_factor']:5.2f} {r['ragas_factor']:7.1f} {r['start'][:16]:>17s} {r['hours']:6.1f} "
              f"{r['question_h_mean']:8.2f} {r['question_h_max']:7.2f} {r['n_at_50']:5d} {r['n_at_80']:5d} {r['n']:3d} "
              f"{r['n_h_p50']:8.1f} {r['n_h_quantile']:7.1f}  {r['start_from']}")
    given_s1 = parse_kv(a.stage_1, int)
    if given_s1 and sorted(given_s1) != sorted(MACHINES):
        raise SystemExit(f"REFUSED: --stage-1 needs a count for each of {MACHINES}")
    s1 = given_s1 or {m: machines[m]["n"] for m in MACHINES}
    for i, m in enumerate(MACHINES):
        cs = list(cost[m].values())
        machines[m].update(stage_1=s1[m], stage_1_from="--stage-1" if given_s1 else "n (fitted)",
                           stage_1_h_p50=round(quantile_cost(cs, s1[m], 0.5, MC_DRAWS, MC_SEED + i), 1),
                           stage_1_h_quantile=round(quantile_cost(cs, s1[m], a.confidence, MC_DRAWS, MC_SEED + i), 1))
    n1 = sum(s1.values())
    if n1 > len(qids):
        raise SystemExit(f"REFUSED: stage 1 would hold {n1} questions, more than the {len(qids)}: everything fits; "
                         f"no second stage is needed (Valerio's call)")
    answers_sha = {c: A.sha256((Path(a.runs) / f"exp_01__{c}__{INDEX}" / "answers.jsonl").read_bytes()) for c in CONFIGS}
    inputs = {"starts": {m: machines[m]["start"] for m in MACHINES},
              "question_cost_h": {m: {q: round(v, 3) for q, v in cost[m].items()} for m in MACHINES},
              "rc_factor": rc_f, "ragas_factor": rg_f, "per_answer": "upper end (SIZE in S451's docstring)",
              "answers_sha256": answers_sha}
    asg = compute({"1": s1}, inputs)
    print(f"\nStage 1: {n1} questions ({n1 * len(CONFIGS)} answers): "
          + ", ".join(f"{m} {s1[m]}" for m in MACHINES) + (" (--stage-1)" if given_s1 else "")
          + f"; target end {local(target)} ({target.astimezone(dt.timezone.utc).strftime('%H:%M')} UTC)")
    print(f"Stage 2: {len(qids) - n1} questions, dealt so the machines end together (the stage 2 rule): "
          + ", ".join(f"{m} {asg['stage_sizes']['2'][m]}" for m in MACHINES))
    print_ends(asg, {"machines": machines, "confidence": a.confidence, "target_end": target.isoformat()})
    print(f"\nLaptop S2 ({S2_TAG}): progress {s2.get('progress')}, exp05 ETA end {s2.get('exp05_eta_end')}, "
          f"per-strategy end {s2.get('strategy_end')} ({s2.get('strategy_remaining_h')} h; {S2_REF_TAG} ratio "
          f"{s2.get('ratio_to_ref')} over {s2.get('pairs')} attempts)")
    for s, v in s2.get("strategies", {}).items():
        if v["remaining"]:
            print(f"    {s:28s} {v['stored']:2d} stored, {v['remaining']:2d} to run, {v['s_per_attempt']} s each ({v['how']})")
    doc = {"_provenance": {"script": "scripts/S451_k1_assign.py size", "script_sha256": A.sha256(Path(__file__).read_bytes()),
                           "computed": now.isoformat(timespec="minutes"), "runs": str(a.runs), "store": a.store,
                           "answers_sha256": answers_sha, "decision": "D86 (Q183)"},
           "computed": now.isoformat(timespec="minutes"), "target_end": target.isoformat(timespec="minutes"),
           "confidence": a.confidence, "mc": {"draws": MC_DRAWS, "seed": MC_SEED},
           "per_answer_upper": {"chars_per_claim": RC_UPPER_CHARS_PER_CLAIM, "gt_chars_per_claim": GT_CHARS_PER_CLAIM,
                                "s_per_check": RC_UPPER_S_PER_CHECK, "overhead_s": RC_OVERHEAD_S, "ragas_fit": RAGAS_FIT},
           "starts": {m: machines[m]["start"] for m in MACHINES}, "strategies": table, "machines": machines,
           "laptop_s2": s2, "stage_1_size": n1,
           "stage_sizes": asg["stage_sizes"], "stage_2_inputs": inputs}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(doc, indent=1) + "\n")
        print(f"\nwrote {rel(Path(a.out))}; next: uv run python scripts/S451_k1_assign.py write --sizing {rel(Path(a.out))}")
    return 0


# ---------------------------------------------------------------- GATE

def _rec(path: Path) -> dict:
    return json.loads(path.read_text())


def gate(records: Path) -> list[str]:
    """What keeps G1's draw 1 from being final (GATE in the docstring); empty when it is."""
    why = []
    rerun = records / "q151_rerun.json"
    if not rerun.exists():
        found = sorted(records.glob("q151_before_rerun_*/rerun.json"))
        rerun = found[-1] if found else rerun
    try:
        t0 = _rec(rerun)["q151_rerun"]
    except (OSError, ValueError, KeyError) as e:
        return [f"no Q151 rerun record ({rerun}: {type(e).__name__})"]
    for c in CONFIGS:
        try:
            s, e = _rec(records / f"g1_{c}.start.json"), _rec(records / f"g1_{c}.end.json")
        except (OSError, ValueError) as err:
            why.append(f"g1_{c}: start or end record unreadable ({type(err).__name__})")
            continue
        if e.get("rc") != 0:
            why.append(f"g1_{c}: end record rc {e.get('rc')}")
        if not str(e.get("end", "")) >= str(s.get("start", "~")):
            why.append(f"g1_{c}: ended {e.get('end')} before its last start {s.get('start')} (running)")
        if c == "multi_hop" and not (str(s.get("start", "")) >= t0 and str(e.get("end", "")) > t0):
            why.append(f"g1_multi_hop: start {s.get('start')} and end {e.get('end')} are not both after the Q151 "
                       f"rerun's start {t0}")
    return why


def cmd_gate(a) -> int:
    why = gate(Path(a.records))
    print(f"G1 GATE {'PASSED' if not why else 'REFUSED'}: {a.records}" + "".join(f"\n  {w}" for w in why))
    return 0 if not why else 1


# ---------------------------------------------------------------- PLAN

def cmd_plan(a) -> int:
    asg = A.load(OUT)
    refs = {q["id"]: q.get("expected_answer", "") for q in json.loads(ex.KEY_D5.read_text())["questions"]}
    items = []
    for c in asg["configs"]:
        items += R.read_run(Path(a.runs) / f"exp_01__{c}__{INDEX}", store=Path(a.store) if a.store else None,
                            immutable=a.immutable)
    plan = {}
    for m in asg["machines"]:
        for k in (A.STAGES if A.staged(asg) else (None,)):
            est = [estimate(x, refs.get(x["question_id"], "")) for x in A.select(items, asg, m, stage=k, base_ok=True)]
            hours = lambda key: sum(e["rc_s"].get(key, 0.0) for e in est) / 3600          # noqa: E731
            plan[f"{m}" + (f" stage {k}" if k else "")] = {
                "answers": len(est), "status": dict(Counter(e["status"] for e in est)),
                "scored": sum(e["scored"] for e in est),
                "checking_calls": [round(sum(e["checks"][x] for e in est)) for x in ("low", "high")],
                "ragchecker_h": {o: [round(hours(f"{o}_{x}"), 1) for x in ("low", "high")] for o in RC_S_PER_CHECK},
                "ragchecker_upper_h": round(sum(e["rc_upper_s"] for e in est) * RC_FACTOR.get(m, 1.0) / 3600, 1),
                "ragas_h": round(sum(e["ragas_s"] for e in est) * RAGAS_FACTOR.get(m, RAGAS_BEELINK_FACTOR) / 3600, 1),
                "largest_context_chars": sorted((e["context_chars"] for e in est), reverse=True)[:3]}
    print(json.dumps({"assignment_sha256": asg["assignment_sha256"], "plan": plan}, indent=1))
    return 0


# ---------------------------------------------------------------- HELPERS (Valerio, 17 October)
#
# "if it lasts really long, plan it in a way that we can also spawn other runs on the other machines to help if there is
# computational availability". Workers, the amendment chain, fences, moves, releases, progress and suggestions; the
# commands, in order, are in findings/recompute/K1/README.md ("Helping K1"). RULE and compute() above are unchanged:
# assignment.json (e2c3ab33ccdb) is never edited, and with an empty chain every worker selects exactly what its machine
# selected before.

AMEND = K1 / "amendments.json"
FENCES = K1 / "fences"
ESTIMATES = K1 / "estimates.json"
LOCK_FILE = ROOT / "experiments" / "LOCK.toml"
REGISTRY = {"studio": {"machine": "studio", "port": 11441, "clone": "~/projects/mentori-runs-k1"},
            "beelink": {"machine": "beelink", "port": 11434, "clone": "~/projects/mentori-runs"},
            "laptop": {"machine": "laptop", "port": 11434, "clone": "~/projects/mentori-runs-k1"}}
MULTI_SERVER = ("studio", "beelink")   # machines with more than one Ollama server: the only ones a new worker can be on
                                        # (the Beelink since D89 A2: a second server on 127.0.0.1:11435 beside the app's)
REFUSED_PORTS = {("studio", 11434): "the Mentori app's port, never a paper port",
                 ("studio", 11453): "Figure 3's verifier port (G1, G4), never a K1 port"}
PASSES = ((1, "ragchecker"), (1, "ragas"), (2, "ragchecker"), (2, "ragas"))   # each launcher's order of passes
STOP_COST_H = 12.0               # suggest: a pair is proposed only if it gains this much (an RLM answer redone, a hand unload)
FILES = {"ragchecker_rows": A.ROWS["ragchecker"], "ragchecker_calls": A.CALLS["ragchecker"],
         "ragas_rows": A.ROWS["ragas"], "ragas_calls": A.CALLS["ragas"]}
FENCE_UNSIGNED = ("fence_id", "released", "released_at", "released_head", "released_by")
MOVE_RULE = (
    "K1 moves (helpers; Valerio, 17 October). A worker is a name bound to a machine, a port and a clone; the base "
    "assignment's three machines are the first three workers, each named as its machine, and a helper is named "
    "<machine>_<port>, on a machine that runs more than one Ollama server. A move gives questions from a source worker "
    "to a target worker and is made only from a fence of the source, and of the target when the target already exists: "
    "the worker's launcher and scorer stopped, its lock held, its four files hashed, and the questions it has begun "
    "counted (any row, any call record naming the question, and, for a scorer whose call log holds a record that names "
    "no question, that scorer's next question). Only questions the source has not begun move: the last N in the "
    "source's order of work (stage 1 then stage 2, each in the key's order), so stage 2 questions go first; a stage "
    "filter restricts the move to one stage. A question keeps its stage. A stage 1 question moves only when the "
    "target's projected stage 1 end after the move is earlier than the source's before it. A fence is used by one "
    "record only, a move or an abandon, and a worker restarts only after its fence is released against a chain that "
    "holds that record. A question's six answers are scored by one worker with both scorers (Q142); every row and call "
    "record carries the machine and the worker.")


class Refused(Exception):
    pass


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone().replace(microsecond=0)


def iso(t: dt.datetime) -> str:
    return t.isoformat(timespec="minutes")


def expand(clone: str, home: Path | None = None) -> Path:
    """A registry clone ("~/...") on this machine (home given: in place of $HOME, for the offline checks)."""
    if home is not None and clone.startswith("~"):
        return Path(str(home) + clone[1:])
    return Path(os.path.expanduser(clone))


def file_state(path: Path) -> dict:
    b = path.read_bytes() if path.exists() else b""
    return {"exists": path.exists(), "bytes": len(b), "lines": b.count(b"\n"), "sha256": A.sha256(b)}


def prefix_sha256(path: Path, nbytes: int) -> str | None:
    """sha256 of the first nbytes of a file (a fence's state of a log that has grown since); None when shorter."""
    with open(path, "rb") as fh:
        b = fh.read(nbytes)
    return A.sha256(b) if len(b) == nbytes else None


def fence_id_of(doc: dict) -> str:
    return A.sha256(A.canon({k: v for k, v in doc.items() if k not in FENCE_UNSIGNED}))


def git_head(root: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=30).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _procs():
    """findings/recompute/K1/k1_procs.py: the one definition of a worker's processes, shared by the fence and the stop
    (README "Helping K1"; standard library, so a clone still on c7ad841 runs it from stdin)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("k1_procs", K1 / "k1_procs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = _procs()
ps_rows, own_tree, launcher_worker, naming = P.ps_rows, P.own_tree, P.launcher_worker, P.naming


def run_ps() -> str:
    try:
        return P.run_ps()
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        raise Refused(f"{e}; a fence needs the process list") from None


def tracked_changes(root: Path) -> list[str]:
    """Tracked files of the clone that differ from its HEAD, amendments.json excepted (the launcher's rule): a fence
    runs only on HEAD's code, so its clone's HEAD holds the helpers (K1 helper review F2: S451 and assignment.py
    checked out over a c7ad841 HEAD would leave its scorers selecting without the chain). Refused when git fails."""
    try:
        p = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise Refused(f"git status failed in {root} ({e}); a fence needs a clean clone") from None
    if p.returncode != 0:
        raise Refused(f"git status failed in {root} ({p.stderr.strip()[:200]}); a fence needs a clean clone")
    return [ln for ln in p.stdout.splitlines() if ln.strip() and ln[3:] != "findings/recompute/K1/amendments.json"]


def load_all(k1: Path = K1) -> tuple[dict, dict, dict]:
    """(base, chain, effective) from a K1 directory; Refused on any failure of the checks."""
    try:
        base = A.load(k1 / "assignment.json")
        chain = A.load_chain(k1 / "amendments.json", base)
        return base, chain, A.effective(base, chain)
    except (A.AssignmentError, OSError) as e:
        raise Refused(str(e)) from None


def worker_files(out: Path, lenient: bool = False) -> tuple[dict, dict]:
    """({scorer: rows}, {scorer: call records}) of a worker's output directory; rows must all be JSON (a cut row would
    also stop the scorer's resume; lenient, for progress of a running worker: a line being written is left out), a
    call line that is not JSON is None (it names no question: touched() counts it)."""
    try:
        rows = {s: [r for r in A.read_jsonl(out / A.ROWS[s], lenient=lenient) if r] for s in A.SCORERS}
    except A.AssignmentError as e:
        raise Refused(f"{e}; repair the file by hand before a fence") from None
    calls = {s: A.read_jsonl(out / A.CALLS[s], lenient=True) for s in A.SCORERS}
    return rows, calls


def in_order(ids, order: list[str]) -> list[str]:
    pos = {q: i for i, q in enumerate(order)}
    return sorted(set(ids), key=lambda q: (pos.get(q, len(pos)), q))


# ---- fence (on the worker's machine, in its clone, the worker stopped)

def fence(worker: str, k1: Path = K1, root: Path = ROOT, home: Path | None = None, ps_text: str | None = None,
          me: int | None = None, now: dt.datetime | None = None) -> dict:
    """D3: hold the worker's launcher lock, hash its four files, count the questions it has begun, write
    <out>/fence.json. Refused while a live launcher or any process of the worker runs, in a clone that is not the
    worker's, and while an unreleased fence exists."""
    base, chain, eff = load_all(k1)
    reg = eff["registry"]
    if worker not in reg:
        raise Refused(f"worker {worker!r} is not in the registry ({sorted(reg)})")
    w = reg[worker]
    if expand(w["clone"], home).resolve() != Path(root).resolve():
        raise Refused(f"this clone ({Path(root).resolve()}) is not {worker}'s ({w['clone']}); run the fence in its clone")
    dirty = tracked_changes(Path(root))
    if dirty:
        raise Refused(f"tracked files differ from HEAD in {Path(root).resolve()} (only amendments.json may): "
                      f"{'; '.join(dirty[:3])}; check the whole clone out at the helpers' commit (README step 4)")
    out = k1 / worker
    out.mkdir(parents=True, exist_ok=True)
    f = out / "fence.json"
    st = A.fence_status(k1, worker, chain)
    if st.startswith("unreleased"):
        raise Refused(f"{f} holds fence {st.split(':')[1]}, not released: move with it, or abandon it "
                      f"(S451 abandon, then release --abandon)")
    if st != "none" and st != "released":
        raise Refused(f"{f} is {st}: the chain here does not hold the head its fence was released against (check out "
                      f"the chain it was released against)")
    rows_ps = ps_rows(ps_text if ps_text is not None else run_ps())
    own = own_tree(rows_ps, os.getpid() if me is None else me)
    lock = out / ".launcher"
    owner = None
    if (lock / "owner.json").exists():
        try:
            owner = json.loads((lock / "owner.json").read_text())
        except ValueError:
            owner = None
    if owner and owner.get("role") == "launcher" and any(p == owner.get("pid") and "run_k1" in a for p, _, a in rows_ps):
        raise Refused(f"a live launcher holds {lock} (pid {owner['pid']}); stop it and its scorer first")
    users = naming(rows_ps, own, worker, w["machine"])
    if users:
        raise Refused(f"{len(users)} processes are {worker}'s (an orphaned scorer, F5, or its launcher): "
                      + "; ".join(f"pid {u['pid']}: {u['args'][:120]}" for u in users[:3]))
    try:
        lock.mkdir()
        taken = "free"
    except FileExistsError:
        taken = "stale"                           # no live owner and no process of the worker: taken over
    rows, calls = worker_files(out)
    qs = A.worker_questions(eff, worker)
    order = [q["id"] for q in qs]
    t = A.touched(order, rows, calls)
    doc = {"kind": "k1_fence", "worker": worker, "machine": w["machine"], "port": w["port"], "clone": w["clone"],
           "clone_resolved": str(Path(root).resolve()), "at": (now or now_local()).isoformat(timespec="seconds"),
           "chain_head": chain["head"],
           "chain_records": len(chain["records"]), "base_assignment_sha256": base["assignment_sha256"],
           "lock_taken": taken, "code_commit": git_head(Path(root)),
           "files": {k: file_state(out / v) for k, v in FILES.items()},
           "rows": {s: len(rows[s]) for s in A.SCORERS},
           "touched_rows": in_order(t["rows"], order), "touched_calls": in_order(t["calls"], order),
           "questions": qs, "nonce": os.urandom(8).hex()}       # two fences of the same state never share an id
    doc["fence_id"] = fence_id_of(doc)
    (lock / "owner.json").write_text(json.dumps({"role": "fence", "pid": os.getpid(), "fence_id": doc["fence_id"],
                                                 "at": doc["at"]}) + "\n")
    f.write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def read_fence(path: Path) -> dict:
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise Refused(f"no fence at {path} ({type(e).__name__})") from None
    if doc.get("kind") != "k1_fence" or fence_id_of(doc) != doc.get("fence_id"):
        raise Refused(f"{path}: fence_id does not recompute; the fence was changed after it was written")
    return doc


def check_fence(d: Path, worker: str, chain: dict, eff: dict, base: dict, questions: bool = True) -> tuple[dict, dict]:
    """A fence copied to the coordinator (<d>/fence.json, <d>/ragchecker.jsonl, <d>/ragas.jsonl), checked: its own
    signature, its worker, its base, not used by a record of the chain, the copied rows equal to what it hashed, the
    questions it begun recomputed from them, and (questions=True) its question list equal to the worker's under the
    chain now. Returns (fence, {scorer: rows})."""
    fz = read_fence(Path(d) / "fence.json")
    if fz["worker"] != worker:
        raise Refused(f"{d}: the fence is {fz['worker']}'s, not {worker}'s")
    if fz["base_assignment_sha256"] != base["assignment_sha256"]:
        raise Refused(f"{d}: the fence is of another base ({fz['base_assignment_sha256'][:12]})")
    if fz.get("released"):
        raise Refused(f"{d}: the fence was released ({fz.get('released_by')}); fence the worker again")
    for r in chain["records"]:
        if fz["fence_id"] in A.fence_ids(r):
            raise Refused(f"{d}: fence {fz['fence_id'][:12]} was already used by record {r['seq']} ({r['kind']}); "
                          f"a fence is used once")
    rows = {}
    for s, key in (("ragchecker", "ragchecker_rows"), ("ragas", "ragas_rows")):
        p = Path(d) / Path(A.ROWS[s]).name
        st = file_state(p)
        want = fz["files"][key]
        if (st["bytes"], st["sha256"]) != (want["bytes"], want["sha256"]):
            raise Refused(f"{d}: {p.name} is {st['bytes']} bytes, sha256 {st['sha256'][:12]}; the fence hashed "
                          f"{want['bytes']} bytes, {want['sha256'][:12]}: copy the worker's {A.ROWS[s]} again")
        rows[s] = A.read_jsonl(p)
    order = [q["id"] for q in fz["questions"]]
    again = A.touched(order, rows, {})["rows"]
    if in_order(again, order) != fz["touched_rows"]:
        raise Refused(f"{d}: the questions begun recomputed from the copied rows differ from the fence's")
    if questions and fz["questions"] != A.worker_questions(eff, worker):
        raise Refused(f"{d}: the fence's question list for {worker} ({len(fz['questions'])}) is not its list under the "
                      f"chain now ({len(A.worker_questions(eff, worker))}): its clone missed an amendment that touched "
                      f"it; check it out there and fence again")
    return fz, rows


def fence_summary(fz: dict) -> dict:
    return {k: fz[k] for k in ("fence_id", "worker", "at", "chain_head", "code_commit", "files", "touched_rows",
                               "touched_calls")}


# ---- estimates and the projection (move's stage 1 rule, suggest)

def per_answer_estimates(runs: str, store: str | None, immutable: bool) -> dict:
    """{question: {config: [RAGChecker seconds at the Beelink's speed, RAGAS seconds at the Studio's]}}: SIZE's upper end
    per answer (estimate()), before the machine factors."""
    out: dict = {}
    for e in read_estimates(runs, store, immutable):
        out.setdefault(e["question_id"], {})[e["config"]] = [e["rc_upper_s"], e["ragas_s"]]
    return out


def estimates_reproduce(per: dict, inputs: dict) -> list:
    """The (machine, question) whose signed question_cost_h the per-answer estimates do not give again."""
    rc, rg = inputs["rc_factor"], inputs["ragas_factor"]
    bad = []
    for m, qs in inputs["question_cost_h"].items():
        for q, h in qs.items():
            got = sum(v[0] * rc[m] + v[1] * rg[m] for v in per.get(q, {}).values()) / 3600
            if round(got, 3) != h:
                bad.append((m, q))
    return bad


def load_estimates(base: dict, path: Path = ESTIMATES) -> dict:
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise Refused(f"no estimates at {path} ({type(e).__name__}); run S451 estimates") from None
    bad = estimates_reproduce(doc["per_answer"], base["stage_2_inputs"])
    if bad or doc.get("answers_sha256") != base["stage_2_inputs"]["answers_sha256"]:
        raise Refused(f"{path} does not give the assignment's question_cost_h again ({len(bad)} differ) or is of other "
                      f"answers")
    return doc["per_answer"]


def progress_doc(worker: str, machine: str, rows: dict, touched_ids, chain_head: str | None, at: str,
                 headers: dict | None = None, fence_state: str | None = None) -> dict:
    """D8: what `progress` prints and `suggest` reads: per scorer, each answer's latest status and its summed wall
    time (RAGAS rows give one time per metric), the questions begun, the chain head and the last row's time."""
    ans = {}
    for s in A.SCORERS:
        tot, last = {}, {}
        for r in rows.get(s, ()):
            k = (r["question_id"], r["config"], r.get("draw", 1))
            w = r.get("wall_s")
            tot[k] = tot.get(k, 0.0) + (sum(w.values()) if isinstance(w, dict) else float(w or 0.0))
            last[k] = r.get("status")
        ans[s] = [[q, c, d, last[(q, c, d)], round(tot[(q, c, d)], 1)] for (q, c, d) in tot]
    stamps = [r.get("at") for s in A.SCORERS for r in rows.get(s, ()) if r.get("at")]
    return {"kind": "k1_progress", "worker": worker, "machine": machine, "at": at, "chain_head": chain_head,
            "fence": fence_state, "answers": ans, "touched": sorted(touched_ids),
            "rows": {s: len(rows.get(s, ())) for s in A.SCORERS}, "last_row_at": max(stamps) if stamps else None,
            "headers": headers or {}}


def project(lists: dict, reg: dict, per: dict, factors: dict, prog: dict, starts: dict, now: dt.datetime) -> dict:
    """D8's projection. lists {worker: [{"id", "stage"}]}; prog {worker: progress_doc}; starts {worker: datetime} for a
    worker with no row yet (it starts at the later of that and now; a worker with rows is running, from now). Rate per
    (worker, scorer): its actual wall time over the estimate on the questions it finished with that scorer; without one,
    another worker's on the same machine; else 1.0. Each pass's hours are its unfinished answers' estimates times the
    rate; the passes run one after another (PASSES)."""
    done = {"ragchecker": A.DONE_RC, "ragas": A.DONE_RAGAS}

    def est(q, c, s, m):
        return per[q][c][0 if s == "ragchecker" else 1] * factors[s][m]
    fin = {w: {s: {(a[0], a[1]): a[4] for a in (prog.get(w) or {}).get("answers", {}).get(s, []) if a[3] in done[s]}
               for s in A.SCORERS} for w in lists}
    own = {}
    for w in sorted(lists):
        m = reg[w]["machine"]
        for s in A.SCORERS:
            full = sorted({q for q, _ in fin[w][s] if q in per and all((q, c) in fin[w][s] for c in per[q])})
            e = sum(est(q, c, s, m) for q in full for c in per[q])
            if full and e > 0:
                own[(w, s)] = (sum(fin[w][s][(q, c)] for q in full for c in per[q]) / e, f"own, {len(full)} questions")
    out = {}
    for w in sorted(lists):
        m = reg[w]["machine"]
        rate = {}
        for s in A.SCORERS:
            peer = [v for v in sorted(own) if v[1] == s and v[0] != w and reg[v[0]]["machine"] == m]
            rate[s] = own.get((w, s)) or ((own[peer[0]][0], f"{peer[0][0]}'s, same machine") if peer
                                          else (1.0, "1.0, no finished question on this machine"))
        hours = {}
        for k, s in PASSES:
            sec = sum(est(q["id"], c, s, m) for q in lists[w] if q["stage"] == k for c in per[q["id"]]
                      if (q["id"], c) not in fin[w][s])
            hours[f"{s} stage {k}"] = sec * rate[s][0] / 3600
        has_rows = any((prog.get(w) or {}).get("answers", {}).get(s) for s in A.SCORERS)
        h1 = sum(v for k, v in hours.items() if k.endswith("stage 1"))
        h2 = sum(v for k, v in hours.items() if k.endswith("stage 2"))
        t0 = now if has_rows or h1 + h2 == 0 else max(now, starts.get(w, now))   # nothing left: it ends now
        out[w] = {"rate": {s: [round(rate[s][0], 3), rate[s][1]] for s in A.SCORERS}, "start": t0,
                  "stage_1_end": t0 + dt.timedelta(hours=h1), "end": t0 + dt.timedelta(hours=h1 + h2),
                  "hours": {k: round(v, 1) for k, v in hours.items()}}
    return out


def project_json(p: dict) -> dict:
    return {w: {"rate": v["rate"], "start": iso(v["start"]), "stage_1_end": iso(v["stage_1_end"]), "end": iso(v["end"]),
                "hours": v["hours"]} for w, v in p.items()}


def lists_of(eff: dict) -> dict:
    return {w: A.worker_questions(eff, w) for w in eff["workers"]}


def keypos(base: dict) -> dict:
    return {q["id"]: i for i, q in enumerate(base["questions"])}


def apply_lists(lists: dict, src: str, dst: str, pick: list[dict], kp: dict) -> dict:
    """The worker lists after moving pick from src to dst (dst's order: stage, then the key's order)."""
    out = {w: list(v) for w, v in lists.items()}
    ids = {q["id"] for q in pick}
    out[src] = [q for q in out[src] if q["id"] not in ids]
    out[dst] = sorted(out.get(dst, []) + list(pick), key=lambda q: (q["stage"], kp[q["id"]]))
    return out


def starts_of(base: dict, reg: dict, now: dt.datetime) -> dict:
    """A base worker with no row starts at its signed start (stage_2_inputs); a new worker now."""
    s = base["stage_2_inputs"]["starts"]
    return {w: dt.datetime.fromisoformat(s[w]) if w in s else now for w in reg}


def factors_of(base: dict) -> dict:
    inp = base["stage_2_inputs"]
    return {"ragchecker": inp["rc_factor"], "ragas": inp["ragas_factor"]}


def pick_last(qs: list[dict], begun: set, n: int, stage: int | None) -> list[dict]:
    """The last n questions of a worker's order that it has not begun (of one stage when given), in its order."""
    free = [q for q in qs if q["id"] not in begun and (stage is None or q["stage"] == stage)]
    return free[len(free) - n:] if 0 < n <= len(free) else []


def read_progress_dir(d: Path | None) -> dict:
    out = {}
    for p in sorted(Path(d).glob("*.json")) if d else ():
        try:
            doc = json.loads(p.read_text())
        except ValueError:
            continue
        if doc.get("kind") == "k1_progress":
            out[doc["worker"]] = doc
    return out


# ---- move, abandon (on the coordinator), release (in the worker's clone)

def parse_new(name: str, reg: dict, clone: str | None) -> dict:
    m = re.fullmatch(r"([a-z]+)_(\d{4,5})", name)
    if not m:
        raise Refused(f"a new worker is named <machine>_<port>, not {name!r}")
    machine, port = m[1], int(m[2])
    if machine not in MACHINES:
        raise Refused(f"{name}: {machine} is not one of {MACHINES}")
    if machine not in MULTI_SERVER:
        raise Refused(f"{name}: {machine} runs one Ollama server, which its own worker uses; a helper there is that "
                      f"worker (move to {machine} itself, with its fence)")
    if (machine, port) in REFUSED_PORTS:
        raise Refused(f"{name}: port {port} on {machine} is {REFUSED_PORTS[(machine, port)]}")
    clone = clone or f"~/projects/mentori-runs-k1-{port}"
    for w, v in reg.items():
        if v["machine"] == machine and (v["port"] == port or v["clone"] == clone):
            raise Refused(f"{name}: worker {w} already uses {machine} port {v['port']} or clone {v['clone']}")
    return {"machine": machine, "port": port, "clone": clone}


def write_chain(k1: Path, base: dict, chain: dict, record: dict, fences: list[dict]) -> None:
    """Append a record: the new file is checked with load_chain before it replaces the old; the fences are copied to
    k1/fences/<worker>_<id12>.json."""
    path = k1 / "amendments.json"
    doc = json.loads(path.read_text())
    doc["records"] = doc["records"] + [record]
    tmp = path.with_name(path.name + ".new")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    try:
        A.load_chain(tmp, base)
    except A.AssignmentError as e:
        tmp.unlink()
        raise Refused(f"the new chain does not verify ({e}); nothing written") from None
    (k1 / "fences").mkdir(exist_ok=True)
    for fz in fences:
        (k1 / "fences" / f"{fz['worker']}_{fz['fence_id'][:12]}.json").write_text(json.dumps(fz, indent=1) + "\n")
    os.replace(tmp, path)


def signed_record(chain: dict, rec: dict) -> dict:
    rec = {**rec, "seq": len(chain["records"]) + 1, "prev": chain["head"]}
    rec["amendment_sha256"] = A.record_sha256(rec)
    return rec


def move(src: str, dst: str, n: int, *, fence_from: Path, reason: str, fence_to: Path | None = None, new: bool = False,
         stage: int | None = None, to_clone: str | None = None, k1: Path = K1,
         progress: Path | None = None, estimates: Path | None = None, now: dt.datetime | None = None,
         write: bool = True) -> dict:
    """D4 (README "Helping K1"): the move record, appended to k1/amendments.json (write=False: returned only)."""
    now = now or now_local()
    if not (reason or "").strip():
        raise Refused("a move needs --reason")
    base, chain, eff = load_all(k1)
    reg = eff["registry"]
    if src not in reg:
        raise Refused(f"source {src!r} is not a worker ({sorted(reg)})")
    if src == dst:
        raise Refused("the source and the target are the same worker")
    defined = None
    if new:
        if dst in reg:
            raise Refused(f"worker {dst!r} already exists; a new worker needs a new name")
        defined = parse_new(dst, reg, to_clone)
    elif dst not in reg:
        raise Refused(f"target {dst!r} is not a worker; a new one is made with --new")
    elif fence_to is None:
        raise Refused(f"target {dst} exists: it needs its own fence (--fence-to), so it is stopped and restarts on the "
                      f"amended chain")
    if n < 1:
        raise Refused("--questions must be at least 1")
    fs, rows_s = check_fence(Path(fence_from), src, chain, eff, base)
    ft, rows_t = check_fence(Path(fence_to), dst, chain, eff, base) if fence_to is not None else (None, {})
    if ft and ft["fence_id"] == fs["fence_id"]:
        raise Refused("the two fences are one")
    lists = lists_of(eff)
    begun = set(fs["touched_rows"]) | set(fs["touched_calls"])
    pick = pick_last(lists[src], begun, n, stage)
    if not pick:
        free = [q for q in lists[src] if q["id"] not in begun and (stage is None or q["stage"] == stage)]
        raise Refused(f"{src} has {len(free)} questions it has not begun{' in stage ' + str(stage) if stage else ''}; "
                      f"{n} cannot move (never part of them)")
    reg2 = {**reg, **({dst: defined} if defined else {})}
    lists.setdefault(dst, [])
    per = load_estimates(base, estimates or k1 / "estimates.json")
    prog = read_progress_dir(progress)
    prog[src] = progress_doc(src, reg[src]["machine"], rows_s, begun, fs["chain_head"], fs["at"])
    if ft:
        prog[dst] = progress_doc(dst, reg[dst]["machine"], rows_t, set(ft["touched_rows"]) | set(ft["touched_calls"]),
                                 ft["chain_head"], ft["at"])
    else:
        prog.pop(dst, None)
    starts = starts_of(base, reg2, now)
    before = project(lists, reg2, per, factors_of(base), prog, starts, now)
    after_lists = apply_lists(lists, src, dst, pick, keypos(base))
    after = project(after_lists, reg2, per, factors_of(base), prog, starts, now)
    ones = [q["id"] for q in pick if q["stage"] == 1]
    if ones and not after[dst]["stage_1_end"] < before[src]["stage_1_end"]:
        raise Refused(f"{len(ones)} stage 1 questions would move, but {dst}'s projected stage 1 end after the move "
                      f"({local(after[dst]['stage_1_end'])}) is not earlier than {src}'s before it "
                      f"({local(before[src]['stage_1_end'])}); stage 1 moves only to end sooner")
    rec = {"kind": "move", "at": iso(now), "from": src, "to": dst, **({"to_defined": defined} if defined else {}),
           "stage_filter": stage, "questions": pick, "reason": reason.strip(), "fence_from": fence_summary(fs),
           "fence_to": fence_summary(ft) if ft else None,
           "projection": {"now": iso(now), "before": project_json({w: before[w] for w in (src, dst)}),
                          "after": project_json({w: after[w] for w in (src, dst)}),
                          "progress_from": sorted(prog), "note": "a report, signed with the record; the rule reads "
                          "only the stage 1 ends"}}
    rec = signed_record(chain, rec)
    if write:
        write_chain(k1, base, chain, rec, [fs] + ([ft] if ft else []))
    return rec


def abandon(worker: str, fence_dir: Path, reason: str, k1: Path = K1, now: dt.datetime | None = None,
            write: bool = True) -> dict:
    """A record that releases a fence no move used, so the worker can restart unchanged; after it, no move can use
    the fence (load_chain: a fence is used once)."""
    if not (reason or "").strip():
        raise Refused("an abandon needs --reason")
    base, chain, eff = load_all(k1)
    fz, _ = check_fence(Path(fence_dir), worker, chain, eff, base, questions=False)
    rec = signed_record(chain, {"kind": "abandon", "at": iso(now or now_local()), "worker": worker,
                                "fence": fence_summary(fz), "reason": reason.strip()})
    if write:
        write_chain(k1, base, chain, rec, [fz])
    return rec


def release(worker: str, k1: Path = K1, abandon_: bool = False, now: dt.datetime | None = None) -> dict:
    """D5: in the worker's clone, after the amended amendments.json is checked out there. Refused unless the local
    chain verifies and holds a record naming the fence (a move, or with --abandon an abandon record), and unless the
    worker's four files are still exactly what the fence hashed (nothing ran since). Marks fence.json released and
    removes the lock."""
    out = k1 / worker
    fz = read_fence(out / "fence.json")
    if fz.get("released"):
        raise Refused(f"fence {fz['fence_id'][:12]} is already released")
    base, chain, eff = load_all(k1)
    named = [r for r in chain["records"] if fz["fence_id"] in A.fence_ids(r)]
    kinds = {r["kind"] for r in named}
    if abandon_ and "abandon" not in kinds:
        raise Refused(f"no abandon record names fence {fz['fence_id'][:12]} in {k1 / 'amendments.json'} (head "
                      f"{chain['head'][:12]}){'; a move used it, so it cannot be abandoned' if 'move' in kinds else ''}: "
                      f"write it with S451 abandon on the coordinator and check the file out here first")
    if not abandon_ and "move" not in kinds:
        raise Refused(f"no move record names fence {fz['fence_id'][:12]} in {k1 / 'amendments.json'} (head "
                      f"{chain['head'][:12]}): check out the amended file first"
                      + ("; it was abandoned: release --abandon" if "abandon" in kinds else ""))
    changed = [k for k, v in FILES.items() if file_state(out / v) != fz["files"][k]]
    if changed:
        raise Refused(f"{changed} changed since the fence: something ran while it held the lock")
    fz.update(released=True, released_at=iso(now or now_local()), released_head=chain["head"],
              released_by="abandon" if abandon_ else "move")
    (out / "fence.json").write_text(json.dumps(fz, indent=1) + "\n")
    lock = out / ".launcher"
    try:
        own = json.loads((lock / "owner.json").read_text())
    except (OSError, ValueError):
        own = {}
    if own.get("role") == "fence" and own.get("fence_id") == fz["fence_id"]:
        (lock / "owner.json").unlink()
        lock.rmdir()
    else:
        raise Refused(f"{lock} is not held by this fence ({own}); fence.json is marked released, the lock left as it is")
    return fz


def fence_state(out: Path, chain: dict) -> str:
    """A.fence_status of the worker whose output directory is out: "released" only against a head the chain holds."""
    return A.fence_status(out.parent, out.name, chain)


# ---- progress (on the worker's machine) and suggest (on the coordinator; writes nothing)

def progress(worker: str, k1: Path = K1, now: dt.datetime | None = None) -> dict:
    base, chain, eff = load_all(k1)
    if worker not in eff["registry"]:
        raise Refused(f"worker {worker!r} is not in the registry")
    out = k1 / worker
    rows, calls = worker_files(out, lenient=True)
    order = [q["id"] for q in A.worker_questions(eff, worker)]
    t = A.touched(order, rows, calls)
    heads = {}
    for s in A.SCORERS:
        h = A.read_jsonl(out / Path(A.ROWS[s]).parent / f"{s}_headers.jsonl", lenient=True)
        h = [x for x in h if x]
        if h:
            heads[s] = {"started": h[-1].get("_provenance", {}).get("started"), "k1_stage": h[-1].get("k1_stage"),
                        "to_do": h[-1].get("to_do"), "worker": h[-1].get("worker")}
    return progress_doc(worker, eff["registry"][worker]["machine"], rows, t["rows"] | t["calls"], chain["head"],
                        iso(now or now_local()), heads, fence_state(out, chain))


def suggest(progress_dir: Path | None, free: list[str], min_gain_h: float = STOP_COST_H, k1: Path = K1,
            now: dt.datetime | None = None, estimates: Path | None = None) -> dict:
    """D8: the moves that bring the latest end in, as S451 move commands; writes nothing. Greedy: the last question the
    latest-ending worker has not begun goes to the earliest-ending worker (for a stage 1 question: a worker on the same
    machine first, R1, and only if that worker's stage 1 then ends before the source's), while the latest end improves.
    One round pairs each source with one target and each target with one source (a fence is used by one move, so a
    second target would cost the source a second stop, fence and release): once a source has given to a target it
    gives only to it, and a target takes only from its source. The moves are then grouped per (source, target) as
    `move` would select them (the last N not begun), and a pair is proposed only if it lowers the later of its two
    workers' ends by at least min_gain_h (the stop it costs). After a round's moves, run suggest again."""
    now = now or now_local()
    base, chain, eff = load_all(k1)
    per = load_estimates(base, estimates or k1 / "estimates.json")
    prog = read_progress_dir(progress_dir)
    reg = dict(eff["registry"])
    notes = []
    for f in free:
        m, _, port = f.partition(":")
        name = f"{m}_{port}"
        if name in reg:
            notes.append(f"{f}: worker {name} exists; give it questions with a move to it")
            continue
        try:
            reg[name] = parse_new(name, reg, None)
        except Refused as e:
            notes.append(f"{f}: not usable ({e})")
    lists = {w: A.worker_questions(eff, w) for w in eff["workers"]}
    for w in reg:
        lists.setdefault(w, [])
    for w in eff["workers"]:
        if w not in prog:
            notes.append(f"no progress for {w}: projected as not started")
        elif prog[w].get("chain_head") != chain["head"]:
            notes.append(f"{w}'s progress is on chain head {str(prog[w].get('chain_head'))[:12]}, the file's is "
                         f"{chain['head'][:12]}")
    begun = {w: set(prog.get(w, {}).get("touched", [])) for w in reg}
    starts = starts_of(base, reg, now)
    fac, kp = factors_of(base), keypos(base)
    P = project(lists, reg, per, fac, prog, starts, now)
    first = {w: dict(v) for w, v in P.items()}
    cur, moved, steps = {w: list(v) for w, v in lists.items()}, set(), []
    to_of, from_of = {}, {}                       # one round: a source gives to one target, a target takes from one
    while True:
        src = max(sorted(cur), key=lambda w: P[w]["end"])
        movable = [q for q in cur[src] if q["id"] not in begun[src] and q["id"] not in moved]
        if not movable:
            break
        q = movable[-1]
        late = P[src]["end"]
        targets = [to_of[src]] if src in to_of else sorted(
            (w for w in cur if w != src and w not in to_of and from_of.get(w, src) == src), key=lambda w: (P[w]["end"], w))
        if q["stage"] == 1:
            same = [w for w in targets if reg[w]["machine"] == reg[src]["machine"]]
            targets = same + [w for w in targets if w not in same]
        took = None
        for dst in targets:
            trial = apply_lists(cur, src, dst, [q], kp)
            P2 = project(trial, reg, per, fac, prog, starts, now)
            if q["stage"] == 1 and not P2[dst]["stage_1_end"] < P[src]["stage_1_end"]:
                continue
            if max(v["end"] for v in P2.values()) < max(v["end"] for v in P.values()) and P2[dst]["end"] < late:
                took = (dst, trial, P2)
                break
        if took is None:
            break
        dst, cur, P = took
        to_of[src], from_of[dst] = dst, src
        moved.add(q["id"])
        steps.append((q["id"], q["stage"], src, dst))
    pairs: dict = {}
    for qid, k, src, dst in steps:
        pairs.setdefault((src, dst), []).append((qid, k))
    proposals, applied = [], {w: list(v) for w, v in lists.items()}
    Pa = project(applied, reg, per, fac, prog, starts, now)
    for (src, dst), qs in sorted(pairs.items(), key=lambda kv: (-Pa[kv[0][0]]["end"].timestamp(), kv[0])):
        st = 2 if all(k == 2 for _, k in qs) else None
        pick = pick_last(applied[src], begun[src], len(qs), st)
        if not pick:
            continue
        trial = apply_lists(applied, src, dst, pick, kp)
        Pt = project(trial, reg, per, fac, prog, starts, now)
        gain = (max(Pa[src]["end"], Pa[dst]["end"]) - max(Pt[src]["end"], Pt[dst]["end"])).total_seconds() / 3600
        ones = [q["id"] for q in pick if q["stage"] == 1]
        if gain < min_gain_h or (ones and not Pt[dst]["stage_1_end"] < Pa[src]["stage_1_end"]):
            notes.append(f"{src} -> {dst}: {len(pick)} questions gain {gain:.1f} h, under {min_gain_h:g} h or not "
                         f"ending stage 1 sooner: not proposed")
            continue
        new = dst not in eff["registry"]
        cmd = (f"uv run python scripts/S451_k1_assign.py move --from {src} --to {dst}{' --new' if new else ''} "
               f"--questions {len(pick)}{' --stage 2' if st == 2 else ''} --fence-from <copy of {src}'s fence>"
               f"{'' if new else ' --fence-to <copy of ' + dst + chr(39) + 's fence>'} --reason \"...\"")
        proposals.append({"from": src, "to": dst, "new": new, "questions": [q["id"] for q in pick],
                          "stages": sorted({q["stage"] for q in pick}), "gain_h": round(gain, 1),
                          "ends_before": {w: iso(Pa[w]["end"]) for w in (src, dst)},
                          "ends_after": {w: iso(Pt[w]["end"]) for w in (src, dst)}, "command": cmd})
        applied, Pa = trial, Pt
        if new and any(v["machine"] == reg[dst]["machine"] for w, v in eff["registry"].items()):
            notes.append(f"{dst} shares {reg[dst]['machine']}'s GPU: its speed and the slowdown it causes the other "
                         f"workers there are unknown until it has run (R3); run suggest again after about 6 h of its rows")
    notes = list(dict.fromkeys(notes))
    return {"now": iso(now), "chain_head": chain["head"], "min_gain_h": min_gain_h,
            "ends_now": {w: {"stage_1_end": iso(v["stage_1_end"]), "end": iso(v["end"]), "rate": v["rate"]}
                         for w, v in first.items()},
            "proposals": proposals,
            "ends_after": {w: {"stage_1_end": iso(v["stage_1_end"]), "end": iso(v["end"])} for w, v in Pa.items()},
            "notes": notes}


# ---- the command line

def _run(fn) -> int:
    try:
        out = fn()
    except Refused as e:
        print(f"REFUSED: {e}")
        return 1
    if out is not None:
        print(json.dumps(out, indent=1, default=str))
    return 0


def genesis_doc(base: dict) -> dict:
    g = {"base_assignment_sha256": base["assignment_sha256"], "base_file_sha256": base["file_sha256"],
         "lock_sha256": A.sha256(LOCK_FILE.read_bytes()), "workers": REGISTRY, "move_rule": MOVE_RULE,
         "move_rule_sha256": A.sha256(MOVE_RULE)}
    g["genesis_sha256"] = A.genesis_sha256(g)
    return {"_about": "K1's amendment chain (S451 helpers; findings/recompute/K1/README.md, 'Helping K1'). Written by "
                      "S451 genesis, move and abandon only; never by hand.", "genesis": g, "records": []}


def cmd_genesis(a) -> int:
    base = A.load(OUT)
    doc = genesis_doc(base)
    if AMEND.exists():
        old = json.loads(AMEND.read_text())
        if old.get("genesis") == doc["genesis"]:
            print(f"unchanged: {AMEND.relative_to(ROOT)} holds genesis {doc['genesis']['genesis_sha256'][:12]}")
            return 0
        print(f"REFUSED: {AMEND.relative_to(ROOT)} holds another genesis; it is never rewritten")
        return 1
    AMEND.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    A.load_chain(AMEND, base)
    print(f"wrote {AMEND.relative_to(ROOT)}: genesis {doc['genesis']['genesis_sha256'][:12]} over assignment "
          f"{base['assignment_sha256'][:12]}, lock {doc['genesis']['lock_sha256'][:12]}")
    return 0


def cmd_estimates(a) -> int:
    base = A.load(OUT)
    per = per_answer_estimates(a.runs, a.store, a.immutable)
    sha = {c: A.sha256((Path(a.runs) / f"exp_01__{c}__{INDEX}" / "answers.jsonl").read_bytes()) for c in CONFIGS}
    bad = estimates_reproduce(per, base["stage_2_inputs"])
    if bad or sha != base["stage_2_inputs"]["answers_sha256"]:
        print(f"REFUSED: these answers do not give the assignment's question_cost_h again ({len(bad)} (machine, question) "
              f"differ; answers equal: {sha == base['stage_2_inputs']['answers_sha256']}); nothing written")
        return 1
    doc = {"_provenance": {"script": "scripts/S451_k1_assign.py estimates", "computed": iso(now_local()),
                           "runs": str(a.runs), "store": a.store,
                           "what": "per answer of draw 1: [RAGChecker seconds at the Beelink's speed (upper end), RAGAS "
                                   "seconds by the Studio fit]; times rc_factor and ragas_factor of stage_2_inputs they "
                                   "give question_cost_h exactly (S451 check)"},
           "assignment_sha256": base["assignment_sha256"], "answers_sha256": sha, "per_answer": per}
    ESTIMATES.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"wrote {ESTIMATES.relative_to(ROOT)}: {sum(len(v) for v in per.values())} answers of {len(per)} questions; "
          f"they give every signed question_cost_h again")
    return 0


def cmd_worker(a) -> int:
    """The launcher's lookup (D6): the worker's machine, port, clone, the chain head to pin, its fence state."""
    try:
        base = A.load(Path(a.assignment))
        chain = A.load_chain(Path(a.amendments), base)
        eff = A.effective(base, chain)
    except (A.AssignmentError, OSError) as e:
        print(f"REFUSED: {e}")
        return 1
    if a.worker not in eff["registry"]:
        print(f"REFUSED: worker {a.worker!r} is not in the registry of {a.amendments} ({eff['workers']})")
        return 1
    lock_now = A.sha256(LOCK_FILE.read_bytes())
    if lock_now != chain["genesis"]["lock_sha256"]:
        print(f"REFUSED: {rel(LOCK_FILE)} is {lock_now[:8]}, K1 runs under {chain['genesis']['lock_sha256'][:8]} "
              f"(the genesis): check the clone out at a commit with that lock")
        return 1
    w = eff["registry"][a.worker]
    qs = A.worker_questions(eff, a.worker)
    fs = fence_state(Path(a.amendments).parent / a.worker, chain)
    if a.fields:
        print(w["machine"], w["port"], w["clone"], chain["head"], fs)
    else:
        print(json.dumps({"worker": a.worker, **w, "head": chain["head"], "records": len(chain["records"]),
                          "questions": {k: sum(q["stage"] == k for q in qs) for k in A.STAGES}, "fence": fs}))
    return 0


def check_chain(base: dict) -> list[str]:
    """S451 check's part for the helpers: the chain verifies, its genesis is this script's (registry, move rule), the
    estimates give question_cost_h again. Returns the failures. The genesis lock is printed, not checked: a later
    LOCK.toml does not change the assignment, and `S451 worker` (the launcher's lookup) refuses a clone whose lock is
    not the genesis's with that reason (K1 helper review, defect 5)."""
    why = []
    try:
        chain = A.load_chain(AMEND, base)
    except (A.AssignmentError, OSError) as e:
        return [f"amendments: {e}"]
    g = chain["genesis"]
    if g["workers"] != REGISTRY or g["move_rule"] != MOVE_RULE:
        why.append("amendments: the genesis registry or move rule is not this script's")
    lock_now = A.sha256(LOCK_FILE.read_bytes())
    print(f"amendments: genesis lock {g['lock_sha256'][:8]}, experiments/LOCK.toml here {lock_now[:8]}"
          + ("" if lock_now == g["lock_sha256"] else ": a K1 worker refuses to start in this tree (S451 worker)"))
    try:
        load_estimates(base)
    except Refused as e:
        why.append(f"estimates: {e}")
    eff = A.effective(base, chain)
    moves = [r for r in chain["records"] if r["kind"] == "move"]
    print(f"amendments: genesis {g['genesis_sha256'][:12]}, {len(chain['records'])} records ({len(moves)} moves), head "
          f"{chain['head'][:12]}; workers {', '.join(eff['workers'])}")
    if moves:
        cost = base["stage_2_inputs"]["question_cost_h"]
        st = starts_of(base, eff["registry"], now_local())
        made = {r["to"]: dt.datetime.fromisoformat(r["at"]) for r in moves if r.get("to_defined")}
        print("  effective (point estimates, from each worker's signed start or its move; no progress read):")
        for w in eff["workers"]:
            m = eff["registry"][w]["machine"]
            t = made.get(w, st[w])
            qs = A.worker_questions(eff, w)
            h1 = sum(cost[m][q["id"]] for q in qs if q["stage"] == 1)
            h2 = sum(cost[m][q["id"]] for q in qs if q["stage"] == 2)
            print(f"  {w:14s} {m:8s} | stage 1 {sum(q['stage'] == 1 for q in qs):3d} {h1:6.1f} h "
                  f"{local(t + dt.timedelta(hours=h1)):>20s} | stage 2 {sum(q['stage'] == 2 for q in qs):3d} {h2:6.1f} h "
                  f"{local(t + dt.timedelta(hours=h1 + h2)):>20s}")
    return why


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--sizing", default=str(SIZING), help="the file `size` wrote (default findings/recompute/K1/sizing.json)")
    sub.add_parser("check")
    g = sub.add_parser("gate")
    g.add_argument("--records", required=True, help="G1's records: the Studio's findings/recompute/G1_runs or the "
                   "inputs' g1_records/")
    for name in ("plan", "size", "estimates"):
        p = sub.add_parser(name)
        p.add_argument("--runs", required=True, help="the directory holding the six exp_01__<config>__exp_v4_s20_n0 sinks")
        p.add_argument("--store", help="the Chroma directory (default: the store each run recorded)")
        p.add_argument("--immutable", action="store_true", help="open the store's sqlite as immutable (a copy nobody writes)")
        if name == "size":
            p.add_argument("--target-end", default=TARGET_END)
            p.add_argument("--start", nargs="*", help="machine=ISO time with offset, e.g. laptop=2026-10-18T14:00+02:00")
            p.add_argument("--rc-factor", nargs="*", help="machine=x, RAGChecker time relative to the Beelink")
            p.add_argument("--ragas-factor", nargs="*", help="machine=x, RAGAS time relative to the Studio fit")
            p.add_argument("--confidence", type=float, default=CONFIDENCE)
            p.add_argument("--s2-laptop", default=str(S2_LAPTOP), help="the laptop clone running the S2 variant")
            p.add_argument("--stage-1", nargs="*", help="machine=n for all three: the stage 1 counts, in place of "
                           "the fitted n (to keep a stage 1 already drawn when the answers change)")
            p.add_argument("--out", default=str(SIZING), help="where to write the sizing ('' writes nothing)")
    # helpers (Valerio, 17 October; README "Helping K1")
    sub.add_parser("genesis", help="write amendments.json's genesis (refuses to change an existing one)")
    p = sub.add_parser("worker", help="the launcher's lookup: machine, port, clone, chain head, fence state")
    p.add_argument("--worker", required=True)
    p.add_argument("--amendments", default=str(AMEND))
    p.add_argument("--assignment", default=str(OUT))
    p.add_argument("--fields", action="store_true", help="one line: machine port clone head fence")
    for name in ("fence", "progress"):
        p = sub.add_parser(name, help="in the worker's clone" + (", the worker stopped" if name == "fence" else ""))
        p.add_argument("--worker", required=True)
        if name == "progress":
            p.add_argument("--k1", default=str(K1), help="a K1 directory (default this clone's); a copy on the "
                           "coordinator of a worker still on c7ad841: assignment.json, amendments.json and "
                           "<worker>/ragchecker/ragchecker.jsonl, <worker>/ragas/ragas.jsonl (calls optional)")
    p = sub.add_parser("release", help="in the worker's clone, after the amended amendments.json is checked out there")
    p.add_argument("--worker", required=True)
    p.add_argument("--abandon", action="store_true", help="release against an abandon record (nothing moved)")
    p = sub.add_parser("move", help="on the coordinator: append a move to amendments.json")
    p.add_argument("--from", dest="src", required=True)
    p.add_argument("--to", dest="dst", required=True)
    p.add_argument("--new", action="store_true", help="the target is a new worker <machine>_<port>")
    p.add_argument("--to-clone", help="--new: its clone (default ~/projects/mentori-runs-k1-<port>)")
    p.add_argument("--questions", type=int, required=True)
    p.add_argument("--stage", type=int, choices=[1, 2])
    p.add_argument("--fence-from", required=True, help="the source's fence.json, ragchecker.jsonl, ragas.jsonl, copied")
    p.add_argument("--fence-to", help="the target's, when the target exists")
    p.add_argument("--progress", help="a directory of other workers' `progress` JSON (for rates)")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("abandon", help="on the coordinator: release a fence no move used")
    p.add_argument("--worker", required=True)
    p.add_argument("--fence", required=True, help="the copied fence directory")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("suggest", help="on the coordinator: proposed moves; writes nothing")
    p.add_argument("--progress", required=True, help="a directory of `progress` JSON, one per worker")
    p.add_argument("--free", nargs="*", default=[], help="free servers, machine:port (e.g. studio:11451)")
    p.add_argument("--min-gain-h", type=float, default=STOP_COST_H)
    p.add_argument("--now", help="ISO time with offset (default now)")
    a = ap.parse_args()
    tnow = lambda: dt.datetime.fromisoformat(a.now) if getattr(a, "now", None) else None    # noqa: E731
    helpers = {
        "fence": lambda: fence(a.worker),
        "release": lambda: release(a.worker, abandon_=a.abandon),
        "progress": lambda: progress(a.worker, k1=Path(a.k1)),
        "move": lambda: move(a.src, a.dst, a.questions, fence_from=Path(a.fence_from), reason=a.reason,
                             fence_to=Path(a.fence_to) if a.fence_to else None, new=a.new, stage=a.stage,
                             to_clone=a.to_clone,
                             progress=Path(a.progress) if a.progress else None),
        "abandon": lambda: abandon(a.worker, Path(a.fence), a.reason),
        "suggest": lambda: suggest(Path(a.progress), a.free, a.min_gain_h, now=tnow()),
    }
    if a.cmd in helpers:
        return _run(helpers[a.cmd])
    return {"write": cmd_write, "check": cmd_check, "gate": cmd_gate, "plan": cmd_plan, "size": cmd_size,
            "genesis": cmd_genesis, "estimates": cmd_estimates, "worker": cmd_worker}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
