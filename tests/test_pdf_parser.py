"""
Tests for PDF Parser
"""

import pytest
from pathlib import Path
from backend.retrieval.parsers.pdf import PDFParser


# Test PDF files
TEST_PDF_DIR = Path("tests/test_files_rag/papers")
TEST_PDF_FILES = list(TEST_PDF_DIR.glob("*.pdf")) if TEST_PDF_DIR.exists() else []


@pytest.fixture
def parser():
    """Create PDF parser for tests."""
    return PDFParser()


def test_parser_initialization(parser):
    """Test parser can be initialized."""
    assert parser is not None


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_parse_pdf_basic(parser):
    """Test basic PDF parsing."""
    pdf_path = TEST_PDF_FILES[0]

    result = parser.parse(str(pdf_path))

    # Check required fields
    assert 'text' in result
    assert 'pages' in result
    assert 'metadata' in result
    assert 'num_pages' in result
    assert 'file_name' in result

    # Check content
    assert len(result['text']) > 0
    assert result['num_pages'] > 0
    assert len(result['pages']) > 0


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_parse_pdf_metadata(parser):
    """Test PDF metadata extraction."""
    pdf_path = TEST_PDF_FILES[0]

    result = parser.parse(str(pdf_path))

    metadata = result['metadata']

    # Metadata fields should exist (may be None)
    assert 'title' in metadata
    assert 'author' in metadata
    assert 'creation_date' in metadata


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_parse_pdf_pages(parser):
    """Test page-by-page parsing."""
    pdf_path = TEST_PDF_FILES[0]

    result = parser.parse(str(pdf_path))

    pages = result['pages']

    # Each page should have required fields
    for page in pages:
        assert 'page_number' in page
        assert 'text' in page
        assert 'char_count' in page
        assert len(page['text']) > 0


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_parse_specific_pages(parser):
    """Test parsing specific pages only."""
    pdf_path = TEST_PDF_FILES[0]

    # Parse only first 2 pages
    pages = parser.parse_pages(str(pdf_path), page_numbers=[1, 2])

    assert len(pages) <= 2

    if len(pages) > 0:
        assert pages[0]['page_number'] == 1

    if len(pages) > 1:
        assert pages[1]['page_number'] == 2


@pytest.mark.skipif(len(TEST_PDF_FILES) < 2, reason="Need at least 2 test PDFs")
def test_parse_multiple_pdfs(parser):
    """Test parsing multiple PDF files."""
    results = []

    for pdf_path in TEST_PDF_FILES[:2]:
        result = parser.parse(str(pdf_path))
        results.append(result)

    assert len(results) == 2

    # Each should have extracted content
    for result in results:
        assert len(result['text']) > 0
        assert result['num_pages'] > 0


def test_parse_nonexistent_file(parser):
    """Test error handling for nonexistent file."""
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent_file.pdf")


def test_parse_non_pdf_file(parser):
    """Test error handling for non-PDF file."""
    with pytest.raises(ValueError):
        parser.parse("tests/test_rag_poc.py")


@pytest.mark.skipif(len(TEST_PDF_FILES) == 0, reason="No test PDF files available")
def test_text_cleaning(parser):
    """Test that extracted text is cleaned."""
    pdf_path = TEST_PDF_FILES[0]

    result = parser.parse(str(pdf_path))

    text = result['text']

    # Text should not have excessive whitespace
    assert "\n\n\n\n" not in text  # No excessive newlines

    # Pages should have cleaned text
    for page in result['pages']:
        page_text = page['text']
        # Should not start/end with whitespace
        assert page_text == page_text.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
