import pytest
from pathlib import Path
from backend.retrieval.parsers.pdf import PDFParser

class TestReferenceIntegration:
    
    def setup_method(self):
        self.parser = PDFParser(extract_citations=True)
        self.papers_dir = Path("tests/test_files_rag/papers")
        
    def test_references_in_real_paper(self):
        # We'll use one of the known papers
        # Find a .pdf file in the papers directory
        pdf_files = list(self.papers_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/test_files_rag/papers")
            
        pdf_path = str(pdf_files[0])
        print(f"Testing with file: {pdf_path}")
        
        result = self.parser.parse(pdf_path)
        
        # Verify metadata enhancement
        assert "references" in result
        assert "reference_count" in result["metadata"]
        
        # We expect some references in a scientific paper
        references = result["references"]
        print(f"Found {len(references)} references")
        
        if len(references) > 0:
            # Check structure of first reference
            ref = references[0]
            assert "raw_text" in ref
            assert "authors" in ref
            # Reference should be reasonably long
            assert len(ref["raw_text"]) > 10
