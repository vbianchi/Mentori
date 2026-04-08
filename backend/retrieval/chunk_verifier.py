"""
LLM-based Chunk Relevance Verification

Classifies retrieved chunks as RELEVANT/PARTIAL/IRRELEVANT using a judge LLM.
Filters out noise before generation to prevent hallucination at scale.

Key design choices:
- Single batched LLM call for all chunks (not per-chunk)
- Document reinforcement: if 2+ chunks from same doc are RELEVANT, promote PARTIAL
- Truncates chunk text to 500 chars to fit 15 chunks in context
- num_predict=5000 for thinking models (gpt-oss:20b uses invisible thinking tokens)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VerifiedChunk:
    """A chunk with its verification verdict."""
    chunk: Dict[str, Any]
    label: str  # RELEVANT, PARTIAL, IRRELEVANT
    reason: str = ""
    promoted: bool = False  # True if promoted from PARTIAL via document reinforcement


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
        verified = await verifier.verify(query, chunks)
        relevant = verifier.filter_relevant(verified)
    """

    def __init__(
        self,
        model_router,
        model_identifier: str = "ollama::gpt-oss:20b",
        num_predict: int = 5000,
        max_chunk_chars: int = 500,
    ):
        self.router = model_router
        self.model_identifier = model_identifier
        self.num_predict = num_predict
        self.max_chunk_chars = max_chunk_chars

    async def verify(
        self, query: str, chunks: List[Dict[str, Any]]
    ) -> List[VerifiedChunk]:
        """
        Classify each chunk's relevance to the query.

        Args:
            query: The research question
            chunks: Retrieved chunks with 'text' and 'metadata' keys

        Returns:
            List of VerifiedChunk with labels
        """
        if not chunks:
            return []

        # Format passages for prompt
        passage_lines = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            file_name = meta.get("file_name", "unknown")
            page = meta.get("page", "?")
            text = chunk.get("text", "")[:self.max_chunk_chars]
            passage_lines.append(
                f"[{i}] Source: {file_name}, Page {page}\n{text}"
            )

        passages_text = "\n\n".join(passage_lines)
        prompt = VERIFICATION_PROMPT.replace("{query}", query).replace(
            "{passages}", passages_text
        )

        try:
            response = await self.router.generate(
                model_identifier=self.model_identifier,
                prompt=prompt,
                options={"temperature": 0, "num_predict": self.num_predict},
            )

            response_text = response.get(
                "response", response.get("message", {}).get("content", "")
            )
            if not response_text:
                # Thinking models may put output in thinking field
                response_text = response.get("thinking", str(response))

            verdicts = self._parse_verdicts(response_text, len(chunks))

        except Exception as e:
            logger.error(f"Verification LLM call failed: {e}")
            # On failure, treat all as RELEVANT (fail open)
            verdicts = [
                {"id": i + 1, "label": "RELEVANT", "reason": "verification failed"}
                for i in range(len(chunks))
            ]

        # Build VerifiedChunk list
        verified = []
        for i, chunk in enumerate(chunks):
            verdict = verdicts[i] if i < len(verdicts) else {
                "label": "RELEVANT", "reason": "missing verdict"
            }
            verified.append(
                VerifiedChunk(
                    chunk=chunk,
                    label=verdict.get("label", "RELEVANT").upper(),
                    reason=verdict.get("reason", ""),
                )
            )

        # Document reinforcement
        verified = self._apply_document_reinforcement(verified)

        # Log stats
        labels = [v.label for v in verified]
        logger.info(
            f"Verification: {labels.count('RELEVANT')} relevant, "
            f"{labels.count('PARTIAL')} partial, "
            f"{labels.count('IRRELEVANT')} irrelevant "
            f"(out of {len(verified)} chunks)"
        )

        return verified

    def filter_relevant(
        self, verified: List[VerifiedChunk], include_partial: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter to only relevant chunks.

        Args:
            verified: Output from verify()
            include_partial: If True, also include PARTIAL chunks

        Returns:
            List of chunk dicts (same format as input to verify)
        """
        accepted = {"RELEVANT"}
        if include_partial:
            accepted.add("PARTIAL")

        return [v.chunk for v in verified if v.label in accepted]

    def _parse_verdicts(
        self, text: str, expected_count: int
    ) -> List[Dict[str, Any]]:
        """Parse LLM verdict JSON, with regex fallback."""
        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.replace("```", "")

        # Try JSON array extraction
        array_match = re.search(r"\[[\s\S]*\]", cleaned)
        if array_match:
            try:
                data = json.loads(array_match.group())
                if isinstance(data, list):
                    # Sort by id to ensure correct order
                    data.sort(key=lambda x: x.get("id", 0))
                    return data
            except json.JSONDecodeError:
                pass

        # Fallback: extract individual verdict objects
        verdicts = []
        pattern = r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"label"\s*:\s*"(\w+)"'
        for match in re.finditer(pattern, cleaned):
            chunk_id = int(match.group(1))
            label = match.group(2).upper()
            if label not in ("RELEVANT", "PARTIAL", "IRRELEVANT"):
                label = "RELEVANT"
            reason_match = re.search(
                rf'"id"\s*:\s*{chunk_id}[^}}]*"reason"\s*:\s*"([^"]*)"',
                cleaned,
            )
            verdicts.append({
                "id": chunk_id,
                "label": label,
                "reason": reason_match.group(1) if reason_match else "",
            })

        if verdicts:
            verdicts.sort(key=lambda x: x.get("id", 0))
            return verdicts

        # Complete failure: mark all as RELEVANT (fail open)
        logger.warning("Could not parse verification response, treating all as RELEVANT")
        return [
            {"id": i + 1, "label": "RELEVANT", "reason": "parse failure"}
            for i in range(expected_count)
        ]

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
