"""
Document Retriever for RAG

Performs semantic search with hybrid (dense + sparse) ranking,
optionally enhanced with CrossEncoder reranking for higher precision.
"""

from typing import List, Dict, Any, Optional
import logging
import time

from backend.agents import lock_adapter  # noqa: F401  (puts the reanalysis root on sys.path for experiments.runner)
from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.hybrid_search import AdaptiveHybridSearch, RRFHybridSearch, metadata_matches
from backend.retrieval.reranker import CrossEncoderReranker, get_reranker
from backend.retrieval.query_refinement import classify_query, QueryType, extract_proper_nouns

from experiments.runner import run_context as rc

logger = logging.getLogger(__name__)

# Mentori's candidate widths when the caller names none (limits #7, #8, #11, #12; stated in Methods): dense search
# takes 3 x top_k, fusion keeps 2 x top_k, BM25 takes 3 x the fused width, the reranker returns top_k.
DENSE_WIDTH = 3
FUSED_WIDTH = 2
RETRIEVALS = "retrievals.jsonl"   # <sink>/retrievals.jsonl: one record per retrieve() inside a run context (D37, D70)


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
            use_reranker: Whether to use CrossEncoder reranking (default True). False is refused by retrieve():
                every strategy reranks (A4, D40).
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
        use_reranker: Optional[bool] = None,
        dense_top_k: Optional[int] = None,
        hybrid_top_k: Optional[int] = None,
        trace: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            collection_name: Target collection
            use_hybrid: Whether to use hybrid search
            auto_adjust_alpha: Auto-adjust hybrid weights
            where: Metadata filter, applied to dense and to keyword search, and to the fused results (Q14, D68)
            min_similarity: not applied (limits #10, #123). It was a 0.25 cut on dense similarity reached only when
                the reranker had not run; every retrieval now reranks (A4, D40), so a result list longer than one
                that comes back unreranked raises "reranker unavailable", and a single candidate is kept unfiltered.
                The parameter stays so existing callers keep their signature.
            use_reranker: Override instance setting for CrossEncoder reranking. False (here or on the instance) is
                refused: every strategy reranks (A4, D40).
            dense_top_k: dense candidates; None = DENSE_WIDTH x top_k. The verified pass passes 100 (Q16, D68).
            hybrid_top_k: fused candidates handed to the reranker; None = FUSED_WIDTH x top_k. The verified pass
                passes 50 (Q16, D68).
            trace: a list this call appends its retrieval record to; inside a run context the same record also goes
                to <sink>/retrievals.jsonl (D37). The record holds query_type (D70), the widths used, whether
                reranking ran (read from rerank_score in the results, records.md F19), the filter and the passage ids.
                Q150 (D83): it also holds search_s, the seconds from the start of this call to its record
                (time.perf_counter, rounded to the microsecond), and of those, load_s and loads: the seconds this
                call spent getting what the retriever did not yet hold, by name: "embedding_model" (the encoder's
                first load in the process), "bm25_index" (this retriever's keyword index, built on its first hybrid
                call) and "reranker" (the process's shared reranker: loaded on its first use in the process, else
                only fetched). A call that raises before its record (a failed embed, search or load) records nothing,
                as before.

        Returns:
            List of results with scores and metadata
        """
        t0 = time.perf_counter()   # Q150 (D83): the search's own time, written to its record by _record
        loads: Dict[str, float] = {}   # Q150: what this call had to load or build first, and its seconds
        collection = collection_name or self.collection_name
        should_rerank = use_reranker if use_reranker is not None else self.use_reranker
        if not should_rerank:
            raise ValueError("every retrieval reranks (A4, D40): use_reranker=False is refused; the code that built "
                             "this retriever or called retrieve() must turn reranking on")
        for name, value in (("top_k", top_k), ("dense_top_k", dense_top_k), ("hybrid_top_k", hybrid_top_k)):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
                raise ValueError(f"{name} must be a positive integer, got {value!r}")
        n_dense = dense_top_k if dense_top_k is not None else top_k * DENSE_WIDTH
        n_fused = hybrid_top_k if hybrid_top_k is not None else top_k * FUSED_WIDTH

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

        # The retrieval's record (D37); query_type on every retrieval (D70)
        record = {
            "query": query, "query_type": query_type, "query_subtype": query_meta.get("query_subtype"),
            "author_query": is_author_query, "expanded_query": None, "collection": collection, "where": where,
            "use_hybrid": use_hybrid, "top_k": top_k, "dense_top_k": n_dense,
            "hybrid_top_k": n_fused, "n_dense": 0, "n_fused": 0,   # n_fused cuts the dense list too without hybrid
            "docs_outside_filter": 0, "outside_filter_ids": [], "rerank_skipped": None, "reranked": False,
            "n_removed_by_author_filter": 0, "n_returned": 0, "passages": [],
            "search_s": None, "load_s": None, "loads": {},   # Q150 (D83): set by _record
        }

        # Step 1: Embed query. Q150: an encoder not yet loaded in this process loads first (embed_query would load it
        # itself; loading it here only times the load apart from the query's embedding)
        if getattr(self.embedder, "model", "") is None and callable(getattr(self.embedder, "_ensure_model", None)):
            t = time.perf_counter()
            self.embedder._ensure_model()
            loads["embedding_model"] = time.perf_counter() - t
        query_embedding = self.embedder.embed_query(query)

        # Step 2: Dense search (dense_top_k candidates; Q16 lets the caller widen it)
        dense_results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_dense,
            collection_name=collection,
            where=where
        )

        # Convert to standard format
        results = self._format_dense_results(dense_results)
        record["n_dense"] = len(results)

        if not results:
            logger.warning(f"No results found for query: {query}")
            self._record(record, trace, t0, loads)
            return []

        # Step 3: Hybrid reranking (BM25 + dense fusion)
        if use_hybrid:
            # Ensure BM25 index is built (Q150: its build, on this retriever's first hybrid call, is timed as a load)
            building = not self._bm25_indexed
            t = time.perf_counter()
            self._ensure_bm25_index(collection)
            if building:
                loads["bm25_index"] = time.perf_counter() - t

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

            # Apply hybrid search: hybrid_top_k fused candidates for the reranker (Q16 lets the caller widen it);
            # the filter applies to keyword search too (Q14, D68)
            fusion: Dict[str, Any] = {}
            if isinstance(self.hybrid_search, RRFHybridSearch):
                results = self.hybrid_search.search(
                    query=expanded_query,
                    dense_results=results,
                    top_k=n_fused,
                    auto_adjust=auto_adjust_alpha,
                    where=where,
                    trace=fusion,
                )
            else:
                # AdaptiveHybridSearch only reorders the dense results, which Chroma already filtered
                results = self.hybrid_search.search(
                    query=expanded_query,
                    dense_results=results,
                    top_k=n_fused,
                    auto_adjust=auto_adjust_alpha
                )
            record.update(fusion)
            record["expanded_query"] = expanded_query if expanded_query != query else None
        else:
            results = results[:n_fused]
        record["n_fused"] = len(results)

        # Q14 (D68): the fused results are filtered by where, and the passages dropped are counted (records F20).
        # Keyword hits are already filtered before fusion, so the count is 0 unless metadata_matches reads a filter
        # differently from Chroma's dense search.
        if where:
            outside = [r.get("id") for r in results if not metadata_matches(r.get("metadata"), where)]
            record["docs_outside_filter"] = len(outside)
            record["outside_filter_ids"] = outside
            if outside:
                logger.warning(f"{len(outside)} fused passages outside the filter {where!r} dropped (Q14)")
                results = [r for r in results if metadata_matches(r.get("metadata"), where)]
                record["n_fused"] = len(results)

        # Step 4: CrossEncoder reranking, every strategy (A4, D40). D70 keeps the author-query exception for the
        # explicit author phrasings: a query that matches one of the five metadata patterns of
        # query_refinement.classify_query ("papers by ...", "who wrote ...", "author of ...", "written by", "by me")
        # is an author search and is not reranked. Q95 (D75) deleted Mentori's other two patterns
        # ("find/get/list ... by|from ..." and "title of/is/contains"), which caught content queries.
        # A reranker that fails to load or to score raises (reranker.py); one candidate is returned unscored.
        if len(results) > 1 and not is_author_query:
            # Q150: a retriever without its reranker gets the process's shared one first, timed as a load
            fetching = self._reranker is None
            t = time.perf_counter()
            reranker = self._get_reranker()
            if fetching:
                loads["reranker"] = time.perf_counter() - t
            results = reranker.rerank(
                query=query,
                candidates=results,
                top_k=top_k
            )
            logger.info(f"Applied CrossEncoder reranking")
        else:
            record["rerank_skipped"] = "author_query" if is_author_query else "single_candidate"
            if is_author_query:
                logger.info("Skipping CrossEncoder for author query (D70: a metadata pattern matched)")
            results = results[:top_k]

        # Step 5: what follows reranking. Whether reranking ran is read from the results (records.md F19).
        reranked = bool(results) and all("rerank_score" in r for r in results)
        pre_filter_count = len(results)

        if reranked:
            # A4: the -5 cut on rerank_score is deleted. It removed nothing (this reranker scores 0 to 1, limits F1).
            pass
        elif is_author_query:
            # The author exception kept by D70, as built: results with a fused or BM25 score above 0 (on the
            # hybrid path every fused result has hybrid_score > 0)
            results = [
                r for r in results
                if r.get("hybrid_score", 0) > 0.0 or r.get("sparse_score", 0) > 0
            ]
            record["n_removed_by_author_filter"] = pre_filter_count - len(results)
        elif len(results) > 1:
            # limits #10, #123: the 0.25 min_similarity cut was reached only without reranking; it is gone
            self._record(record, trace, t0, loads)
            raise RuntimeError(f"reranker unavailable: {len(results)} results came back without rerank scores "
                               f"(A4, D40)")
        # else: a single candidate, kept unfiltered (limits #10, #123)

        if len(results) < pre_filter_count:
            logger.info(f"Author filter removed {pre_filter_count - len(results)} results")

        record.update(reranked=reranked, n_returned=len(results), passages=[r.get("id") for r in results])
        self._record(record, trace, t0, loads)
        logger.info(f"Retrieved {len(results)} results")
        return results

    @staticmethod
    def _record(record: Dict[str, Any], trace: Optional[List[Dict[str, Any]]], t0: float,
                loads: Dict[str, float]) -> None:
        """Appends the retrieval's record to trace (when given) and, inside a run context, to <sink>/retrievals.jsonl
        (D37; query_type on every retrieval, D70). Outside a run (Mentori's own app) there is no sink. Q150 (D83):
        first sets search_s (seconds since t0, the call's start), loads (seconds per thing loaded) and load_s (the sum
        of the values in loads), each rounded to the microsecond, so the time to write the record is not in it."""
        record["search_s"] = round(time.perf_counter() - t0, 6)
        record["loads"] = {k: round(v, 6) for k, v in loads.items()}
        record["load_s"] = round(float(sum(record["loads"].values())), 6)   # the sum of the values stored in loads
        if trace is not None:
            trace.append(record)
        try:
            rc.current()
        except rc.RunContextError:
            return
        rc.append(dict(record), RETRIEVALS)

    def _get_reranker(self) -> CrossEncoderReranker:
        """
        The reranker given to the constructor, else the process's one shared instance (get_reranker, A4). A load
        failure raises.

        Returns:
            CrossEncoderReranker instance
        """
        if self._reranker is None:
            self._reranker = get_reranker()

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
    )   # every retrieval reranks (A4, D40): use_reranker=False is refused by retrieve()
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
