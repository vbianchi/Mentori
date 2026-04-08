"""
Hybrid Search: Dense (embeddings) + Sparse (BM25)

Combines semantic similarity with keyword matching for scientific accuracy.
"""

from typing import List, Dict, Any
import re as _re
import numpy as np
from rank_bm25 import BM25Okapi
import tiktoken


# Minimal stopword set — kept small to avoid filtering scientific terms
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "it", "its", "this", "that", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "not", "no", "can", "may", "so", "if", "than", "also",
})

# Regex that preserves hyphens and dots within tokens
_TOKEN_RE = _re.compile(r'[\w][\w\-\.]*[\w]|[\w]+')


def _scientific_tokenize(text: str) -> List[str]:
    """
    Tokenize text for BM25 with scientific-text awareness.

    - Preserves hyphens and dots inside tokens (CRISPR-Cas9, H2O2, IC50, p53)
    - Expands hyphenated terms as sub-tokens (CRISPR-Cas9 → [crispr-cas9, crispr, cas9])
    - Removes a minimal stopword set
    - Lowercases everything for matching
    """
    tokens = _TOKEN_RE.findall(text.lower())

    expanded: List[str] = []
    for tok in tokens:
        if tok in _STOPWORDS:
            continue
        expanded.append(tok)
        # Expand hyphenated terms into sub-tokens
        if "-" in tok:
            parts = tok.split("-")
            for part in parts:
                if part and part not in _STOPWORDS:
                    expanded.append(part)

    return expanded


class HybridSearchEngine:
    """
    Combines dense vector search with sparse BM25 keyword search.

    Why hybrid for science:
    - Dense: Captures semantic meaning ("gene editing" → "CRISPR")
    - Sparse: Exact matches for acronyms, citations, chemical formulas
    """

    def __init__(self, alpha: float = 0.5):
        """
        Args:
            alpha: Weight between dense (0.0) and sparse (1.0)
                   0.5 = balanced (recommended for science)
                   0.7 = favor keywords (for highly technical queries)
                   0.3 = favor semantics (for conceptual queries)
        """
        self.alpha = alpha
        self.bm25 = None
        self.documents = []
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def index_documents(self, documents: List[str]):
        """
        Build BM25 index from documents.

        Args:
            documents: List of document texts to index
        """
        self.documents = documents

        # Tokenize documents for BM25
        tokenized_docs = [self._tokenize(doc) for doc in documents]

        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 (delegates to shared scientific tokenizer)."""
        return _scientific_tokenize(text)

    def search(
        self,
        query: str,
        dense_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining dense and sparse results.

        Args:
            query: Search query
            dense_results: Results from vector similarity search
                Format: [{"id": "...", "text": "...", "score": 0.95}, ...]
            top_k: Number of results to return

        Returns:
            Reranked results with combined scores
        """
        if not self.bm25:
            # No BM25 index built yet, return dense results only
            return dense_results[:top_k]

        # Step 1: Get sparse (BM25) scores
        query_tokens = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)

        # Normalize BM25 scores to [0, 1]
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        # Step 2: Create sparse results lookup
        sparse_scores = {}
        for i, score in enumerate(bm25_scores):
            if i < len(self.documents):
                # Match by document text (in production, use IDs)
                sparse_scores[self.documents[i]] = score

        # Step 3: Combine dense and sparse scores
        for result in dense_results:
            dense_score = result.get("score", 0.0)
            sparse_score = sparse_scores.get(result.get("text", ""), 0.0)

            # Hybrid score: weighted combination
            result["hybrid_score"] = (
                (1 - self.alpha) * dense_score +
                self.alpha * sparse_score
            )
            result["dense_score"] = dense_score
            result["sparse_score"] = sparse_score

        # Step 4: Rerank by hybrid score
        reranked = sorted(
            dense_results,
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        return reranked[:top_k]

    def auto_adjust_alpha(self, query: str) -> float:
        """
        Automatically adjust alpha based on query characteristics.

        Technical queries (acronyms, formulas) → higher alpha (favor keywords)
        Conceptual queries → lower alpha (favor semantics)

        Args:
            query: Search query

        Returns:
            Optimal alpha value for this query
        """
        query_lower = query.lower()

        # Heuristics for scientific queries
        technical_indicators = [
            query.isupper(),  # Acronyms: PCR, DNA, RNA
            any(char.isdigit() for char in query),  # Formulas: H2O2, CO2
            "-" in query,  # Hyphenated terms: CRISPR-Cas9
            "protocol" in query_lower,
            "method" in query_lower,
            len(query.split()) <= 3,  # Short, specific queries
        ]

        technical_score = sum(technical_indicators) / len(technical_indicators)

        # If query is technical, favor keywords (higher alpha)
        if technical_score > 0.5:
            return 0.7  # 70% keywords, 30% semantics
        else:
            return 0.3  # 30% keywords, 70% semantics


class AdaptiveHybridSearch(HybridSearchEngine):
    """
    Enhanced hybrid search that automatically adjusts weights per query.
    """

    def search(
        self,
        query: str,
        dense_results: List[Dict[str, Any]],
        top_k: int = 10,
        auto_adjust: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search with automatic alpha adjustment.

        Args:
            query: Search query
            dense_results: Dense search results
            top_k: Number of results
            auto_adjust: Whether to auto-adjust alpha based on query
        """
        if auto_adjust:
            original_alpha = self.alpha
            self.alpha = self.auto_adjust_alpha(query)

            # Optional: Log adjustment for debugging
            if abs(self.alpha - original_alpha) > 0.1:
                print(f"[Hybrid Search] Adjusted α: {original_alpha:.2f} → {self.alpha:.2f}")

        return super().search(query, dense_results, top_k)


class RRFHybridSearch:
    """
    True Reciprocal Rank Fusion - retrieves from both indexes independently.

    Unlike the basic hybrid search that only reranks dense results, this:
    1. Takes dense results from embedding search
    2. INDEPENDENTLY searches BM25 (can find things dense missed!)
    3. Merges using RRF formula: score = sum(1/(k + rank))

    This is critical for proper noun searches (author names, etc.) where
    embeddings fail but BM25 can find exact matches.
    """

    def __init__(self, k: int = 60, dense_weight: float = 1.0, sparse_weight: float = 1.0):
        """
        Initialize RRF hybrid search.

        Args:
            k: RRF constant (default 60, standard in literature)
            dense_weight: Weight for dense results (default 1.0)
            sparse_weight: Weight for sparse/BM25 results (default 1.0)
        """
        self.k = k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        self.doc_metadatas = []

    def index_documents(
        self,
        documents: List[str],
        ids: List[str] = None,
        metadatas: List[Dict] = None
    ):
        """
        Build BM25 index from documents.

        Args:
            documents: List of document texts
            ids: Optional list of document IDs
            metadatas: Optional list of metadata dicts
        """
        self.documents = documents
        self.doc_ids = ids if ids else [str(i) for i in range(len(documents))]
        self.doc_metadatas = metadatas if metadatas else [{} for _ in documents]

        # Tokenize and build BM25
        tokenized = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 (delegates to shared scientific tokenizer)."""
        return _scientific_tokenize(text)

    def search(
        self,
        query: str,
        dense_results: List[Dict[str, Any]],
        top_k: int = 10,
        auto_adjust: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform true RRF hybrid search.

        Args:
            query: Search query
            dense_results: Results from vector/embedding search
            top_k: Number of results to return
            auto_adjust: Adjust weights based on query type

        Returns:
            Merged results with RRF scores
        """
        if not self.bm25:
            # No BM25 index, return dense only
            return dense_results[:top_k]

        # Auto-adjust weights based on query characteristics
        dense_w = self.dense_weight
        sparse_w = self.sparse_weight

        if auto_adjust:
            dense_w, sparse_w = self._adjust_weights(query)

        # Step 1: Get BM25 results INDEPENDENTLY
        query_tokens = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)

        # Get top BM25 results (more than top_k for better fusion)
        n_sparse = min(top_k * 3, len(self.documents))
        sparse_ranking = sorted(
            enumerate(bm25_scores),
            key=lambda x: x[1],
            reverse=True
        )[:n_sparse]

        # Step 2: Build RRF scores
        rrf_scores = {}
        result_data = {}  # Store result data by ID

        # Add dense results with RRF scoring
        for rank, result in enumerate(dense_results):
            doc_id = result.get("id", str(rank))
            rrf_score = dense_w * (1.0 / (self.k + rank + 1))

            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            result_data[doc_id] = {
                **result,
                "dense_rank": rank + 1,
                "dense_score": result.get("score", 0),
            }

        # Add BM25 results with RRF scoring (INDEPENDENTLY!)
        for rank, (idx, bm25_score) in enumerate(sparse_ranking):
            if bm25_score <= 0:
                continue  # Skip zero-score results

            doc_id = self.doc_ids[idx]
            rrf_score = sparse_w * (1.0 / (self.k + rank + 1))

            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score

            # If this doc wasn't in dense results, add it
            if doc_id not in result_data:
                result_data[doc_id] = {
                    "id": doc_id,
                    "text": self.documents[idx],
                    "metadata": self.doc_metadatas[idx],
                    "score": 0,  # No dense score
                    "dense_rank": None,
                    "dense_score": 0,
                }

            result_data[doc_id]["sparse_rank"] = rank + 1
            result_data[doc_id]["sparse_score"] = float(bm25_score)

        # Step 3: Sort by RRF score and build final results
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        final_results = []
        for doc_id in sorted_ids[:top_k]:
            result = result_data[doc_id]
            result["hybrid_score"] = rrf_scores[doc_id]
            result["rrf_score"] = rrf_scores[doc_id]

            # Set sparse_score to 0 if not found by BM25
            if "sparse_score" not in result:
                result["sparse_score"] = 0
                result["sparse_rank"] = None

            final_results.append(result)

        return final_results

    def _adjust_weights(self, query: str) -> tuple:
        """
        Adjust dense/sparse weights based on query characteristics.

        Proper nouns (names) → favor sparse (BM25)
        Conceptual queries → favor dense (embeddings)

        Returns:
            (dense_weight, sparse_weight)
        """
        # Check for proper nouns (capitalized multi-word phrases)
        import re
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', query)

        # Check for technical indicators
        query_lower = query.lower()
        has_acronyms = any(word.isupper() and len(word) > 1 for word in query.split())
        has_numbers = any(c.isdigit() for c in query)
        is_short = len(query.split()) <= 4

        # Proper nouns (likely author names) → heavily favor BM25
        if proper_nouns and is_short:
            return (0.3, 1.5)  # Strong BM25 preference

        # Technical/acronym queries → favor BM25
        if has_acronyms or (has_numbers and is_short):
            return (0.5, 1.2)

        # Conceptual queries → favor dense
        conceptual_words = ['how', 'why', 'explain', 'describe', 'compare', 'relationship']
        if any(word in query_lower for word in conceptual_words):
            return (1.2, 0.5)

        # Default: balanced
        return (1.0, 1.0)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Example demonstrating hybrid search superiority.
    """

    # Sample scientific documents
    documents = [
        "CRISPR-Cas9 is a genome editing tool that revolutionized molecular biology.",
        "The polymerase chain reaction (PCR) amplifies DNA sequences.",
        "Doudna et al. (2012) demonstrated CRISPR effectiveness in mammalian cells.",
        "H2O2 acts as a reactive oxygen species in cellular signaling.",
        "Off-target effects remain a challenge in gene editing applications.",
    ]

    # Simulate dense search results (from vector DB)
    dense_results = [
        {"id": "1", "text": documents[0], "score": 0.85},
        {"id": "2", "text": documents[1], "score": 0.72},
        {"id": "3", "text": documents[2], "score": 0.68},
        {"id": "4", "text": documents[3], "score": 0.45},
        {"id": "5", "text": documents[4], "score": 0.91},
    ]

    # Initialize hybrid search
    hybrid = AdaptiveHybridSearch(alpha=0.5)
    hybrid.index_documents(documents)

    # Test queries
    queries = [
        "CRISPR-Cas9 mechanism",  # Exact term match important
        "gene editing challenges",  # Semantic understanding needed
        "Doudna research",  # Author name (exact match critical)
        "PCR protocol",  # Acronym match
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = hybrid.search(query, dense_results.copy(), top_k=3, auto_adjust=True)

        for i, result in enumerate(results, 1):
            print(f"  {i}. [Hybrid: {result['hybrid_score']:.2f} | "
                  f"Dense: {result['dense_score']:.2f} | "
                  f"Sparse: {result['sparse_score']:.2f}]")
            print(f"     {result['text'][:70]}...")
