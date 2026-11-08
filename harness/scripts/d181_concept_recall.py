#!/usr/bin/env python3
"""d181_concept_recall - D181's concept recall for the L3 (S471) and L2 (S474) final runs: S505's loose matcher with
the question rule, Q-need, reading (b), on key v2.5. Imported by S471 and S474 under --d181; their default run does
not call it.

D181 (experiments/README.md:1301-1308, Valerio, 30 October): "concept recall (L3, L2, signal C, Figure 3a, Figure 5)
uses the loose matcher with the question rule, S505's loose Q-need under reading (b): a concept's content words that
also occur in the question do not count; the loose matcher's own need rule applies to the words left; a concept made
only of question words is left out of that question's denominator. [...] Implementation: L3 and L2 final runs read
S505's matcher on key v2.5."

THE KEY. data/ground_truth_v2/ground_truth_v2_5_as_v1.json, sha256 a4216184 (S508 pins it the same way,
scripts/S508_judge_49_v25.py:77-78). the_key_v25() also requires: version "2.5"; source_v24_sha256 equal to the v2.4
source key's sha256 that S470.the_key() checked; its provenance's key_v2_4_sha256 equal to the v2.4 key S470 loaded;
the same question ids, question texts, answerable flags and dropped_d7 list as the v2.4 key. So the answers, the
groups (Rule 8) and the question text are those of today's run, and only the concepts change.

THE VALUE OF AN ANSWER (score()). The text is the stored answer with the turn-limit note removed exactly where the
record flags it (scripts/turn_limit_note.strip, as S471 and S474). concept_recall = S505.recall_q(text, concepts,
question, "loose", "need", "b") (scripts/S505_question_aware_matcher.py:148-157): found concepts / concepts counted,
four decimals, None when no concept is counted. Each concept's status, removed words and found flag come from
S505.question_aware with the same indexes, and the found count over the counted concepts must give recall_q's value.
Beside it, the base values on the same v2.5 concepts and text: D12's loose matcher (concept_match_loose) and its rule
1, the exact substring test, as concept_recall_loose_base and concept_recall_exact_base. The headline column is
named concept_recall, not concept_recall_loose, so a reader written for the provisional folders (S473, S497, S475,
S476 read concept_recall_loose) fails on a D181 folder instead of reading another quantity under the old name.

THE GATES (README.md:75-79), all before anything is written. Each script runs its own today's gate first (G-A: S471
reproduces S432 107 of 107, S474 reproduces S383 1,362 of 1,362, on the v2.4 key), then:
  G-B  in the script: score() with an empty question, on the v2.4 concepts, gives the same reference's stored loose
       value on every answer (S432 107 of 107; S383 1,362 of 1,362). With an empty question nothing is removed, so
       this holds the new code path to the old values (S505's own gate G3 states the same of the matcher).
  G-C  here, gate_m4(): score() WITH the questions reproduces S505's stored M4 (findings/recompute/S505_question_aware/
       results.json, sha256 69417cf6, committed with S505 at 9db7065e): the mean of loose_Qneed_b per strategy and
       over all 516 answerable exp04 answers on the v2.4 key (0.4749 overall; D181's "0.534 -> 0.475"), and the
       population's concept counts under the loose removal (571 distinct concepts, 160 with a removed word, 18 with
       none remaining, the 18 listed). The answers are read from the frozen deposit copy (D155)
       findings/recompute/upstream_inputs/publication/results/exp04_generation_latest.json, checked against
       frozen_inputs/SHA256SUMS and against the sha256 S505 recorded for it; the population is S439's selection
       (S439_concept_label_sheet.py:296-324): the rows of the 135 questions (experiment.questions()) whose Rule 8 group
       is answerable, one per strategy and question, the question and concepts from the v2.4 key.
  G-D  in the script: on this run's own inputs, score() with an empty question on the v2.4 concepts gives the
       committed provisional reading's concept_recall_loose on every scored answer (S471: findings/recompute/L3/;
       S474: L2/ for --frozen, L2_d135/ for --frozen-d135), so the answers read are the ones that reading scored.
None of these is a v2.5 value: no concept recall on the final key existed before these runs.

    uv run --frozen python scripts/check_d181_L3_L2.py      the checks and mutants of this module and the --d181 runs
"""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import concept_match_loose  # noqa: E402
import turn_limit_note  # noqa: E402
import S505_question_aware_matcher as S505  # noqa: E402

KEY25 = ROOT / "data" / "ground_truth_v2" / "ground_truth_v2_5_as_v1.json"
KEY25_SHA256 = "a42161841980792f5da521819c97b16dc54999b45838b8eb87cd4315f798270a"     # c1c13184; S508:77-78
KEY25_VERSION = "2.5"
MATCHER, RULE, EMPTY = "loose", "need", "b"                                           # D181
S505_RESULTS = ROOT / "findings" / "recompute" / "S505_question_aware" / "results.json"
S505_RESULTS_SHA256 = "69417cf61ed7dfb7de9080b9e684b7090cf4d0df793a886aa890f138baa069e3"   # committed at 9db7065e
EXP04 = ROOT / "findings" / "recompute" / "upstream_inputs" / "publication" / "results" / "exp04_generation_latest.json"
EXP04_REL = "deposit/publication/results/exp04_generation_latest.json"                  # its name in S505's provenance
M4_COLUMN = "loose_Qneed_b"
M4_TOL = 1e-12                       # the means are sums of four-decimal values: a summation-order allowance only
MATCHER_TEXT = ("D181: S505's loose matcher with the question rule, Q-need, reading (b) "
                "(scripts/S505_question_aware_matcher.py recall_q(text, concepts, question, 'loose', 'need', 'b')): "
                "content words of a concept that also occur in its question do not count, the loose need rule "
                "applies to the words left, a concept made only of question words leaves the denominator; key v2.5")
COLUMNS_TEXT = ("concept_recall: the D181 value (the headline); n_counted, found, concept_status, concept_removed: its "
                "parts per concept; concept_recall_loose_base, concept_recall_exact_base, found_loose_base, "
                "found_exact_base, found_by_base: D12's loose matcher and its exact rule on the same v2.5 concepts, "
                "beside it")
NA_FIELDS = ("note_removed", "scored_text_sha256", "n_concepts", "n_counted", "found", "concept_recall",
             "concept_status", "concept_removed", "found_loose_base", "found_exact_base", "concept_recall_loose_base",
             "concept_recall_exact_base", "found_by_base", "empty_text")


class Refused(Exception):
    """A refusal before anything is written."""


class GateFail(Exception):
    """A D181 gate did not reproduce."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def rel(path: Path) -> str:
    p = Path(path).resolve()
    return p.relative_to(ROOT).as_posix() if ROOT in p.parents or p == ROOT else str(path)


# ---------------------------------------------------------------- the key

def the_key_v25(key24: dict) -> dict:
    """Key v2.5 in S470.the_key()'s shape, held to its pin and to the v2.4 key S470 loaded (module docstring)."""
    raw = KEY25.read_bytes()
    got = sha256_bytes(raw)
    if got != KEY25_SHA256:
        raise Refused(f"{rel(KEY25)} sha256 {got[:12]} is not the v2.5 pin {KEY25_SHA256[:12]}")
    d = json.loads(raw)
    if str(d.get("version")) != KEY25_VERSION:
        raise Refused(f"{KEY25.name} says version {d.get('version')!r}, not {KEY25_VERSION}")
    if d.get("source_v24_sha256") != key24["source"]["sha256"]:
        raise Refused(f"{KEY25.name} was not built from {key24['source']['path']} (source_v24_sha256)")
    if (d.get("provenance") or {}).get("key_v2_4_sha256") != key24["sha256"]:
        raise Refused(f"{KEY25.name}'s provenance names another v2.4 key than {key24['path']}")
    qs = {q["id"]: q for q in d["questions"]}
    old = key24["questions"]
    if set(qs) != set(old) or list(d["dropped_d7"]) != list(key24["dropped_d7"]):
        raise Refused(f"{KEY25.name} holds other questions or another dropped_d7 list than the v2.4 key")
    diff = [q for q in qs if (qs[q].get("question"), qs[q].get("answerable"))
            != (old[q].get("question"), old[q].get("answerable"))]
    if diff:
        raise Refused(f"{KEY25.name}: question text or answerable flag differs from v2.4 on {len(diff)}, first {diff[:3]}")
    return {"path": rel(KEY25), "file": KEY25, "sha256": got, "version": KEY25_VERSION,
            "source": dict(key24["source"]), "dropped_d7": list(d["dropped_d7"]), "questions": qs}


# ---------------------------------------------------------------- the value of an answer

def score(answer: str, concepts: list, question: str, flagged) -> dict:
    """One answer under D181 (module docstring, THE VALUE OF AN ANSWER), with the base values beside it."""
    text, removed = turn_limit_note.strip(answer, flagged)
    value = S505.recall_q(text, list(concepts), question, MATCHER, RULE, EMPTY)
    ai, qi = S505._Index(text), S505._Index(question, content_only=True)
    per = [S505.question_aware(text, c, question, MATCHER, RULE, ai, qi) for c in concepts]
    counted = [p for p in per if not (EMPTY == "b" and p["status"] == "no_remaining")]
    found = sum(p["found"] for p in counted)
    if value != (round(found / len(counted), 4) if counted else None):
        raise Refused(f"S505.recall_q gives {value} where its per-concept verdicts give {found} of {len(counted)}")
    loose, base = concept_match_loose.concept_recall_loose(text, list(concepts), detail=True)
    n_exact = sum(1 for x in base if x["found_by"] == "exact")
    return {"note_removed": removed, "scored_text_sha256": sha256_bytes(text.encode("utf-8")),   # S470.sha256_text
            "n_concepts": len(concepts), "n_counted": len(counted), "found": found, "concept_recall": value,
            "concept_status": [p["status"] for p in per], "concept_removed": [p["removed"] for p in per],
            "found_loose_base": sum(1 for x in base if x["found_by"] is not None), "found_exact_base": n_exact,
            "concept_recall_loose_base": loose, "concept_recall_exact_base": round(n_exact / len(concepts), 4),
            "found_by_base": [x["found_by"] for x in base], "empty_text": not text.strip()}


def na_fields() -> dict:
    """A row concept recall does not score (S471's not-answerable questions): every value null."""
    return dict.fromkeys(NA_FIELDS) | {"note_removed": False}


def base_view(row: dict) -> dict:
    """The row with its base values under the provisional names, for S471.counts() (S474.counts() reads no value)."""
    out = dict(row)
    for k in ("concept_recall_loose", "concept_recall_exact", "found_loose", "found_exact", "found_by"):
        out[k] = row.get(f"{k}_base")
    return out


def concept_counts(rows: list) -> dict:
    """Over the scored rows, each pair of an answer and one of its concepts: pairs by status, pairs whose concept
    loses a word to the question; and the rows with no value."""
    st = collections.Counter(s for r in rows for s in (r.get("concept_status") or []))
    return {"pairs_by_status": dict(sorted(st.items())),
            "pairs_with_a_removed_word": sum(bool(x) for r in rows for x in (r.get("concept_removed") or [])),
            "rows_no_value": sum(r.get("concept_status") is not None and r.get("concept_recall") is None
                                 for r in rows)}


# ---------------------------------------------------------------- gates and rule cases

Q_MQC = S505.Q_MQC
SPEC_CASES = [
    # (name, answer, concepts, question, flagged, concept_recall, n_counted)
    ("reading (b): a concept made only of question words leaves the denominator", "It supports 22 tools.",
     ["common bioinformatics tools", "22 common bioinformatics tools"], Q_MQC, None, 1.0, 1),
    ("the echo of the question earns nothing", "MultiQC supports many common bioinformatics tools.",
     ["22 common bioinformatics tools"], Q_MQC, None, 0.0, 1),
    ("Q-need, not Q-all: 3 of 4 remaining words", "tumour and normal reads", ["tumour normal paired reads"],
     "Which tool is used?", None, 1.0, 1),
    ("an empty question is the base loose matcher", "MultiQC supports many common bioinformatics tools.",
     ["22 common bioinformatics tools"], "", None, 1.0, 1),
    ("the note removed where flagged", "A partial report." + turn_limit_note.NOTE, ["turn limit analysis"],
     "Which report?", True, 0.0, 1),
    ("the note read where not flagged", "A partial report." + turn_limit_note.NOTE, ["turn limit analysis"],
     "Which report?", False, 1.0, 1),
    ("an empty text scores 0", "", ["partial report", "22 tools"], "Which report?", None, 0.0, 2),
]


def spec_failures() -> list:
    """S505's own cases, then SPEC_CASES through score()."""
    bad = list(S505.spec_failures())
    for name, a, cs, q, fl, want, n in SPEC_CASES:
        got = score(a, cs, q, fl)
        if (got["concept_recall"], got["n_counted"]) != (want, n):
            bad.append(f"{name}: concept_recall {got['concept_recall']}, counted {got['n_counted']}; want {want}, {n}")
    return bad


def exp04_population(key24: dict, groups) -> list[dict]:
    """S439's population from the frozen exp04 file: (strategy, question_id, text, concepts, question) of every row
    whose question is one of the 135 and answerable (Rule 8), in S505's order (strategy as listed in the file's
    configs, then question id). groups(qid) is records.group_of."""
    from experiments.runner import experiment as ex
    import fig_repro
    try:
        fig_repro.check_committed(EXP04)
    except fig_repro.FrozenInputError as e:
        raise GateFail(f"the frozen exp04 file: {e}") from None
    doc = json.loads(EXP04.read_text(encoding="utf-8"))
    ids = {q["id"] for q in ex.questions()}
    configs = list(doc["configs"])
    seen, out = set(), []
    for r in doc["per_question_results"]:
        q = r["question_id"]
        if q not in ids or groups(q) != "answerable":
            continue
        if (r["config"], q) in seen or r["config"] not in configs:
            raise GateFail(f"exp04: {r['config']} {q} twice, or a strategy outside {configs}")
        seen.add((r["config"], q))
        text = (r.get("generation") or {}).get("answer")
        if not isinstance(text, str) or text.startswith("GenerationResult("):
            raise GateFail(f"exp04: {r['config']} {q} holds no plain answer text")
        k = key24["questions"][q]
        out.append({"strategy": r["config"], "question_id": q, "text": text,
                    "concepts": list(k["expected_concepts"]), "question": k["question"]})
    out.sort(key=lambda a: (configs.index(a["strategy"]), a["question_id"]))
    return out


def gate_m4(key24: dict, groups=None) -> dict:
    """G-C (module docstring): score() with the questions reproduces S505's stored M4 on the v2.4 key."""
    if groups is None:
        from experiments.scorers import records
        groups = records.group_of
    got_sha = sha256_file(S505_RESULTS)
    if got_sha != S505_RESULTS_SHA256:
        raise GateFail(f"{rel(S505_RESULTS)} sha256 {got_sha[:12]} is not the committed {S505_RESULTS_SHA256[:12]}")
    res = json.loads(S505_RESULTS.read_text(encoding="utf-8"))
    prov = res["provenance"]
    if prov["key"]["v1_format_sha256"] != key24["sha256"]:
        raise GateFail(f"S505's M4 was measured on key {prov['key']['v1_format_sha256'][:12]}, not {key24['sha256'][:12]}")
    if prov["inputs_sha256"].get(EXP04_REL) != sha256_file(EXP04):
        raise GateFail(f"{rel(EXP04)} is not the exp04 file S505 read")
    pop = exp04_population(key24, groups)
    per = collections.defaultdict(list)
    for a in pop:
        v = score(a["text"], a["concepts"], a["question"], None)["concept_recall"]
        if v is not None:
            per[a["strategy"]].append(v)
            per["all"].append(v)
    table = {r["strategy"]: r for r in res["M4_recall"]["table"]}
    bad = []
    for s, r in table.items():
        vals = per.get(s, [])
        mean = sum(vals) / len(vals) if vals else None
        if mean is None or len(vals) != r[f"{M4_COLUMN}_n"] or abs(mean - r[M4_COLUMN]) > M4_TOL:
            bad.append(f"{s}: {mean} on {len(vals)} (stored {r[M4_COLUMN]} on {r[f'{M4_COLUMN}_n']})")
    if set(per) != set(table) or bad:
        raise GateFail(f"S505's M4 {M4_COLUMN} not reproduced: {bad[:3] or sorted(set(per) ^ set(table))}")
    seen = {}
    for a in pop:
        for c in a["concepts"]:
            seen[(a["question_id"], c)] = a["question"]
    removed_any, lst = 0, []
    for (qid, c), qtext in sorted(seen.items()):
        d = S505.question_aware("", c, qtext, MATCHER, RULE)
        removed_any += bool(d["removed"])
        if d["status"] == "no_remaining":
            lst.append({"question_id": qid, "concept": c, "content_words": d["content_words"]})
    want = res["M4_recall"]["population_concepts"][MATCHER]
    mine = {"distinct_concepts": len(seen), "with_a_removed_word": removed_any, "no_remaining": len(lst),
            "no_remaining_list": lst}
    if mine != want:
        raise GateFail(f"S505's population concept counts not reproduced: {({k: v for k, v in mine.items() if k != 'no_remaining_list'})} "
                       f"against {({k: v for k, v in want.items() if k != 'no_remaining_list'})}")
    return {"reference": rel(S505_RESULTS), "reference_sha256": got_sha, "answers": rel(EXP04),
            "answers_sha256": sha256_file(EXP04), "column": M4_COLUMN,
            "reproduced": {s: [round(sum(per[s]) / len(per[s]), 4), len(per[s])] for s in table},
            "population_concepts": {k: v for k, v in mine.items() if k != "no_remaining_list"},
            "compared": "the mean of score()'s concept_recall per strategy and over all answers equals S505's "
                        "M4_recall loose_Qneed_b (and its n) within 1e-12; the population's loose removal counts and "
                        "no-remaining list equal population_concepts.loose"}


def code_sha256() -> dict:
    return {"scripts/d181_concept_recall.py": sha256_file(Path(__file__)),
            "scripts/S505_question_aware_matcher.py": sha256_file(SCRIPTS / "S505_question_aware_matcher.py"),
            "scripts/concept_match_stem.py": sha256_file(SCRIPTS / "concept_match_stem.py"),
            "scripts/concept_match_loose.py": sha256_file(SCRIPTS / "concept_match_loose.py"),
            "scripts/turn_limit_note.py": sha256_file(SCRIPTS / "turn_limit_note.py")}
