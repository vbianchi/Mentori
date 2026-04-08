"""
Tests for Vector Store
"""

import pytest
import numpy as np
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.embeddings import EmbeddingEngine


@pytest.fixture
def embedder():
    """Create embedding engine for tests."""
    return EmbeddingEngine()


@pytest.fixture
def vector_store():
    """Create in-memory vector store for tests."""
    return VectorStore(collection_name="test_collection")


def test_vector_store_initialization(vector_store):
    """Test vector store can be initialized."""
    assert vector_store is not None
    assert vector_store.default_collection_name == "test_collection"


def test_add_and_count_documents(vector_store, embedder):
    """Test adding documents and counting."""
    texts = ["Document 1", "Document 2", "Document 3"]
    embeddings = embedder.embed_documents(texts)

    ids = vector_store.add_documents(
        texts=texts,
        embeddings=embeddings
    )

    assert len(ids) == 3
    assert vector_store.count() == 3


def test_search_documents(vector_store, embedder):
    """Test searching for similar documents."""
    # Add documents
    documents = [
        "CRISPR-Cas9 is a genome editing tool.",
        "The Cas9 enzyme cuts DNA sequences.",
        "Python is a programming language."
    ]

    embeddings = embedder.embed_documents(documents)
    vector_store.add_documents(texts=documents, embeddings=embeddings)

    # Search
    query = "How does CRISPR work?"
    query_emb = embedder.embed_query(query)
    results = vector_store.search(query_emb, n_results=2)

    assert len(results['ids'][0]) == 2
    assert len(results['documents'][0]) == 2

    # Top result should be CRISPR-related
    top_doc = results['documents'][0][0]
    assert "CRISPR" in top_doc or "Cas9" in top_doc


def test_get_by_ids(vector_store, embedder):
    """Test retrieving documents by ID."""
    texts = ["Doc 1", "Doc 2", "Doc 3"]
    embeddings = embedder.embed_documents(texts)

    ids = vector_store.add_documents(texts=texts, embeddings=embeddings)

    # Get specific documents
    results = vector_store.get_by_ids(ids[:2])

    assert len(results['ids']) == 2
    assert results['documents'][0] == "Doc 1"
    assert results['documents'][1] == "Doc 2"


def test_delete_documents(vector_store, embedder):
    """Test deleting documents."""
    texts = ["Doc 1", "Doc 2", "Doc 3"]
    embeddings = embedder.embed_documents(texts)

    ids = vector_store.add_documents(texts=texts, embeddings=embeddings)

    assert vector_store.count() == 3

    # Delete one document
    vector_store.delete_by_ids([ids[0]])

    assert vector_store.count() == 2


def test_metadata_storage(vector_store, embedder):
    """Test storing and retrieving metadata."""
    texts = ["Doc 1", "Doc 2"]
    embeddings = embedder.embed_documents(texts)

    metadatas = [
        {"source": "file1.pdf", "page": 1},
        {"source": "file2.pdf", "page": 5}
    ]

    ids = vector_store.add_documents(
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    # Retrieve and check metadata
    results = vector_store.get_by_ids([ids[0]])
    assert results['metadatas'][0]['source'] == "file1.pdf"
    assert results['metadatas'][0]['page'] == 1


def test_multiple_collections():
    """Test using multiple collections."""
    store = VectorStore()
    embedder = EmbeddingEngine()

    # Add to collection 1
    texts1 = ["Collection 1 doc"]
    emb1 = embedder.embed_documents(texts1)
    store.add_documents(texts=texts1, embeddings=emb1, collection_name="col1")

    # Add to collection 2
    texts2 = ["Collection 2 doc"]
    emb2 = embedder.embed_documents(texts2)
    store.add_documents(texts=texts2, embeddings=emb2, collection_name="col2")

    # Check counts
    assert store.count("col1") == 1
    assert store.count("col2") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
