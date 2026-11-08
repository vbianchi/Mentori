"""
Scientific RAG Pipeline

Orchestrates the full retrieve-rerank-verify-generate flow.
Wraps SimpleRetriever with configurable widths and optional LLM verification.

Two preset configurations:
- baseline(): Current narrow pipeline (dense*30 → hybrid*20 → rerank*10 → generate)
- verified(): Wide pipeline + LLM verification (dense*100 → hybrid*50 → rerank*15 → verify → generate)

The widths reach the retriever (Q16, D68: before, only rerank_top_k did, so the verified pass ran 45/30/15) and the
result records the widths the retriever used. Passages go to the verifier and the generator whole (D25); the calls
carry no options (the lock's settings, D53) and their records carry the passage ids (rc.set_passages, D37). When the
verifier keeps no passage, generation falls back to the first VERIFY_FALLBACK_N reranked passages (Q17, D68) and the
result says so. A failed verifier or generator call is the result's error, never its answer (A5).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.agents import lock_adapter
from backend.retrieval.chunk_verifier import ChunkVerifier
from backend.retrieval.reranker import CrossEncoderReranker, get_reranker

from experiments.runner import run_context as rc

logger = logging.getLogger(__name__)

VERIFY_FALLBACK_N = 5   # Q17 (D68): the submitted design's fallback when the verifier keeps no passage, recorded


def call_summary(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The fields of a lock_adapter call record an answer keeps beside calls.jsonl (D37): which record (seq), the
    model and role, how it ended, its tokens (thinking where the provider counts it apart) and its time."""
    if not record:
        return None
    keys = ("seq", "model", "role", "provider", "status", "stop_reason", "prompt_tokens", "output_tokens",
            "thinking_tokens", "wall_s", "waited_for_server_s", "error")
    out = {k: record.get(k) for k in keys}
    out["n_passages"] = len(record["passages"]) if isinstance(record.get("passages"), list) else None
    return out


GENERATION_PROMPT = """You are a scientific research assistant. Based ONLY on the following retrieved passages, answer the question. If the passages don't contain enough information, say so clearly.

Cite sources using the format [source_file:page_number] for every factual claim.

## Retrieved Passages

{passages}

## Question

{question}

## Answer
"""


@dataclass
class PipelineConfig:
    """Configuration for the RAG pipeline."""

    # Retrieval widths
    dense_top_k: int = 100
    hybrid_top_k: int = 50
    rerank_top_k: int = 15

    # Verification (Q18, D68: gpt-oss:20b at its maker's default; verify_num_predict 5000 is gone, cuts.md)
    use_verification: bool = True
    verify_model: str = "ollama::gpt-oss:20b"

    # Generation (gen_num_predict 4000 and gen_temperature 0.1 are gone: the lock's settings, cuts.md pipeline.py:55)
    gen_model: str = "ollama::qwen3-coder:latest"

    @classmethod
    def baseline(cls) -> "PipelineConfig":
        """Current narrow pipeline, no verification."""
        return cls(
            dense_top_k=30,
            hybrid_top_k=20,
            rerank_top_k=10,
            use_verification=False,
        )

    @classmethod
    def verified(cls) -> "PipelineConfig":
        """Wide pipeline with LLM verification gate."""
        return cls(
            dense_top_k=100,
            hybrid_top_k=50,
            rerank_top_k=15,
            use_verification=True,
        )


@dataclass
class PipelineResult:
    """Result from a pipeline run."""

    answer: str
    chunks_retrieved: int
    chunks_after_rerank: int
    chunks_after_verify: int
    chunks_used: int  # Final count fed to generator
    latency_s: float
    retrieval_latency_s: float
    verify_latency_s: float
    generation_latency_s: float
    verified_chunks: Optional[List[Dict]] = None    # the passages given to the generator, whole (cuts.md :239)
    error: Optional[str] = None
    verify_fallback: bool = False                   # Q17: the verifier kept none, the first 5 reranked were used
    verification: Optional[Dict] = None             # Verification.to_record(): status, counts, per-passage verdicts
    retrieval: Optional[Dict] = None                # the retriever's record: widths used, query_type, reranked
    passages: Optional[List[str]] = None            # the passage ids in the generation prompt (D37)
    calls: List[Dict] = field(default_factory=list) # call_summary() of the verifier's and the generator's calls


class ScientificRAGPipeline:
    """
    Full retrieve-rerank-verify-generate pipeline.

    Usage:
        pipeline = ScientificRAGPipeline(retriever, collection, router)
        result = await pipeline.answer(query)
    """

    def __init__(
        self,
        retriever,
        collection_name: str,
        model_router,
        config: Optional[PipelineConfig] = None,
    ):
        self.retriever = retriever
        self.collection_name = collection_name
        self.router = model_router
        self.config = config or PipelineConfig.verified()

        # Initialize verifier if needed
        self._verifier = None
        if self.config.use_verification:
            self._verifier = ChunkVerifier(
                model_router=model_router,
                model_identifier=self.config.verify_model,
            )

    async def retrieve_and_verify(
        self, query: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve, rerank, and optionally verify chunks.

        Returns:
            (chunks, stats) where chunks are the final filtered list
            and stats contains timing/count information.
        """
        stats = {
            "dense_top_k": self.config.dense_top_k,
            "hybrid_top_k": self.config.hybrid_top_k,
            "rerank_top_k": self.config.rerank_top_k,
            "use_verification": self.config.use_verification,
        }

        t0 = time.time()

        # Step 1: Broad retrieval (dense + hybrid + rerank handled by retriever). Q16 (D68): the configured dense and
        # fused widths reach the retriever; the record keeps the widths it used.
        trace: List[Dict[str, Any]] = []
        chunks = self.retriever.retrieve(
            query=query,
            top_k=self.config.rerank_top_k,
            collection_name=self.collection_name,
            dense_top_k=self.config.dense_top_k,
            hybrid_top_k=self.config.hybrid_top_k,
            trace=trace,
        )

        retrieval_time = time.time() - t0
        stats["retrieval"] = trace[-1] if trace else None
        stats["chunks_retrieved"] = len(chunks)
        stats["retrieval_latency_s"] = round(retrieval_time, 2)
        stats["verify_fallback"] = False

        # Step 2: LLM verification (if enabled). A failed call comes back as status error with every passage
        # UNVERIFIED, which filter_relevant keeps (fail-open, recorded; limits #78, records.md F17; Q78, D75).
        verify_time = 0.0
        if self._verifier and chunks:
            t1 = time.time()
            verification = await self._verifier.verify(query, chunks)
            relevant = self._verifier.filter_relevant(verification, include_partial=False)
            verify_time = time.time() - t1

            stats["verification"] = verification.to_record()
            stats["verify_call"] = call_summary(verification.call_record)
            stats["chunks_before_verify"] = len(chunks)
            stats["chunks_after_verify"] = len(relevant)
            stats["verify_latency_s"] = round(verify_time, 2)

            # Q17 (D68): if verification kept nothing, fall back to the top reranked passages, recorded. Since
            # UNVERIFIED passages are kept, this happens only when readable verdicts reject every passage.
            if not relevant:
                logger.warning(
                    "Verification filtered all chunks, falling back to "
                    "top reranked results"
                )
                relevant = chunks[:VERIFY_FALLBACK_N]
                stats["verify_fallback"] = True

            chunks = relevant
        else:
            stats["chunks_after_verify"] = len(chunks)
            stats["verify_latency_s"] = 0.0

        stats["chunks_final"] = len(chunks)
        stats["total_latency_s"] = round(retrieval_time + verify_time, 2)

        return chunks, stats

    async def answer(self, query: str) -> PipelineResult:
        """
        Full pipeline: retrieve → rerank → verify → generate.

        Args:
            query: The research question

        Returns:
            PipelineResult with answer and diagnostics
        """
        t_start = time.time()

        def result(answer: str, stats: Dict[str, Any], chunks: Optional[List[Dict]], gen_time: float,
                   calls: List[Dict], error: Optional[str] = None) -> PipelineResult:
            return PipelineResult(
                answer=answer,
                chunks_retrieved=stats.get("chunks_retrieved", 0),
                chunks_after_rerank=stats.get("chunks_retrieved", 0),
                chunks_after_verify=stats.get("chunks_after_verify", 0),
                chunks_used=stats.get("chunks_final", 0),
                latency_s=round(time.time() - t_start, 2),
                retrieval_latency_s=stats.get("retrieval_latency_s", 0),
                verify_latency_s=stats.get("verify_latency_s", 0),
                generation_latency_s=round(gen_time, 2),
                # the passages given to the generator, whole, with their ids (cuts.md pipeline.py:239, D37)
                verified_chunks=None if chunks is None else [
                    {
                        "id": c.get("id"),
                        "text": c.get("text", ""),
                        "source": c.get("metadata", {}).get("file_name", "unknown"),
                        "page": c.get("metadata", {}).get("page", "?"),
                    }
                    for c in chunks
                ],
                error=error,
                verify_fallback=bool(stats.get("verify_fallback")),
                verification=stats.get("verification"),
                retrieval=stats.get("retrieval"),
                passages=None if chunks is None else [c.get("id") for c in chunks],
                calls=[c for c in calls if c],
            )

        # Retrieve and verify. A failed verifier call is recorded in verification (status error, the call in calls)
        # and its passages go on UNVERIFIED (limits #78, records.md F17; Q78, D75 keeps the fail-open).
        chunks, stats = await self.retrieve_and_verify(query)
        calls = [stats.get("verify_call")]

        # Generate answer. A failed call (status other than ok or length) is the result's error, never its answer.
        t_gen = time.time()
        try:
            answer, record = await self._generate(query, chunks)
        except lock_adapter.LockCallError as e:
            logger.error(f"Generation failed: {e}")
            return result("", stats, chunks, time.time() - t_gen, calls + [call_summary(e.record)], error=str(e))
        return result(answer, stats, chunks, time.time() - t_gen, calls + [call_summary(record)])

    async def _generate(self, query: str, chunks: List[Dict]) -> Tuple[str, Dict[str, Any]]:
        """Generate answer from verified chunks. Returns (answer, the call's lock record)."""
        # Format passages, each whole (D25; the 800-character cut is gone, cuts.md pipeline.py:254)
        passages = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("file_name", "unknown")
            page = chunk.get("metadata", {}).get("page", "?")
            text = chunk.get("text", "")
            passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")

        passages_text = "\n\n".join(passages)
        prompt = GENERATION_PROMPT.replace("{passages}", passages_text).replace(
            "{question}", query
        )

        # D37: the call's record carries the ids of the passages in the prompt. No options: the lock's (D53).
        rc.set_passages([c.get("id") for c in chunks])
        response = await self.router.generate(
            model_identifier=self.config.gen_model,
            prompt=prompt,
        )

        # The reply text as the lock returned it; an empty reply stays empty (str(response) is never the answer, A5)
        return response.get("response") or "", response.get("lock_record") or {}
