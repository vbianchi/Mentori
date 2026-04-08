"""
Document Retriever for RAG

Performs semantic search with hybrid (dense + sparse) ranking,
optionally enhanced with CrossEncoder reranking for higher precision.
"""

from typing import List, Dict, Any, Optional
import logging

from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.hybrid_search import AdaptiveHybridSearch, RRFHybridSearch
from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.query_refinement import classify_query, QueryType, extract_proper_nouns

logger = logging.getLogger(__name__)


class SimpleRetriever:
    """
    Retrieves relevant documents using hybrid search.

    Pipeline:
    1. Embed query (dense search)
    2. Search vector DB (get candidates)
    3. Apply BM25 (sparse search)
    4. Combine scores (hybrid ranking)
    5. Return top-k results

    Features:
    - Hybrid search (dense + BM25)
    - Adaptive alpha (auto-adjust weights)
    - Metadata filtering
    - Score transparency (shows dense/sparse breakdown)
    """

    def __init__(
        self,
        embedder: Optional[EmbeddingEngine] = None,
        vector_store: Optional[VectorStore] = None,
        hybrid_search: Optional[AdaptiveHybridSearch] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        collection_name: str = "default",
        alpha: float = 0.5,
        use_reranker: bool = True,
        use_rrf: bool = True,
        embedding_model: Optional[str] = None,
    ):
        """
        Initialize retriever.

        Args:
            embedder: Embedding engine
            vector_store: Vector store
            hybrid_search: Hybrid search engine (ignored if use_rrf=True)
            reranker: CrossEncoder reranker for precision boost
            collection_name: Default collection
            alpha: Default hybrid weight (0=dense, 1=sparse)
            use_reranker: Whether to use CrossEncoder reranking (default True)
            use_rrf: Whether to use true RRF fusion (default True).
                     RRF searches BM25 independently, finding results that
                     dense search might miss (critical for author name queries).
            embedding_model: HuggingFace model name for embeddings. If provided
                and no custom embedder is given, an EmbeddingEngine is created
                with this model. Must match the model used during ingestion.
        """
        if embedder:
            self.embedder = embedder
        elif embedding_model:
            self.embedder = EmbeddingEngine(model_name=embedding_model)
        else:
            self.embedder = EmbeddingEngine()
        self.vector_store = vector_store or VectorStore(
            collection_name=collection_name
        )

        # Choose hybrid search strategy
        self.use_rrf = use_rrf
        if use_rrf:
            self.hybrid_search = RRFHybridSearch()
        else:
            self.hybrid_search = hybrid_search or AdaptiveHybridSearch(alpha=alpha)

        # Initialize reranker (lazy load to avoid startup cost if not used)
        self.use_reranker = use_reranker
        self._reranker = reranker  # Will be initialized on first use if None

        self.collection_name = collection_name

        # Index documents for BM25 (lazy initialization)
        self._bm25_indexed = False

        logger.info(
            f"Initialized SimpleRetriever "
            f"(rrf={'enabled' if use_rrf else 'disabled'}, "
            f"reranker={'enabled' if use_reranker else 'disabled'})"
        )

    def _expand_author_query(self, query: str) -> List[str]:
        """
        Expand author name queries to catch common variations.

        E.g., "Valerio Bianchi" -> ["Valerio Bianchi", "V. Bianchi", "V Bianchi", "Bianchi"]

        Args:
            query: Original query

        Returns:
            List of query variants (original + expansions)
        """
        proper_nouns = extract_proper_nouns(query)

        if not proper_nouns:
            return [query]

        variants = [query]  # Always include original

        for name in proper_nouns:
            parts = name.split()
            if len(parts) >= 2:
                # Assume "FirstName LastName" format
                first_name = parts[0]
                last_name = parts[-1]

                # Add common variations
                variants.extend([
                    f"{first_name[0]}. {last_name}",  # V. Bianchi
                    f"{first_name[0]} {last_name}",   # V Bianchi
                    last_name,                         # Bianchi (surname only)
                    f"{last_name}, {first_name[0]}",  # Bianchi, V
                    f"{last_name} {first_name[0]}",   # Bianchi V
                ])
            else:
                # Single word name, add as-is
                variants.append(name)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for v in variants:
            v_lower = v.lower()
            if v_lower not in seen:
                seen.add(v_lower)
                unique.append(v)

        logger.info(f"Expanded author query '{query}' to {len(unique)} variants: {unique[:5]}...")
        return unique

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        collection_name: Optional[str] = None,
        use_hybrid: bool = True,
        auto_adjust_alpha: bool = True,
        where: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.25,
        use_reranker: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            collection_name: Target collection
            use_hybrid: Whether to use hybrid search
            auto_adjust_alpha: Auto-adjust hybrid weights
            where: Metadata filter
            min_similarity: Minimum similarity score to include (0.0-1.0).
                           Results below this threshold are filtered out to
                           prevent returning garbage/irrelevant content.
            use_reranker: Override instance setting for CrossEncoder reranking.
                         If None, uses the instance default (self.use_reranker).

        Returns:
            List of results with scores and metadata
        """
        collection = collection_name or self.collection_name
        should_rerank = use_reranker if use_reranker is not None else self.use_reranker

        # Detect if this is an author/name query and expand it
        query_type, query_meta = classify_query(query)
        is_author_query = (
            query_type == QueryType.METADATA and
            query_meta.get("query_subtype") == "author_search"
        )

        logger.info(
            f"Retrieving for query: '{query[:50]}...' "
            f"(type: {query_type}, author_query: {is_author_query}, "
            f"proper_nouns: {query_meta.get('proper_nouns', [])})"
        )

        # Step 1: Embed query
        query_embedding = self.embedder.embed_query(query)

        # Step 2: Dense search (get more candidates for hybrid/reranking)
        # Get extra candidates if we're going to rerank
        n_candidates = top_k * 3 if (use_hybrid or should_rerank) else top_k
        dense_results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_candidates,
            collection_name=collection,
            where=where
        )

        # Convert to standard format
        results = self._format_dense_results(dense_results)

        if not results:
            logger.warning(f"No results found for query: {query}")
            return []

        # Step 3: Hybrid reranking (BM25 + dense fusion)
        if use_hybrid:
            # Ensure BM25 index is built
            self._ensure_bm25_index(collection)

            # For author queries, expand to catch name variations
            # E.g., "Valerio Bianchi" -> also search for "V. Bianchi", "Bianchi", etc.
            if is_author_query:
                # Get the detected author name from query metadata
                target_author = query_meta.get("target_author")
                proper_nouns = query_meta.get("proper_nouns", [])

                logger.info(f"Author query detected! target_author={target_author}, proper_nouns={proper_nouns}")

                if target_author:
                    # Expand the specific author name
                    query_variants = self._expand_author_query(target_author)
                elif proper_nouns:
                    # Fallback: expand the first proper noun
                    query_variants = self._expand_author_query(proper_nouns[0])
                else:
                    query_variants = [query]

                # Combine original query with name variants for BM25
                # This ensures both semantic context and name variations are searched
                expanded_query = query + " " + " ".join(query_variants)
                logger.info(f"Author query expanded for BM25: '{expanded_query[:100]}...'")
            else:
                expanded_query = query

            # Apply hybrid search - get more candidates if reranking follows
            hybrid_top_k = top_k * 2 if should_rerank else top_k
            results = self.hybrid_search.search(
                query=expanded_query,
                dense_results=results,
                top_k=hybrid_top_k,
                auto_adjust=auto_adjust_alpha
            )
        else:
            results = results[:top_k * 2 if should_rerank else top_k]

        # Step 4: CrossEncoder reranking (optional, high precision)
        # IMPORTANT: Skip CrossEncoder for author queries!
        # CrossEncoder (MS-MARCO) is trained for Q&A, not name matching.
        # It gives low scores to "V. Bianchi" when query is "Valerio Bianchi",
        # causing relevant results to be filtered out.
        if should_rerank and len(results) > 1 and not is_author_query:
            reranker = self._get_reranker()
            if reranker and reranker.is_available:
                results = reranker.rerank(
                    query=query,
                    candidates=results,
                    top_k=top_k
                )
                logger.info(f"Applied CrossEncoder reranking")
            else:
                results = results[:top_k]
        else:
            if is_author_query:
                logger.info("Skipping CrossEncoder for author query (name matching benefits from BM25 only)")
            results = results[:top_k]

        # Step 5: Filter by minimum similarity threshold
        # This prevents returning garbage results when no good matches exist
        pre_filter_count = len(results)

        # Determine if CrossEncoder reranking was applied
        has_rerank_scores = results and "rerank_score" in results[0]

        if has_rerank_scores:
            # CrossEncoder was applied - use rerank_score threshold
            # MS-MARCO scores range from ~-10 to +10, negative can still be relevant
            # Use -5 as threshold (only filter truly irrelevant results)
            threshold_used = -5
            results = [r for r in results if r.get("rerank_score", -10) >= threshold_used]
        elif is_author_query:
            # Author queries: very lenient threshold - trust BM25/RRF ranking
            # RRF scores are small (0.01-0.03 typical), so use 0 threshold
            threshold_used = 0.0
            results = [
                r for r in results
                if r.get("hybrid_score", 0) > threshold_used or r.get("sparse_score", 0) > 0
            ]
        else:
            # No reranking - use dense/hybrid score threshold
            threshold_used = min_similarity
            results = [
                r for r in results
                if (r.get("score", 0) >= threshold_used or
                    r.get("hybrid_score", 0) >= threshold_used)
            ]

        if len(results) < pre_filter_count:
            logger.info(
                f"Filtered {pre_filter_count - len(results)} results below "
                f"threshold {threshold_used} (author_query={is_author_query})"
            )

        if not results:
            logger.info(f"No results above threshold for query: {query[:50]}...")

        logger.info(f"Retrieved {len(results)} results")
        return results

    def _get_reranker(self) -> Optional[CrossEncoderReranker]:
        """
        Get or initialize the reranker (lazy loading).

        Returns:
            CrossEncoderReranker instance or None if disabled
        """
        if not self.use_reranker:
            return None

        if self._reranker is None:
            logger.info("Initializing CrossEncoder reranker (first use)")
            self._reranker = CrossEncoderReranker()

        return self._reranker

    def _format_dense_results(
        self,
        dense_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert ChromaDB results to standard format.

        Args:
            dense_results: Raw results from vector_store.search()

        Returns:
            List of formatted results
        """
        results = []

        # ChromaDB returns results in nested lists
        ids = dense_results.get("ids", [[]])[0]
        documents = dense_results.get("documents", [[]])[0]
        distances = dense_results.get("distances", [[]])[0]
        metadatas = dense_results.get("metadatas", [[]])[0]

        for i, doc_id in enumerate(ids):
            distance = distances[i]
            # Convert distance to similarity (cosine)
            # ChromaDB uses L2 distance for normalized embeddings
            # For normalized vectors: cosine_similarity = 1 - (L2_distance^2 / 2)
            similarity = max(0.0, 1.0 - (distance ** 2 / 2.0))

            results.append({
                "id": doc_id,
                "text": documents[i],
                "score": similarity,
                "metadata": metadatas[i],
                "distance": distance
            })

        return results

    def _ensure_bm25_index(self, collection_name: str):
        """
        Ensure BM25 index is built for the collection.

        Args:
            collection_name: Collection to index
        """
        if self._bm25_indexed:
            return

        logger.info(f"Building BM25 index for collection: {collection_name}")

        # Get all documents from collection
        count = self.vector_store.count(collection_name)

        if count == 0:
            logger.warning(f"Collection {collection_name} is empty")
            return

        # Fetch all documents (in batches for large collections)
        # For now, fetch all at once (optimize later for production)
        collection = self.vector_store.get_collection(collection_name)
        all_docs = collection.get()

        documents = all_docs.get("documents", [])
        ids = all_docs.get("ids", [])
        metadatas = all_docs.get("metadatas", [])

        if not documents:
            logger.warning(f"No documents in collection {collection_name}")
            return

        # Index for BM25 - RRFHybridSearch needs IDs and metadata too
        if self.use_rrf and hasattr(self.hybrid_search, 'index_documents'):
            # RRFHybridSearch signature: index_documents(documents, ids, metadatas)
            self.hybrid_search.index_documents(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
        else:
            # AdaptiveHybridSearch signature: index_documents(documents)
            self.hybrid_search.index_documents(documents)

        self._bm25_indexed = True

        logger.info(f"✓ BM25 index built ({len(documents)} documents)")

    def get_document_by_id(
        self,
        doc_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.

        Args:
            doc_id: Document ID
            collection_name: Target collection

        Returns:
            Document dict or None if not found
        """
        collection = collection_name or self.collection_name

        results = self.vector_store.get_by_ids(
            ids=[doc_id],
            collection_name=collection
        )

        if not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "text": results["documents"][0],
            "metadata": results["metadatas"][0]
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path for standalone execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from backend.retrieval.ingestor import SimpleIngestor

    # Step 1: Ingest some test documents
    print("Step 1: Ingesting test documents...")
    ingestor = SimpleIngestor(collection_name="test_retrieval")

    test_docs = [
        "CRISPR-Cas9 is a genome editing tool that revolutionized molecular biology.",
        "The Cas9 enzyme uses guide RNA to target specific DNA sequences for cutting.",
        "Off-target effects occur when CRISPR-Cas9 cuts unintended DNA sites.",
        "Deep learning models are being developed to predict CRISPR off-target effects.",
        "Jennifer Doudna won the Nobel Prize for her work on CRISPR technology in 2020.",
        "The polymerase chain reaction (PCR) amplifies DNA sequences rapidly.",
        "Hydrogen peroxide (H2O2) acts as a reactive oxygen species in cellular signaling.",
    ]

    # Create temporary files and ingest
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, doc in enumerate(test_docs):
            file_path = os.path.join(tmpdir, f"doc_{i}.txt")
            with open(file_path, "w") as f:
                f.write(doc)

            ingestor.ingest_file(file_path)

    print(f"✓ Ingested {len(test_docs)} documents\n")

    # Step 2: Initialize retriever
    print("Step 2: Initializing retriever...")
    retriever = SimpleRetriever(
        embedder=ingestor.embedder,
        vector_store=ingestor.vector_store,
        collection_name="test_retrieval",
        use_reranker=False,  # disabled for small test
    )
    print("✓ Retriever ready\n")

    # Step 3: Test queries
    queries = [
        "How does CRISPR work?",
        "Doudna Nobel Prize",
        "PCR protocol",
        "H2O2 signaling"
    ]

    for query in queries:
        print(f"Query: '{query}'")
        print("-" * 70)

        # Dense-only
        dense_results = retriever.retrieve(query, top_k=3, use_hybrid=False)
        print("  Dense-only top result:")
        print(f"    [{dense_results[0]['score']:.3f}] {dense_results[0]['text'][:60]}...")

        # Hybrid
        hybrid_results = retriever.retrieve(query, top_k=3, use_hybrid=True)
        print("  Hybrid top result:")
        if 'hybrid_score' in hybrid_results[0]:
            print(f"    [H:{hybrid_results[0]['hybrid_score']:.3f}, "
                  f"D:{hybrid_results[0]['dense_score']:.3f}, "
                  f"S:{hybrid_results[0]['sparse_score']:.3f}] "
                  f"{hybrid_results[0]['text'][:50]}...")
        else:
            print(f"    [{hybrid_results[0]['score']:.3f}] {hybrid_results[0]['text'][:60]}...")

        print()
