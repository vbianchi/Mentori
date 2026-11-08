#!/usr/bin/env python3
"""S505 - question-aware versions of the loose and the stem concept matchers (Q18, O3, 30 October 2026), and the
measures that show what they change.

WHY. A concept of the answer key often repeats words of its own question: "22 common bioinformatics tools" for "how
many common bioinformatics tools does MultiQC support?". The loose matcher finds a concept when ceil(2/3) of its
content words occur in the answer, so an answer that only repeats the question ("MultiQC supports many common
bioinformatics tools") is credited with the concept: 3 of its 4 content words are there. O3 (Valerio, Q18): words of
the concept that are already in the question do not count. This module gives that rule for both matchers and
measures whether it removes the free credit without taking credit from concepts an answer does state.

THE RULE (question_aware()). It changes neither scripts/concept_match_loose.py nor scripts/concept_match_stem.py and
reuses their parts: the tokeniser, the number test, the trailing-s rule and the Snowball stem as concept_match_stem
writes them (its gate T3 holds them to the loose function's own nested functions), and the loose rule's stop words.
  1. The concept's content words are the base matcher's: its tokens minus the 49 stop words, a number always kept.
  2. The question's content words are found the same way: its tokens minus the stop words, numbers kept.
  3. A content word of the concept is REMOVED when it matches a content word of the question under the matcher's own
     word test: for both matchers, a number matches only the identical number token, any other word matches when
     the two are equal after one trailing "s" is removed from each (tokens longer than 3 characters); the stem
     matcher also counts two words with the same Snowball English stem (a number is never stemmed). The words left
     are the REMAINING words.
  4. Each remaining word is looked up in the answer with the same word test (the answer's tokens, stop words
     included, as both base matchers read the answer).
  5. Q-all: the concept is found when every remaining word occurs in the answer.
     Q-need: the concept is found when at least need(r) remaining words occur, need(r) = (2r + 2) // 3, the base
     matchers' own ceil(2/3) applied to the r remaining words.
     In both, the exact rule (the concept's lower-cased text is a substring of the lower-cased answer) also finds the
     concept, but only when at least one remaining word exists.
  6. A concept with content words of which none remains (every one is in the question) has no remaining word. It is
     scored two ways: (a) not found; (b) left out of the denominator. A concept with no content word at all (stop
     words only) keeps the base rule: found by the exact rule only.
With an empty question nothing is removed and Q-need is the base matcher (gate G3 holds this on every pair).

    uv run python scripts/S505_question_aware_matcher.py          writes findings/recompute/S505_question_aware/
    uv run python scripts/S505_question_aware_matcher_test.py     the hand cases

MEASURES (each with its own docstring below):
  M1  measure_p2: agreement with Valerio's P2 labels (D17), the 249 labelled pairs of S439, as S439 --analyze scores
      the base matchers: found among stated and not stated among found, unweighted and weighted, 95% bootstrap
      intervals from S439's own replicates.
  M2  measure_penalty: every labelled pair stated (yes, or partly) that a base matcher finds and its Q variant does
      not, with the question, the concept, the removed words and the answer passage.
  M3  measure_free_credit: the question text scored as the answer against every concept of its question, on the
      answerable questions of findings/recompute/S504_key_v2_5/ground_truth_v2_5_as_v1.draft_reviewed.json.
  M4  measure_recall: mean concept recall per strategy on S439's population (516 exp04 answers, the concepts of the
      v1-format key that judged_ledger's checked context holds, S373.AS_V1).

READS. Valerio's P2 labels, the "stated?" column of response/concept_match_labels/concept_labels_v1_ai_panel.xlsx
(the blind original concept_labels_v1.xlsx is still unlabelled; findings/recompute/L3_matcher_choice_2026-10-30.md
F1), the sheet S439 --analyze scored (gate G4a), and findings/recompute/S439_concept_label_key.json, through S439's
own readers (read only, for M1 and M2); the deposit's exp04 answers through S439.population(); the
reviewed v2.5 key; S439's analysis JSON and S382's csv, to reproduce known numbers before any new one is written.
WRITES findings/recompute/S505_question_aware/results.json and results.md, through phase3_common.write_outputs.
Calls no model.

GATES, all before anything is written:
  G1  the two base matchers' own cases (spec_failures() of each) and this module's hand cases (HAND_CASES)
  G2  S439's population: 516 answers, 3,426 pairs, loose finds 1,774 (D17's counts)
  G3  with an empty question, Q-need gives the base loose and the base stem verdict on every one of the 3,426 pairs
      and of the v2.5 key's concepts scored on its questions
  G4  the 249 sampled pairs: the base verdicts computed here are those S439's key file records
  G5  the base loose and stem rates of M1, computed here, equal S439_concept_label_analysis.json's (share and
      interval, every reading and weighting)
  G6  loose_o30 per answer reproduces concept_recall_loose_v22 of S382's csv on all 516 answers (S439.csv_gate)
"""
from __future__ import annotations

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import concept_match_loose as cml  # noqa: E402
import concept_match_stem as cms  # noqa: E402
from concept_match_loose import STOP_WORDS  # noqa: E402
from concept_match_stem import is_number, stem, strip_s, tokens  # noqa: E402

ME = "S505"
SCRIPT = "scripts/S505_question_aware_matcher.py"
MATCHERS = ("loose", "stem")
RULES = ("all", "need")
EMPTY = ("a", "b")          # (a) a concept with no remaining word is not found; (b) it is left out of the denominator


def need_of(n: int) -> int:
    """The base matchers' need: ceil(2n/3) in integers, (2n + 2) // 3 (concept_match_loose rule 5)."""
    return (2 * n + 2) // 3


class _Index:
    """The word sets of a text that the matchers' word test reads: exact (every token, for numbers), words (every
    token with one trailing s removed), stems (the Snowball stem of every token that is not a number). With
    content_only, the stop words are dropped first (the question side, rule 2)."""

    def __init__(self, text: str, content_only: bool = False):
        toks = [t for t in tokens(text) if not content_only or is_number(t) or t not in STOP_WORDS]
        self.exact = set(toks)
        self.words = {strip_s(t) for t in toks}
        self.stems = {stem(t) for t in toks if not is_number(t)}


def word_in(word: str, index: _Index, matcher: str) -> bool:
    """The base matchers' word test: a number matches only the identical token; any other word matches after one
    trailing s off each side, and under "stem" also by equal Snowball stems."""
    if is_number(word):
        return word in index.exact
    if strip_s(word) in index.words:
        return True
    return matcher == "stem" and stem(word) in index.stems


def content_words(concept: str) -> list:
    """The concept's distinct content words in sorted order, as concept_recall_loose computes them (rules 2 and 3)."""
    return sorted({t for t in tokens(concept) if is_number(t) or t not in STOP_WORDS})


def question_aware(answer: str, concept: str, question: str, matcher: str, rule: str,
                   _answer_index: _Index | None = None, _question_index: _Index | None = None) -> dict:
    """One concept under the question-aware rule (module docstring, THE RULE). matcher "loose" or "stem", rule "all"
    (Q-all) or "need" (Q-need). Returns {concept, status, found, content_words, removed, remaining, matched, need,
    exact}: status is "found", "not_found", "no_remaining" (every content word is in the question; found is False,
    which is reading (a); a caller using (b) drops the concept) or "no_content" (no content word: the exact rule
    alone decides, as in the base matchers); matched lists the remaining words found in the answer; need is the
    number of remaining words required (all of them under "all")."""
    if matcher not in MATCHERS or rule not in RULES:
        raise ValueError(f"{ME}: matcher is one of {MATCHERS} and rule one of {RULES}")
    ai = _answer_index or _Index(answer)
    qi = _question_index or _Index(question, content_only=True)
    content = content_words(concept)
    exact = concept.lower() in answer.lower()
    removed = [w for w in content if word_in(w, qi, matcher)]
    remaining = [w for w in content if w not in removed]
    matched = [w for w in remaining if word_in(w, ai, matcher)]
    need = len(remaining) if rule == "all" else need_of(len(remaining))
    if not content:
        status = "found" if exact else "not_found"
    elif not remaining:
        status = "no_remaining"
    else:
        status = "found" if (exact or len(matched) >= need) else "not_found"
    return {"concept": concept, "status": status, "found": status == "found", "content_words": content,
            "removed": removed, "remaining": remaining, "matched": matched, "need": need, "exact": exact}


def recall_q(answer: str, concepts: list, question: str, matcher: str, rule: str, empty: str = "a"):
    """Concept recall under the question-aware rule: found concepts / concepts counted, rounded to 4 decimals like
    the base matchers. empty "a": a concept with no remaining word counts and is not found; "b": it is not counted.
    None when nothing is counted (an empty list, or under "b" a list whose every concept has no remaining word)."""
    if empty not in EMPTY:
        raise ValueError(f"{ME}: empty is one of {EMPTY}")
    ai, qi = _Index(answer), _Index(question, content_only=True)
    per = [question_aware(answer, c, question, matcher, rule, ai, qi) for c in concepts]
    counted = [p for p in per if not (empty == "b" and p["status"] == "no_remaining")]
    return round(sum(p["found"] for p in counted) / len(counted), 4) if counted else None


def base_found(answer: str, concepts: list, matcher: str) -> list:
    """The base matcher's verdict per concept, from the base module itself (found_by is not None)."""
    fn = cml.concept_recall_loose if matcher == "loose" else cms.concept_recall_stem
    _, per = fn(answer, list(concepts), detail=True)
    return [p["found_by"] is not None for p in per]


# ---- hand cases: (name, question, concept, answer, matcher, rule, status, removed) ------------------------------
Q_TE3 = ("Based on the benchmarking results, what is the specific F1 score achieved for somatic single-base mutations "
         "(SSM) when using the intersection of GATK4 Mutect2 and Strelka2?")          # 01_sarek_TE3, v2.5 key
Q_MQC = "According to the paper, how many common bioinformatics tools does MultiQC support at the time of writing?"  # 05_multiqc_FR1
Q_050 = ("The rabies Tanzania paper concludes that vaccination campaigns in the Serengeti achieved uniform coverage "
         "across all areas, completely eliminating spatial heterogeneity. Is this accurate?")           # OOD_050
HAND_CASES = [
    # F1 = 0.80: base loose credits "F1 score" without the number (2 of 3); only 0.80 remains under O3
    ("F1 echo", Q_TE3, "F1 score = 0.80", "The F1 score for SSM is reported in the benchmark.", "loose", "need", "not_found", ["f1", "score"]),
    ("F1 echo, all", Q_TE3, "F1 score = 0.80", "The F1 score for SSM is reported in the benchmark.", "stem", "all", "not_found", ["f1", "score"]),
    ("F1 number", Q_TE3, "F1 score = 0.80", "The intersection reached 0.80.", "loose", "need", "found", ["f1", "score"]),
    ("F1 exact", Q_TE3, "F1 score = 0.80", "It gives an F1 score = 0.80 for SSMs.", "stem", "all", "found", ["f1", "score"]),
    # 22 tools: base credits the echo (3 of 4); only 22 remains
    ("22 tools echo", Q_MQC, "22 common bioinformatics tools", "MultiQC supports many common bioinformatics tools.", "loose", "need", "not_found",
     ["bioinformatics", "common", "tools"]),
    ("22 tools stated", Q_MQC, "22 common bioinformatics tools", "It supported 22 tools at the time.", "stem", "need", "found",
     ["bioinformatics", "common", "tools"]),
    ("22 tools exact", Q_MQC, "22 common bioinformatics tools", "MultiQC supports 22 common bioinformatics tools.", "loose", "all", "found",
     ["bioinformatics", "common", "tools"]),
    ("22 tools other number", Q_MQC, "22 common bioinformatics tools", "MultiQC supports 36 common bioinformatics tools.", "stem", "need", "not_found",
     ["bioinformatics", "common", "tools"]),
    # OOD_050: "eliminated" is removed by its stem (question: "eliminating"), not by the trailing-s rule
    ("OOD_050 loose keeps eliminated", Q_050, "reduced, not eliminated", "Heterogeneity was reduced, though it was not eliminated.", "loose", "need", "found", []),
    ("OOD_050 loose needs both", Q_050, "reduced, not eliminated", "Coverage heterogeneity was reduced over time.", "loose", "need", "not_found", []),
    ("OOD_050 stem removes eliminated", Q_050, "reduced, not eliminated", "Coverage heterogeneity was reduced over time.", "stem", "need", "found", ["eliminated"]),
    ("OOD_050 echo of the claim", Q_050, "reduced, not eliminated", "Vaccination eliminated the heterogeneity.", "stem", "need", "not_found", ["eliminated"]),
    ("OOD_050 heterogeneity", Q_050, "heterogeneity in coverage was reduced", "The coverage heterogeneity remained.", "loose", "need", "not_found",
     ["coverage", "heterogeneity"]),
    # a concept fully in the question: no remaining word, not found under (a) even when the answer repeats it
    ("fully in question", Q_MQC, "common bioinformatics tools", "MultiQC supports common bioinformatics tools.", "loose", "need", "no_remaining",
     ["bioinformatics", "common", "tools"]),
    ("fully in question, stem", Q_050, "eliminating spatial heterogeneity", "It eliminated spatial heterogeneity.", "stem", "all", "no_remaining",
     ["eliminating", "heterogeneity", "spatial"]),
    # stated concepts that must still be found
    ("stated, nothing removed", "What is the total storage capacity required?", "about 1.4 TB", "The outputs take 1.4 TB on disk.", "loose", "all", "found", []),
    ("stated, three of four remaining, Q-need", "Which tool is used?", "tumour normal paired reads", "tumour and normal reads", "loose", "need", "found", []),
    ("stated, three of four remaining, Q-all", "Which tool is used?", "tumour normal paired reads", "tumour and normal reads", "loose", "all", "not_found", []),
    # no content word: the exact rule only, as in the base matchers
    ("no content word", "What is it?", "of the", "one of the", "loose", "need", "found", []),
]


def spec_failures() -> list:
    """The HAND_CASES the rule gets wrong (status and removed words), plus: with an empty question Q-need is the
    base matcher on the base modules' own SPEC_CASES; recall_q under (b) drops a no-remaining concept."""
    bad = []
    for name, q, c, a, m, r, status, removed in HAND_CASES:
        got = question_aware(a, c, q, m, r)
        if got["status"] != status or got["removed"] != removed:
            bad.append(f"{name}: status {got['status']}, removed {got['removed']}; the rule says {status}, {removed}")
    for c, a, _ in cml.SPEC_CASES:
        for m in MATCHERS:
            if question_aware(a, c, "", m, "need")["found"] != base_found(a, [c], m)[0]:
                bad.append(f"empty question, {m}: {c!r} in {a!r} differs from the base matcher")
    for c, a, _ in cms.SPEC_CASES:
        if question_aware(a, c, "", "stem", "need")["found"] != base_found(a, [c], "stem")[0]:
            bad.append(f"empty question, stem: {c!r} in {a!r} differs from the base matcher")
    two = ["common bioinformatics tools", "22 common bioinformatics tools"]
    if recall_q("It supports 22 tools.", two, Q_MQC, "loose", "need", "a") != 0.5 \
            or recall_q("It supports 22 tools.", two, Q_MQC, "loose", "need", "b") != 1.0 \
            or recall_q("x", two[:1], Q_MQC, "loose", "need", "b") is not None:
        bad.append("recall_q does not score a no-remaining concept as (a) not found and (b) left out")
    return bad


# ================================================================================================================
# The analysis (main). Imported lazily so that the matcher and its hand cases need no ledger or deposit.
# ================================================================================================================

def _variants():
    """(name, matcher, rule, empty) of every Q variant."""
    return [(f"{m}_Q{r}_{e}", m, r, e) for m in MATCHERS for r in RULES for e in EMPTY]


def _passage(answer: str, words: list, matcher: str, side: int = 110, cap: int = 900) -> str:
    """The answer around the first occurrence of each word (the word test of the matcher, on the answer's tokens),
    windows of side characters merged where they overlap, joined by " [...] ", at most cap characters."""
    norm = unicodedata.normalize("NFKC", answer)
    t, spans = cms._spans(answer)
    src = answer if len(t) == len(answer) else (norm if len(t) == len(norm) else t)
    hits = []
    for w in words:
        for tok, s, e in spans:
            if (tok == w if is_number(w) else (strip_s(tok) == strip_s(w) or (matcher == "stem" and not is_number(tok)
                                                                               and stem(tok) == stem(w)))):
                hits.append((max(0, s - side), min(len(src), e + side)))
                break
    if not hits:
        return src[:2 * side].replace("\n", " ")
    hits.sort()
    merged = [list(hits[0])]
    for s, e in hits[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out = " [...] ".join(src[s:e].replace("\n", " ").strip() for s, e in merged)
    return out if len(out) <= cap else out[:cap] + " [...]"


def measure_p2(s439, p3, labels, key, pop) -> dict:
    """M1. For each base matcher and each Q variant, on the 249 pairs of S439's sample, the two rates of S439
    --analyze: "found among stated" = (pairs the matcher finds and Valerio labelled stated) / (pairs labelled stated),
    the sensitivity; "not stated among found" = (pairs the matcher finds and he labelled not stated) / (pairs the
    matcher finds), the false finds. Two readings of "stated": yes or partly (partly_as_stated), yes only
    (partly_as_not_stated). Unweighted, and weighted by 1 / inclusion probability as S439 weights. The 95% interval is
    the 2.5th to 97.5th percentile over S439's 10,000 bootstrap replicates, rebuilt here with S439's code and seed
    (S439.rate()). The question of a pair is the question of its key entry (the record S439's population holds).
    Under (b) a pair whose concept has no remaining word (for that matcher's removal) is left out of both rates; the
    base matcher is then also reported on the same reduced set (name ending "_base_b") so the two compare on equal
    pairs. Returns the table rows and the per-pair verdicts M2 reads."""
    import numpy as np
    by_key = {a["key"]: a for a in pop["answers"]}
    answers = key["answers"]
    aid = [a["answer_id"] for a in answers]
    pi = np.array([float(a["inclusion_probability"]) for a in answers])
    cell = [(a["strategy"], a["stratum"]) for a in answers]
    n = len(answers)
    rs = np.random.RandomState(s439.SEED + 1)                # S439 analyze(), line for line
    reps = np.zeros((s439.N_BOOT, n))
    for c in sorted(set(cell)):
        idx = [i for i in range(n) if cell[i] == c]
        if len(idx) == 1:
            reps[:, idx[0]] = 1.0
            continue
        picks = rs.randint(0, len(idx), size=(s439.N_BOOT, len(idx) - 1))
        for k, i in enumerate(idx):
            reps[:, i] = (picks == k).sum(axis=1) * len(idx) / (len(idx) - 1)
    weights = {"unweighted": np.ones(n), "weighted": 1 / pi}

    pairs, stale = [], []
    for rid, rec in key["rows"].items():
        a = by_key[rec["ledger_key"]]
        ci = rec["concept_index"]
        concept = a["concepts"][ci]
        v = a["verdicts"][ci]
        if {m: v[m] for m in s439.MATCHERS} != rec["verdicts"]:
            stale.append(rid)
        ai, qi = _Index(a["text"]), _Index(a["question"], content_only=True)
        q = {f"{m}_Q{r}": question_aware(a["text"], concept, a["question"], m, r, ai, qi) for m in MATCHERS for r in RULES}
        pairs.append({"row_id": rid, "i": aid.index(rec["answer_id"]), "label": labels[rid]["label"],
                      "comment": labels[rid]["comment"], "question_id": rec["question_id"], "strategy": rec["strategy"],
                      "question": a["question"], "concept": concept, "text": a["text"],
                      "base": {"loose": v["loose"], "stem": v["stem"]}, "q": q})

    def per_answer(test) -> np.ndarray:
        out = np.zeros(n)
        for p in pairs:
            out[p["i"]] += bool(test(p))
        return out

    def verdict_of(name):
        if name in MATCHERS:
            return lambda p: p["base"][name]
        if name.endswith("_base_b"):
            m = name[:-len("_base_b")]
            return lambda p: p["base"][m]
        m, r, _e = name.rsplit("_", 2)[0], name.split("_Q")[1].split("_")[0], name[-1]
        return lambda p: p["q"][f"{m}_Q{r}"]["found"]

    def inside_of(name):
        if name in MATCHERS or name.endswith("_a"):
            return lambda p: True
        m = name.split("_")[0]
        return lambda p: p["q"][f"{m}_Qneed"]["status"] != "no_remaining"

    names = []
    for m in MATCHERS:
        names += [m, f"{m}_Qall_a", f"{m}_Qneed_a", f"{m}_base_b", f"{m}_Qall_b", f"{m}_Qneed_b"]
    tables = []
    for reading, as_stated in s439.READINGS.items():
        for name in names:
            found_t, inside = verdict_of(name), inside_of(name)
            den_stated = per_answer(lambda p: inside(p) and p["label"] in as_stated)
            found = per_answer(lambda p: inside(p) and found_t(p))
            both = per_answer(lambda p: inside(p) and found_t(p) and p["label"] in as_stated)
            for weighting, w in weights.items():
                tables.append({"reading": reading, "matcher": name, "weighting": weighting,
                               "pairs": int(per_answer(inside).sum()),
                               "found_among_stated": s439.rate(both, den_stated, w, reps),
                               "not_stated_among_found": s439.rate(found - both, found, w, reps)})
    return {"tables": tables, "pairs": pairs, "stale": stale}


def measure_penalty(pairs: list) -> dict:
    """M2. The pairs on which a Q variant and its base matcher disagree, on the 249 labelled pairs; "stated" is a
    label of yes or partly, "not stated" a label of no.
      lost_stated     every stated pair the base matcher finds and the Q variant does not: the pairs O3 would take
                      credit from. One row per pair, with the variants that lose it, whether the concept has no
                      remaining word (lost under (a), left out under (b)), whether anything was removed (a Q-all loss
                      with nothing removed comes from the stricter all-words rule, not from the question), the
                      question, the concept, the removed words, the remaining words and those the answer holds, his
                      comment, and the answer passage around the concept's content words.
      dropped_not_stated  every not-stated pair the base matcher finds and the Q variant does not: the false finds
                      O3 removes, with the same fields.
      added           every pair the Q variant finds and the base matcher does not, with its label.
      summary         per Q variant, the counts of the three lists under (a) and under (b), each loss split by cause:
                      no_remaining (all content words in the question), removal (some removed, too few left in the
                      answer) and rule_only (nothing removed: the all-words rule alone)."""
    def row(p, lost):
        m0 = "stem" if any(x.startswith("stem") for x in lost) else "loose"
        return {"row_id": p["row_id"], "label": p["label"], "question_id": p["question_id"], "strategy": p["strategy"],
                "question": p["question"], "concept": p["concept"], "variants": lost,
                "no_remaining": {m: p["q"][f"{m}_Qneed"]["status"] == "no_remaining" for m in MATCHERS},
                "removed": {m: p["q"][f"{m}_Qneed"]["removed"] for m in MATCHERS},
                "remaining": {m: p["q"][f"{m}_Qneed"]["remaining"] for m in MATCHERS},
                "remaining_in_answer": {m: p["q"][f"{m}_Qneed"]["matched"] for m in MATCHERS},
                "comment": p["comment"], "passage": _passage(p["text"], p["q"][f"{m0}_Qneed"]["content_words"], m0)}

    names = [f"{m}_Q{r}" for m in MATCHERS for r in RULES]
    lists = {"lost_stated": [], "dropped_not_stated": [], "added": []}
    summary = {n: Counter() for n in names}
    for p in pairs:
        stated = p["label"] in ("yes", "partly")
        lost = [n for n in names if p["base"][n.split("_")[0]] and not p["q"][n]["found"]]
        added = [n for n in names if not p["base"][n.split("_")[0]] and p["q"][n]["found"]]
        for n in lost:
            d = p["q"][n]
            cause = "no_remaining" if d["status"] == "no_remaining" else ("removal" if d["removed"] else "rule_only")
            side = "lost_stated" if stated else "dropped_not_stated"
            summary[n][f"{side}_a"] += 1
            summary[n][f"{side}_b"] += cause != "no_remaining"
            summary[n][f"{side}_{cause}"] += 1
        for n in added:
            summary[n]["added_stated" if stated else "added_not_stated"] += 1
        if lost:
            lists["lost_stated" if stated else "dropped_not_stated"].append(row(p, lost))
        if added:
            lists["added"].append(row(p, added))
    return {**lists, "summary": {n: dict(c) for n, c in summary.items()}}


def measure_free_credit(key25: dict) -> dict:
    """M3. On every answerable question of the reviewed v2.5 key, the question's own text is scored as the answer
    against each of its concepts. Reports, per matcher (exact, loose, stem and each Q variant), how many concepts are
    credited (found) out of all the concepts, and lists every concept a Q variant still credits. Also lists every
    concept with no remaining word (all its content words in the question) under each matcher's removal, and the
    concepts with no content word. Under (b) the no-remaining concepts leave the denominator; the credited count is
    the same under (a) and (b), since such a concept is never found."""
    qs = [q for q in key25["questions"] if q.get("answerable")]
    rows = []
    for q in qs:
        qi_a = _Index(q["question"])
        qi = _Index(q["question"], content_only=True)
        base = {m: base_found(q["question"], q["expected_concepts"], m) for m in MATCHERS}
        for k, c in enumerate(q["expected_concepts"]):
            rows.append({"question_id": q["id"], "question": q["question"], "concept": c,
                         "exact": c.lower() in q["question"].lower(), "loose": base["loose"][k], "stem": base["stem"][k],
                         "q": {f"{m}_Q{r}": question_aware(q["question"], c, q["question"], m, r, qi_a, qi)
                               for m in MATCHERS for r in RULES}})
    counts = {"concepts": len(rows), "questions": len(qs),
              "exact": sum(r["exact"] for r in rows), "loose": sum(r["loose"] for r in rows),
              "stem": sum(r["stem"] for r in rows)}
    for name in (f"{m}_Q{r}" for m in MATCHERS for r in RULES):
        counts[name] = sum(r["q"][name]["found"] for r in rows)
    no_rem = {m: [{"question_id": r["question_id"], "concept": r["concept"], "content_words": r["q"][f"{m}_Qneed"]["content_words"],
                   "question": r["question"]} for r in rows if r["q"][f"{m}_Qneed"]["status"] == "no_remaining"] for m in MATCHERS}
    no_content = [{"question_id": r["question_id"], "concept": r["concept"]} for r in rows
                  if r["q"]["loose_Qneed"]["status"] == "no_content"]
    still = [{"question_id": r["question_id"], "concept": r["concept"], "variants": [n for n in r["q"] if r["q"][n]["found"]],
              "remaining": r["q"]["stem_Qneed"]["remaining"], "exact": r["exact"]}
             for r in rows if any(x["found"] for x in r["q"].values())]
    base_lists = {m: [{"question_id": r["question_id"], "concept": r["concept"]} for r in rows if r[m]] for m in MATCHERS}
    removed_any = {m: sum(bool(r["q"][f"{m}_Qneed"]["removed"]) for r in rows) for m in MATCHERS}
    return {"counts": counts, "no_remaining": no_rem, "no_content": no_content, "still_credited": still,
            "base_credited": base_lists, "concepts_with_a_removed_word": removed_any, "_rows": rows}


def measure_recall(pop: dict, configs: list) -> dict:
    """M4. On S439's population (516 answerable exp04 answers, 86 questions x 6 strategies; the concepts of the
    v1-format key judged_ledger's checked context holds), concept recall per answer = found concepts / concepts
    counted, and its mean over the answers of each strategy (and over all 516), for: loose and stem (base, each
    concept's verdict from the base module), loose_o30 (S382's concept_recall_loose_v22, reproduced by gate G6), and
    each Q variant. Under (b) an answer whose every concept has no remaining word has no recall and is left out of the
    mean; the number of answers averaged is given. Also counts, over the population's distinct (question, concept)
    entries, the concepts with no remaining word and the concepts with at least one removed word."""
    per = []
    for a in pop["answers"]:
        n = len(a["concepts"])
        row = {"strategy": a["strategy"], "question_id": a["question_id"],
               "loose": sum(v["loose"] for v in a["verdicts"]) / n, "stem": sum(v["stem"] for v in a["verdicts"]) / n,
               "loose_o30": sum(v["loose_o30"] for v in a["verdicts"]) / n}
        for name, m, r, e in _variants():
            row[name] = recall_q(a["text"], a["concepts"], a["question"], m, r, e)
        per.append(row)
    cols = ["loose_o30", "loose", "stem"] + [v[0] for v in _variants()]
    table = []
    for s in list(configs) + ["all"]:
        rows = [r for r in per if s == "all" or r["strategy"] == s]
        entry = {"strategy": s, "answers": len(rows)}
        for c in cols:
            vals = [r[c] for r in rows if r[c] is not None]
            entry[c] = sum(vals) / len(vals) if vals else None
            entry[f"{c}_n"] = len(vals)
        table.append(entry)
    seen = {}
    for a in pop["answers"]:
        for c in a["concepts"]:
            seen[(a["question_id"], c)] = a["question"]
    entries = {}
    for m in MATCHERS:
        st = Counter()
        lst = []
        for (qid, c), qtext in sorted(seen.items()):
            d = question_aware("", c, qtext, m, "need")
            st["removed_any"] += bool(d["removed"])
            if d["status"] == "no_remaining":
                lst.append({"question_id": qid, "concept": c, "content_words": d["content_words"]})
        entries[m] = {"distinct_concepts": len(seen), "with_a_removed_word": st["removed_any"],
                      "no_remaining": len(lst), "no_remaining_list": lst}
    return {"columns": cols, "table": table, "population_concepts": entries}


# ---- the report ---------------------------------------------------------------------------------------------

def _pc(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def _cell(x: dict) -> str:
    lo, hi = x["interval_95"]
    iv = "no interval" if lo is None else f"{_pc(lo)} to {_pc(hi)}"
    return f"{_pc(x['share'])} ({x['numerator']}/{x['denominator']}; {iv})"


def report(doc: dict) -> str:
    prov = doc["provenance"]
    L = ["# S505: question-aware concept matchers (Q18, O3)", "",
         f"Written by `{prov['command']}` (script sha256 `{prov['script_sha256'][:12]}`, {prov['written_utc']}). "
         f"Inputs and their sha256 are in `results.json` under provenance. The rule is the docstring of "
         f"`question_aware` in `{SCRIPT}`; nothing in `concept_match_loose.py` or `concept_match_stem.py` changed.", "",
         "Variant names: `<matcher>_Q<rule>_<empty>`. rule `all`: every remaining word must be in the answer; `need`: "
         "ceil(2/3) of the remaining words, the base matchers' own proportion. empty `a`: a concept whose content words "
         "are all in the question is not found; `b`: it is left out of the denominator. `<matcher>_base_b` is the base "
         "matcher on the pairs left under (b), for an equal comparison.", ""]
    m3 = doc["M3_free_credit"]
    c = m3["counts"]
    L += ["## M3. Free credit: the question scored as its own answer", "",
          f"{c['questions']} answerable questions, {c['concepts']} concepts of the reviewed v2.5 key.", "",
          "| matcher | concepts credited by the question alone |", "|---|---:|"]
    for k in ("exact", "loose", "stem", "loose_Qall", "loose_Qneed", "stem_Qall", "stem_Qneed"):
        L.append(f"| {k} | {c[k]} of {c['concepts']} ({_pc(c[k] / c['concepts'])}) |")
    L += ["", f"Still credited under a Q variant ({len(m3['still_credited'])}):", ""]
    L += [f"- {x['question_id']}: \"{x['concept']}\" ({', '.join(x['variants'])}; remaining {x['remaining']}, exact {x['exact']})"
          for x in m3["still_credited"]] or ["- none"]
    for m in MATCHERS:
        lst = m3["no_remaining"][m]
        L += ["", f"Concepts with no remaining word under the {m} removal ({len(lst)} of {c['concepts']}):", ""]
        L += [f"- {x['question_id']}: \"{x['concept']}\" (content words {x['content_words']})" for x in lst] or ["- none"]
    L += ["", f"Concepts with no content word at all: {len(m3['no_content'])}.",
          f"Concepts with at least one word removed: loose {m3['concepts_with_a_removed_word']['loose']}, "
          f"stem {m3['concepts_with_a_removed_word']['stem']}.", ""]

    m1 = doc["M1_p2"]
    L += ["## M1. Agreement with the P2 labels (249 pairs, 36 answers)", "",
          "found among stated = sensitivity; not stated among found = false finds. In brackets: pairs, then the 95% "
          "bootstrap interval (S439's replicates). Weighted = 1 / inclusion probability, as S439.", ""]
    for reading, rtext in (("partly_as_stated", "stated = yes or partly"), ("partly_as_not_stated", "stated = yes only")):
        L += [f"### {rtext}", "", "| matcher | pairs | found among stated, unweighted | weighted | not stated among found, "
              "unweighted | weighted |", "|---|---:|---|---|---|---|"]
        for name in dict.fromkeys(t["matcher"] for t in m1["tables"]):
            u, w = (next(t for t in m1["tables"] if t["reading"] == reading and t["matcher"] == name and t["weighting"] == k)
                    for k in ("unweighted", "weighted"))
            L.append(f"| {name} | {u['pairs']} | {_cell(u['found_among_stated'])} | {_cell(w['found_among_stated'])} | "
                     f"{_cell(u['not_stated_among_found'])} | {_cell(w['not_stated_among_found'])} |")
        L.append("")

    m2 = doc["M2_penalty"]
    L += ["## M2. Where the Q variants and the base matchers disagree on the labelled pairs", "",
          "stated = yes or partly. lost: stated pairs the base finds and the variant does not (the penalty). dropped: "
          "pairs labelled no that the base finds and the variant does not (false finds removed). Causes of a loss: "
          "no remaining word (lost under (a), left out under (b)); removal (some words removed, too few remaining "
          "words in the answer); rule only (nothing removed, the all-words rule alone).", "",
          "| variant | stated lost (a) | stated lost (b) | of which: no remaining / removal / rule only | false finds dropped (a) "
          "| (b) | added: stated / not stated |", "|---|---:|---:|---|---:|---:|---|"]
    for n, c in m2["summary"].items():
        L.append(f"| {n} | {c.get('lost_stated_a', 0)} | {c.get('lost_stated_b', 0)} | {c.get('lost_stated_no_remaining', 0)} / "
                 f"{c.get('lost_stated_removal', 0)} / {c.get('lost_stated_rule_only', 0)} | {c.get('dropped_not_stated_a', 0)} | "
                 f"{c.get('dropped_not_stated_b', 0)} | {c.get('added_stated', 0)} / {c.get('added_not_stated', 0)} |")
    L.append("")
    for title, key in (("Stated pairs lost (the penalty list)", "lost_stated"),
                       ("False finds dropped (pairs labelled no)", "dropped_not_stated"),
                       ("Pairs a Q variant finds and the base does not", "added")):
        L += [f"### {title} ({len(m2[key])})", ""]
        for x in m2[key]:
            nr = [m for m in MATCHERS if x["no_remaining"][m]]
            L += [f"**{x['row_id']}** ({x['label']}), {x['question_id']}, {x['strategy']}", "",
                  f"- question: {x['question']}", f"- concept: \"{x['concept']}\"",
                  f"- variants: {', '.join(x['variants'])}" + (f"; no remaining word under {', '.join(nr)}" if nr else ""),
                  f"- removed: loose {x['removed']['loose']}, stem {x['removed']['stem']}",
                  f"- remaining: loose {x['remaining']['loose']} (in the answer {x['remaining_in_answer']['loose']}), "
                  f"stem {x['remaining']['stem']} (in the answer {x['remaining_in_answer']['stem']})"]
            if x["comment"]:
                L.append(f"- Valerio's comment: {x['comment']}")
            L += [f"- answer passage: > {x['passage']}", ""]

    m4 = doc["M4_recall"]
    L += ["## M4. Mean concept recall per strategy (516 exp04 answers)", "",
          "Key: the v1-format key of S439's population (" + doc["M4_recall"]["key_file"] + "). Under (b) the mean is over "
          "the answers with a defined recall (n in brackets when below the strategy's count).", ""]
    cols = m4["columns"]
    L += ["| strategy | n | " + " | ".join(cols) + " |", "|---|---:|" + "---:|" * len(cols)]
    for e in m4["table"]:
        cells = []
        for col in cols:
            v = e[col]
            s = "n/a" if v is None else f"{v:.4f}"
            if e[f"{col}_n"] != e["answers"]:
                s += f" ({e[f'{col}_n']})"
            cells.append(s)
        L.append(f"| {e['strategy']} | {e['answers']} | " + " | ".join(cells) + " |")
    pcs = m4["population_concepts"]
    L += ["", "Concepts of the population key (distinct question and concept): "
          + "; ".join(f"{m}: {pcs[m]['with_a_removed_word']} of {pcs[m]['distinct_concepts']} lose a word, "
                      f"{pcs[m]['no_remaining']} lose all" for m in MATCHERS) + ".", ""]
    for m in MATCHERS:
        L += [f"No remaining word under the {m} removal, population key:", ""]
        L += [f"- {x['question_id']}: \"{x['concept']}\" ({x['content_words']})" for x in pcs[m]["no_remaining_list"]] or ["- none"]
        L.append("")
    L += ["## Gates", "", "| gate | result | what was tested |", "|---|---|---|"]
    L += [f"| {g['name']} | {'ok' if g['ok'] else 'FAIL'} | {g['message']} |" for g in prov["gates"]] + [""]
    return "\n".join(L)


def main() -> int:
    import judged_ledger as jl
    import phase3_common as p3
    import S439_concept_label_sheet as s439

    out_dir = p3.RECOMPUTE / "S505_question_aware"
    key25_path = p3.RECOMPUTE / "S504_key_v2_5" / "ground_truth_v2_5_as_v1.draft_reviewed.json"
    g = p3.Gates(ME)
    fails = cml.spec_failures() + cms.spec_failures() + spec_failures()
    g.gate("G1", not fails, f"base matchers' own cases and {len(HAND_CASES)} hand cases hold"
           + (f"; first failure: {fails[0]}" if fails else ""))

    scorer_cr, configs, lifted = s439.scorer()
    pop = s439.population(scorer_cr, configs)
    n_pairs = sum(len(a["concepts"]) for a in pop["answers"])
    n_loose = sum(v["loose"] for a in pop["answers"] for v in a["verdicts"])
    g.gate("G2", len(pop["answers"]) == s439.KNOWN["answers"] and n_pairs == s439.KNOWN["pairs"] and n_loose == s439.KNOWN["loose_found"],
           f"S439 population: {len(pop['answers'])} answers, {n_pairs} pairs, loose finds {n_loose} (known "
           f"{s439.KNOWN['answers']}, {s439.KNOWN['pairs']}, {s439.KNOWN['loose_found']})")

    key25 = p3.read_json(ME, key25_path)
    off = 0
    total = 0
    for a in pop["answers"]:
        ai, qi = _Index(a["text"]), _Index("", content_only=True)
        for c, v in zip(a["concepts"], a["verdicts"]):
            total += 1
            off += any(question_aware(a["text"], c, "", m, "need", ai, qi)["found"] != v[m] for m in MATCHERS)
    for q in key25["questions"]:
        if q.get("answerable"):
            base = {m: base_found(q["question"], q["expected_concepts"], m) for m in MATCHERS}
            for k, c in enumerate(q["expected_concepts"]):
                total += 1
                off += any(question_aware(q["question"], c, "", m, "need")["found"] != base[m][k] for m in MATCHERS)
    g.gate("G3", off == 0, f"with an empty question Q-need equals the base loose and stem verdicts on {total - off} of {total} "
                           "pairs (3,426 exp04 pairs and the v2.5 key's concepts scored on their questions)")

    key = p3.read_json(ME, s439.OUT_KEY)
    sheet = p3.ROOT / "response/concept_match_labels/concept_labels_v1_ai_panel.xlsx"   # his labels: the "stated?" column
    known_sheet = p3.read_json(ME, s439.OUT_AN_JSON)["provenance"]["sheet"]
    g.gate("G4a", p3.shown(sheet) == known_sheet["file"] and p3.sha256_file(ME, sheet) == known_sheet["sha256"],
           f"the labelled sheet is the one S439 --analyze scored ({known_sheet['file']}, sha256 {known_sheet['sha256'][:12]})")
    labels = s439.read_labels(sheet, key)
    m1 = measure_p2(s439, p3, labels, key, pop)
    g.gate("G4", not m1["stale"], f"the base verdicts of the {len(m1['pairs'])} sampled pairs are S439's key file's"
           + (f"; differ on {len(m1['stale'])}" if m1["stale"] else ""))

    known = p3.read_json(ME, s439.OUT_AN_JSON)
    ref = {(t["reading"], t["matcher"], t["weighting"]): t for t in known["tables"] if t["subset"] == "all_pairs"}
    bad = 0
    checked = 0
    for t in m1["tables"]:
        if t["matcher"] in MATCHERS:
            r = ref[(t["reading"], t["matcher"], t["weighting"])]
            for k in ("found_among_stated", "not_stated_among_found"):
                checked += 1
                a, b = t[k], r[k]
                same = (a["numerator"], a["denominator"]) == (b["numerator"], b["denominator"]) \
                    and p3.close(a["share"], b["share"], 1e-12, "a share of S439_concept_label_analysis.json", ME) \
                    and all(p3.close(x, y, 1e-12, "an interval of S439_concept_label_analysis.json", ME) for x, y in zip(a["interval_95"], b["interval_95"]))
                bad += not same
    g.gate("G5", bad == 0 and checked == 16, f"the base loose and stem rates reproduce S439_concept_label_analysis.json on "
                                             f"{checked - bad} of {checked} cells (share, counts, interval)")

    ok_exact, ok_loose, same = s439.csv_gate(pop)
    g.gate("G6", ok_loose == len(pop["answers"]) and same,
           f"loose_o30 per answer equals S382 csv concept_recall_loose_v22 on {ok_loose} of {len(pop['answers'])} answers; "
           f"csv records the present key and answers file: {same}")

    m2 = measure_penalty(m1["pairs"])
    m3 = measure_free_credit(key25)
    m4 = measure_recall(pop, configs)
    m4["key_file"] = p3.shown(jl.S373.AS_V1)

    extra = {"gates": g.finish(), "libraries": {"nltk": __import__("nltk").__version__}}
    prov = p3.provenance(__file__, f"uv run python {SCRIPT}",
                         [("exp04", jl.MAIN_JUDGE), pop["deposit"], *lifted, Path(jl.MANIFEST), sheet, s439.S382_CSV], extra)
    m1_out = {"tables": m1["tables"], "pairs": len(m1["pairs"]),
              "labels": dict(Counter(p["label"] for p in m1["pairs"]))}
    m3_out = {k: v for k, v in m3.items() if not k.startswith("_")}
    doc = {"provenance": prov, "rule": question_aware.__doc__, "measures": {
               "M1": measure_p2.__doc__, "M2": measure_penalty.__doc__, "M3": measure_free_credit.__doc__,
               "M4": measure_recall.__doc__},
           "M1_p2": m1_out, "M2_penalty": m2, "M3_free_credit": m3_out, "M4_recall": m4}
    out_dir.mkdir(exist_ok=True)
    p3.write_outputs(ME, {out_dir / "results.json": json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                          out_dir / "results.md": report(doc)})
    print(f"{ME}: wrote {p3.shown(out_dir / 'results.json')} and {p3.shown(out_dir / 'results.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
