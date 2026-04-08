import pytest
from unittest.mock import MagicMock, patch
from backend.retrieval.planner import DocumentAnalyzer, IngestionStrategy

@pytest.fixture
def mock_pdf_doc():
    with patch("fitz.open") as mock_open:
        doc = MagicMock()
        mock_open.return_value = doc
        yield doc

def test_planner_detects_text_pdf(mock_pdf_doc):
    # Setup standard text PDF page
    page = MagicMock()
    page.get_text.return_value = "This is a normal text PDF with plenty of characters." * 10
    mock_pdf_doc.__iter__.return_value = [page]
    
    analyzer = DocumentAnalyzer()
    strategy = analyzer.analyze("dummy.pdf")
    
    assert strategy.is_scanned == False
    assert strategy.page_strategies[0].action == "text"

def test_planner_detects_scanned_pdf(mock_pdf_doc):
    # Setup canned/image PDF page (low text)
    page = MagicMock()
    page.get_text.return_value = " "
    mock_pdf_doc.__iter__.return_value = [page]
    
    analyzer = DocumentAnalyzer()
    strategy = analyzer.analyze("dummy.pdf")
    
    assert strategy.is_scanned == True
    assert strategy.page_strategies[0].action == "ocr"
