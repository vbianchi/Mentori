#!/usr/bin/env python3
"""turn_limit_note - Mentori's fixed turn-limit note, removed from an answer before concept recall (D115 L1e O-a).

Why. When the RLM reaches its turn cap with a report, Mentori returns the report with a fixed note appended
(TURN_LIMIT_NOTE, experiments/mentori/backend/retrieval/rlm/orchestrator.py:32, appended at :347) and its run record
flags it: turn_limit_note True in the RLM metadata (exp_01 stores it at generation.rlm.metadata.turn_limit_note, the
depth sweep at rlm.turn_limit_note). The note's words are not the model's, and the word matchers of concept recall
could find a key concept in them. D115 L1e O-a (Valerio, 22 October): concept recall removes the note exactly before
matching; the judge keeps it (D68 Q11), so this module is for concept recall only.

strip(answer, flagged) is the rule. When flagged is True (the bool, nothing else), the answer must end with NOTE and
that one trailing copy is removed; a flagged answer that does not end with NOTE raises NoteMismatch (the record and the
text disagree, and nothing is guessed). When flagged is anything else the answer is returned unchanged, even when it
holds the note's words: a submitted record carries the same text with no flag (S438_depth_log_recovery.py:189), and
D115 removes the note only where a record flags it.

    uv run --no-sync python scripts/turn_limit_note.py      runs spec_failures(): the rule's cases, and NOTE against
                                                             the orchestrator's TURN_LIMIT_NOTE

Callers: scripts/S471_l3_concept_recall.py (L3), findings/recompute/G5_runs/g5_faults.py (G5's unscorable count).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = ROOT / "experiments" / "mentori" / "backend" / "retrieval" / "rlm" / "orchestrator.py"
NOTE = "\n\n---\n*Note: Analysis reached turn limit. Results may be incomplete.*"


class NoteMismatch(ValueError):
    """A record flags the note and its answer does not end with it."""


def strip(answer: str, flagged) -> tuple[str, bool]:
    """(the text concept recall reads, whether the note was removed). The module docstring states the rule."""
    if flagged is not True:
        return answer, False
    if not answer.endswith(NOTE):
        raise NoteMismatch(f"the record flags turn_limit_note but the answer does not end with the note "
                           f"(it ends {answer[-60:]!r})")
    return answer[:-len(NOTE)], True


def orchestrator_note(path: Path = ORCHESTRATOR):
    """TURN_LIMIT_NOTE as the orchestrator's source assigns it (read with ast; the backend is not imported)."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "TURN_LIMIT_NOTE" for t in node.targets):
            return ast.literal_eval(node.value)
    return None


# (answer, flagged, the text expected, removed expected); None for the text: NoteMismatch expected
SPEC_CASES = [
    ("The report." + NOTE, True, "The report.", True),                  # flagged, the note at the end: removed
    ("The report." + NOTE, False, "The report." + NOTE, False),          # not flagged: unchanged
    ("The report." + NOTE, None, "The report." + NOTE, False),           # no flag recorded: unchanged
    ("The report." + NOTE, "true", "The report." + NOTE, False),         # a flag that is not the bool True
    ("The report." + NOTE, 1, "The report." + NOTE, False),              # 1 is not True
    ("The report.", True, None, None),                                   # flagged, no note: refused
    ("The report." + NOTE + " More.", True, None, None),                 # flagged, the note not at the end: refused
    ("The report." + NOTE.strip(), True, None, None),                    # flagged, the note without its blank lines
    ("A" + NOTE + NOTE, True, "A" + NOTE, True),                         # one trailing copy removed, no more
    ("The report.\n" + NOTE, True, "The report.\n", True),               # the report's own whitespace kept
    (NOTE, True, "", True),                                              # the note alone: an empty text
]


def spec_failures() -> list:
    """The SPEC_CASES strip gets wrong, and NOTE against the orchestrator's TURN_LIMIT_NOTE."""
    bad = []
    for answer, flagged, want_text, want_removed in SPEC_CASES:
        try:
            got = strip(answer, flagged)
        except NoteMismatch:
            got = (None, None)
        if got != (want_text, want_removed):
            bad.append(f"strip({answer[-40:]!r}, {flagged!r}) gave {got!r}, the rule says {(want_text, want_removed)!r}")
    theirs = orchestrator_note()
    if theirs != NOTE:
        bad.append(f"NOTE is not orchestrator.py's TURN_LIMIT_NOTE ({theirs!r})")
    return bad


if __name__ == "__main__":
    fails = spec_failures()
    for f in fails:
        print("  FAIL " + f)
    print(f"{len(SPEC_CASES)} of {len(SPEC_CASES)} rule cases hold; NOTE is orchestrator.py's TURN_LIMIT_NOTE"
          if not fails else f"{len(fails)} failures")
    raise SystemExit(1 if fails else 0)
