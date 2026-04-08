"""
Tests for Document Retriever
"""

import pytest
import tempfile
import os
from backend.retrieval.retriever import SimpleRetriever
from backend.retrieval.ingestor import SimpleIngestor


@pytest.fixture
def test_collection():
    """Create test collection with sample documents."""
    collection_name = "test_retrieval"

    # Create ingestor
    ingestor = SimpleIngestor(collection_name=collection_name)

    # Create test documents
    test_docs = [
        "CRISPR-Cas9 is a revolutionary genome editing tool that has transformed molecular biology.",
        "The Cas9 enzyme uses guide RNA to target and cut specific DNA sequences with high precision.",
        "Off-target effects occur when CRISPR-Cas9 accidentally cuts unintended DNA sites in the genome.",
        "Deep learning models are being developed to predict and minimize CRISPR off-target effects.",
        "Jennifer Doudna and Emmanuelle Charpentier won the Nobel Prize for CRISPR research in 2020.",
        "The polymerase chain reaction (PCR) is a technique used to amplify DNA sequences rapidly.",
        "Hydrogen peroxide (H2O2) acts as a reactive oxygen species in cellular signaling pathways.",
        "Base editing is an advanced CRISPR technique that allows precise single-nucleotide changes.",
    ]

    # Ingest documents
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, doc in enumerate(test_docs):
            file_path = os.path.join(tmpdir, f"doc_{i}.txt")
            with open(file_path, "w") as f:
                f.write(doc)

            ingestor.ingest_file(file_path)

    return {
        "collection_name": collection_name,
        "embedder": ingestor.embedder,
        "vector_store": ingestor.vector_store,
        "num_docs": len(test_docs)
    }


def test_retriever_initialization(test_collection):
    """Test retriever can be initialized."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    assert retriever is not None


def test_retrieve_basic(test_collection):
    """Test basic retrieval."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    query = "How does CRISPR work?"
    results = retriever.retrieve(query, top_k=3, use_hybrid=False)

    assert len(results) == 3
    assert all('text' in r for r in results)
    assert all('score' in r for r in results)
    assert all('metadata' in r for r in results)


def test_retrieve_relevance(test_collection):
    """Test that retrieval returns relevant results."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    query = "CRISPR genome editing mechanism"
    results = retriever.retrieve(query, top_k=5, use_hybrid=False)

    # Top results should mention CRISPR or Cas9
    top_texts = [r['text'].lower() for r in results[:3]]
    assert any("crispr" in t or "cas9" in t for t in top_texts)


def test_retrieve_with_hybrid_search(test_collection):
    """Test retrieval with hybrid search enabled."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    query = "Doudna Nobel Prize"
    results = retriever.retrieve(query, top_k=3, use_hybrid=True)

    assert len(results) == 3

    # Should have hybrid scores
    assert 'hybrid_score' in results[0]
    assert 'dense_score' in results[0]
    assert 'sparse_score' in results[0]

    # Top result should mention Doudna (exact match helps)
    top_text = results[0]['text'].lower()
    assert "doudna" in top_text


def test_retrieve_exact_term_matching(test_collection):
    """Test that hybrid search improves exact term matching."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    # Query with specific terms that should match exactly
    query = "H2O2 signaling"

    # Dense-only
    dense_results = retriever.retrieve(query, top_k=3, use_hybrid=False)

    # Hybrid
    hybrid_results = retriever.retrieve(query, top_k=3, use_hybrid=True)

    # Hybrid should rank H2O2 document higher
    hybrid_top = hybrid_results[0]['text'].lower()
    assert "h2o2" in hybrid_top or "hydrogen peroxide" in hybrid_top


def test_retrieve_top_k(test_collection):
    """Test that top_k parameter works correctly."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    query = "DNA editing"

    results_3 = retriever.retrieve(query, top_k=3)
    assert len(results_3) == 3

    results_5 = retriever.retrieve(query, top_k=5)
    assert len(results_5) == 5


def test_retrieve_with_auto_adjust_alpha(test_collection):
    """Test adaptive alpha adjustment."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    # Technical query (should favor keywords)
    query1 = "PCR protocol"
    results1 = retriever.retrieve(query1, top_k=2, use_hybrid=True, auto_adjust_alpha=True)

    # Conceptual query (should favor semantics)
    query2 = "gene editing challenges"
    results2 = retriever.retrieve(query2, top_k=2, use_hybrid=True, auto_adjust_alpha=True)

    # Both should return results
    assert len(results1) == 2
    assert len(results2) == 2


def test_get_document_by_id(test_collection):
    """Test retrieving specific document by ID."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    # First get some results to get an ID
    results = retriever.retrieve("CRISPR", top_k=1, use_hybrid=False)
    doc_id = results[0]['id']

    # Retrieve by ID
    doc = retriever.get_document_by_id(doc_id)

    assert doc is not None
    assert doc['id'] == doc_id
    assert 'text' in doc
    assert 'metadata' in doc


def test_retrieve_empty_query(test_collection):
    """Test retrieval with empty query."""
    retriever = SimpleRetriever(
        embedder=test_collection["embedder"],
        vector_store=test_collection["vector_store"],
        collection_name=test_collection["collection_name"]
    )

    # Empty query should still work (will return based on embeddings)
    results = retriever.retrieve("", top_k=1)

    assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
