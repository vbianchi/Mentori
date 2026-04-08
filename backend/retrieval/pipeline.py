"""
Scientific RAG Pipeline

Orchestrates the full retrieve-rerank-verify-generate flow.
Wraps SimpleRetriever with configurable widths and optional LLM verification.

Two preset configurations:
- baseline(): Current narrow pipeline (dense*30 → hybrid*20 → rerank*10 → generate)
- verified(): Wide pipeline + LLM verification (dense*100 → hybrid*50 → rerank*15 → verify → generate)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.retrieval.chunk_verifier import ChunkVerifier
from backend.retrieval.reranker import CrossEncoderReranker, get_reranker

logger = logging.getLogger(__name__)


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

    # Verification
    use_verification: bool = True
    verify_model: str = "ollama::gpt-oss:20b"
    verify_num_predict: int = 5000

    # Generation
    gen_model: str = "ollama::qwen3-coder:latest"
    gen_num_predict: int = 4000
    gen_temperature: float = 0.1

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
    verified_chunks: Optional[List[Dict]] = None
    error: Optional[str] = None


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
                num_predict=self.config.verify_num_predict,
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

        # Step 1: Broad retrieval (dense + hybrid + rerank handled by retriever)
        # The retriever internally does: dense → hybrid → rerank
        # We call it with our wider top_k
        chunks = self.retriever.retrieve(
            query=query,
            top_k=self.config.rerank_top_k,
            collection_name=self.collection_name,
        )

        retrieval_time = time.time() - t0
        stats["chunks_retrieved"] = len(chunks)
        stats["retrieval_latency_s"] = round(retrieval_time, 2)

        # Step 2: LLM verification (if enabled)
        verify_time = 0.0
        if self._verifier and chunks:
            t1 = time.time()
            verified = await self._verifier.verify(query, chunks)
            relevant = self._verifier.filter_relevant(verified, include_partial=False)
            verify_time = time.time() - t1

            stats["chunks_before_verify"] = len(chunks)
            stats["chunks_after_verify"] = len(relevant)
            stats["verify_latency_s"] = round(verify_time, 2)

            # If verification filtered everything, fall back to top reranked
            if not relevant:
                logger.warning(
                    "Verification filtered all chunks, falling back to "
                    "top reranked results"
                )
                relevant = chunks[:5]
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

        # Retrieve and verify
        chunks, stats = await self.retrieve_and_verify(query)

        # Generate answer
        t_gen = time.time()
        try:
            answer = await self._generate(query, chunks)
            gen_time = time.time() - t_gen
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            gen_time = time.time() - t_gen
            return PipelineResult(
                answer="",
                chunks_retrieved=stats.get("chunks_retrieved", 0),
                chunks_after_rerank=stats.get("chunks_retrieved", 0),
                chunks_after_verify=stats.get("chunks_after_verify", 0),
                chunks_used=stats.get("chunks_final", 0),
                latency_s=round(time.time() - t_start, 2),
                retrieval_latency_s=stats.get("retrieval_latency_s", 0),
                verify_latency_s=stats.get("verify_latency_s", 0),
                generation_latency_s=round(gen_time, 2),
                error=str(e),
            )

        total_time = time.time() - t_start

        return PipelineResult(
            answer=answer,
            chunks_retrieved=stats.get("chunks_retrieved", 0),
            chunks_after_rerank=stats.get("chunks_retrieved", 0),
            chunks_after_verify=stats.get("chunks_after_verify", 0),
            chunks_used=stats.get("chunks_final", 0),
            latency_s=round(total_time, 2),
            retrieval_latency_s=stats.get("retrieval_latency_s", 0),
            verify_latency_s=stats.get("verify_latency_s", 0),
            generation_latency_s=round(gen_time, 2),
            verified_chunks=[
                {
                    "text": c.get("text", "")[:200],
                    "source": c.get("metadata", {}).get("file_name", "unknown"),
                    "page": c.get("metadata", {}).get("page", "?"),
                }
                for c in chunks
            ],
        )

    async def _generate(self, query: str, chunks: List[Dict]) -> str:
        """Generate answer from verified chunks."""
        # Format passages
        passages = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("file_name", "unknown")
            page = chunk.get("metadata", {}).get("page", "?")
            text = chunk.get("text", "")[:800]
            passages.append(f"[{i}] Source: {source}, Page {page}\n{text}")

        passages_text = "\n\n".join(passages)
        prompt = GENERATION_PROMPT.replace("{passages}", passages_text).replace(
            "{question}", query
        )

        response = await self.router.generate(
            model_identifier=self.config.gen_model,
            prompt=prompt,
            options={
                "temperature": self.config.gen_temperature,
                "num_predict": self.config.gen_num_predict,
            },
        )

        answer = response.get(
            "response", response.get("message", {}).get("content", "")
        )
        if not answer:
            answer = str(response)

        return answer
