"""
LLM-based Chunk Relevance Verification

Classifies retrieved chunks as RELEVANT/PARTIAL/IRRELEVANT using a judge LLM.
Filters out noise before generation to prevent hallucination at scale.

Key design choices:
- Single batched LLM call for all chunks (not per-chunk)
- Document reinforcement: if 2+ chunks from same doc are RELEVANT, promote PARTIAL
- Every chunk is shown whole (D25: the 500-character cut is gone) and the call carries no options of its own
  (cuts.md: num_predict 5000 and temperature 0 are gone; the lock sends gpt-oss:20b's settings, Q18, D66)

Failures are recorded, never turned into verdicts (A5, records.md F17, limits #78):
- verdicts are matched to passages by their id, never by list position;
- a passage with no verdict, an unparsed reply or a label other than RELEVANT, PARTIAL or IRRELEVANT is UNVERIFIED
  with its fail_open_reason (the old code made each of these RELEVANT);
- an empty reply is status "empty" (the old code parsed the thinking text or str(response));
- a failed call returns status "error" with the call's record, every passage UNVERIFIED (limits #78; the old code
  marked every passage RELEVANT).
An UNVERIFIED passage still reaches the generator, as Mentori's fail-open sent it, and the record says why
(records.md F17: fail_open_reason). So empty, unparsed and failed are handled alike, and Q17's fallback runs only when
readable verdicts reject every passage. Q78 (D75) keeps this fail-open as Mentori built it, recorded, for a failed,
empty or unparsed reply and for a single passage the verifier skipped; verifier_status_report() counts the
verified-pass answers whose verifier status was not ok, by status, and lists them, so Figure 2's verified-pass score
can be given with and without them.
verify() returns a Verification: the per-passage verdicts, the status, the raw reply and the counts.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.agents import lock_adapter
from experiments.runner import run_context as rc

logger = logging.getLogger(__name__)

LABELS = ("RELEVANT", "PARTIAL", "IRRELEVANT")
UNVERIFIED = "UNVERIFIED"     # no verdict for the passage, or one that could not be read (A5)
# fail_open_reason of an UNVERIFIED passage (records.md F17)
FAIL_OPEN_REASONS = {"missing": "missing verdict", "label": "unknown label", "empty": "empty reply",
                     "unparsed": "unparsed reply", "error": "verifier call failed"}


@dataclass
class Verification:
    """What verify() returns: the passages with their verdicts, and what happened to the call."""
    verified: List["VerifiedChunk"]
    status: str                          # ok | length (the reply hit the context) | empty | unparsed | error
    raw_text: str = ""                   # the verifier's whole reply
    call_seq: Optional[int] = None       # the seq of its record in <sink>/calls.jsonl
    n_verdicts_parsed: int = 0
    unmatched_ids: List[Any] = field(default_factory=list)    # verdict ids naming no passage
    duplicate_ids: List[int] = field(default_factory=list)    # ids given more than one verdict (the first is used)
    call_record: Optional[Dict[str, Any]] = field(default=None, repr=False)   # the call's lock record, as written
    error: Optional[str] = None          # status error: the failed call's error (limits #78)

    def counts(self) -> Dict[str, int]:
        out = {label: 0 for label in LABELS + (UNVERIFIED,)}
        for v in self.verified:
            out[v.label] = out.get(v.label, 0) + 1
        out["promoted"] = sum(1 for v in self.verified if v.promoted)
        return out

    def to_record(self) -> Dict[str, Any]:
        """The verification as the answer stores it (records.md F17): per passage its uid, verdict id, the label as
        the model wrote it, the label used, the reason and whether reinforcement promoted it."""
        return {
            "status": self.status, "error": self.error, "call_seq": self.call_seq,
            "n_verdicts_parsed": self.n_verdicts_parsed,
            "unmatched_ids": self.unmatched_ids, "duplicate_ids": self.duplicate_ids, "counts": self.counts(),
            "raw_text": self.raw_text,
            "verdicts": [{"uid": v.chunk.get("id"), "verdict_id": i, "label_raw": v.label_raw, "label": v.label,
                          "reason": v.reason, "promoted": v.promoted, "fail_open_reason": v.fail_open_reason}
                         for i, v in enumerate(self.verified, 1)],
        }


def verifier_status_report(answers) -> Dict[str, Any]:
    """Q78 (D75): over answer records (the lines of answers.jsonl, as stored), the verified-pass answers' verifier
    status. A key's answer is its last line; earlier lines of the key are failed attempts (exp_01 appends, never
    rewrites) and are not counted, as in matched_budget.last_answers. Returns {n_verified_pass, status_counts,
    not_ok: [{answer_key, question_id, draw, status}], no_verification: [answer_key]}; status_counts counts every
    status (ok, length, empty, unparsed, error), and not_ok lists each answer whose status is not ok, so the score can
    be computed with and without them. An answer that stopped before its verifier ran has no verification and is
    listed apart."""
    last: Dict[Any, Dict[str, Any]] = {}
    for rec in answers:
        last[rec.get("answer_key")] = rec          # dict order: a key's first line; value: its last line
    counts: Dict[str, int] = {}
    not_ok, missing, n = [], [], 0
    for rec in last.values():
        gen = rec.get("generation") or {}
        if gen.get("config", rec.get("config")) != "verified_pass":
            continue
        n += 1
        status = (gen.get("verification") or {}).get("status")
        if status is None:
            missing.append(rec.get("answer_key"))
            continue
        counts[status] = counts.get(status, 0) + 1
        if status != "ok":
            not_ok.append({"answer_key": rec.get("answer_key"), "question_id": rec.get("question_id"),
                           "draw": rec.get("draw"), "status": status})
    return {"n_verified_pass": n, "status_counts": dict(sorted(counts.items())), "not_ok": not_ok,
            "no_verification": missing}


@dataclass
class VerifiedChunk:
    """A chunk with its verification verdict."""
    chunk: Dict[str, Any]
    label: str  # RELEVANT, PARTIAL, IRRELEVANT, or UNVERIFIED (no readable verdict, A5)
    reason: str = ""
    promoted: bool = False  # True if promoted from PARTIAL via document reinforcement
    label_raw: Optional[str] = None  # the label as the model wrote it; None when it gave no verdict for the passage
    fail_open_reason: Optional[str] = None  # UNVERIFIED only: why, from FAIL_OPEN_REASONS (records.md F17)


VERIFICATION_PROMPT = """You are a scientific relevance judge. Given a research question and retrieved text passages from scientific papers, classify each passage's relevance.

## Question
{query}

## Passages
{passages}

## Rules
- RELEVANT: Directly helps answer the question (specific facts, methods, results)
- PARTIAL: Useful background/context but doesn't directly answer
- IRRELEVANT: Unrelated topic, retrieved by vocabulary coincidence

## Output
JSON array, no markdown fences:
[{{"id": 1, "label": "RELEVANT", "reason": "..."}}, ...]"""


class ChunkVerifier:
    """
    Verifies chunk relevance using an LLM judge before generation.

    Usage:
        verifier = ChunkVerifier(router)
        verification = await verifier.verify(query, chunks)     # inside a run context
        relevant = verifier.filter_relevant(verification)
    """

    def __init__(
        self,
        model_router,
        model_identifier: str = "ollama::gpt-oss:20b",
    ):
        # Q18 (D68): the verifier is gpt-oss:20b, a generator component at its maker's default (D66). The
        # num_predict and max_chunk_chars parameters are gone (cuts.md chunk_verifier.py:65, :94, :108).
        self.router = model_router
        self.model_identifier = model_identifier

    async def verify(
        self, query: str, chunks: List[Dict[str, Any]]
    ) -> Verification:
        """
        Classify each chunk's relevance to the query.

        Args:
            query: The research question
            chunks: Retrieved chunks with 'id', 'text' and 'metadata' keys

        Returns:
            Verification: the passages with their labels (UNVERIFIED where no verdict could be read), the status
            and the raw reply. A failed call is status "error", every passage UNVERIFIED (limits #78, A5). A lock
            refusal (LockError, RunContextError) is not caught: it is a setup error (Q38).
        """
        if not chunks:
            return Verification(verified=[], status="ok")

        # Format passages for prompt: each passage whole (D25)
        passage_lines = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            file_name = meta.get("file_name", "unknown")
            page = meta.get("page", "?")
            text = chunk.get("text", "")
            passage_lines.append(
                f"[{i}] Source: {file_name}, Page {page}\n{text}"
            )

        passages_text = "\n\n".join(passage_lines)
        prompt = VERIFICATION_PROMPT.replace("{query}", query).replace(
            "{passages}", passages_text
        )

        # D37/A6: the call's record carries the ids of the passages in its prompt
        rc.set_passages([c.get("id") for c in chunks])
        try:
            # Role "generator" (D68 Q18): the verifier is a component of the system under test, so the lock sends
            # the model's own sampling and the run's draw and thinking.
            with lock_adapter.role("generator"):
                response = await self.router.generate(
                    model_identifier=self.model_identifier,
                    prompt=prompt,
                )
        except lock_adapter.LockCallError as e:
            # limits #78: the failed call is recorded and returned as status error; no passage gets a verdict
            logger.error(f"Verifier call failed: {e}")
            return Verification(
                verified=[VerifiedChunk(chunk=c, label=UNVERIFIED, fail_open_reason=FAIL_OPEN_REASONS["error"])
                          for c in chunks],
                status="error", error=str(e), call_seq=(e.record or {}).get("seq"), call_record=e.record or None)

        record = response.get("lock_record") or {}
        response_text = response.get("response") or ""
        if not response_text.strip():
            status = "empty"          # the thinking text is not parsed as verdicts (limits #78 added)
            verdicts, info = {}, {"n_parsed": 0, "unmatched_ids": [], "duplicate_ids": []}
        else:
            verdicts, info = self._parse_verdicts(response_text, len(chunks))
            status = "unparsed" if not info["n_parsed"] else (
                "length" if response.get("done_reason") == "length" else "ok")

        # Build VerifiedChunk list: verdict i belongs to passage [i] of the prompt, matched by id
        verified = []
        for i, chunk in enumerate(chunks, 1):
            verdict = verdicts.get(i)
            if verdict is None:
                why = FAIL_OPEN_REASONS[status if status in ("empty", "unparsed") else "missing"]
                verified.append(VerifiedChunk(chunk=chunk, label=UNVERIFIED, reason="", label_raw=None,
                                              fail_open_reason=why))
                continue
            raw = verdict.get("label")
            label = raw.strip().upper() if isinstance(raw, str) else None
            verified.append(
                VerifiedChunk(
                    chunk=chunk,
                    label=label if label in LABELS else UNVERIFIED,
                    fail_open_reason=None if label in LABELS else FAIL_OPEN_REASONS["label"],
                    reason=verdict.get("reason", "") if isinstance(verdict.get("reason", ""), str)
                    else json.dumps(verdict.get("reason")),
                    label_raw=raw if isinstance(raw, str) else json.dumps(raw),
                )
            )

        # Document reinforcement
        verified = self._apply_document_reinforcement(verified)

        result = Verification(verified=verified, status=status, raw_text=response_text,
                              call_seq=record.get("seq"), n_verdicts_parsed=info["n_parsed"],
                              unmatched_ids=info["unmatched_ids"], duplicate_ids=info["duplicate_ids"],
                              call_record=record or None)

        # Log stats
        c = result.counts()
        logger.info(
            f"Verification ({status}): {c['RELEVANT']} relevant, {c['PARTIAL']} partial, "
            f"{c['IRRELEVANT']} irrelevant, {c[UNVERIFIED]} unverified (out of {len(verified)} chunks)"
        )

        return result

    def filter_relevant(
        self, verified: List[VerifiedChunk], include_partial: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter to only relevant chunks. An UNVERIFIED passage is kept (fail-open as Mentori built it, with its
        fail_open_reason recorded; records.md F17), so only a passage the verifier read and labelled IRRELEVANT
        (or PARTIAL without include_partial) is dropped.

        Args:
            verified: Output from verify()
            include_partial: If True, also include PARTIAL chunks

        Returns:
            List of chunk dicts (same format as input to verify)
        """
        accepted = {"RELEVANT", UNVERIFIED}
        if include_partial:
            accepted.add("PARTIAL")

        if isinstance(verified, Verification):
            verified = verified.verified
        return [v.chunk for v in verified if v.label in accepted]

    def _parse_verdicts(
        self, text: str, expected_count: int
    ) -> tuple:
        """Parse LLM verdict JSON, with regex fallback. Returns ({id: verdict}, info): each verdict keyed by the
        passage number it names (1 to expected_count), the first one where an id repeats; info holds n_parsed,
        unmatched_ids (ids naming no passage, or not integers) and duplicate_ids. Labels are not validated here:
        verify() makes any label other than the three UNVERIFIED, on both paths alike (records.md F17)."""
        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.replace("```", "")

        items: List[Dict[str, Any]] = []
        # Try JSON array extraction
        array_match = re.search(r"\[[\s\S]*\]", cleaned)
        if array_match:
            try:
                data = json.loads(array_match.group())
                if isinstance(data, list):
                    items = [d for d in data if isinstance(d, dict)]
            except json.JSONDecodeError:
                pass

        if not items:
            # Fallback: extract individual verdict objects
            pattern = r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"label"\s*:\s*"(\w+)"'
            for match in re.finditer(pattern, cleaned):
                chunk_id = int(match.group(1))
                reason_match = re.search(
                    rf'"id"\s*:\s*{chunk_id}[^}}]*"reason"\s*:\s*"([^"]*)"',
                    cleaned,
                )
                items.append({
                    "id": chunk_id,
                    "label": match.group(2),
                    "reason": reason_match.group(1) if reason_match else "",
                })

        verdicts: Dict[int, Dict[str, Any]] = {}
        unmatched, duplicates = [], []
        for item in items:
            vid = item.get("id")
            if isinstance(vid, str) and vid.strip().isdigit():
                vid = int(vid.strip())
            if isinstance(vid, bool) or not isinstance(vid, int) or not 1 <= vid <= expected_count:
                unmatched.append(vid)
            elif vid in verdicts:
                duplicates.append(vid)
            else:
                verdicts[vid] = item
        if not verdicts:
            # No readable verdict: every passage is UNVERIFIED, recorded as unparsed (A5, F17); the old code made
            # every one RELEVANT
            logger.warning("Could not parse verification response: every passage is UNVERIFIED")
        return verdicts, {"n_parsed": len(verdicts), "unmatched_ids": unmatched, "duplicate_ids": duplicates}

    def _apply_document_reinforcement(
        self, verified: List[VerifiedChunk]
    ) -> List[VerifiedChunk]:
        """
        Promote PARTIAL chunks from documents that have 2+ RELEVANT chunks.

        Rationale: if multiple chunks from a document are relevant, the
        document itself is on-topic, and PARTIAL chunks likely contain
        useful context.
        """
        # Count RELEVANT chunks per source document
        doc_relevant_count: Dict[str, int] = {}
        for v in verified:
            if v.label == "RELEVANT":
                source = v.chunk.get("metadata", {}).get(
                    "file_name", v.chunk.get("metadata", {}).get("file_path", "unknown")
                )
                doc_relevant_count[source] = doc_relevant_count.get(source, 0) + 1

        # Promote PARTIAL chunks from docs with 2+ relevant
        reinforced_docs = {doc for doc, count in doc_relevant_count.items() if count >= 2}
        if not reinforced_docs:
            return verified

        for v in verified:
            if v.label == "PARTIAL":
                source = v.chunk.get("metadata", {}).get(
                    "file_name", v.chunk.get("metadata", {}).get("file_path", "unknown")
                )
                if source in reinforced_docs:
                    v.label = "RELEVANT"
                    v.promoted = True
                    logger.debug(f"Promoted PARTIAL chunk from {source} to RELEVANT")

        promoted_count = sum(1 for v in verified if v.promoted)
        if promoted_count:
            logger.info(f"Document reinforcement: promoted {promoted_count} PARTIAL chunks")

        return verified
