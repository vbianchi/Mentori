#!/usr/bin/env python3
"""S576 (D249 O1): G17's draws 2 and 3, D249's hypotheses H1 to H5 as experiments/README.md D249 writes them.

THE TEST (D249, written before any answer of draws 2 and 3 existed; not changed here). Per arm and question, the mean of
draws 2 and 3 of pass at 4 and of concept recall; per contrast, the mean over questions of the per-question difference
with the 95% percentile interval over 10,000 question resamples (S463.interval, default_rng(20261013), S463.PCT); all
86 answerable questions unless named. Arms: control R' (rlm_10_ctrl), B search off (rlm_10_nosearch), C gate off
(rlm_10_nogate), and the package RLM, whose draws 2 and 3 are G6's (cap 10, stored and judged).

  H1  package - control, concept recall: below 0.
  H2  search off - control, concept recall: below 0; and search off - package, concept recall: interval contains 0.
  H3  gate off - control, concept recall: below 0.
  H4  for B and for C: (control - arm) on one-paper questions minus (control - arm) on many-paper questions, concept
      recall: above 0.
  H5  search off - control and gate off - control, pass at 4: below 0; package - control, pass at 4: interval contains 0.

How "below 0", "above 0" and "contains 0" are read: the 95% interval lies wholly below 0 (its upper end < 0), wholly
above 0 (its lower end > 0), or holds 0 (lower end <= 0 <= upper end). A hypothesis with several parts (H2, H4, H5) is
HELD when every part holds, else NOT HELD; each part's verdict is reported beside it.

H4's interval. S463.interval gives a ratio of sums over one set of drawn questions; H4 is a difference between two
groups' means. On each of the same 10,000 resamples of the 86 (S463.resample_counts(86), the counts S463.interval uses
for 86 questions) H4's statistic is the mean of (control - arm) over the drawn one-paper questions minus its mean over
the drawn many-paper questions (each question as often as drawn); a resample that draws no question of one kind is left
out (as S463.interval leaves out a resample with no denominator); percentiles S463.PCT.

Values per answer, as S575 reads them (Rule 10): a failed answer passes nothing and scores concept recall 0; a judge cell
without a score (unscored) counts as not passing, as in S575; the number of such cells per arm is reported. An answer
that did not fail but has no judge cell or no concept recall is refused (it would be read as 0 silently).

Beside the test, descriptive and without a verdict: the same contrasts on the mean of draws 1, 2 and 3 per question.

INPUT. S571 --g17 --g17-d23's reading (findings/recompute/S571_rlm_reading/g17_d123/g17_reading.json): per answer at
draws 1 to 3 the strategy, question, kind, judge cell, pass at 4 and concept recall, G17's from S572 and S573, G6's from
Figure 3's cells and L2_d135_d181. Refused unless it is D249's (draws 1, 2, 3), judged and with concept recall, and each
of the four arms has exactly one answer per question at each of draws 1, 2 and 3 on the 86.

REPRODUCE FIRST (README.md:75-79). From the reading's draw-1 rows, S575's own functions (values, contrast) must give
every number of S575's committed contrasts.json (findings/recompute/S575_g17_contrasts/), 36 contrasts: n, means,
difference, interval, P, counts. Otherwise nothing is written.

OUT. --out (default findings/recompute/S576_d249/): s576_d249.json and s576_d249.md. README.md there is the
integrator's steps, not written by this script. No model call.

    uv run --frozen python scripts/S576_d249_hypotheses.py [--reading FILE] [--s575 FILE] [--out DIR]
    uv run --frozen python scripts/S576_d249_hypotheses_test.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import S463_fig2_ranking as S463  # noqa: E402
import S575_g17_contrasts as S575  # noqa: E402

SCRIPT = "scripts/S576_d249_hypotheses.py"
READING = ROOT / "findings/recompute/S571_rlm_reading/g17_d123/g17_reading.json"
S575_JSON = ROOT / "findings/recompute/S575_g17_contrasts/contrasts.json"
OUT = ROOT / "findings/recompute/S576_d249"
ARMS = {"ctrl": "rlm_10_ctrl", "search_off": "rlm_10_nosearch", "gate_off": "rlm_10_nogate", "package": "cap10"}
LABEL = {"ctrl": "control R'", "search_off": "B search off", "gate_off": "C gate off", "package": "package RLM (G6)"}
N_QUESTIONS = 86
TEST_DRAWS = (2, 3)
ALL_DRAWS = (1, 2, 3)
GROUPS = ("all", "one", "many")
REPRO_FIELDS = ("n_questions", "mean_a", "mean_b", "diff", "ci95", "p_two_sided", "a_higher", "b_higher")

# (part id, kind, a, b, group, metric, criterion); kind "diff": a - b; kind "h4": (b - a) one-paper minus (b - a)
# many-paper, a being the arm and b the control
HYPOTHESES = {
    "H1": [("H1", "diff", "package", "ctrl", "all", "cr", "below")],
    "H2": [("H2a", "diff", "search_off", "ctrl", "all", "cr", "below"),
           ("H2b", "diff", "search_off", "package", "all", "cr", "contains")],
    "H3": [("H3", "diff", "gate_off", "ctrl", "all", "cr", "below")],
    "H4": [("H4 B", "h4", "search_off", "ctrl", "one - many", "cr", "above"),
           ("H4 C", "h4", "gate_off", "ctrl", "one - many", "cr", "above")],
    "H5": [("H5a", "diff", "search_off", "ctrl", "all", "pass4", "below"),
           ("H5b", "diff", "gate_off", "ctrl", "all", "pass4", "below"),
           ("H5c", "diff", "package", "ctrl", "all", "pass4", "contains")],
}
WORDING = {
    "H1": "package minus control on concept recall below 0",
    "H2": "search off minus control on concept recall below 0, and search off minus package on concept recall with an "
          "interval containing 0",
    "H3": "gate off minus control on concept recall below 0",
    "H4": "for B and for C, (control minus arm) on one-paper questions minus (control minus arm) on many-paper "
          "questions above 0, on concept recall",
    "H5": "search off minus control and gate off minus control on pass at 4 below 0; package minus control on pass at 4 "
          "with an interval containing 0",
}


class Refused(Exception):
    pass


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p: Path) -> str:
    """p relative to the repository when it lies in it (S612 F2: provenance keys that do not depend on the checkout's
    location), else as given."""
    q = Path(p).resolve()
    return str(q.relative_to(ROOT)) if q.is_relative_to(ROOT) else str(p)


# ---------------------------------------------------------------- reading the rows

def per_answer(rows: list, draws=ALL_DRAWS) -> tuple[dict, dict]:
    """{arm: {(question, draw): {"group", "pass4", "cr"}}} by S575's rule (module docstring), and per arm the count of
    unscored judge cells. Refused when an arm has another number of answers than one per question and draw, or a
    non-failed answer has no judge cell or no concept recall."""
    by_strategy = {s: a for a, s in ARMS.items()}
    out = {a: {} for a in ARMS}
    unscored = {a: 0 for a in ARMS}
    bad = []
    for r in rows:
        arm = by_strategy.get(r["strategy"])
        if arm is None or r["draw"] not in draws:
            continue
        k = (r["question_id"], r["draw"])
        if k in out[arm]:
            raise Refused(f"two answers of {arm} to {k[0]} at draw {k[1]}")
        failed = bool(r.get("failed"))
        if not failed and r.get("cell") is None:
            bad.append(f"{arm} {k[0]} d{k[1]}: no judge cell")
        if not failed and r.get("concept_recall") is None:
            bad.append(f"{arm} {k[0]} d{k[1]}: no concept recall")
        unscored[arm] += r.get("cell") == "unscored"
        cr = r.get("concept_recall")
        out[arm][k] = {"group": r["group"], "pass4": 0 if failed else int(r.get("pass4") or 0),
                       "cr": 0.0 if failed else float(cr if cr is not None else 0.0)}
    for arm, x in out.items():
        qs = {q for q, _ in x}
        for d in draws:
            n = sum(1 for _, dd in x if dd == d)
            if n != N_QUESTIONS:
                raise Refused(f"{arm} ({ARMS[arm]}) has {n} answers at draw {d}, not {N_QUESTIONS}: every arm needs "
                              f"answers at draws {', '.join(map(str, draws))}")
        if len(qs) != N_QUESTIONS:
            raise Refused(f"{arm} answers {len(qs)} questions, not {N_QUESTIONS}")
    if bad:
        raise Refused(f"{len(bad)} answers not failed but unread (first {bad[:3]})")
    qsets = {a: frozenset(q for q, _ in x) for a, x in out.items()}
    if len(set(qsets.values())) != 1:
        raise Refused("the four arms answer different questions")
    return out, unscored


def question_means(ans: dict, draws: tuple) -> dict:
    """{arm: {question: {"group", "pass4", "cr"}}}: per question the mean over the draws given."""
    out = {}
    for arm, x in ans.items():
        qs = sorted({q for q, _ in x})
        out[arm] = {}
        for q in qs:
            v = [x[(q, d)] for d in draws]
            groups = {e["group"] for e in v}
            if len(groups) != 1:
                raise Refused(f"{arm} {q}: kinds {groups} differ between draws")
            out[arm][q] = {"group": v[0]["group"], "pass4": sum(e["pass4"] for e in v) / len(v),
                           "cr": sum(e["cr"] for e in v) / len(v)}
    return out


# ---------------------------------------------------------------- intervals

def diff_interval(a: dict, b: dict, group: str, metric: str) -> dict:
    """Mean of a - b per question over the group's questions, with S463.interval's 95% interval (scaled to percentage
    points for pass at 4)."""
    qs = sorted(q for q in a if q in b and (group == "all" or a[q]["group"] == group))
    diffs = [a[q][metric] - b[q][metric] for q in qs]
    n = len(qs)
    lo, hi = S463.interval(diffs, [1.0] * n)
    sc = 100 if metric == "pass4" else 1
    return {"n_questions": n, "mean_a": sc * sum(a[q][metric] for q in qs) / n,
            "mean_b": sc * sum(b[q][metric] for q in qs) / n, "diff": sc * sum(diffs) / n, "ci95": [sc * lo, sc * hi],
            "a_higher": sum(x > 0 for x in diffs), "b_higher": sum(x < 0 for x in diffs)}


def counts(n: int):
    """S463's resample counts for n questions, from S463's own cache (the counts S463.interval uses)."""
    if n not in S463._COUNTS:
        S463._COUNTS[n] = S463.resample_counts(n)
    return S463._COUNTS[n]


def group_difference_interval(d: list, is_one: list) -> list[float]:
    """H4's 95% interval (module docstring): per resample of the n questions, the mean of d over the drawn one-paper
    questions minus its mean over the drawn many-paper ones; resamples without both kinds left out."""
    import numpy as np
    w = counts(len(d))
    dv = np.array(d, dtype=float)
    one = np.array([1.0 if x else 0.0 for x in is_one])
    many = 1.0 - one
    b1, b2 = w @ one, w @ many
    ok = (b1 > 0) & (b2 > 0)
    stat = (w @ (dv * one))[ok] / b1[ok] - (w @ (dv * many))[ok] / b2[ok]
    return [float(v) for v in np.percentile(stat, S463.PCT)]


def h4(arm: dict, ctrl: dict, metric: str) -> dict:
    qs = sorted(q for q in ctrl if q in arm)
    d = [ctrl[q][metric] - arm[q][metric] for q in qs]
    is_one = [ctrl[q]["group"] == "one" for q in qs]
    one = [x for x, o in zip(d, is_one) if o]
    many = [x for x, o in zip(d, is_one) if not o]
    lo, hi = group_difference_interval(d, is_one)
    sc = 100 if metric == "pass4" else 1
    return {"n_questions": len(qs), "n_one": len(one), "n_many": len(many),
            "ctrl_minus_arm_one": sc * sum(one) / len(one), "ctrl_minus_arm_many": sc * sum(many) / len(many),
            "diff": sc * (sum(one) / len(one) - sum(many) / len(many)), "ci95": [sc * lo, sc * hi]}


def meets(ci: list, criterion: str) -> bool:
    lo, hi = ci
    return {"below": hi < 0, "above": lo > 0, "contains": lo <= 0 <= hi}[criterion]


def evaluate(means: dict, verdict: bool) -> dict:
    """Every hypothesis part on the per-question means; with verdict, each part's and each hypothesis's HELD."""
    out = {}
    for h, parts in HYPOTHESES.items():
        res = []
        for pid, kind, a, b, group, metric, crit in parts:
            x = diff_interval(means[a], means[b], group, metric) if kind == "diff" else h4(means[a], means[b], metric)
            e = {"part": pid, "kind": kind, "a": a, "b": b, "group": group, "metric": metric, "criterion": crit, **x}
            if verdict:
                e["holds"] = meets(x["ci95"], crit)
            res.append(e)
        out[h] = {"wording": WORDING[h], "parts": res}
        if verdict:
            out[h]["verdict"] = "HELD" if all(p["holds"] for p in res) else "NOT HELD"
    return out


def arm_means(means: dict) -> dict:
    return {a: {g: {"n_questions": len(qs), "pass4_pct": 100 * sum(means[a][q]["pass4"] for q in qs) / len(qs),
                    "concept_recall": sum(means[a][q]["cr"] for q in qs) / len(qs)}
                for g in GROUPS for qs in [[q for q in means[a] if g == "all" or means[a][q]["group"] == g]]}
            for a in means}


# ---------------------------------------------------------------- reproduce S575 from the draw-1 rows

def reproduce_s575(rows: list, s575: dict) -> list[str]:
    """S575's values and contrast on the reading's draw-1 rows must give every committed number."""
    v = {arm: S575.values(rows, arm) for arm in S575.ARMS}
    bad = []
    for arm, x in v.items():
        if len(x) != N_QUESTIONS:
            bad.append(f"{arm}: {len(x)} draw-1 answers, not {N_QUESTIONS}")
    if bad:
        return bad
    want = s575["contrasts"]
    if len(want) != len(S575.PAIRS) * len(S575.GROUPS) * 2:
        return [f"S575 holds {len(want)} contrasts, not {len(S575.PAIRS) * len(S575.GROUPS) * 2}"]
    for c in want:
        got = S575.contrast(v[c["a"]], v[c["b"]], c["group"], c["metric"])
        for f in REPRO_FIELDS:
            g, w = got[f], c[f]
            same = (all(abs(x - y) <= 1e-12 for x, y in zip(g, w)) if isinstance(w, list) else abs(g - w) <= 1e-12)
            if not same:
                bad.append(f"{c['a']}-{c['b']} {c['group']} {c['metric']} {f}: {g} vs S575 {w}")
    return bad


# ---------------------------------------------------------------- output

def fmt(x: float, metric: str) -> str:
    return f"{x:.1f}" if metric == "pass4" else f"{x:.3f}"


def write_md(res: dict, path: Path) -> None:
    pv = res["_provenance"]
    L = ["# S576: D249's hypotheses on G17's draws 2 and 3", "",
         f"Generated by `uv run --frozen python {SCRIPT}` (code sha256 {pv['code_sha256'][SCRIPT][:12]}). Per arm and "
         "question the mean of draws 2 and 3; per contrast the mean over questions of the per-question difference with "
         "the 95% percentile interval over 10,000 question resamples (seed 20261013). Pass at 4 in percentage points, "
         "concept recall as a share. Below 0: the interval's upper end under 0; above 0: its lower end over 0; contains "
         "0: lower end at most 0 and upper end at least 0. A hypothesis is held when every part holds.", "",
         f"Reproduced first: S575's {res['reproduce']['contrasts']} draw-1 contrasts from this reading's draw-1 rows, "
         "every number equal.", "", "## Verdicts, draws 2 and 3 (the test)", "",
         "| Hypothesis | Part | Contrast | Questions | Metric | Value | 95% interval | Criterion | Part holds | "
         "Hypothesis |", "|---|---|---|---|---|---|---|---|---|---|"]

    def contrast_text(p):
        if p["kind"] == "diff":
            return f"{LABEL[p['a']]} minus {LABEL[p['b']]}"
        return f"(control minus {LABEL[p['a']]}): one-paper minus many-paper"

    for h, x in res["test_draws_2_3"].items():
        for i, p in enumerate(x["parts"]):
            L.append(f"| {h if i == 0 else ''} | {p['part']} | {contrast_text(p)} | {p['group']} ({p['n_questions']}) "
                     f"| {p['metric']} | {fmt(p['diff'], p['metric'])} | {fmt(p['ci95'][0], p['metric'])} to "
                     f"{fmt(p['ci95'][1], p['metric'])} | {p['criterion']} 0 | {'yes' if p['holds'] else 'no'} | "
                     f"{x['verdict'] if i == 0 else ''} |")
    L += ["", "## Beside: draws 1, 2 and 3 together (descriptive, no verdict)", "",
          "| Hypothesis | Part | Contrast | Questions | Metric | Value | 95% interval |", "|---|---|---|---|---|---|---|"]
    for h, x in res["descriptive_draws_1_3"].items():
        for i, p in enumerate(x["parts"]):
            L.append(f"| {h if i == 0 else ''} | {p['part']} | {contrast_text(p)} | {p['group']} ({p['n_questions']}) "
                     f"| {p['metric']} | {fmt(p['diff'], p['metric'])} | {fmt(p['ci95'][0], p['metric'])} to "
                     f"{fmt(p['ci95'][1], p['metric'])} |")
    L += ["", "## Arm means per question kind", "",
          "| Arm | Kind | Questions | Pass at 4, draws 2-3 | Concept recall, draws 2-3 | Pass at 4, draws 1-3 | "
          "Concept recall, draws 1-3 |", "|---|---|---|---|---|---|---|"]
    for a in ARMS:
        for g in GROUPS:
            t, d = res["arm_means"]["draws_2_3"][a][g], res["arm_means"]["draws_1_3"][a][g]
            L.append(f"| {LABEL[a]} | {g} | {t['n_questions']} | {t['pass4_pct']:.1f} | {t['concept_recall']:.3f} | "
                     f"{d['pass4_pct']:.1f} | {d['concept_recall']:.3f} |")
    L += ["", "Judge cells without a score (counted as not passing, as S575), per arm over draws 1 to 3: " +
          ", ".join(f"{LABEL[a]} {n}" for a, n in res["unscored_cells"].items()) + "."]
    path.write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reading", type=Path, default=READING, help="S571 --g17 --g17-d23's g17_d123/g17_reading.json")
    ap.add_argument("--s575", type=Path, default=S575_JSON, help="S575's committed contrasts.json (the reproduce)")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    try:
        if not a.reading.exists():
            raise Refused(f"no {a.reading} (S571 --g17 ... --g17-d23 ... writes it)")
        d = json.loads(a.reading.read_text())
        if d.get("decision") != "D249" or d.get("draws") != list(ALL_DRAWS):
            raise Refused(f"{a.reading} is not S571's D249 reading of draws 1, 2, 3 (decision {d.get('decision')}, "
                          f"draws {d.get('draws')})")
        if not (d.get("judged") and d.get("concept_recall_given")):
            raise Refused(f"{a.reading} lacks the judge or the concept recall")
        rows = d["answers"]
        bad = reproduce_s575(rows, json.loads(a.s575.read_text()))
        print(f"  {'ok  ' if not bad else 'FAIL'}  REPRODUCE S575's draw-1 contrasts from the reading's draw-1 rows"
              f"{'' if not bad else ': ' + '; '.join(bad[:5])}")
        if bad:
            raise Refused(f"reproduce failed ({len(bad)} numbers differ from S575)")
        ans, unscored = per_answer(rows)
    except Refused as e:
        print(f"REFUSED: {e}\nNOTHING WRITTEN", file=sys.stderr)
        return 2
    m23, m123 = question_means(ans, TEST_DRAWS), question_means(ans, ALL_DRAWS)
    res = {"_provenance": {"script": SCRIPT,  # no run time or git head (S608, 9 Nov): a rerun of the same code on the same inputs is byte-equal
                           "command": " ".join([f"uv run --frozen python {SCRIPT}"] +
                                               list(argv if argv is not None else sys.argv[1:])),
                           "inputs_sha256": {rel(a.reading): sha(a.reading), rel(a.s575): sha(a.s575)},
                           "code_sha256": {SCRIPT: sha(Path(__file__)),
                                           "scripts/S463_fig2_ranking.py": sha(SCRIPTS / "S463_fig2_ranking.py"),
                                           "scripts/S575_g17_contrasts.py": sha(SCRIPTS / "S575_g17_contrasts.py")},
                           "boot": S463.N_BOOT, "seed": S463.SEED, "percentiles": list(S463.PCT),
                           "decision": "D249"},
           "reproduce": {"contrasts": len(json.loads(a.s575.read_text())["contrasts"]), "equal": True,
                         "what": "S575.values and S575.contrast on the reading's draw-1 rows give every number of "
                                 "S575's contrasts.json"},
           "arms": {k: {"strategy": v, "label": LABEL[k]} for k, v in ARMS.items()},
           "rules": {"below": "interval upper end < 0", "above": "interval lower end > 0",
                     "contains": "interval lower end <= 0 <= upper end", "held": "every part holds",
                     "values": "failed answer: pass 0, concept recall 0; unscored judge cell: not passing (S575)",
                     "h4_interval": "per resample of the 86 (S463.resample_counts(86)): mean of (control - arm) over "
                                    "the drawn one-paper questions minus over the drawn many-paper ones"},
           "test_draws_2_3": evaluate(m23, verdict=True),
           "descriptive_draws_1_3": evaluate(m123, verdict=False),
           "arm_means": {"draws_2_3": arm_means(m23), "draws_1_3": arm_means(m123)},
           "unscored_cells": unscored}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "s576_d249.json").write_text(json.dumps(res, indent=1) + "\n")
    write_md(res, a.out / "s576_d249.md")
    for h, x in res["test_draws_2_3"].items():
        parts = "; ".join(f"{p['part']} {fmt(p['diff'], p['metric'])} [{fmt(p['ci95'][0], p['metric'])}, "
                          f"{fmt(p['ci95'][1], p['metric'])}] {p['criterion']} 0: {'yes' if p['holds'] else 'no'}"
                          for p in x["parts"])
        print(f"{h} {x['verdict']}: {parts}")
    print(f"wrote {a.out / 's576_d249.json'} and s576_d249.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
