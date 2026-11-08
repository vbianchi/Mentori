"""
Cross-Encoder Reranker for RAG

Re-ranks initial retrieval results using a cross-encoder model.
Provides higher precision for top-k results by scoring query-document
pairs jointly rather than independently.

This is restored from the old RAG system - it significantly improves
retrieval precision for scientific queries.

Under the lock: the model is the snapshot experiments/LOCK.toml [retrieval] reranker names, loaded from the local
cache on the lock's device and never downloaded (Q20, D68; Q37, D69). Every strategy reranks (A4, D40), so a model
that fails to load or to score raises instead of turning reranking off; a (query, passage) pair longer than the
model's limit raises instead of being cut (D25). One instance serves the process (get_reranker, A4).
"""

from sentence_transformers import CrossEncoder
from typing import List, Dict, Optional
import logging
import threading

from backend.retrieval.embeddings import check_encoder_lengths, lock_encoder

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

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the reranker.

        Args:
            model_name: None (the lock's [retrieval] reranker, BAAI/bge-reranker-v2-m3) or that same name; any other
                model is refused (Q20, D68).

        A load failure raises (A4, limits #12, cuts.md F11): it no longer turns reranking off with a warning.
        """
        spec = lock_encoder("reranker")
        if model_name is not None and model_name != spec["hf_repo"]:
            raise RuntimeError(f"reranker {model_name!r} is not the lock's [retrieval] reranker {spec['hf_repo']!r} "
                               f"(Q20, D68)")
        logger.info(f"Loading CrossEncoder model: {spec['hf_repo']}@{spec['revision']} (device={spec['device']}, "
                    f"local files only)")
        # Q37/D69: the lock's device (cpu); the old code read MENTORI_EMBED_DEVICE, else let sentence-transformers pick
        self.model = CrossEncoder(spec["hf_repo"], device=spec["device"], revision=spec["revision"],
                                  local_files_only=spec["local_files_only"])
        self.model_name = spec["hf_repo"]
        self.revision = spec["revision"]
        self.device = spec["device"]
        self.is_available = True

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
        if not candidates:
            return []

        if len(candidates) <= 1:
            return candidates   # one candidate is returned unscored; the retriever records it as not reranked

        logger.info(f"Reranking {len(candidates)} candidates for query: '{query[:50]}...'")

        # Prepare query-document pairs
        pairs = [[query, candidate.get('text', '')] for candidate in candidates]
        # D25: a pair over the model's limit raises; CrossEncoder.predict would cut it at max_length
        check_encoder_lengths(self.model.tokenizer, pairs, self.model.max_length, "reranker")

        # Score all pairs. A failure raises (A4, limits #12): the old code returned the candidates unreranked.
        scores = self.model.predict(pairs)

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


# Singleton instance for reuse: one reranker per process, shared by every retriever (A4)
_default_reranker: Optional[CrossEncoderReranker] = None
_default_lock = threading.Lock()


def get_reranker() -> CrossEncoderReranker:
    """
    Get the default reranker instance (singleton pattern). Built once per process, under a lock so two threads
    (the RLM's sub-call thread and the event loop) never load two copies; a load failure raises (A4).

    Returns:
        CrossEncoderReranker instance
    """
    global _default_reranker
    with _default_lock:
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
