"""S141 step 1.1 — the arm store: per-arm directories, atomic writes, four-part resume keys.

Gate P19, and the reason it exists. The archived runner resumes on
`result_key(config, question_id)` (`exp_v4_common.result_key`), which contains neither the generator
nor the seed, and it rewrites one fixed intermediate file whole. Three arms running at once would
read each other's rows as their own, skip work they had never done, overwrite each other's output,
and report success. Downstream, `S03_master_join.py` joins on `(question_id, config)`, which cannot
separate six generators either.

So this module is not a convenience layer. It is the fix, and every element of it is load-bearing:

  per-arm directory   keyed (generator, seed, run_id) — two arms cannot address the same file
  four-part key       (question_id, config, gen_model, seed) — resume and join cannot confuse arms
  os.replace          atomic rename; a killed process leaves either the old row or the new, never half
  one file per row    a crash cannot corrupt rows that were already written
  no shared _latest   nothing outside the arm directory is written during a run

Rule 3 from `S141_RUN_REQUIREMENTS.md` — never write a number the runner did not measure — is
enforced here rather than left to callers, because the archive's characteristic failure is a zero or
a default substituted for a missing value with nothing recorded. `validate_row` refuses such rows.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

# ── Provenance vocabulary ────────────────────────────────────────────────────
# Every quantity that could be absent carries one of these. "absent" is a first-class value: it is
# what the archive wrote as 0 and is the distinction P24 turns on.
MEASURED = "measured"      # the provider returned every part and the identity closes
PARTIAL = "partial"        # the provider returned some parts and omitted others
CONSTANT = "constant"      # a declared constant, not a measurement (e.g. llm_calls for a fixed path)
DERIVED = "derived"        # computed from measured quantities, formula recorded
ABSENT = "absent"          # the provider did not return it. NOT zero.
PROVENANCE = {MEASURED, PARTIAL, CONSTANT, DERIVED, ABSENT}

# PARTIAL exists because of a measured case, not a hypothetical one: `gemini-3.6-flash` returned the
# text "OK" while omitting `candidatesTokenCount` entirely, on 2 of 20 calls with thinking enabled.
# The archived client reads that field as `getattr(um, "candidates_token_count", 0) or 0`
# (gemini.py:184), so it would store a real answer as zero output tokens. Collapsing "absent" into
# either "measured" or "zero" is exactly the failure Rule 3 exists to prevent, so it gets its own
# label and the identity check is skipped rather than forced.

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(value: str) -> str:
    """Model tags carry ':' and '/', which are not portable in path components."""
    return _SAFE.sub("-", value).strip("-")


def result_key(question_id: str, config: str, gen_model: str, seed: int | None) -> str:
    """The four-part key. All four parts, always, including when seed is None.

    The archive's two-part key is the defect; an unseeded cloud arm still needs its seed slot filled
    so that a seeded and an unseeded row can never collide on the same string.
    """
    return f"{question_id}|{config}|{gen_model}|{'none' if seed is None else seed}"


@dataclass(frozen=True)
class ArmKey:
    """One arm: one generator, one seed, one run. The unit of isolation."""

    gen_model: str
    seed: int | None
    run_id: str

    @property
    def dirname(self) -> str:
        return f"{_slug(self.gen_model)}__seed-{'none' if self.seed is None else self.seed}__{_slug(self.run_id)}"

    def as_dict(self) -> dict[str, Any]:
        return {"gen_model": self.gen_model, "seed": self.seed, "run_id": self.run_id}


class RowInvalid(Exception):
    """Raised instead of writing a row that breaks Rule 3."""


def validate_row(row: dict[str, Any]) -> None:
    """Structural enforcement of Rule 3. Raises RowInvalid rather than writing a bad row.

    These are the archive's actual failure modes, each turned into a refusal:
      - a score written when the judge errored (four zeros, `exp_common.py:405-418`)
      - a token count that is a word count or a constant, with nothing saying so (`exp1:228,333`)
      - an empty error string, which every aggregator reads as success (229 deposited rows)
      - `prompt + completion != total`, which on Gemini means reasoning tokens went unrecorded
    """
    for f in ("question_id", "config", "gen_model", "seed", "run_id"):
        if f not in row:
            raise RowInvalid(f"missing required field: {f}")

    # An error must be nameable. "" is the deposit's silent-success bug.
    if "error" in row and row["error"] is not None:
        if not str(row.get("error")).strip():
            raise RowInvalid("empty error string: write a non-empty error class or no error field")
        if row.get("judge_scores") not in (None, {}):
            raise RowInvalid("row carries both an error and judge scores")

    # Judge scores are never zero-filled. A dimension the parser could not find is None.
    scores = row.get("judge_scores")
    if isinstance(scores, dict):
        status = row.get("judge_status")
        if status not in (None, "ok"):
            raise RowInvalid(f"judge_status={status!r} must not carry scores")
        if scores and all(v == 0 for v in scores.values()):
            # An all-zero verdict is refused only when nothing shows the judge produced it.
            #
            # The first version of this rule refused every all-zero block, which is the inverse of
            # the archive's defect and just as damaging: the deposit contains 19 rows the judge
            # genuinely scored 0/0/0/0, with justifications explaining why ("does not provide any
            # factual information … only a repetitive search query"), 16 of them multi_hop. P12's
            # multi_hop target is 68/88, so silently refusing those rows would have moved the
            # denominator of the gate that decides whether the campaign starts.
            #
            # The distinction is provenance, not value. This runner's parser returns None for a
            # dimension it cannot find, so a 0 can only have come from the model — but only if the
            # row carries evidence of a successful parse. A row without that evidence was built by
            # something else, and for that the archive's zero-fill is the likelier explanation.
            parse_mode = row.get("judge_parse_mode")
            if parse_mode not in ("json", "regex"):
                raise RowInvalid(
                    "all-zero judge scores with no parse evidence "
                    f"(judge_parse_mode={parse_mode!r}): use None per dimension and judge_status. "
                    "A genuine all-zero verdict must carry the parse mode that produced it"
                )

    # Every countable quantity declares where it came from.
    for name in ("tokens", "llm_calls", "retrieval_calls"):
        block = row.get(name)
        if block is None:
            continue
        if not isinstance(block, dict) or "provenance" not in block:
            raise RowInvalid(f"{name} must be a dict carrying a 'provenance' key")
        prov = block["provenance"]
        if prov not in PROVENANCE:
            raise RowInvalid(f"{name}.provenance={prov!r} not one of {sorted(PROVENANCE)}")
        if prov == ABSENT and any(
            v is not None for k, v in block.items() if k != "provenance"
        ):
            raise RowInvalid(f"{name}.provenance='absent' but values are present")

    # P7, extended for reasoning tokens: the identity must close where it is claimed to be measured.
    tk = row.get("tokens")
    if isinstance(tk, dict) and tk.get("provenance") == MEASURED:
        parts = [tk.get("prompt"), tk.get("completion"), tk.get("total")]
        if any(p is None for p in parts):
            raise RowInvalid(
                "tokens.provenance='measured' requires prompt, completion and total. "
                "Use 'partial' when the provider omitted one"
            )
        reasoning = tk.get("reasoning") or 0
        if tk["prompt"] + tk["completion"] + reasoning != tk["total"]:
            raise RowInvalid(
                f"token identity does not close: {tk['prompt']} + {tk['completion']} "
                f"+ {reasoning} != {tk['total']}. On Gemini this means reasoning tokens "
                f"were not recorded"
            )
    if isinstance(tk, dict) and tk.get("provenance") == PARTIAL:
        # Partial must name what is missing, or it is indistinguishable from carelessness.
        if not tk.get("missing"):
            raise RowInvalid("tokens.provenance='partial' requires a 'missing' list naming the "
                             "fields the provider omitted")


@dataclass
class ArmStore:
    """One arm's directory. Nothing outside it is written while the arm runs."""

    root: Path
    arm: ArmKey
    _seen: set[str] = field(default_factory=set, init=False)

    @property
    def path(self) -> Path:
        return self.root / self.arm.dirname

    def ensure_empty(self) -> None:
        """P19: the arm directory must be empty before an arm starts.

        A non-empty directory means either a previous run of this exact arm (resume, which must be
        explicit) or — the dangerous case — another arm writing into the same place.
        """
        if self.path.exists() and any(self.path.iterdir()):
            raise RowInvalid(
                f"arm directory not empty: {self.path}. Resume explicitly with load_existing(), "
                f"or choose a fresh run_id. Never write into a populated arm directory."
            )
        self.path.mkdir(parents=True, exist_ok=True)

    def load_existing(self) -> int:
        """Resume: read back what this arm already has, keyed four ways."""
        self.path.mkdir(parents=True, exist_ok=True)
        for row in self.read_rows():
            self._seen.add(
                result_key(row["question_id"], row["config"], row["gen_model"], row["seed"])
            )
        return len(self._seen)

    def has(self, question_id: str, config: str) -> bool:
        """Resume test. Uses the arm's own generator and seed, so it cannot match another arm."""
        return result_key(question_id, config, self.arm.gen_model, self.arm.seed) in self._seen

    def _row_path(self, key: str) -> Path:
        # Hash rather than sanitise: question ids and configs are free-form, and a collision here
        # would silently overwrite a result.
        return self.path / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"

    def write_row(self, row: dict[str, Any]) -> Path:
        """Atomic single-row write. Validated first; a bad row raises rather than lands."""
        row = {**row, **self.arm.as_dict()}
        validate_row(row)
        key = result_key(row["question_id"], row["config"], row["gen_model"], row["seed"])
        target = self._row_path(key)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({**row, "_key": key}, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, target)          # atomic within a filesystem; never a half-written row
        self._seen.add(key)
        return target

    def read_rows(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        for p in sorted(self.path.glob("*.json")):
            yield json.loads(p.read_text())

    def count(self) -> int:
        return sum(1 for _ in self.read_rows())


def join_rows(stores: Iterable[ArmStore]) -> list[dict[str, Any]]:
    """Join on the four-part key. Raises on collision rather than silently keeping one row.

    The archive's join is on `(question_id, config)`, which maps six generators onto one row and
    reports the last writer's value. P19 asserts `len(join) == len(inputs)`, which is only true if
    the key separates every arm.
    """
    out: dict[str, dict[str, Any]] = {}
    for store in stores:
        for row in store.read_rows():
            key = row.get("_key") or result_key(
                row["question_id"], row["config"], row["gen_model"], row["seed"]
            )
            if key in out:
                raise RowInvalid(f"join collision on {key}: two rows claim the same arm and question")
            out[key] = row
    return list(out.values())
