"""
Tests for Document Ingestor
"""

import pytest
import tempfile
import os
from pathlib import Path
from backend.retrieval.ingestor import SimpleIngestor


# Test PDF files
TEST_PDF_DIR = Path("tests/test_files_rag/papers")
TEST_PDF_FILES = list(TEST_PDF_DIR.glob("*.pdf")) if TEST_PDF_DIR.exists() else []


@pytest.fixture
def ingestor():
    """Create ingestor with in-memory storage for tests."""
    return SimpleIngestor(collection_name="test_ingest")


def test_ingestor_initialization(ingestor):
    """Test ingestor can be initialized."""
    assert ingestor is not None
    assert ingestor.embedder is not None
    assert ingestor.vector_store is not None
    assert ingestor.chunker is not None


def test_ingest_text_file(ingestor):
    """Test ingesting a plain text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document about CRISPR-Cas9 genome editing.")
        temp_path = f.name

    try:
        result = ingestor.ingest_file(temp_path)

        assert result['status'] == 'success'
        assert result['num_chunks'] > 0
        assert result['total_tokens'] > 0
        assert 'chunk_ids' in result

        # Check storage
        stats = ingestor.get_ingestion_stats()
        assert stats['total_chunks'] > 0

    finally:
        os.unlink(temp_path)


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_ingest_pdf_file(ingestor):
    """Test ingesting a PDF file."""
    pdf_path = TEST_PDF_FILES[0]

    result = ingestor.ingest_file(str(pdf_path))

    assert result['status'] == 'success'
    assert result['num_chunks'] > 0
    assert result['total_tokens'] > 0
    assert result['num_pages'] > 0
    assert result['file_name'] == pdf_path.name


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_ingest_with_custom_metadata(ingestor):
    """Test ingesting with custom metadata."""
    pdf_path = TEST_PDF_FILES[0]

    metadata = {
        "category": "scientific_paper",
        "year": 2020
    }

    result = ingestor.ingest_file(str(pdf_path), metadata=metadata)

    assert result['status'] == 'success'

    # Retrieve a chunk and check metadata
    chunk_id = result['chunk_ids'][0]
    doc = ingestor.vector_store.get_by_ids([chunk_id])

    assert doc['metadatas'][0]['category'] == "scientific_paper"
    assert doc['metadatas'][0]['year'] == 2020


def test_ingest_empty_file(ingestor):
    """Test ingesting an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("")
        temp_path = f.name

    try:
        result = ingestor.ingest_file(temp_path)

        # Should skip empty files
        assert result['status'] == 'skipped'

    finally:
        os.unlink(temp_path)


def test_ingest_unsupported_file_type(ingestor):
    """Test error handling for unsupported file types."""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        temp_path = f.name

    try:
        result = ingestor.ingest_file(temp_path)

        assert result['status'] == 'error'
        assert 'error' in result

    finally:
        os.unlink(temp_path)


@pytest.mark.skipif(len(TEST_PDF_FILES) < 2, reason="Need at least 2 test PDFs")
def test_ingest_directory(ingestor):
    """Test ingesting all files from a directory."""
    result = ingestor.ingest_directory(str(TEST_PDF_DIR), pattern="*.pdf")

    assert result['status'] == 'completed'
    assert result['successful'] > 0
    assert result['total_chunks'] > 0
    assert len(result['results']) > 0


def test_ingest_directory_no_files(ingestor):
    """Test ingesting from directory with no matching files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = ingestor.ingest_directory(tmpdir, pattern="*.pdf")

        assert result['status'] == 'no_files'


def test_get_ingestion_stats(ingestor):
    """Test getting ingestion statistics."""
    # Ingest a test document
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test document for statistics.")
        temp_path = f.name

    try:
        ingestor.ingest_file(temp_path)

        stats = ingestor.get_ingestion_stats()

        assert 'collection' in stats
        assert 'total_chunks' in stats
        assert 'embedding_dimension' in stats
        assert 'model_name' in stats
        assert stats['total_chunks'] > 0

    finally:
        os.unlink(temp_path)


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_ingest_large_pdf(ingestor):
    """Test ingesting a larger PDF file."""
    # Find the largest PDF
    largest_pdf = max(TEST_PDF_FILES, key=lambda p: p.stat().st_size)

    result = ingestor.ingest_file(str(largest_pdf))

    assert result['status'] == 'success'
    assert result['num_chunks'] > 5  # Should have multiple chunks
    assert result['num_pages'] > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
