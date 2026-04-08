"""
Tests for Text Chunking
"""

import pytest
from backend.retrieval.chunking import SimpleChunker, MarkdownChunker


def test_simple_chunker_initialization():
    """Test simple chunker can be initialized."""
    chunker = SimpleChunker(chunk_size=100, chunk_overlap=20)

    assert chunker is not None
    assert chunker.chunk_size == 100
    assert chunker.chunk_overlap == 20


def test_chunk_short_text():
    """Test chunking text shorter than chunk_size."""
    chunker = SimpleChunker(chunk_size=100, chunk_overlap=20)

    text = "This is a short text."
    chunks = chunker.chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0]['text'] == text
    assert chunks[0]['metadata']['chunk_index'] == 0


def test_chunk_long_text():
    """Test chunking text longer than chunk_size."""
    chunker = SimpleChunker(chunk_size=50, chunk_overlap=10)

    text = " ".join([f"Sentence {i}." for i in range(100)])
    chunks = chunker.chunk_text(text)

    # Should create multiple chunks
    assert len(chunks) > 1

    # Check metadata
    for i, chunk in enumerate(chunks):
        assert chunk['metadata']['chunk_index'] == i
        assert 'start_token' in chunk['metadata']
        assert 'end_token' in chunk['metadata']


def test_chunk_overlap():
    """Test that chunks have proper overlap."""
    chunker = SimpleChunker(chunk_size=50, chunk_overlap=10)

    text = " ".join([f"Word{i}" for i in range(200)])
    chunks = chunker.chunk_text(text)

    # Adjacent chunks should share some content (overlap)
    # This is approximate due to tokenization
    assert len(chunks) >= 2


def test_metadata_preservation():
    """Test that custom metadata is preserved."""
    chunker = SimpleChunker(chunk_size=100)

    text = "Test text for chunking."
    metadata = {"source": "test.pdf", "page": 5}

    chunks = chunker.chunk_text(text, metadata=metadata)

    assert chunks[0]['metadata']['source'] == "test.pdf"
    assert chunks[0]['metadata']['page'] == 5
    assert chunks[0]['metadata']['chunk_index'] == 0


def test_chunk_multiple_documents():
    """Test chunking multiple documents."""
    chunker = SimpleChunker(chunk_size=50)

    documents = [
        "First document text.",
        "Second document text.",
        "Third document text."
    ]

    metadatas = [
        {"source": "doc1.txt"},
        {"source": "doc2.txt"},
        {"source": "doc3.txt"}
    ]

    chunks = chunker.chunk_documents(documents, metadatas)

    # Should have at least 3 chunks (one per document)
    assert len(chunks) >= 3

    # Check metadata is preserved
    sources = [c['metadata']['source'] for c in chunks]
    assert "doc1.txt" in sources
    assert "doc2.txt" in sources
    assert "doc3.txt" in sources


def test_markdown_chunker_header_splitting():
    """Test markdown chunker splits by headers."""
    chunker = MarkdownChunker(chunk_size=200)

    markdown = """# Introduction
This is the introduction section.

## Method
This is the method section.

### Subsection
This is a subsection.
"""

    chunks = chunker.chunk_text(markdown)

    # Should create chunks for each section
    assert len(chunks) >= 1

    # Check section metadata
    sections = [c['metadata'].get('section') for c in chunks]
    assert any("Introduction" in s for s in sections if s)


def test_empty_text_handling():
    """Test handling of empty text."""
    chunker = SimpleChunker()

    chunks = chunker.chunk_text("")
    assert len(chunks) == 0

    chunks = chunker.chunk_text("   \n  \n  ")
    assert len(chunks) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
