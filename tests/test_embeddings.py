"""
Tests for Embedding Engine
"""

import pytest
import numpy as np
from backend.retrieval.embeddings import EmbeddingEngine


def test_embedding_engine_initialization():
    """Test embedding engine can be initialized."""
    embedder = EmbeddingEngine(model_name="all-MiniLM-L6-v2")

    assert embedder is not None
    assert embedder.get_dimension() == 384
    assert embedder.get_model_name() == "all-MiniLM-L6-v2"


def test_embed_single_query():
    """Test embedding a single query."""
    embedder = EmbeddingEngine()

    query = "What is CRISPR-Cas9?"
    embedding = embedder.embed_query(query)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert not np.isnan(embedding).any()


def test_embed_multiple_documents():
    """Test embedding multiple documents."""
    embedder = EmbeddingEngine()

    documents = [
        "CRISPR-Cas9 is a genome editing tool.",
        "The Cas9 enzyme cuts DNA at specific sites.",
        "Guide RNA directs Cas9 to target sequences."
    ]

    embeddings = embedder.embed_documents(documents)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)
    assert not np.isnan(embeddings).any()


def test_embeddings_are_normalized():
    """Test that embeddings are L2-normalized."""
    embedder = EmbeddingEngine(normalize=True)

    query = "Test query"
    embedding = embedder.embed_query(query)

    # Check L2 norm is approximately 1
    norm = np.linalg.norm(embedding)
    assert abs(norm - 1.0) < 0.01


def test_embeddings_similarity():
    """Test that similar texts have high cosine similarity."""
    embedder = EmbeddingEngine()

    doc1 = "CRISPR-Cas9 is a genome editing tool."
    doc2 = "Cas9 is used for genome editing."
    doc3 = "The weather is nice today."

    emb1 = embedder.embed_query(doc1)
    emb2 = embedder.embed_query(doc2)
    emb3 = embedder.embed_query(doc3)

    # Cosine similarity
    sim_12 = np.dot(emb1, emb2)
    sim_13 = np.dot(emb1, emb3)

    # Similar documents should have higher similarity
    assert sim_12 > sim_13
    assert sim_12 > 0.5  # Should be reasonably high


def test_batch_interface():
    """Test the unified batch interface."""
    embedder = EmbeddingEngine()

    # Single string
    single_emb = embedder.embed_batch("Test query")
    assert single_emb.shape == (384,)

    # List of strings
    batch_emb = embedder.embed_batch(["Query 1", "Query 2"])
    assert batch_emb.shape == (2, 384)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
