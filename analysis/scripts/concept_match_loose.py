#!/usr/bin/env python3
"""concept_match_loose - the loose concept matcher, reported beside the exact one (Q26, 10 October 2026).

Why. Concept recall in the harness is compute_concept_recall
(recovered_harness/tests/experiments_v4/exp_v4_9_depth_sweep.py:200-210): the answer is lower-cased and a
key concept counts as found when its exact lower-cased text is a substring of it. The concepts of the v2.2
key and of the current v2.4 (S381's v1-format files; the callers read S373.AS_V1,
data/ground_truth_v2/ground_truth_v2_4_as_v1.json since 11 October, Q50) are longer phrases than v1's (median 4
words against 2 in both: "about 1.4 TB" where v1 had "1.4 TB"), so the exact rule misses concepts an answer states with
other words around them. Valerio's decision (Q26, 10 October): keep the exact matcher unchanged and report
this loose one beside it, so that no concept is lost because of extra words around it.

The rule was fixed on 10 October 2026, before any v2.2 loose number was looked at, and is not tuned after. Later
that day, after v2.2 loose values had been computed, the code's reading of rule 4 for numbers was tightened (a number
token is never shortened, in the concept or in the answer); the rule text did not change and no value changed
(3,587 of 3,587 answer-key values equal before and after), and two cases pinning the 3-letter boundary were added.
It is the single function concept_recall_loose below; its docstring is the rule as decided.

    uv run python scripts/concept_match_loose.py      runs spec_failures(): the cases in SPEC_CASES, STOP_WORDS
                                                      against rule 3's list, each stop word dropped

Callers: scripts/S383_depth_concept_recall_v22.py and scripts/S382_exp04_objective_v22.py, which run
spec_failures() as a gate before writing any loose value.
"""
from __future__ import annotations

import unicodedata

STOP_WORDS = frozenset(
    "a an the of in on for to and or with by from at as is are was were be been this that these those it "
    "its their than then about approximately around roughly nearly almost some any each per via into over "
    "under between within without not no".split())


def concept_recall_loose(answer: str, expected_concepts: list, detail: bool = False):
    """Loose concept recall: the fraction of expected concepts found in the answer under this rule.

    1. A concept the exact matcher finds is found (so loose recall is never below exact).
    2. Otherwise normalise concept and answer the same way: Unicode NFKC, lower case; every character
       that is not a letter, a digit, or a '.' or ',' between two digits becomes a space (so "1.4" and
       "10,000" stay one token, "tumour-normal" becomes two); split on whitespace.
    3. Content words of the concept: its tokens minus this fixed stop-word list: a, an, the, of, in, on,
       for, to, and, or, with, by, from, at, as, is, are, was, were, be, been, this, that, these, those,
       it, its, their, than, then, about, approximately, around, roughly, nearly, almost, some, any, each,
       per, via, into, over, under, between, within, without, not, no. A token of the concept that is a
       number (digits with optional '.' or ',') is always a content word.
    4. A word matches when the same token occurs in the answer, after removing one trailing "s" from
       tokens longer than 3 letters on both sides (files/file); numbers must match exactly.
    5. The concept is found when its distinct content words that match are at least ceil(2/3 of its
       distinct content words); a concept with no content words is found only by the exact rule.
    Loose concept recall = found concepts / all concepts, rounded to 4 decimals like the exact one.

    How the code reads the rule where the text leaves a choice:
      - "the exact matcher" is the harness's: concept.lower() in answer.lower(), unchanged.
      - letter = str.isalpha(), digit = str.isdigit(), tested after NFKC and lower case.
      - "distinct" is over the content tokens as they come out of step 2, before the trailing "s" of
        step 4 is removed; "longer than 3 letters" is len(token) > 3, counted in characters.
      - "numbers must match exactly": a number of the concept (rule 3's definition, digits with an
        optional '.' or ',') is looked up among the answer's tokens as step 2 gives them, with no
        trailing "s" removed on either side, so it matches only an identical token: "1990" does not
        match "1990s", "1.4" does not match "1,4" or "14". A token with a letter in it, such as "1990s",
        is not a number and is matched like any other word.
      - ceil(2n/3) is computed in integers, (2n + 2) // 3: 1 of 1, 2 of 2, 2 of 3, 3 of 4, 4 of 5, 4 of 6.
      - every entry of expected_concepts counts once, duplicates included, as in the exact function.
      - an empty concept list has no recall: the function returns None (the harness's exact function
        returns 0.0 and the deposited exp04 scorer 1.0; the rule names neither, so the caller decides).

    With detail=True it returns (recall, per_concept), where per_concept lists for each concept: the
    concept, found_by ("exact", "loose" or None), its distinct content words, those that matched, and
    how many were needed.
    """
    def tokens(text: str) -> list:
        t = unicodedata.normalize("NFKC", text).lower()
        kept = [ch if (ch.isalpha() or ch.isdigit()
                       or (ch in ".," and 0 < i < len(t) - 1 and t[i - 1].isdigit() and t[i + 1].isdigit()))
                else " " for i, ch in enumerate(t)]
        return "".join(kept).split()

    def is_number(tok: str) -> bool:
        return tok.replace(".", "").replace(",", "").isdigit()

    def strip_s(tok: str) -> str:
        return tok[:-1] if len(tok) > 3 and tok.endswith("s") else tok

    if not expected_concepts:
        return (None, []) if detail else None
    answer_lower = answer.lower()
    answer_tokens = tokens(answer)
    answer_exact = set(answer_tokens)                                                # numbers match here
    answer_words = {strip_s(t) for t in answer_tokens}                               # every other word here
    found, per_concept = 0, []
    for concept in expected_concepts:
        if concept.lower() in answer_lower:                                          # rule 1
            found += 1
            per_concept.append({"concept": concept, "found_by": "exact", "content_words": [],
                                "matched": [], "need": 0})
            continue
        content = sorted({t for t in tokens(concept) if is_number(t) or t not in STOP_WORDS})   # rules 2, 3
        matched = [w for w in content                                                # rule 4
                   if (w in answer_exact if is_number(w) else strip_s(w) in answer_words)]
        need = (2 * len(content) + 2) // 3                                           # rule 5
        hit = bool(content) and len(matched) >= need
        found += hit
        per_concept.append({"concept": concept, "found_by": "loose" if hit else None,
                            "content_words": content, "matched": matched, "need": need})
    recall = round(found / len(expected_concepts), 4)
    return (recall, per_concept) if detail else recall


# (concept, answer, found) taken from the rule's own text; each must hold before a caller writes a value
SPEC_CASES = [
    ("about 1.4 TB", "The index takes about 1.4 TB.", True),             # rule 1, exact
    ("about 1.4 TB", "The index takes 1.4 TB on disk.", True),           # 1.4 one token; "about" a stop word
    ("about 1.4 TB", "The index takes 14 TB on disk.", False),           # numbers match exactly
    ("1.4 TB", "The index takes 1,4 TB on disk.", False),                # "1,4" is not "1.4"
    ("10,000 reads", "It keeps 10,000 paired reads.", True),             # 10,000 one token
    ("10,000 reads", "It keeps 10 000 reads.", False),                   # 10 and 000 are other tokens
    ("tumour-normal pairs", "tumour and normal sample pairs", True),     # two tokens, 3 of 3
    ("tumour-normal pairs", "matched tumour samples", False),            # 1 of 3, 2 needed
    ("large files", "a large file", True),                               # files/file
    ("gas leaks", "a gas leak", True),                                   # "gas" (3) kept, "leaks" -> leak
    ("BAM files", "a BAM index", False),                                 # 1 of 2, 2 needed
    ("read group tag", "the read group is set", True),                   # 2 of 3
    ("read group tag value", "the read group is set", False),            # 2 of 4, 3 needed
    ("of the", "the of", False),                                         # no content words, exact only
    ("of the", "one of the", True),                                      # found by the exact rule
    ("Ｒeads", "two reads", True),                                        # NFKC folds the full-width R
    ("1.4 TB", "1 and 4 TB", False),                                     # '.' between digits kept: 1.4 one token
    ("10,000 reads", "10000 reads", False),                              # ',' between digits kept; numbers exact
    ("1990 census", "the 1990s census", False),                          # numbers exact: 1990 is not 1990s
    ("gas", "a ga", False),                                              # "gas" is 3 long, not shortened
    ("class", "a cla", False),                                           # one trailing s only: class -> clas
    ("about 30 samples", "about samples", False),                        # "about" a stop word: 1 of 2 content words
    ("reads read data", "we read it", True),                             # distinct before the s goes: 2 of 3
    ("sets", "one set", True),                                           # 4 letters, longer than 3: sets -> set
    ("gene sets", "the gene set", True),                                 # the same boundary inside a phrase
]


def _rule3_stop_words() -> list:
    """The stop-word list as rule 3 of concept_recall_loose's docstring writes it."""
    import re
    m = re.search(r"stop-word list:(.*?)\. A token", concept_recall_loose.__doc__, re.S)
    return [w.strip() for w in m.group(1).split(",")] if m else []


def spec_failures() -> list:
    """The SPEC_CASES the function gets wrong, plus checks that STOP_WORDS is rule 3's list and that
    each of its words is dropped, that recall is never below the exact rule, and that an empty list
    returns None."""
    bad = []
    for concept, answer, want in SPEC_CASES:
        got = concept_recall_loose(answer, [concept]) == 1.0
        if got != want:
            bad.append(f"{concept!r} in {answer!r}: found {got}, the rule says {want}")
    listed = _rule3_stop_words()
    if len(listed) != 49 or set(listed) != STOP_WORDS:
        bad.append(f"STOP_WORDS is not rule 3's list of 49: only in the code {sorted(STOP_WORDS - set(listed))}, "
                   f"only in the rule {sorted(set(listed) - STOP_WORDS)}")
    for w in sorted(STOP_WORDS):         # each one dropped: "<w> zebra" is no substring of "zebra", needs 1 of 1
        if concept_recall_loose("zebra", [f"{w} zebra"]) != 1.0:
            bad.append(f"stop word {w!r} counted as a content word")
    exact = sum(c.lower() in "one of the read group".lower() for c in ("of the", "read group", "x y"))
    if concept_recall_loose("one of the read group", ["of the", "read group", "x y"]) < round(exact / 3, 4):
        bad.append("loose recall fell below exact recall")
    if concept_recall_loose("anything", []) is not None:
        bad.append("an empty concept list did not return None")
    return bad


if __name__ == "__main__":
    fails = spec_failures()
    for f in fails:
        print("  FAIL " + f)
    print(f"{len(SPEC_CASES)} of {len(SPEC_CASES)} rule cases hold; STOP_WORDS is rule 3's list of "
          f"{len(STOP_WORDS)} and each is dropped" if not fails else f"{len(fails)} failures")
    raise SystemExit(1 if fails else 0)
