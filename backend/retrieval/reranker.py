"""
Cross-Encoder Reranker for RAG

Re-ranks initial retrieval results using a cross-encoder model.
Provides higher precision for top-k results by scoring query-document
pairs jointly rather than independently.

This is restored from the old RAG system - it significantly improves
retrieval precision for scientific queries.
"""

from sentence_transformers import CrossEncoder
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Re-ranks initial retrieval results using a cross-encoder model.

    Cross-encoders score (query, document) pairs jointly, which is more
    accurate than bi-encoders but slower. Use after initial retrieval
    to improve precision of top-k results.

    Why this matters for scientific RAG:
    - Bi-encoders (used in initial retrieval) encode query and document separately
    - Cross-encoders see both together, catching nuanced relevance
    - Especially helpful for technical queries where word overlap matters
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize the reranker.

        Args:
            model_name: Cross-encoder model to use. Options:
                - "BAAI/bge-reranker-v2-m3" (fast, good quality)
                - "cross-encoder/ms-marco-MiniLM-L-12-v2" (slower, better quality)
                - "cross-encoder/stsb-roberta-large" (best quality, slowest)
                - "ncbi/MedCPT-Cross-Encoder" (biomedical domain, requires trust_remote_code)
        """
        logger.info(f"Loading CrossEncoder model: {model_name}")
        try:
            # Respect MENTORI_EMBED_DEVICE to prevent MPS/GPU wired memory leak
            # on macOS. Without this, CrossEncoder defaults to MPS → wired memory
            # → kernel panic on long-running batch experiments.
            device = os.environ.get("MENTORI_EMBED_DEVICE", None)
            if device:
                self.model = CrossEncoder(model_name, device=device)
            else:
                self.model = CrossEncoder(model_name)
            self.model_name = model_name
            self.is_available = True
            logger.info(f"CrossEncoder loaded successfully (device={device or 'default'})")
        except Exception as e:
            logger.warning(f"Could not load CrossEncoder model: {e}. Reranking disabled.")
            self.model = None
            self.is_available = False

    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Re-rank candidate chunks using cross-encoder scoring.

        Args:
            query: User query
            candidates: Initial retrieval results from hybrid search
                Format: [{"id": "...", "text": "...", "score": 0.95, "metadata": {...}}, ...]
            top_k: Number of results to return after re-ranking
            score_threshold: Optional minimum score to include (cross-encoder scores
                            are typically in range [-10, 10] for ms-marco models)

        Returns:
            Top-k re-ranked results with updated scores. Each result includes:
            - Original fields (id, text, metadata, etc.)
            - rerank_score: The cross-encoder score
            - original_score: The score before reranking
        """
        if not self.is_available or not candidates:
            return candidates[:top_k]

        if len(candidates) <= 1:
            return candidates

        logger.info(f"Reranking {len(candidates)} candidates for query: '{query[:50]}...'")

        # Prepare query-document pairs
        pairs = [[query, candidate.get('text', '')] for candidate in candidates]

        # Score all pairs
        try:
            scores = self.model.predict(pairs)
        except Exception as e:
            logger.error(f"CrossEncoder prediction failed: {e}")
            return candidates[:top_k]

        # Combine scores with candidates
        scored_candidates = []
        for candidate, score in zip(candidates, scores):
            scored_candidate = {
                **candidate,
                'rerank_score': float(score),
                'original_score': candidate.get('score', candidate.get('hybrid_score', 0))
            }
            scored_candidates.append(scored_candidate)

        # Sort by re-rank score (descending)
        reranked = sorted(
            scored_candidates,
            key=lambda x: x['rerank_score'],
            reverse=True
        )

        # Apply score threshold if specified
        if score_threshold is not None:
            reranked = [r for r in reranked if r['rerank_score'] >= score_threshold]

        # Log score distribution for debugging
        if reranked:
            top_score = reranked[0]['rerank_score']
            bottom_score = reranked[-1]['rerank_score'] if len(reranked) > 1 else top_score
            logger.info(f"Rerank scores: top={top_score:.3f}, bottom={bottom_score:.3f}")

        return reranked[:top_k]

    def rerank_with_diversity(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10,
        max_per_source: int = 3
    ) -> List[Dict]:
        """
        Re-rank with source diversity constraint.

        Prevents too many results from a single document, ensuring
        diverse coverage across the corpus.

        Args:
            query: User query
            candidates: Initial retrieval results
            top_k: Number of results to return
            max_per_source: Maximum results from any single source document

        Returns:
            Diversified top-k results
        """
        # First, do standard reranking
        reranked = self.rerank(query, candidates, top_k=len(candidates))

        # Apply diversity filter
        final_results = []
        source_counts = {}

        for result in reranked:
            if len(final_results) >= top_k:
                break

            # Get source document
            metadata = result.get('metadata', {})
            source = metadata.get('file_path') or metadata.get('source') or metadata.get('file_name') or 'unknown'

            # Check if we've hit the limit for this source
            current_count = source_counts.get(source, 0)
            if current_count < max_per_source:
                final_results.append(result)
                source_counts[source] = current_count + 1

        logger.info(f"Diversity filter: {len(final_results)} results from {len(source_counts)} sources")

        return final_results


# Singleton instance for reuse
_default_reranker: Optional[CrossEncoderReranker] = None


def get_reranker() -> CrossEncoderReranker:
    """
    Get the default reranker instance (singleton pattern).

    Returns:
        CrossEncoderReranker instance
    """
    global _default_reranker
    if _default_reranker is None:
        _default_reranker = CrossEncoderReranker()
    return _default_reranker


_scientific_reranker: Optional[CrossEncoderReranker] = None


def get_scientific_reranker() -> CrossEncoderReranker:
    """
    Get a scientific/biomedical reranker instance.

    Tries MedCPT-Cross-Encoder (biomedical domain) first,
    falls back to ms-marco if it fails.

    Returns:
        CrossEncoderReranker instance
    """
    global _scientific_reranker
    if _scientific_reranker is not None:
        return _scientific_reranker

    # Try MedCPT first
    try:
        reranker = CrossEncoderReranker(model_name="ncbi/MedCPT-Cross-Encoder")
        if reranker.is_available:
            _scientific_reranker = reranker
            logger.info("Using MedCPT-Cross-Encoder for scientific reranking")
            return _scientific_reranker
    except Exception as e:
        logger.info(f"MedCPT-Cross-Encoder not available: {e}")

    # Fall back to default bge-reranker-v2-m3
    _scientific_reranker = get_reranker()
    logger.info("Falling back to bge-reranker-v2-m3 for scientific reranking")
    return _scientific_reranker
