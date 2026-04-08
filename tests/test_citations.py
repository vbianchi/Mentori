import pytest
from backend.retrieval.parsers.citations import CitationExtractor
from backend.retrieval.bibliography import BibliographyGenerator

class TestCitationExtractor:
    
    def setup_method(self):
        self.extractor = CitationExtractor()
        
    def test_extract_author_year_citations(self):
        text = "This method was first proposed by (Smith, 2020) and later refined (Jones et al., 2021)."
        citations = self.extractor.extract_citations(text)
        
        assert len(citations) == 2
        
        # Check first citation
        assert citations[0]["text"] == "(Smith, 2020)"
        assert citations[0]["type"] == "author-year"
        assert citations[0]["authors"] == ["Smith"]
        assert citations[0]["year"] == "2020"
        
        # Check second citation
        assert citations[1]["text"] == "(Jones et al., 2021)"
        assert citations[1]["authors"] == ["Jones"]
        assert citations[1]["year"] == "2021"

    def test_extract_numbered_citations(self):
        text = "Deep learning has revolutionized the field [1]. Others argue different approaches [2-5] work better."
        citations = self.extractor.extract_citations(text)
        
        assert len(citations) == 2
        
        assert citations[0]["text"] == "[1]"
        assert citations[0]["type"] == "numbered"
        assert citations[0]["numbers"] == ["1"]
        
        assert citations[1]["text"] == "[2-5]"
        assert citations[1]["numbers"] == ["2-5"]

    def test_extract_dois(self):
        text = "The paper can be found at https://doi.org/10.1038/s41586-020-2649-2 or 10.1101/2020.05.01.072942."
        dois = self.extractor.extract_dois(text)
        
        assert len(dois) == 2
        assert "10.1038/s41586-020-2649-2" in dois
        assert "10.1101/2020.05.01.072942" in dois

    def test_extract_references_numbered(self):
        # Add filler text so "References" is in the second half
        filler = "\n".join([f"Page {i} content..." for i in range(20)])
        text = f"""
        {filler}
        
        References
        
        [1] Smith, J. (2020). Deep Learning. Nature.
        
        [2] Doe, A. (2021). Transformers. Science, 10.1126/science.12345.
        """
        refs = self.extractor.extract_references(text)
        
        assert len(refs) == 2
        assert refs[0]["index"] == 1
        assert "Smith" in refs[0]["raw_text"]
        assert refs[0]["year"] == "2020"
        
        assert refs[1]["index"] == 2
        assert refs[1]["doi"] == "10.1126/science.12345"

class TestBibliographyGenerator:
    
    def setup_method(self):
        self.generator = BibliographyGenerator()
        self.sample_ref = {
            "authors": ["Doe, J.", "Smith, A."],
            "year": "2023",
            "title": "A Great Paper",
            "journal": "Journal of Science",
            "volume": "10",
            "doi": "10.1000/xyz"
        }
        
    def test_format_apa(self):
        result = self.generator.generate([self.sample_ref], style="apa")
        assert "Doe, J., & Smith, A." in result
        assert "(2023)." in result
        assert "A Great Paper." in result
        assert "*Journal of Science*, *10*." in result
        assert "https://doi.org/10.1000/xyz" in result
        
    def test_format_ieee(self):
        result = self.generator.generate([self.sample_ref], style="ieee")
        assert "[1]" in result
        assert "Doe, J., Smith, A." in result
        assert "\"A Great Paper,\"" in result
        assert "in *Journal of Science*, 2023." in result
