#!/usr/bin/env python3
"""concept_match_stem - a CANDIDATE concept matcher: the loose rule with word stems added (D17, O71, 13 October 2026).

STATUS. A candidate. It stands beside the exact rule and scripts/concept_match_loose.py and replaces neither.
Valerio's ruling (D17, notes/DECISIONS_2026-10-13.md:117-128): the loose matcher gets word stems, every match it
finds today stays, the matchers are scored against concept and answer pairs he labels by hand, and the chosen
matcher is then run where concept recall is read. Until then D12's loose value is the working one. This file
holds the candidate and its self-test. It writes no file, so it uses neither phase3_common.write_outputs nor a
write of its own; the label sheet is not written here.

WHY. The loose rule matches a concept word to an answer token after one trailing "s" is removed from each, so
"files" finds "file", and "generating" does not find "generated". A stemmer gives both of those one stem. A
stemmer alone loses matches the loose rule has: Snowball leaves "ssms" as it is, so the concept "SSMs" would not
find "SSM", which the loose rule finds by removing the s. The candidate is therefore the loose rule OR the stems.

THE RULE is the docstring of concept_recall_stem. For exp04, stem_exp04 is the O30 form: rule 1 read as the
deposited exp04 scorer, as S382's loose_exp04 reads it for the loose rule.

WHAT IS CALLED AND WHAT IS WRITTEN A SECOND TIME. concept_recall_stem calls
concept_match_loose.concept_recall_loose and takes from its detail whether the loose rule finds the concept, the
concept's content words, the words the loose word test matched and how many are needed. STOP_WORDS is imported.
The loose function's tokeniser, its number test and its trailing-s rule are functions nested inside it, which
cannot be imported, so tokens(), is_number() and strip_s() write them a second time here. The candidate uses
tokens() and is_number() for the answer's stems and for the rule that a number is never stemmed. The self-test
holds the three to the loose function twice: against the nested functions themselves, built from the code objects
the loose function carries (gate T3), and by deriving every decision of the loose function from them (gate T4).

    import concept_match_stem as cms
    cms.spec_failures()                                        # [] when the rule's cases hold; a caller's gate
    recall = cms.concept_recall_stem(answer, concepts)         # None for an empty concept list
    recall, per_concept = cms.concept_recall_stem(answer, concepts, detail=True)
    o30 = cms.stem_exp04(scorer_cr, answer, concepts, published)   # exp04: the deposited scorer as rule 1

SELF-TEST. uv run python scripts/concept_match_stem.py. It reads the exp04 rows of the main judge through
judged_ledger.load("exp04") (groups answerable and refutation), each answer's text from the deposit's exp04 file
through S374's reader, the concepts from the v1-format key (S373.AS_V1) and S382's csv
(findings/recompute/S382_exp04_objective_v22.csv); it imports S382 through phase3_common.published for its
deposited_scorer, loose_exp04, CONFIGS and the paths of the two deposited files deposited_scorer lifts from
(S382's main is not called) and asks git, with rev-parse and hash-object, whether the csv on disk is its blob at
HEAD. It writes no file and no bytecode cache and calls no model. A guard installed before nltk, the loose
matcher and the repository's other modules are imported records and refuses every call of socket.connect,
connect_ex, create_connection and getaddrinfo (gate T9: none was made). It draws no random sample, so it has no
seed: the 2,000 tokens of T8 and the 25 concepts it shows are one of every k of a sorted list. Its last line is
the sha256 of everything it printed before that line, so two runs are compared by one line. A check that fails
is a gate line with FAIL and exit 1; an input that cannot be read is one sentence that starts
"concept_match_stem REFUSED:" (or the refusal of judged_ledger, key_scope, phase3_common or S382, passed
through).

  T1  spec_failures(): SPEC_CASES, DETAIL_CASES, STEMS and STEM_PAIRS, written on 13 October before the candidate
      had been run on any text (the first run showed one case written wrongly, which was corrected: the comment
      at "differ" in SPEC_CASES); the cases of concept_match_loose.SPEC_CASES, each with the loose rule's own
      outcome; recall never below the loose rule's; an empty concept list returns None
  T2  the loose rule's own checks (concept_match_loose.spec_failures())
  T3  tokens(), is_number() and strip_s() against the loose function's nested functions, on every answer and
      concept of the two groups and on the texts of the spec cases
  T4  the loose rule's five steps, written out with those three functions (_loose_rule), against
      concept_recall_loose's detail: every concept's found_by, content words, matched words and need, and every
      answer's recall, each group on its own
  T5  superset, each group on its own: a concept the loose function finds is found by the candidate with the
      loose function's found_by, a concept the candidate finds by "stem" is one the loose function does not find,
      no answer's recall is below the loose one, and the candidate finds a concept exactly when the loose
      function finds it or part B of the rule holds, B written out a second time without the loose function
      (_b_holds)
  T6  counts with the plain exact rule as rule 1, group answerable: answers, concepts and the concepts the loose
      function finds against KNOWN; the candidate's count is printed with them. The scratch prototype's count
      (PROTOTYPE_FOUND) was read in its code as the count of a variant with stems in place of the trailing-s
      test and no call of the loose function, so that variant is counted here too (_stems_alone) and printed
      beside it, with the concepts the candidate finds and the variant does not. The prototype's count and the
      variant's are no gate, the prototype being no repository artifact
  T7  O30: the deposited scorer's decision per concept reproduces the scorer on the whole list and the csv's
      concept_recall_v22; S382.loose_exp04's union equals the csv's concept_recall_loose_v22; this module's O30
      form given the loose function returns what S382.loose_exp04 returns, key by key; the union of each matcher
      is its count of found concepts over all concepts, and the candidate's is not below the loose one; all on
      every row of the two groups. Then the candidate's O30 values per strategy, beside the csv's, each group on
      its own
  T8  the stemmer: 2,000 distinct tokens stemmed twice by a stemmer made for the test and once through stem()
      give the same stems
  T9  no connection was attempted during the run
"""
from __future__ import annotations

import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

LABEL = "concept_match_stem"


def _guard_network() -> list:
    """For the self-test: from this call on, a call of socket.socket.connect, socket.socket.connect_ex,
    socket.create_connection or socket.getaddrinfo in this process is added to the returned list and raises
    OSError. Nothing installs the guard when the module is imported."""
    import socket
    attempts: list = []

    def blocked(name: str):
        def call(*args, **kwargs):
            attempts.append(name)
            raise OSError(f"{LABEL}: the self-test opens no connection, and {name} was called")
        return call

    socket.socket.connect = blocked("socket.connect")
    socket.socket.connect_ex = blocked("socket.connect_ex")
    socket.create_connection = blocked("socket.create_connection")
    socket.getaddrinfo = blocked("socket.getaddrinfo")
    return attempts


_ATTEMPTS: list | None = None
if __name__ == "__main__":
    sys.dont_write_bytecode = True                   # the self-test leaves no cache file in the repository
    _ATTEMPTS = _guard_network()                     # before nltk is imported and the stemmer is made

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nltk  # noqa: E402
from nltk.stem.snowball import SnowballStemmer  # noqa: E402
import concept_match_loose  # noqa: E402
from concept_match_loose import STOP_WORDS, concept_recall_loose  # noqa: E402

STEMMER = "english"                                  # the Snowball English rule set (Porter2), as nltk implements it
_SNOWBALL = SnowballStemmer(STEMMER)                 # ignore_stopwords is nltk's default, False: no corpus is read
FOUND_BY = ("exact", "loose", "stem")                # found_by of a found concept; None when it is not found
WORD_TESTS = ("number", "loose", "stem")             # matched_by of a matched content word


def refuse(message: str):
    """Stop in the repository's form: SystemExit("concept_match_stem REFUSED: <one sentence>")."""
    raise SystemExit(f"{LABEL} REFUSED: {message}")


# ---- the loose function's three nested functions, written a second time (gates T3 and T4) ------------------

def _spans(text: str) -> tuple:
    """(the text after Unicode NFKC and lower case, [(token, start, end)]): the tokens of step 2 of the loose rule
    with the place of each in that text. A character is kept when it is a letter, a digit, or a '.' or ','
    between two digits; a token is a longest run of kept characters."""
    t = unicodedata.normalize("NFKC", text).lower()
    out, start = [], None
    for i, ch in enumerate(t):
        keep = (ch.isalpha() or ch.isdigit()
                or (ch in ".," and 0 < i < len(t) - 1 and t[i - 1].isdigit() and t[i + 1].isdigit()))
        if keep and start is None:
            start = i
        elif not keep and start is not None:
            out.append((t[start:i], start, i))
            start = None
    if start is not None:
        out.append((t[start:], start, len(t)))
    return t, out


def tokens(text: str) -> list:
    """The tokens of a text as step 2 of the loose rule gives them (concept_recall_loose's nested tokens())."""
    return [tok for tok, _, _ in _spans(text)[1]]


def is_number(tok: str) -> bool:
    """Rule 3's number: digits with optional '.' or ',' (concept_recall_loose's nested is_number())."""
    return tok.replace(".", "").replace(",", "").isdigit()


def strip_s(tok: str) -> str:
    """Rule 4's shortening: one trailing "s" off a token longer than 3 characters (the nested strip_s())."""
    return tok[:-1] if len(tok) > 3 and tok.endswith("s") else tok


@lru_cache(maxsize=None)
def stem(token: str) -> str:
    """The Snowball English stem of a token, as nltk.stem.snowball.SnowballStemmer("english").stem returns it.
    The result is kept per token for the life of the process."""
    return _SNOWBALL.stem(token)


# ---- the candidate ---------------------------------------------------------------------------------------

def concept_recall_stem(answer: str, expected_concepts: list, detail: bool = False):
    """Concept recall under the candidate rule: the fraction of expected concepts found in the answer.

    A concept is found when
      A. the loose matcher finds it: concept_match_loose.concept_recall_loose, called here, by its exact rule or
         by its loose rule; or
      B. at least ceil(2/3) of the concept's distinct content words occur in the answer, the content words
         being the loose rule's (its tokenisation, its stop-word list, a number always a content word), and a
         content word occurring when
           - it is a number: the identical number token is in the answer, as in the loose rule;
           - it is any other word: it matches under the loose rule's own word test (the same token occurs in the
             answer after one trailing "s" is removed from tokens longer than 3 letters on both sides), or it
             and a token of the answer have the same stem under the Snowball English stemmer
             (nltk.stem.snowball.SnowballStemmer("english")).
         A concept with no content words is found only by the exact rule, as in the loose rule.
    Recall = found concepts / all concepts, rounded to 4 decimals like the exact and the loose one. An empty
    concept list has no recall and returns None, as the loose function does.

    How the code reads the rule where the text leaves a choice:
      - the loose function is called once per answer with detail=True. A concept it finds is found, with its
        found_by ("exact" or "loose"). For a concept it does not find, its content words, the words its word
        test matched and the number needed are taken as it returns them, and B adds the stem test for the
        content words it left unmatched. So "found by stem" means: B holds and the loose function does not find
        the concept; some of the words counted may be matched by the loose test or as numbers.
      - a number of the concept (is_number: digits with optional '.' or ',') is never stemmed, and a number
        token of the answer is in no stem set, so a number matches only the identical token: "1990" does not
        match "1990s", "1.4" does not match "14". A concept token with a letter in it, such as "1990s", is not a
        number: the loose test matches it as it does today, and the stem test compares its stem.
      - the answer's stems are those of every token of the answer that is not a number, as tokens() gives them.
        The loose rule drops stop words from the concept only, never from the answer, and so does this one: a
        content word of the concept can match an answer token that is on the stop-word list when the two have
        the same stem.
      - both tokens are stemmed as they come out of the tokeniser (after NFKC and lower case), with no trailing
        "s" removed first; the stemmer is nltk's SnowballStemmer("english") with its default
        ignore_stopwords=False.
      - ceil(2n/3) is the loose function's own number ("need" of its detail): (2n + 2) // 3.
      - every entry of expected_concepts counts once, duplicates included, as in the loose function.

    With detail=True it returns (recall, per_concept). per_concept lists for each concept: concept; found_by
    ("exact", "loose", "stem" or None); content_words, its distinct content words in sorted order; matched, those
    that matched; matched_by, the test that matched each ("number", "loose" or "stem", tried in that order);
    need, how many were needed. For a concept the loose function finds these are the loose function's own
    content_words, matched and need (all empty or 0 under "exact"), and no stem is computed for it.

    TypeError, in one sentence, for an answer that is not text or a concept list that is not a list or tuple of
    texts."""
    if not expected_concepts:
        return (None, []) if detail else None
    if not isinstance(answer, str) or not isinstance(expected_concepts, (list, tuple)) \
            or not all(isinstance(c, str) for c in expected_concepts):
        raise TypeError(f"{LABEL}: concept_recall_stem takes the answer as text and the concepts as a list of texts")
    _, per_loose = concept_recall_loose(answer, list(expected_concepts), detail=True)            # A
    if len(per_loose) != len(expected_concepts) or any(p["concept"] != c for p, c in zip(per_loose, expected_concepts)):
        refuse("concept_recall_loose's per-concept detail does not follow the concept list")
    answer_stems = {stem(t) for t in tokens(answer) if not is_number(t)}
    found, per_concept = 0, []
    for concept, lp in zip(expected_concepts, per_loose):
        content, need, found_by = lp["content_words"], lp["need"], lp["found_by"]
        by = {w: "number" if is_number(w) else "loose" for w in lp["matched"]}
        if found_by is None:                                                                     # B
            for w in content:
                if w not in by and not is_number(w) and stem(w) in answer_stems:
                    by[w] = "stem"
            if content and len(by) >= need:
                found_by = "stem"
        found += found_by is not None
        per_concept.append({"concept": concept, "found_by": found_by, "content_words": list(content),
                            "matched": [w for w in content if w in by],
                            "matched_by": {w: by[w] for w in content if w in by}, "need": need})
    recall = round(found / len(expected_concepts), 4)
    return (recall, per_concept) if detail else recall


# ---- exp04: rule 1 read as the deposited scorer (O30) -------------------------------------------------------

def _o30(matcher, scorer_cr, answer: str, concepts: list, published: float) -> dict:
    """S382's loose_exp04 with the matcher as an argument: matcher(answer, concepts, detail=True) gives the
    matcher's recall and its per-concept found_by; scorer_cr is the lifted deposited compute_concept_recall, whose
    decision on one concept is the function called on [concept]. A concept counts when either finds it. Returns
    loose_exp04's five keys: union (found concepts / all concepts, rounded to 4 decimals), plain (the matcher's
    recall alone), scorer_added (concepts the scorer finds and the matcher does not), reproduces_whole and
    reproduces_published (whether the per-concept scorer decisions give the scorer's value on the whole list,
    and at 4 decimals the published value). Refused in one sentence where loose_exp04 exits: a detail that does
    not follow the concept list, and a scorer value on one concept other than 0.0 or 1.0; and for an empty
    concept list, which loose_exp04 does not handle (S382's main refuses such a question before it calls it)."""
    if not concepts:
        refuse("the O30 form was called with no expected concepts, for which no recall is defined")
    plain, per = matcher(answer, concepts, detail=True)
    if len(per) != len(concepts) or any(p["concept"] != c for p, c in zip(per, concepts)):
        refuse("the matcher's per-concept detail does not follow the concept list")
    single = [scorer_cr(answer, [c]) for c in concepts]
    if any(v not in (0.0, 1.0) for v in single):
        refuse("the deposited compute_concept_recall returned other than 0.0 or 1.0 on one concept")
    by_scorer = [v == 1.0 for v in single]
    by_matcher = [p["found_by"] is not None for p in per]
    union = [a or b for a, b in zip(by_scorer, by_matcher)]
    whole = scorer_cr(answer, concepts)
    return {"union": round(sum(union) / len(concepts), 4), "plain": plain,
            "scorer_added": sum(a and not b for a, b in zip(by_scorer, by_matcher)),
            "reproduces_whole": sum(by_scorer) / len(concepts) == whole,
            "reproduces_published": round(sum(by_scorer) / len(concepts), 4) == published}


def stem_exp04(scorer_cr, answer: str, concepts: list, published: float) -> dict:
    """The candidate's concept recall with rule 1 read as the scorer exp04 used (O30), for one answer: the
    signature and the returned keys of S382's loose_exp04, with concept_recall_stem where loose_exp04 calls
    concept_recall_loose. A concept counts when the deposited compute_concept_recall, called on that concept
    alone, or the candidate finds it. See _o30 for the keys and the refusals; gate T7 of the self-test holds
    _o30, given the loose function, to S382.loose_exp04 on every exp04 row of the two groups."""
    return _o30(concept_recall_stem, scorer_cr, answer, concepts, published)


# ---- the rule's cases, written on 13 October before the candidate had been run on any text ----------------

# (concept, answer, found_by): what concept_recall_stem must give for the one concept
SPEC_CASES = [
    # tense and form pairs: the stem test finds them, the loose rule does not
    ("generating", "the reads were generated", "stem"),                  # generating, generated: generat
    ("implemented", "an implementation in C", "stem"),                   # implemented, implementation: implement
    # The next two were one case before the first run of the self-test: ("differ", "the two are different", "stem").
    # That run gave "exact": "differ" is a substring of "different", and the exact rule is a substring test, so it
    # finds the concept before any stem is read. The case was corrected to "exact" and the pair was added with
    # the two words exchanged, where the stem test decides. No other case of these tables was changed.
    ("differ", "the two are different", "exact"),
    ("different", "the two differ", "stem"),                             # different, differ: differ
    ("portable", "for portability", "stem"),                             # portable, portability: portabl
    ("case studies", "one case study", "stem"),                          # studies, study: studi; "case" by the loose test
    ("read mapping", "reads are mapped", "stem"),                        # mapping, mapped: map; "read" by the loose test
    # forms Snowball does not give one stem: not matched, so not found
    ("shrinking", "the index has shrunk", None),                         # shrink and shrunk: an irregular past
    ("reduction", "it reduces memory", None),                            # reduct and reduc
    # the loose rule finds them, a stemmer alone would not: found, by "loose"
    ("SSMs", "an SSM", "loose"),                                         # Snowball leaves ssms; the loose rule drops the s
    ("RNAs", "one RNA", "loose"),                                        # Snowball leaves rnas
    # numbers match only the identical number token, with stems as without
    ("1990 census", "the 1990s census", None),                           # 1990 is not 1990s: 1 of 2
    ("1.4 TB", "it takes 14 TB", None),                                  # 1.4 is not 14
    ("14 TB", "it takes 1.4 TB", None),                                  # nor 14 the number 1.4
    ("30 generating", "30 were generated", "stem"),                      # the number exact, the word by stem: 2 of 2
    ("30 generating", "31 were generated", None),                        # the number missing: 1 of 2
    # stop words and the two-thirds threshold, as in the loose rule
    ("about generating reads", "it generated a read", "stem"),           # "about" a stop word: 2 of 2
    ("implemented portable index", "an implementation of the index", "stem"),          # 2 of 3
    ("implemented portable index format", "an implementation of the index", None),     # 2 of 4, 3 needed
    ("of the", "the of", None),                                          # no content words: exact only
    ("of the", "one of the", "exact"),                                   # found by the exact rule
    # the order of the tests: exact, then loose, then stem
    ("generated reads", "the generated reads", "exact"),
    ("gene sets", "the gene set", "loose"),
    ("generating sets", "generated one set", "stem"),                    # one word by stem, one by the loose test
]

# (concept, answer, content_words, matched_by, need): the detail concept_recall_stem must give
DETAIL_CASES = [
    ("30 generating", "30 were generated", ["30", "generating"], {"30": "number", "generating": "stem"}, 2),
    ("about generating reads", "it generated a read", ["generating", "reads"],
     {"generating": "stem", "reads": "loose"}, 2),
    ("implemented portable index", "an implementation of the index", ["implemented", "index", "portable"],
     {"implemented": "stem", "index": "loose"}, 2),
    ("implemented portable index format", "an implementation of the index",
     ["format", "implemented", "index", "portable"], {"implemented": "stem", "index": "loose"}, 3),
    ("gene sets", "the gene set", ["gene", "sets"], {"gene": "loose", "sets": "loose"}, 2),
    ("of the", "one of the", [], {}, 0),
]

# token -> its Snowball English stem, as the published rule set gives it
STEMS = {"generating": "generat", "generated": "generat", "implemented": "implement", "implementation": "implement",
         "differ": "differ", "different": "differ", "portable": "portabl", "portability": "portabl",
         "studies": "studi", "study": "studi", "mapping": "map", "mapped": "map",
         "shrinking": "shrink", "shrunk": "shrunk", "reduction": "reduct", "reduces": "reduc",
         "ssms": "ssms", "ssm": "ssm", "rnas": "rnas", "rna": "rna"}

# (token, token, whether Snowball gives the two one stem)
STEM_PAIRS = [("generating", "generated", True), ("implemented", "implementation", True), ("differ", "different", True),
              ("portable", "portability", True), ("studies", "study", True), ("mapping", "mapped", True),
              ("shrinking", "shrunk", False), ("reduction", "reduces", False),
              ("ssms", "ssm", False), ("rnas", "rna", False)]


def spec_failures() -> list:
    """The cases the candidate gets wrong: SPEC_CASES (found_by of the one concept, and recall 1.0 or 0.0 with
    it), DETAIL_CASES (content_words, matched_by, matched and need), STEMS and STEM_PAIRS (the stemmer), the cases
    of concept_match_loose.SPEC_CASES (found or not as the loose rule says, and found_by never "stem"), recall
    never below the loose rule's on a three-concept example, and None for an empty concept list with and without
    detail. An empty list when all hold."""
    bad = []
    for concept, answer, want in SPEC_CASES:
        recall, per = concept_recall_stem(answer, [concept], detail=True)
        if per[0]["found_by"] != want or recall != (0.0 if want is None else 1.0):
            bad.append(f"{concept!r} in {answer!r}: found_by {per[0]['found_by']!r} with recall {recall}, the rule says {want!r}")
    for concept, answer, content, by, need in DETAIL_CASES:
        p = concept_recall_stem(answer, [concept], detail=True)[1][0]
        got = (p["content_words"], p["matched_by"], p["matched"], p["need"])
        if got != (content, by, [w for w in content if w in by], need):
            bad.append(f"{concept!r} in {answer!r}: detail {got}, the rule says {(content, by, need)}")
    for token, want in STEMS.items():
        if stem(token) != want:
            bad.append(f"stem of {token!r} is {stem(token)!r}, the table says {want!r}")
    for a, b, same in STEM_PAIRS:
        if (stem(a) == stem(b)) is not same:
            bad.append(f"{a!r} and {b!r}: stems {stem(a)!r} and {stem(b)!r}, the table says {'one stem' if same else 'two stems'}")
    for concept, answer, want in concept_match_loose.SPEC_CASES:
        recall, per = concept_recall_stem(answer, [concept], detail=True)
        if (recall == 1.0) is not want or per[0]["found_by"] == "stem":
            bad.append(f"loose case {concept!r} in {answer!r}: found_by {per[0]['found_by']!r}, the loose rule says {want}")
    three = ["of the", "read group", "generating reads"]
    if concept_recall_stem("one of the reads generated", three) < concept_recall_loose("one of the reads generated", three):
        bad.append("recall fell below the loose rule's")
    if concept_recall_stem("anything", []) is not None or concept_recall_stem("anything", [], detail=True) != (None, []):
        bad.append("an empty concept list did not return None")
    return bad


# ---- self-test --------------------------------------------------------------------------------------------

# The counts D17 records for the group answerable of exp04 with the plain exact rule as rule 1
# (notes/DECISIONS_2026-10-13.md:122-123: "loose finds 1,774 and loose with stems 1,912"). They come from a scratch
# prototype, which is no repository artifact. The first three are gate T6. The fourth is the count of the
# prototype's variant with stems in place of the trailing-s test (_stems_alone); it is printed and is no gate.
KNOWN = {"answers": 516, "concepts": 3426, "loose_found": 1774}
PROTOTYPE_FOUND = 1912
GROUP_ROWS = {"answerable": 516, "refutation": 60}       # judged_ledger.EXPECTED["exp04_groups"], 13 October
N_TOKENS = 2000                                          # T8: distinct tokens stemmed
N_SHOWN = 25                                             # concepts shown to the author
PASSAGE = 70                                             # characters shown on each side of a stemmed token
S382_MODULE = "S382_exp04_objective_v22"
S382_CSV = "S382_exp04_objective_v22.csv"                # under findings/recompute/
CSV_COLUMNS = ("question_id", "config", "group", "n_concepts_v22", "concept_recall_v22", "concept_recall_loose_v22")


def _loose_rule(answer: str, concepts: list) -> tuple:
    """The loose rule's five steps written out with this module's tokens(), is_number() and strip_s(): (recall,
    [(found_by, content words, matched words, need) per concept]). Gate T4 compares it with concept_recall_loose's
    detail; the candidate does not call it."""
    low, toks = answer.lower(), tokens(answer)
    exact, words = set(toks), {strip_s(t) for t in toks}
    out = []
    for concept in concepts:
        if concept.lower() in low:
            out.append(("exact", [], [], 0))
            continue
        content = sorted({t for t in tokens(concept) if is_number(t) or t not in STOP_WORDS})
        matched = [w for w in content if (w in exact if is_number(w) else strip_s(w) in words)]
        need = (2 * len(content) + 2) // 3
        out.append(("loose" if content and len(matched) >= need else None, content, matched, need))
    return round(sum(o[0] is not None for o in out) / len(concepts), 4), out


def _answer_parts(answer: str) -> tuple:
    """(the answer's tokens as a set, the same after strip_s, the stems of its tokens that are not numbers)."""
    toks = tokens(answer)
    return set(toks), {strip_s(t) for t in toks}, {stem(t) for t in toks if not is_number(t)}


def _b_holds(parts: tuple, concept: str) -> bool:
    """Part B of the rule for one concept, written out with this module's tokens(), is_number() and strip_s() and
    without the loose function: at least ceil(2/3) of the concept's distinct content words occur, a number as the
    identical token, any other word by the trailing-s test or by its stem. parts is _answer_parts(answer). Gate T5
    compares "the loose function finds it or _b_holds" with the candidate's decision; the candidate does not call
    it."""
    exact, words, stems = parts
    content = {t for t in tokens(concept) if is_number(t) or t not in STOP_WORDS}
    hits = sum((w in exact) if is_number(w) else (strip_s(w) in words or stem(w) in stems) for w in content)
    return bool(content) and hits >= (2 * len(content) + 2) // 3


def _stems_alone(answer: str, concepts: list) -> list:
    """Whether each concept is found under the scratch prototype's variant with stems in place of the trailing-s
    test: by the exact rule, or when at least ceil(2/3) of its content words match, a number by the identical
    number token and any other word when its stem is the stem of an answer token that is not a number or is
    itself a token of the answer. The loose function is not called and no trailing "s" is removed. T6 prints its
    count beside PROTOTYPE_FOUND; the candidate does not call it."""
    low, toks = answer.lower(), tokens(answer)
    numbers = {t for t in toks if is_number(t)}
    forms = {stem(t) for t in toks if not is_number(t)} | set(toks)
    out = []
    for concept in concepts:
        content = sorted({t for t in tokens(concept) if is_number(t) or t not in STOP_WORDS})
        matched = [w for w in content if (w in numbers if is_number(w) else stem(w) in forms)]
        out.append(concept.lower() in low or (bool(content) and len(matched) >= (2 * len(content) + 2) // 3))
    return out


def _nested(name: str):
    """The function nested in concept_recall_loose under this name, built from the code object the loose function
    carries, with the loose module's globals. None when the loose function holds no such code object, or one that
    reads a variable of the enclosing call."""
    import types
    for const in concept_recall_loose.__code__.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name and not const.co_freevars:
            return types.FunctionType(const, vars(concept_match_loose))
    return None


def _exp04(jl, p3, results: Path, shown) -> list:
    """The exp04 answers of the groups answerable and refutation: [{row, answer, concepts}], group answerable
    first, each group in the order of the deposit file. row is judged_ledger's Row; answer is the text S374's
    reader gives for the deposit row the ledger key names; concepts is expected_concepts of the question in
    S373.AS_V1. Refused, naming the file: group counts other than GROUP_ROWS, rows on more than one deposit file,
    a deposit file S374's reader cannot read, an answer that is not text of the length and question the ledger row
    records, and a question of these rows without a list of concept texts that is not empty."""
    try:
        rows = jl.load("exp04")
    except ValueError as e:
        refuse(f"judged_ledger.load('exp04') gave no rows: {e}")
    wanted = sorted((r for r in rows if r.group in GROUP_ROWS), key=lambda r: (list(GROUP_ROWS).index(r.group), r.row))
    counts = {g: sum(r.group == g for r in wanted) for g in GROUP_ROWS}
    tags = sorted({r.tag for r in wanted})
    if counts != GROUP_ROWS or len(tags) != 1 or len({(r.question_id, r.config) for r in wanted}) != len(wanted):
        refuse(f"judged_ledger.load('exp04') holds {counts} rows of the two groups on {len(tags)} deposit files, where "
               f"{GROUP_ROWS} on one file, one row per question and strategy, are read")
    deposit = results / tags[0]
    try:
        _doc, dep = jl.s374_load_rows(str(deposit))
        got = {r.key: (jl.s374_qid(dep[r.row]), jl.s374_answer(dep[r.row])) for r in wanted}
    except (OSError, KeyError, TypeError, AttributeError, ValueError, RecursionError, IndexError) as e:
        refuse(f"{shown(deposit)} cannot be read by S374's reader ({type(e).__name__}: {e})")
    off = [r.key for r in wanted if got[r.key][0] != r.question_id or not isinstance(got[r.key][1], str)
           or len(got[r.key][1]) != r.answer_chars]
    if off:
        refuse(f"{shown(deposit)} does not hold, for {len(off)} ledger rows, an answer of the question and the length "
               f"the row records, the first {off[0]!r}")
    key = p3.read_json(LABEL, jl.S373.AS_V1)
    try:
        concepts = {q["id"]: q["expected_concepts"] for q in key["questions"]}
    except (KeyError, TypeError) as e:
        refuse(f"{shown(jl.S373.AS_V1)} is not the v1-format key: its questions lack id or expected_concepts ({type(e).__name__}: {e})")
    bad = sorted({r.question_id for r in wanted if not (isinstance(concepts.get(r.question_id), list) and concepts[r.question_id]
                                                        and all(isinstance(c, str) for c in concepts[r.question_id]))})
    if bad:
        refuse(f"{shown(jl.S373.AS_V1)} gives {len(bad)} questions of these rows no list of concept texts, the first {bad[0]}")
    return [{"row": r, "answer": got[r.key][1], "concepts": concepts[r.question_id]} for r in wanted]


def _blob_at_head(root: Path, path: Path):
    """Whether the file on disk is the blob git holds for it at HEAD (git rev-parse and git hash-object, which
    write nothing); None when git gives no answer."""
    import subprocess
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        head = subprocess.run(["git", "-C", str(root), "rev-parse", f"HEAD:{rel}"], capture_output=True, text=True)
        disk = subprocess.run(["git", "-C", str(root), "hash-object", str(path)], capture_output=True, text=True)
    except (OSError, ValueError):
        return None
    if head.returncode or disk.returncode or not head.stdout.strip():
        return None
    return head.stdout.strip() == disk.stdout.strip()


def _passage(answer: str, start: int, end: int) -> str:
    """The answer from PASSAGE characters before start to PASSAGE after end, the stretch start:end in square
    brackets, runs of white space as one space. start and end are places in the answer after NFKC and lower case
    (_spans). The passage is cut from the answer after NFKC with its capitals when lower case leaves its length
    as it is, and from the lower-case text otherwise."""
    norm = unicodedata.normalize("NFKC", answer)
    text = norm if len(norm.lower()) == len(norm) else norm.lower()
    a, b = max(0, start - PASSAGE), min(len(text), end + PASSAGE)
    cut = f"{text[a:start]}[{text[start:end]}]{text[end:b]}"
    return ("..." if a else "") + " ".join(cut.split()) + ("..." if b < len(text) else "")


def _mean(xs) -> float:
    xs = list(xs)
    return round(sum(xs) / len(xs), 4)


def _checks(g, p3, jl, results: Path, recompute: Path, root: Path, shown) -> None:
    """The gates T1 to T8 and the lists printed for the author (module docstring)."""
    import hashlib
    import json
    from collections import Counter

    # T1, T2: the rule's cases and the loose rule's own
    fails = spec_failures()
    for f in fails:
        print("  FAIL " + f)
    n_loose_cases = len(concept_match_loose.SPEC_CASES)
    g.gate("T1", not fails, f"{len(SPEC_CASES)} of {len(SPEC_CASES)} cases of SPEC_CASES, {len(DETAIL_CASES)} of DETAIL_CASES, "
                            f"{len(STEMS)} stems of STEMS and {len(STEM_PAIRS)} pairs of STEM_PAIRS hold; the {n_loose_cases} "
                            "cases of concept_match_loose.SPEC_CASES keep the loose rule's outcome, none found by stem; an "
                            "empty concept list returns None" if not fails else f"{len(fails)} cases fail (listed above)")
    loose_fails = concept_match_loose.spec_failures()
    g.gate("T2", not loose_fails, "concept_match_loose.spec_failures() is empty" if not loose_fails
           else f"the loose rule fails {len(loose_fails)} of its own checks, the first: {loose_fails[0]}")

    data = _exp04(jl, p3, results, shown)
    groups = {grp: [d for d in data if d["row"].group == grp] for grp in GROUP_ROWS}
    n_concepts = {grp: sum(len(d["concepts"]) for d in ds) for grp, ds in groups.items()}
    print(f"  read: {', '.join(f'{len(ds)} answers and {n_concepts[grp]:,} concepts in the group {grp}' for grp, ds in groups.items())}"
          f"; answers from {shown(results / data[0]['row'].tag)}, concepts from {shown(jl.S373.AS_V1)}")

    # T3: the three functions written a second time, against the loose function's nested ones
    nested = {name: _nested(name) for name in ("tokens", "is_number", "strip_s")}
    texts = sorted({d["answer"] for d in data} | {c for d in data for c in d["concepts"]}
                   | {t for case in SPEC_CASES + DETAIL_CASES + concept_match_loose.SPEC_CASES for t in case[:2]})
    if all(nested.values()):
        tok_off = [t for t in texts if tokens(t) != nested["tokens"](t)]
        distinct = sorted({tok for t in texts for tok in tokens(t)})
        one_off = [tok for tok in distinct if is_number(tok) is not nested["is_number"](tok) or strip_s(tok) != nested["strip_s"](tok)]
        n_tok = sum(len(tokens(t)) for t in texts)
        g.gate("T3", not tok_off and not one_off,
               f"tokens() gives the nested tokens() of concept_recall_loose on {len(texts) - len(tok_off):,} of {len(texts):,} texts "
               f"({n_tok:,} tokens); is_number() and strip_s() give the nested ones on {len(distinct) - len(one_off):,} of "
               f"{len(distinct):,} distinct tokens")
    else:
        lacking = [name for name, fn in nested.items() if fn is None]
        g.gate("T3", False, f"concept_recall_loose carries no nested function {', '.join(lacking)} that can be built from its code object")

    # T4: every decision of the loose function, derived from the three functions; T5: superset. Each group on its own.
    per_loose, per_stem = {}, {}
    t4, t5 = [], []
    for grp, ds in groups.items():
        dec_off = rec_off = lost = other_by = stem_on_found = below = second_off = 0
        for d in ds:
            k = d["row"].key
            recall_l, pl = concept_recall_loose(d["answer"], d["concepts"], detail=True)
            recall_s, ps = concept_recall_stem(d["answer"], d["concepts"], detail=True)
            recall_r, pr = _loose_rule(d["answer"], d["concepts"])
            per_loose[k], per_stem[k] = (recall_l, pl), (recall_s, ps)
            dec_off += sum((a["found_by"], a["content_words"], a["matched"], a["need"]) != b for a, b in zip(pl, pr))
            rec_off += recall_l != recall_r
            lost += sum(a["found_by"] is not None and b["found_by"] is None for a, b in zip(pl, ps))
            other_by += sum(a["found_by"] is not None and b["found_by"] != a["found_by"] for a, b in zip(pl, ps))
            stem_on_found += sum(b["found_by"] == "stem" and a["found_by"] is not None for a, b in zip(pl, ps))
            below += recall_s < recall_l
            parts = _answer_parts(d["answer"])
            second_off += sum((a["found_by"] is not None or _b_holds(parts, c)) != (b["found_by"] is not None)
                              for a, b, c in zip(pl, ps, d["concepts"]))
        n, a = n_concepts[grp], len(ds)
        t4.append((dec_off == 0 and rec_off == 0, f"{grp}: {n - dec_off:,} of {n:,} concepts and the recall of {a - rec_off} of {a} answers"))
        t5.append((lost == 0 and other_by == 0 and stem_on_found == 0 and below == 0 and second_off == 0,
                   f"{grp}: {lost} of the concepts the loose function finds are lost, {other_by} carry another found_by, "
                   f"{stem_on_found} concepts found by stem are ones it finds, {below} of {a} answers have a lower recall, and "
                   f"on {n - second_off:,} of {n:,} concepts the candidate finds the concept exactly when the loose function "
                   "finds it or part B of the rule, written out a second time (_b_holds), holds"))
    g.gate("T4", all(ok for ok, _ in t4), "the loose rule written out with tokens(), is_number() and strip_s() gives "
                                           "concept_recall_loose's found_by, content words, matched words and need on "
                                           + "; ".join(m for _, m in t4))
    g.gate("T5", all(ok for ok, _ in t5), "superset of the loose function, " + "; ".join(m for _, m in t5))

    # T6: counts with the plain exact rule as rule 1
    by = {grp: {f: sum(p["found_by"] == f for d in ds for p in per_stem[d["row"].key][1]) for f in FOUND_BY} for grp, ds in groups.items()}
    loose_found = {grp: sum(p["found_by"] is not None for d in ds for p in per_loose[d["row"].key][1]) for grp, ds in groups.items()}
    cand_found = {grp: sum(by[grp].values()) for grp in groups}
    got = {"answers": len(groups["answerable"]), "concepts": n_concepts["answerable"], "loose_found": loose_found["answerable"]}
    g.gate("T6", got == KNOWN, f"group answerable, plain exact rule as rule 1: {got['answers']} answers, {got['concepts']:,} concepts, "
                               f"the loose function finds {got['loose_found']:,} (D17 records {KNOWN['answers']}, "
                               f"{KNOWN['concepts']:,} and {KNOWN['loose_found']:,})")
    print("  concepts found with the plain exact rule as rule 1 (found_by of the candidate; the loose function finds the "
          "first two, the candidate all three):")
    print("    group        answers  concepts  by exact  by loose  by stem  loose function  candidate  answers with a higher recall")
    for grp, ds in groups.items():
        higher = sum(per_stem[d["row"].key][0] > per_loose[d["row"].key][0] for d in ds)
        print(f"    {grp:<11}  {len(ds):>7}  {n_concepts[grp]:>8,}  {by[grp]['exact']:>8,}  {by[grp]['loose']:>8,}  {by[grp]['stem']:>7,}  "
              f"{loose_found[grp]:>14,}  {cand_found[grp]:>9,}  {higher:>28}")
    alone = {d["row"].key: _stems_alone(d["answer"], d["concepts"]) for d in groups["answerable"]}
    pairs = [(a, p) for d in groups["answerable"] for a, p in zip(alone[d["row"].key], per_stem[d["row"].key][1])]
    extra = Counter((p["concept"], p["found_by"]) for a, p in pairs if p["found_by"] is not None and not a)
    print(f"    group answerable, stems in place of the trailing-s test (the scratch prototype's variant, no loose function): "
          f"{sum(a for a, _ in pairs):,} concepts found, and the prototype gave {PROTOTYPE_FOUND:,}; the candidate finds "
          f"{sum(a and p['found_by'] is not None for a, p in pairs):,} of them and {sum(extra.values())} that the variant does not"
          + (": " + "; ".join(f"{c!r} in {n} answer{'s' if n > 1 else ''}, found_by {by_!r}" for (c, by_), n in sorted(extra.items()))
             if extra else ""))

    # T7: rule 1 read as the deposited exp04 scorer (O30)
    S382 = p3.published(S382_MODULE)
    for f in (S382.SCORER, S382.HARNESS_COMMON):
        p3.sha256_file(LABEL, f)                             # a missing file is a refusal that names it
    try:
        ns, _sources, _sink = S382.deposited_scorer()
        scorer_cr = ns["compute_concept_recall"]
    except (OSError, SyntaxError, ValueError, KeyError, TypeError) as e:
        refuse(f"S382.deposited_scorer() could not lift the deposited scorer from {shown(S382.SCORER)} ({type(e).__name__}: {e})")
    configs = list(S382.CONFIGS)
    csv_path = recompute / S382_CSV
    comments, crows = p3.read_csv_rows(LABEL, csv_path, CSV_COLUMNS)
    try:
        prov = json.loads(comments[0][2:]) if comments and comments[0].startswith("# {") else {}
        csv_key, csv_matcher = prov["key_sha256"], prov["loose_matcher"]["sha256"]
    except (ValueError, KeyError, TypeError, RecursionError) as e:
        refuse(f"{shown(csv_path)} does not open with S382's '# {{provenance}}' line holding key_sha256 and loose_matcher "
               f"({type(e).__name__}: {e})")
    try:
        cells = {(r["question_id"], r["config"]): (r["group"], int(r["n_concepts_v22"]), float(r["concept_recall_v22"]),
                                                  float(r["concept_recall_loose_v22"])) for r in crows}
    except ValueError as e:
        refuse(f"{shown(csv_path)} holds a cell that is no number in n_concepts_v22, concept_recall_v22 or "
               f"concept_recall_loose_v22 ({e})")
    key_sha = p3.sha256_file(LABEL, jl.S373.AS_V1)
    loose_sha = p3.sha256_file(LABEL, concept_match_loose.__file__)
    ledger = {(d["row"].question_id, d["row"].config): d for d in data}
    both = set(cells) & set(ledger)
    off = [k for k in both if cells[k][:2] != (ledger[k]["row"].group, len(ledger[k]["concepts"]))]
    if csv_key != key_sha or len(crows) != len(cells) or set(cells) != set(ledger) or off or {k[1] for k in ledger} != set(configs):
        refuse(f"{shown(csv_path)} is not on the present key and rows: it records the key {str(csv_key)[:12]} (present "
               f"{key_sha[:12]}) and holds {len(crows)} rows on {len(cells)} answers, {len(both)} of them among the "
               f"{len(ledger)} ledger rows of the two groups, {len(off)} of those with another group or number of concepts, "
               f"and its strategies are {'' if {k[1] for k in cells} == set(configs) else 'not '}S382's")
    o30_l, o30_s, mine_l, scorer_found, union_found = {}, {}, {}, {}, {}
    for k, d in ledger.items():
        published = cells[k][2]
        o30_l[k] = S382.loose_exp04(scorer_cr, d["answer"], d["concepts"], published)
        mine_l[k] = _o30(concept_recall_loose, scorer_cr, d["answer"], d["concepts"], published)
        o30_s[k] = stem_exp04(scorer_cr, d["answer"], d["concepts"], published)
        single = [scorer_cr(d["answer"], [c]) == 1.0 for c in d["concepts"]]
        scorer_found[k] = sum(single)
        union_found[k] = tuple(sum(a or p["found_by"] is not None for a, p in zip(single, per[d["row"].key][1]))
                               for per in (per_loose, per_stem))
    n_rows = len(ledger)
    not_scorer = sum(not (x["reproduces_whole"] and x["reproduces_published"]) for x in o30_l.values())
    not_csv = sum(o30_l[k]["union"] != cells[k][3] for k in ledger)
    not_form = sum(mine_l[k] != o30_l[k] for k in ledger)
    not_count = sum(round(union_found[k][0] / len(d["concepts"]), 4) != o30_l[k]["union"]
                    or round(union_found[k][1] / len(d["concepts"]), 4) != o30_s[k]["union"]
                    or not (o30_s[k]["reproduces_whole"] and o30_s[k]["reproduces_published"])
                    or o30_s[k]["union"] < o30_l[k]["union"] for k, d in ledger.items())
    at_head = _blob_at_head(root, csv_path)
    g.gate("T7", not_scorer == 0 and not_csv == 0 and not_form == 0 and not_count == 0,
           f"O30 on the {n_rows} rows of the two groups ({', '.join(f'{len(ds)} {grp}' for grp, ds in groups.items())}): the "
           f"scorer's per-concept decisions reproduce it on the whole list and concept_recall_v22 on {n_rows - not_scorer}; "
           f"S382.loose_exp04's union equals concept_recall_loose_v22 of {shown(csv_path)} on {n_rows - not_csv}; this module's "
           f"O30 form given the loose function returns S382.loose_exp04's five values on {n_rows - not_form}; the union of each "
           f"matcher is its count of found concepts over all concepts, the candidate's not below the loose one, on {n_rows - not_count}")
    print(f"    {shown(csv_path)}: sha256 {p3.sha256_file(LABEL, csv_path)[:12]}; "
          + ("git gave no answer on whether it is its blob at HEAD" if at_head is None
             else f"the file on disk {'is' if at_head else 'is not'} its blob at HEAD")
          + f"; it records the loose matcher {str(csv_matcher)[:12]}, and {shown(Path(concept_match_loose.__file__))} has sha256 "
          f"{loose_sha[:12]}")
    print("  concepts found with the deposited scorer's rule as rule 1 (O30):")
    print("    group        answers  concepts  scorer  scorer or loose function  scorer or candidate")
    for grp, ds in groups.items():
        ks = [(d["row"].question_id, d["row"].config) for d in ds]
        print(f"    {grp:<11}  {len(ds):>7}  {n_concepts[grp]:>8,}  {sum(scorer_found[k] for k in ks):>6,}  "
              f"{sum(union_found[k][0] for k in ks):>24,}  {sum(union_found[k][1] for k in ks):>19,}")
    print("  concept recall per strategy with the deposited scorer's rule as rule 1 (O30), mean over the answers, 4 decimals:")
    for grp, ds in groups.items():
        print(f"    group {grp}")
        print("      strategy       answers  S382 csv, loose  loose, recomputed  candidate")
        for cfg in configs + ["pooled"]:
            ks = [(d["row"].question_id, d["row"].config) for d in ds if cfg == "pooled" or d["row"].config == cfg]
            print(f"      {cfg:<13}  {len(ks):>7}  {_mean(cells[k][3] for k in ks):>15.4f}  {_mean(o30_l[k]['union'] for k in ks):>17.4f}  "
                  f"{_mean(o30_s[k]['union'] for k in ks):>9.4f}")

    # T8: the stemmer on N_TOKENS distinct tokens, twice with a stemmer of its own and once through stem()
    words = sorted({tok for d in data for t in [d["answer"], *d["concepts"]] for tok in tokens(t) if not is_number(tok)})
    step = max(1, len(words) // N_TOKENS)
    sample = words[::step][:N_TOKENS]
    fresh = SnowballStemmer(STEMMER)
    first, second, cached = [fresh.stem(w) for w in sample], [fresh.stem(w) for w in sample], [stem(w) for w in sample]
    digest = hashlib.sha256("\n".join(first).encode("utf-8")).hexdigest()
    g.gate("T8", len(sample) == N_TOKENS and first == second == cached,
           f"nltk {nltk.__version__}, SnowballStemmer({STEMMER!r}): {len(sample):,} distinct tokens (one of every {step} of the "
           f"{len(words):,} distinct tokens of the answers and concepts that are not numbers, in sorted order) stemmed twice by "
           f"a stemmer made for the test and once through stem() give the same stems; sha256 of the stems {digest[:12]}; "
           f"{sum(a != b for a, b in zip(sample, first)):,} of them differ from their token")

    # for the author: N_SHOWN concepts the candidate finds and the loose function does not, group answerable
    added = []
    for d in groups["answerable"]:
        for i, p in enumerate(per_stem[d["row"].key][1]):
            if p["found_by"] == "stem":
                added.append((d["row"].question_id, configs.index(d["row"].config), i, d, p))
    added.sort(key=lambda x: x[:3])
    stem_words = [(d, w) for _, _, _, d, p in added for w, test in p["matched_by"].items() if test == "stem"]
    only_stop = 0
    for d, w in stem_words:
        only_stop += all(tok in STOP_WORDS for tok in tokens(d["answer"]) if not is_number(tok) and stem(tok) == stem(w))
    print(f"  group answerable, plain exact rule as rule 1: the candidate finds {len(added)} concepts the loose function does "
          f"not, in {len({x[3]['row'].key for x in added})} answers; in them {len(stem_words)} content words are matched by the "
          f"stem test ({len({w for _, w in stem_words})} distinct words); for {only_stop} of the {len(stem_words)}, every answer "
          "token with the word's stem is on the loose rule's stop-word list")
    k_th = max(1, len(added) // N_SHOWN)
    shown_ones = added[::k_th][:N_SHOWN]
    print(f"  {len(shown_ones)} of the {len(added)}, one of every {k_th} from the first, in the order question, strategy "
          f"({', '.join(configs)}), place of the concept in the key; for each word matched by the stem test, the first token "
          f"of the answer with its stem, in brackets, with {PASSAGE} characters of the answer on each side:")
    for n, (qid, _, i, d, p) in enumerate(shown_ones, 1):
        print(f"  [{n:02d}] {qid} | {d['row'].config} | concept {i + 1} of {len(d['concepts'])}: {p['concept']!r} | "
              f"{len(p['matched'])} of {len(p['content_words'])} content words matched, {p['need']} needed")
        _, spans = _spans(d["answer"])
        for w in p["content_words"]:
            test = p["matched_by"].get(w)
            if test != "stem":
                print(f"       {w}: " + {"number": "the identical number token", "loose": "the loose word test",
                                         None: "not matched"}[test])
                continue
            tok, a, b = next(s for s in spans if not is_number(s[0]) and stem(s[0]) == stem(w))
            print(f"       {w}: stem {stem(w)!r}, in the answer as {tok!r}: {_passage(d['answer'], a, b)}")


class _Tee:
    """Passes what is printed to the stream and keeps its sha256."""

    def __init__(self, stream):
        import hashlib
        self.stream, self.sha = stream, hashlib.sha256()

    def write(self, text: str) -> int:
        self.sha.update(text.encode("utf-8"))
        return self.stream.write(text)

    def flush(self) -> None:
        self.stream.flush()


def self_test() -> int:
    import contextlib
    import judged_ledger as jl
    import phase3_common as p3
    from machine import RECOMPUTE, RESULTS, ROOT, shown

    tee = _Tee(sys.stdout)
    with contextlib.redirect_stdout(tee):
        print(f"{LABEL} self-test: {shown(Path(__file__).resolve())}; nltk {nltk.__version__}, SnowballStemmer({STEMMER!r}); "
              f"python {sys.version.split()[0]}")
        g = p3.Gates(LABEL)
        _checks(g, p3, jl, RESULTS, RECOMPUTE, ROOT, shown)
        g.gate("T9", _ATTEMPTS == [], "no connection was attempted: 0 calls of socket.connect, connect_ex, create_connection "
                                      "or getaddrinfo since the guard was installed, before nltk was imported" if _ATTEMPTS == []
               else f"connections attempted, or no guard installed (the module was not run as a script): {_ATTEMPTS!r}")
        failed = [r["name"] for r in g.records if not r["ok"]]
        print(f"\n{'PASSED' if not failed else 'FAILED ' + ' '.join(failed)}: {len(g.records) - len(failed)} of {len(g.records)} "
              "gates; nothing written")
    print(f"sha256 of the lines above: {tee.sha.hexdigest()}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(self_test())
