"""S141 step 1.4 — one judge, two settings, and a parser that never invents a score.

There are three judge implementations in the archive, at three different option sets:
`tests/experiments_v4/exp_common.py` (qwen3-coder, 8192/16384, think False — the one that produced
exp04), `tests/experiments/exp_common.py` (gpt-oss:20b, num_predict 4000, think "medium", no
num_ctx), and a dead copy at `exp1_rlm_vs_singlepass.py:545`. Having three is how the wrong one gets
used; this module is the only judge the runner has, and the arm chooses its settings.

The two settings, and why both must exist:

    new arms                 truncate_chars=None,  num_ctx 40960, num_predict 1024
    archive-replication arm  truncate_chars=3000,  the archived settings

Getting these backwards fails a gate in either direction. Remove the cut in the replication arm and
the six published cells stop reproducing; keep it in the P12 arm and P12 fails on multi_hop and
rlm_10 — measured: 4 multi_hop rows in exp04 have full-answer prompts above the 8,192-token budget
that `num_predict 8192` leaves inside a 16,384 window, so P12 and P4 are one gate.

Three defects are fixed here rather than reproduced:

  zero-fill      `scores[dim] = ... if match else 0` (`exp_common.py:437,449`) makes an unparseable
                 dimension indistinguishable from a genuine 0. The parser returns None.
  four zeros     the exception handler (`:405-418`) writes 0/0/0/0 with a justification string, so a
                 crashed call scores worse than a wrong answer. Errors carry judge_status, no score.
  flat-brace JSON `re.search(r'\\{[^{}]*\\}')` (`executor.py:419`) cannot match nested objects and
                 silently returns the innermost one. This uses a balanced scan.

The out-of-domain prompt scores three dimensions, not four. Section 2 of the pre-registration says
"all four dimensions", which is true of 88 questions and wrong for the 50 in every main arm.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .providers import CallRecord, OllamaProvider
from .store import ABSENT, MEASURED

# The repository's copy of the archived harness file, so the judge runs on any machine. It was read from
# /Users/bioinfo-001/projects/Mentori (Mac Studio only) until 9 October; the two are byte-identical, and the
# hash below stops a run if the copy ever changes.
V4_COMMON = Path(__file__).resolve().parents[2] / "recovered_harness/tests/experiments_v4/exp_common.py"
V4_COMMON_SHA256 = "9ed9fb531789f788d24b616603e603a2d47dd0debe9abfb88658213451bb5c83"

ANSWERABLE_DIMS = ("correctness", "completeness", "faithfulness", "citation_quality")
UNANSWERABLE_DIMS = ("refusal_accuracy", "hallucination_avoidance", "explanation_quality")

# The settings that produced P12's targets (S21 arm F). Using them verbatim keeps P12 free of a new
# variable; `num_predict` 1024 clears the longest measured judge output (243 tokens) 4x over.
NEW_ARM = {"temperature": 0, "num_predict": 1024, "num_ctx": 40960}
# gpt-oss needs more: at 1024 its 20b sibling capped on 13 of 827 calls.
ROBUSTNESS_ARM = {"temperature": 0, "num_predict": 8192, "num_ctx": 40960}
# Exactly what the archive sent, for the replication arm only.
ARCHIVE_ARM = {"temperature": 0, "num_predict": 8192, "num_ctx": 16384}


def _template(name: str) -> str:
    """Read the prompt out of the archive rather than restating it, so it cannot drift."""
    raw = V4_COMMON.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V4_COMMON_SHA256:
        raise RuntimeError(f"{V4_COMMON} is not the archived harness file (sha256 differs)")
    src = raw.decode()
    marker = f"{name} = "
    start = src.index(marker) + len(marker)
    body = src.index('"""', start) + 3
    return src[body:src.index('"""', body)]


def build_prompt(question: str, expected: str, concepts: Any, generated: str,
                 answerable: bool, truncate_chars: int | None) -> str:
    """The archived construction (`exp_common.py:378-388`), with the cut made explicit.

    `truncate_chars=None` is the new-arm setting and honours the letter's promise that every
    evaluation signal reads the complete answer.
    """
    if answerable:
        p = _template("ANSWERABLE_JUDGE_PROMPT")
        text = ", ".join(concepts) if concepts else "N/A"
        p = p.replace("{question}", question).replace("{expected_answer}", expected)
        p = p.replace("{expected_concepts}", text)
    else:
        p = _template("UNANSWERABLE_JUDGE_PROMPT").replace("{question}", question)
    answer = generated if truncate_chars is None else generated[:truncate_chars]
    return p.replace("{generated_answer}", answer)


def _balanced_json(text: str) -> dict | None:
    """First balanced {...} object, tolerating nesting. The archive's flat regex cannot."""
    depth = start = 0
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def parse_scores(text: str, answerable: bool = True) -> tuple[dict[str, int | None], str]:
    """Return (scores, parse_mode). A dimension the parser cannot find is None, never 0."""
    dims = ANSWERABLE_DIMS if answerable else UNANSWERABLE_DIMS
    obj = _balanced_json(text or "")
    scores: dict[str, int | None] = {d: None for d in dims}
    mode = "none"

    if isinstance(obj, dict):
        mode = "json"
        for d in dims:
            v = obj.get(d)
            scores[d] = int(v) if isinstance(v, (int, float)) else None
        if "justification" in obj:
            scores["justification"] = obj.get("justification")  # text, not a score

    if all(scores.get(d) is None for d in dims):
        # Fall back to the archive's regex route, still without zero-filling.
        mode = "regex" if text else "none"
        for d in dims:
            m = re.search(rf'"{d}"\s*:\s*(\d+)', text or "")
            scores[d] = int(m.group(1)) if m else None

    return scores, mode


@dataclass
class JudgeResult:
    judge_status: str                 # ok | unparseable | empty | error
    scores: dict[str, int | None] = field(default_factory=dict)
    parse_mode: str = "none"
    truncate_chars: int | None = None
    prompt_chars: int = 0
    attempts: int = 1
    error_class: str | None = None
    call: CallRecord | None = None

    def as_row_fields(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "judge_status": self.judge_status,
            "judge_truncate_chars": self.truncate_chars,
            "judge_prompt_chars": self.prompt_chars,
            "judge_parse_mode": self.parse_mode,
            "judge_attempts": self.attempts,
        }
        # Rule 3: scores exist only when the judge actually produced them.
        if self.judge_status == "ok":
            out["judge_scores"] = {k: v for k, v in self.scores.items() if k != "justification"}
            out["judge_justification"] = self.scores.get("justification")
        if self.error_class:
            out["judge_error_class"] = self.error_class
        if self.call is not None:
            out["judge_tokens"] = self.call.tokens
            out["judge_latency_s"] = round(self.call.latency_s, 3)
            out["judge_finish_reason"] = self.call.finish_reason
            out["judge_length_capped"] = self.call.length_capped
        return out


@dataclass
class Judge:
    """One judge. The arm supplies the options and the truncation, and both are recorded per row."""

    provider: OllamaProvider
    model: str
    options: dict[str, Any]
    truncate_chars: int | None = None
    think: bool = False

    def score(self, question: str, expected: str, concepts: Any, generated: str,
              answerable: bool = True, timeout: float = 900.0) -> JudgeResult:
        if not (generated or "").strip():
            # An empty answer is not a zero-scoring answer; it is an unscorable row.
            return JudgeResult("empty", truncate_chars=self.truncate_chars)

        prompt = build_prompt(question, expected, concepts, generated, answerable,
                              self.truncate_chars)

        last: CallRecord | None = None
        for attempt in (1, 2):          # retried once, then unscored — never zero-filled
            call = self.provider.generate(self.model, prompt, self.options,
                                          think=self.think, timeout=timeout)
            last = call
            if not call.ok:
                if attempt == 2:
                    return JudgeResult("error", truncate_chars=self.truncate_chars,
                                       prompt_chars=len(prompt), attempts=attempt,
                                       error_class=call.error, call=call)
                continue
            scores, mode = parse_scores(call.text or "", answerable)
            dims = ANSWERABLE_DIMS if answerable else UNANSWERABLE_DIMS
            if any(scores.get(d) is not None for d in dims):
                return JudgeResult("ok", scores=scores, parse_mode=mode,
                                   truncate_chars=self.truncate_chars,
                                   prompt_chars=len(prompt), attempts=attempt, call=call)
            if attempt == 2:
                return JudgeResult("unparseable", scores=scores, parse_mode=mode,
                                   truncate_chars=self.truncate_chars,
                                   prompt_chars=len(prompt), attempts=attempt, call=call)
        return JudgeResult("error", truncate_chars=self.truncate_chars,
                           error_class="unreachable", call=last)


def for_new_arm(base_url: str, model: str = "qwen3-coder:30b") -> Judge:
    return Judge(OllamaProvider(base_url), model, dict(NEW_ARM), truncate_chars=None)


def for_archive_replication(base_url: str, model: str = "qwen3-coder:30b") -> Judge:
    return Judge(OllamaProvider(base_url), model, dict(ARCHIVE_ARM), truncate_chars=3000)


def for_robustness(base_url: str, model: str = "gpt-oss:120b") -> Judge:
    return Judge(OllamaProvider(base_url), model, dict(ROBUSTNESS_ARM), truncate_chars=None)
