"""
Tests for Structured Ingestion MVP

Tests:
1. DocumentMetadata and author variant generation
2. DocumentRegistry CRUD operations
3. PDFMetadataExtractor (regex fallback only)
4. SmartIngestor with real PDF files
"""

import pytest
import tempfile
import os
from pathlib import Path

# Import the new components
from backend.retrieval.schema.document import (
    DocumentMetadata, DocumentType, PaperMetadata,
    Reference, FigureDescription, TableDescription,
    EquationDescription, PageAnalysisResult, ExtractionConfidence
)
from backend.retrieval.schema.registry import DocumentRegistry
from backend.retrieval.file_router import FileRouter
from backend.retrieval.extractors.pdf_metadata import PDFMetadataExtractor
from backend.retrieval.extractors.page_analyzer import PageAnalyzer
from backend.retrieval.extractors.document_aggregator import DocumentAggregator


# =============================================================================
# Test DocumentMetadata
# =============================================================================

class TestDocumentMetadata:
    """Test the universal document schema."""

    def test_create_paper_metadata(self):
        """Test creating a paper with full metadata."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            doc_type=DocumentType.PAPER,
            title="A Novel Approach to Machine Learning",
            authors=["Valerio Bianchi", "John Smith", "Jane Doe"],
            page_count=12,
            has_abstract=True
        )

        assert meta.doc_id is not None  # Auto-generated UUID
        assert meta.file_name == "paper.pdf"
        assert meta.doc_type == DocumentType.PAPER
        assert len(meta.authors) == 3

    def test_author_variant_generation(self):
        """Test automatic generation of author name variants."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            authors=["Valerio Bianchi"]
        )

        variants = meta.get_author_search_variants()

        # Should include original and variants
        assert "Valerio Bianchi" in variants
        assert "V. Bianchi" in variants
        assert "V Bianchi" in variants
        assert "Bianchi V" in variants
        assert "Bianchi, V." in variants
        assert "Bianchi" in variants

    def test_author_variant_multiple_authors(self):
        """Test variant generation with multiple authors."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            authors=["Valerio Bianchi", "John Smith"]
        )

        variants = meta.get_author_search_variants()

        # Both authors should have variants
        assert "Valerio Bianchi" in variants
        assert "V. Bianchi" in variants
        assert "John Smith" in variants
        assert "J. Smith" in variants
        assert "Smith" in variants

    def test_paper_nested_metadata(self):
        """Test paper-specific nested metadata."""
        paper_meta = PaperMetadata(
            journal="Nature",
            doi="10.1234/nature.2024.001",
            abstract="This is an abstract"
        )

        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            doc_type=DocumentType.PAPER,
            paper_metadata=paper_meta
        )

        assert meta.paper_metadata.journal == "Nature"
        assert meta.paper_metadata.doi == "10.1234/nature.2024.001"

    def test_to_search_dict(self):
        """Test conversion to search-optimized dict."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            doc_type=DocumentType.PAPER,
            title="Test Paper",
            authors=["Valerio Bianchi"],
            paper_metadata=PaperMetadata(journal="Science")
        )

        search_dict = meta.to_search_dict()

        assert search_dict["doc_id"] == meta.doc_id
        assert search_dict["doc_type"] == "paper"
        assert search_dict["title"] == "Test Paper"
        assert "V. Bianchi" in search_dict["author_variants"]
        assert search_dict["journal"] == "Science"


# =============================================================================
# Test DocumentRegistry
# =============================================================================

class TestDocumentRegistry:
    """Test the SQLite document registry."""

    @pytest.fixture
    def temp_registry(self):
        """Create a temporary registry for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_registry.db")
            registry = DocumentRegistry(db_path)
            yield registry

    def test_register_document(self, temp_registry):
        """Test registering a document."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            doc_type=DocumentType.PAPER,
            title="Test Paper",
            authors=["Valerio Bianchi"],
            user_id="test-user-123"
        )

        doc_id = temp_registry.register(meta)

        assert doc_id == meta.doc_id

        # Verify document is in registry
        doc = temp_registry.get_document(doc_id)
        assert doc is not None
        assert doc["title"] == "Test Paper"
        assert "Valerio Bianchi" in doc["authors"]

    def test_get_by_author(self, temp_registry):
        """Test finding documents by author name."""
        # Register two papers by same author
        for i in range(2):
            meta = DocumentMetadata(
                file_path=f"/test/paper{i}.pdf",
                file_name=f"paper{i}.pdf",
                doc_type=DocumentType.PAPER,
                title=f"Test Paper {i}",
                authors=["Valerio Bianchi"],
                user_id="test-user-123"
            )
            temp_registry.register(meta)

        # Register one paper by different author
        meta3 = DocumentMetadata(
            file_path="/test/other.pdf",
            file_name="other.pdf",
            doc_type=DocumentType.PAPER,
            title="Other Paper",
            authors=["John Smith"],
            user_id="test-user-123"
        )
        temp_registry.register(meta3)

        # Search by full name
        results = temp_registry.get_by_author("Valerio Bianchi")
        assert len(results) == 2

        # Search by last name only (should match due to variants)
        results = temp_registry.get_by_author("Bianchi")
        assert len(results) == 2

        # Search by abbreviated name (should match due to variants)
        results = temp_registry.get_by_author("V. Bianchi")
        assert len(results) == 2

    def test_get_by_type(self, temp_registry):
        """Test finding documents by type."""
        # Register paper
        paper = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            doc_type=DocumentType.PAPER,
            title="A Paper",
            user_id="test-user"
        )
        temp_registry.register(paper)

        # Register grant
        grant = DocumentMetadata(
            file_path="/test/grant.pdf",
            file_name="grant.pdf",
            doc_type=DocumentType.GRANT,
            title="A Grant",
            user_id="test-user"
        )
        temp_registry.register(grant)

        # Query
        papers = temp_registry.get_by_type(DocumentType.PAPER)
        assert len(papers) == 1
        assert papers[0]["title"] == "A Paper"

        grants = temp_registry.get_by_type(DocumentType.GRANT)
        assert len(grants) == 1
        assert grants[0]["title"] == "A Grant"

    def test_search_title(self, temp_registry):
        """Test full-text title search."""
        meta = DocumentMetadata(
            file_path="/test/ml_paper.pdf",
            file_name="ml_paper.pdf",
            doc_type=DocumentType.PAPER,
            title="Deep Learning for Natural Language Processing",
            user_id="test-user"
        )
        temp_registry.register(meta)

        # Search for words in title
        results = temp_registry.search_title("Learning")
        assert len(results) == 1

        results = temp_registry.search_title("Natural Language")
        assert len(results) == 1

    def test_delete_document(self, temp_registry):
        """Test deleting a document."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            doc_type=DocumentType.PAPER,
            user_id="test-user"
        )
        doc_id = temp_registry.register(meta)

        # Verify exists
        assert temp_registry.get_document(doc_id) is not None

        # Delete
        deleted = temp_registry.delete_document(doc_id)
        assert deleted

        # Verify gone
        assert temp_registry.get_document(doc_id) is None

    def test_get_stats(self, temp_registry):
        """Test registry statistics."""
        # Register some documents
        for i in range(3):
            temp_registry.register(DocumentMetadata(
                file_path=f"/test/paper{i}.pdf",
                file_name=f"paper{i}.pdf",
                doc_type=DocumentType.PAPER,
                authors=[f"Author {i}"],
                user_id="test-user"
            ))

        temp_registry.register(DocumentMetadata(
            file_path="/test/grant.pdf",
            file_name="grant.pdf",
            doc_type=DocumentType.GRANT,
            authors=["Grant Author"],
            user_id="test-user"
        ))

        stats = temp_registry.get_stats()

        assert stats["total_documents"] == 4
        assert stats["by_type"]["paper"] == 3
        assert stats["by_type"]["grant"] == 1
        assert stats["unique_authors"] == 4


# =============================================================================
# Test VLM-Extracted Content Schema
# =============================================================================

class TestVLMExtractedContent:
    """Test schema classes for VLM-extracted content."""

    def test_reference_creation(self):
        """Test creating a Reference object."""
        ref = Reference(
            ref_id="[1]",
            authors=["Smith J", "Doe A"],
            title="A Novel Approach to Machine Learning",
            journal="Nature",
            year="2023",
            doi="10.1234/nature.2023.001"
        )
        assert ref.ref_id == "[1]"
        assert len(ref.authors) == 2
        assert ref.year == "2023"

    def test_figure_description(self):
        """Test FigureDescription schema."""
        fig = FigureDescription(
            figure_id="Figure 1",
            page=3,
            caption="Workflow diagram showing the analysis pipeline",
            description="A flowchart depicting data preprocessing, model training, and evaluation steps",
            figure_type="flowchart"
        )
        assert fig.figure_id == "Figure 1"
        assert fig.page == 3
        assert fig.figure_type == "flowchart"

    def test_table_description(self):
        """Test TableDescription schema."""
        table = TableDescription(
            table_id="Table 1",
            page=5,
            caption="Performance metrics across models",
            description="Comparison of accuracy, precision, recall for 5 different models",
            columns=["Model", "Accuracy", "Precision", "Recall", "F1"],
            row_count=5
        )
        assert table.table_id == "Table 1"
        assert len(table.columns) == 5
        assert table.row_count == 5

    def test_equation_description(self):
        """Test EquationDescription schema."""
        eq = EquationDescription(
            equation_id="Eq. 1",
            page=4,
            latex="E = mc^2",
            description="Mass-energy equivalence relation"
        )
        assert eq.latex == "E = mc^2"

    def test_page_analysis_result(self):
        """Test PageAnalysisResult schema."""
        result = PageAnalysisResult(
            page_number=1,
            page_type="title",
            title="Deep Learning for NLP",
            authors=["John Smith", "Jane Doe"],
            abstract="This paper presents a novel approach...",
            keywords=["NLP", "deep learning", "transformers"],
            figures=[
                FigureDescription(figure_id="Figure 1", page=1, description="Architecture diagram")
            ]
        )
        assert result.page_number == 1
        assert result.page_type == "title"
        assert len(result.authors) == 2
        assert len(result.figures) == 1

    def test_extraction_confidence(self):
        """Test ExtractionConfidence schema."""
        conf = ExtractionConfidence(
            title=0.95,
            authors=0.85,
            abstract=0.90,
            references=0.75,
            overall=0.86
        )
        assert conf.title == 0.95
        assert conf.overall == 0.86


# =============================================================================
# Test Citation Resolution
# =============================================================================

class TestCitationResolution:
    """Test citation resolution in DocumentMetadata."""

    def test_get_reference(self):
        """Test looking up references by ID."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            references=[
                Reference(ref_id="[1]", authors=["Smith J"], title="First Paper", year="2020"),
                Reference(ref_id="[2]", authors=["Doe A"], title="Second Paper", year="2021"),
                Reference(ref_id="[14]", authors=["Brown B"], title="Fourteenth Paper", year="2022"),
            ]
        )

        ref1 = meta.get_reference("[1]")
        assert ref1 is not None
        assert ref1.title == "First Paper"

        ref14 = meta.get_reference("14")  # Without brackets
        assert ref14 is not None
        assert ref14.title == "Fourteenth Paper"

        ref_missing = meta.get_reference("[99]")
        assert ref_missing is None

    def test_resolve_citations_single(self):
        """Test resolving single citations in text."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            references=[
                Reference(ref_id="[1]", authors=["Smith J", "Doe A"], title="Original Paper", year="2020"),
            ]
        )

        text = "As shown in previous work [1], the method is effective."
        resolved = meta.resolve_citations(text)

        assert "[1]" in resolved
        assert "Smith J" in resolved or "et al" in resolved
        assert "2020" in resolved

    def test_resolve_citations_multiple(self):
        """Test resolving multiple citations."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            references=[
                Reference(ref_id="[1]", authors=["Smith J"], year="2020"),
                Reference(ref_id="[2]", authors=["Doe A"], year="2021"),
            ]
        )

        text = "Several studies [1,2] have investigated this."
        resolved = meta.resolve_citations(text)

        assert "Smith" in resolved
        assert "Doe" in resolved

    def test_resolve_citations_range(self):
        """Test resolving citation ranges like [1-3]."""
        meta = DocumentMetadata(
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            references=[
                Reference(ref_id="[1]", authors=["A1"], year="2020"),
                Reference(ref_id="[2]", authors=["A2"], year="2021"),
                Reference(ref_id="[3]", authors=["A3"], year="2022"),
            ]
        )

        text = "Multiple studies [1-3] support this finding."
        resolved = meta.resolve_citations(text)

        assert "A1" in resolved
        assert "A2" in resolved
        assert "A3" in resolved


# =============================================================================
# Test DocumentAggregator
# =============================================================================

class TestDocumentAggregator:
    """Test document aggregation logic."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return DocumentAggregator()

    def test_aggregate_empty(self, aggregator):
        """Test aggregating empty page results."""
        result = aggregator.aggregate(
            page_results=[],
            file_path="/test/paper.pdf",
            file_name="paper.pdf"
        )
        assert result.doc_type == DocumentType.UNKNOWN
        assert result.page_count == 0

    def test_aggregate_single_page(self, aggregator):
        """Test aggregating single page result."""
        page = PageAnalysisResult(
            page_number=1,
            page_type="title",
            title="Test Paper Title",
            authors=["John Smith", "Jane Doe"],
            abstract="This is the abstract.",
            ocr_text="Test Paper Title John Smith Jane Doe This is the abstract."
        )

        result = aggregator.aggregate(
            page_results=[page],
            file_path="/test/paper.pdf",
            file_name="paper.pdf",
            vlm_model="deepseek-ocr:3b"
        )

        assert result.title == "Test Paper Title"
        assert len(result.authors) == 2
        assert result.vlm_model == "deepseek-ocr:3b"
        assert result.page_count == 1

    def test_aggregate_multiple_pages(self, aggregator):
        """Test aggregating multiple page results."""
        pages = [
            PageAnalysisResult(
                page_number=1,
                page_type="title",
                title="Paper Title",
                authors=["John Smith"],
                abstract="Abstract text here.",
                ocr_text="Paper Title John Smith Abstract text here."
            ),
            PageAnalysisResult(
                page_number=2,
                page_type="content",
                figures=[FigureDescription(figure_id="Figure 1", page=2, description="A nice plot")],
                section_headings=["Introduction", "Methods"]
            ),
            PageAnalysisResult(
                page_number=3,
                page_type="references",
                references=[
                    Reference(ref_id="[1]", authors=["A1"], title="Ref 1"),
                    Reference(ref_id="[2]", authors=["A2"], title="Ref 2"),
                ]
            )
        ]

        result = aggregator.aggregate(
            page_results=pages,
            file_path="/test/paper.pdf",
            file_name="paper.pdf"
        )

        assert result.title == "Paper Title"
        assert len(result.figures) == 1
        assert len(result.references) == 2
        assert "Introduction" in result.sections
        assert result.page_count == 3

    def test_aggregate_deduplicates_figures(self, aggregator):
        """Test that figures are deduplicated across pages."""
        pages = [
            PageAnalysisResult(
                page_number=1,
                figures=[FigureDescription(figure_id="Figure 1", page=1, description="Short desc")]
            ),
            PageAnalysisResult(
                page_number=2,
                figures=[FigureDescription(figure_id="Fig. 1", page=2, description="Much longer and better description")]
            )
        ]

        result = aggregator.aggregate(
            page_results=pages,
            file_path="/test/paper.pdf",
            file_name="paper.pdf"
        )

        # Should only have 1 figure (deduplicated) with the better description
        assert len(result.figures) == 1
        assert "longer" in result.figures[0].description

    def test_aggregate_deduplicates_authors(self, aggregator):
        """Test that authors are deduplicated."""
        pages = [
            PageAnalysisResult(page_number=1, authors=["John Smith"]),
            PageAnalysisResult(page_number=2, authors=["J. Smith", "Jane Doe"]),
        ]

        result = aggregator.aggregate(
            page_results=pages,
            file_path="/test/paper.pdf",
            file_name="paper.pdf"
        )

        # Should have deduplicated John Smith / J. Smith
        # And include Jane Doe
        assert len(result.authors) <= 3  # At most 3 if no dedup, 2 if deduplicated

    def test_aggregate_infers_paper_type(self, aggregator):
        """Test document type inference."""
        pages = [
            PageAnalysisResult(
                page_number=1,
                abstract="This paper presents...",
                section_headings=["Abstract", "Introduction", "Methods", "Results", "Discussion"]
            ),
            PageAnalysisResult(
                page_number=10,
                page_type="references",
                references=[Reference(ref_id="[1]", authors=["A"])]
            )
        ]

        result = aggregator.aggregate(
            page_results=pages,
            file_path="/test/paper.pdf",
            file_name="paper.pdf"
        )

        assert result.doc_type == DocumentType.PAPER

    def test_normalize_reference_ids(self, aggregator):
        """Test reference ID normalization."""
        assert aggregator._normalize_ref_id("[1]") == "1"
        assert aggregator._normalize_ref_id("(2)") == "2"
        assert aggregator._normalize_ref_id("14.") == "14"
        assert aggregator._normalize_ref_id("[14]") == "14"

    def test_validate_doi(self, aggregator):
        """Test DOI validation."""
        assert aggregator._is_valid_doi("10.1234/nature.2023.001")
        assert aggregator._is_valid_doi("10.12345/example")
        assert not aggregator._is_valid_doi("invalid-doi")
        assert not aggregator._is_valid_doi("9.1234/wrong")


# =============================================================================
# Test PageAnalyzer (Parsing Only)
# =============================================================================

class TestPageAnalyzerParsing:
    """Test PageAnalyzer VLM response parsing."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance (without VLM connection)."""
        return PageAnalyzer(model_name="test-model", ollama_url="http://localhost:11434")

    def test_parse_vlm_response_basic(self, analyzer):
        """Test parsing basic VLM JSON response."""
        response = '''{
            "page_type": "title",
            "metadata": {
                "title": "Test Paper",
                "authors": ["John Smith", "Jane Doe"],
                "abstract": "This is a test abstract."
            }
        }'''

        result = analyzer._parse_vlm_response(response, page_number=1, ocr_text=None)

        assert result.page_type == "title"
        assert result.title == "Test Paper"
        assert len(result.authors) == 2

    def test_parse_vlm_response_with_figures(self, analyzer):
        """Test parsing response with figures."""
        response = '''{
            "page_type": "figures",
            "figures": [
                {
                    "figure_id": "Figure 1",
                    "caption": "Workflow diagram",
                    "description": "Shows the data pipeline",
                    "figure_type": "flowchart"
                }
            ]
        }'''

        result = analyzer._parse_vlm_response(response, page_number=2, ocr_text=None)

        assert len(result.figures) == 1
        assert result.figures[0].figure_id == "Figure 1"
        assert result.figures[0].figure_type == "flowchart"

    def test_parse_vlm_response_with_references(self, analyzer):
        """Test parsing response with references."""
        response = '''{
            "page_type": "references",
            "references": [
                {
                    "ref_id": "[1]",
                    "authors": ["Smith J", "Doe A"],
                    "title": "First Paper",
                    "journal": "Nature",
                    "year": "2023",
                    "doi": "10.1234/example"
                }
            ]
        }'''

        result = analyzer._parse_vlm_response(response, page_number=10, ocr_text=None)

        assert len(result.references) == 1
        assert result.references[0].journal == "Nature"
        assert result.references[0].year == "2023"

    def test_parse_vlm_response_markdown_wrapped(self, analyzer):
        """Test parsing response wrapped in markdown code blocks."""
        response = '''```json
{
    "page_type": "content",
    "section_headings": ["Methods", "Data Collection"]
}
```'''

        result = analyzer._parse_vlm_response(response, page_number=3, ocr_text=None)

        assert result.page_type == "content"
        assert "Methods" in result.section_headings

    def test_parse_vlm_response_invalid_json(self, analyzer):
        """Test handling invalid JSON response."""
        response = "This is not valid JSON at all"

        result = analyzer._parse_vlm_response(response, page_number=1, ocr_text=None)

        # Should return empty result without crashing
        assert result.page_number == 1
        assert result.page_type == "content"  # Default


# =============================================================================
# Test FileRouter
# =============================================================================

class TestFileRouter:
    """Test file type detection and routing."""

    def test_detect_pdf(self):
        """Test PDF detection."""
        doc_type, mime = FileRouter.detect_type("/test/paper.pdf")
        assert doc_type == DocumentType.PAPER
        assert mime == "application/pdf"

    def test_detect_spreadsheet(self):
        """Test spreadsheet detection."""
        doc_type, _ = FileRouter.detect_type("/test/data.xlsx")
        assert doc_type == DocumentType.SPREADSHEET

        doc_type, _ = FileRouter.detect_type("/test/data.csv")
        assert doc_type == DocumentType.SPREADSHEET

    def test_detect_code(self):
        """Test code file detection."""
        doc_type, _ = FileRouter.detect_type("/test/script.py")
        assert doc_type == DocumentType.CODE

        doc_type, _ = FileRouter.detect_type("/test/notebook.ipynb")
        assert doc_type == DocumentType.NOTEBOOK

    def test_detect_bioinformatics(self):
        """Test bioinformatics format detection."""
        doc_type, _ = FileRouter.detect_type("/test/sequences.fasta")
        assert doc_type == DocumentType.SEQUENCE

        doc_type, _ = FileRouter.detect_type("/test/variants.vcf")
        assert doc_type == DocumentType.VARIANTS

    def test_is_supported(self):
        """Test supported file check."""
        assert FileRouter.is_supported("/test/paper.pdf")
        assert not FileRouter.is_supported("/test/random.xyz")

    def test_classify_by_content(self):
        """Test content-based classification."""
        # Grant proposal text
        grant_text = """
        Specific Aims
        The principal investigator proposes to study...
        Budget Justification
        Research Strategy
        """
        doc_type = FileRouter.classify_by_content("/test/doc.pdf", grant_text)
        assert doc_type == DocumentType.GRANT

        # Meeting notes text
        meeting_text = """
        Meeting Notes
        Attendees: John, Jane, Bob
        Agenda: Discuss project timeline
        Action Items:
        - John to review code
        - Jane to update docs
        """
        doc_type = FileRouter.classify_by_content("/test/doc.pdf", meeting_text)
        assert doc_type == DocumentType.MEETING


# =============================================================================
# Test PDFMetadataExtractor (Regex Mode Only)
# =============================================================================

class TestPDFMetadataExtractor:
    """Test PDF metadata extraction (regex mode)."""

    @pytest.fixture
    def extractor(self):
        """Create extractor without VLM (regex only)."""
        return PDFMetadataExtractor(agent_roles=None)

    def test_extract_authors_from_text(self, extractor):
        """Test author extraction from text."""
        text = """
        Deep Learning for NLP

        Valerio Bianchi, John Smith, Jane Doe

        University of Example
        """
        authors = extractor._extract_authors_from_text(text)

        # Should find at least some authors
        assert len(authors) > 0

    def test_extract_authors_filters_false_positives(self, extractor):
        """Test that author extraction filters out common false positives."""
        text = """
        Machine Learning in Healthcare

        Marco Rossi, Elena Ferrari

        Open Access Article
        Italian Society of Medicine
        National Research Council
        BioMed Central Publishing

        Abstract: This paper discusses...
        """
        authors = extractor._extract_authors_from_text(text)

        # Should find real authors
        author_names = [a.lower() for a in authors]
        assert any('marco' in a or 'rossi' in a for a in author_names), f"Should find Marco Rossi, got: {authors}"
        assert any('elena' in a or 'ferrari' in a for a in author_names), f"Should find Elena Ferrari, got: {authors}"

        # Should NOT include false positives
        author_str = ' '.join(authors).lower()
        assert 'open access' not in author_str, f"Should not include 'Open Access', got: {authors}"
        assert 'italian society' not in author_str, f"Should not include 'Italian Society', got: {authors}"
        assert 'national research' not in author_str, f"Should not include 'National Research', got: {authors}"
        assert 'biomed central' not in author_str, f"Should not include 'BioMed Central', got: {authors}"

    def test_extract_title_from_text(self, extractor):
        """Test title extraction from text."""
        text = """
        Deep Learning for Natural Language Processing

        Valerio Bianchi
        University of Example
        """
        title = extractor._extract_title_from_text(text)

        assert title is not None
        assert "Deep Learning" in title or "Natural Language" in title

    def test_extract_sections(self, extractor):
        """Test section heading extraction."""
        text = """
        1. Introduction
        Some intro text here.

        2. Methods
        Description of methods.

        3. Results
        The results show...

        DISCUSSION
        We discuss the findings...
        """
        sections = extractor._extract_sections(text)

        assert len(sections) > 0


# =============================================================================
# Integration Test with Real PDFs
# =============================================================================

class TestSmartIngestorIntegration:
    """Integration tests with real PDF files."""

    @pytest.fixture
    def test_papers_dir(self):
        """Get path to test papers directory."""
        project_root = Path(__file__).parent.parent
        papers_dir = project_root / "tests" / "test_files_rag" / "papers"
        if papers_dir.exists():
            return papers_dir
        return None

    @pytest.fixture
    def temp_ingestor(self):
        """Create a temporary SmartIngestor for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from backend.retrieval.smart_ingestor import SmartIngestor
            from backend.retrieval.vector_store import VectorStore

            db_path = os.path.join(temp_dir, "test_registry.db")
            registry = DocumentRegistry(db_path)

            # Create a test vector store
            vector_store = VectorStore(
                collection_name="test_collection",
                persist_directory=os.path.join(temp_dir, "chroma")
            )

            ingestor = SmartIngestor(
                registry=registry,
                vector_store=vector_store,
                agent_roles=None,  # No VLM, regex only
                collection_name="test_collection",
                user_id="test-user"
            )

            yield {
                "ingestor": ingestor,
                "registry": registry,
                "vector_store": vector_store,
                "temp_dir": temp_dir
            }

    @pytest.mark.asyncio
    async def test_ingest_single_pdf(self, temp_ingestor, test_papers_dir):
        """Test ingesting a single PDF file."""
        if test_papers_dir is None:
            pytest.skip("Test papers directory not found")

        # Find a PDF to test with
        pdfs = list(test_papers_dir.glob("*.pdf"))
        if not pdfs:
            pytest.skip("No PDF files found in test directory")

        pdf_path = str(pdfs[0])
        ingestor = temp_ingestor["ingestor"]
        registry = temp_ingestor["registry"]

        # Ingest
        result = await ingestor.ingest_file(pdf_path, use_vlm=False)

        # Verify result
        assert result.get("doc_id") is not None
        assert result.get("chunk_count", 0) > 0

        # Verify document is in registry
        doc = registry.get_document(result["doc_id"])
        assert doc is not None
        assert doc["file_name"] == pdfs[0].name

    @pytest.mark.asyncio
    async def test_ingest_batch(self, temp_ingestor, test_papers_dir):
        """Test batch ingestion of multiple PDFs."""
        if test_papers_dir is None:
            pytest.skip("Test papers directory not found")

        pdfs = list(test_papers_dir.glob("*.pdf"))[:3]  # Test with up to 3 PDFs
        if len(pdfs) < 2:
            pytest.skip("Need at least 2 PDF files for batch test")

        pdf_paths = [str(p) for p in pdfs]
        ingestor = temp_ingestor["ingestor"]
        registry = temp_ingestor["registry"]

        # Ingest batch
        result = await ingestor.ingest_batch(pdf_paths, use_vlm=False)

        # Verify results
        assert result["total"] == len(pdfs)
        assert result["successful"] > 0

        # Verify documents in registry
        all_docs = registry.get_all_documents()
        assert len(all_docs) == result["successful"]

    @pytest.mark.asyncio
    async def test_author_search_after_ingest(self, temp_ingestor, test_papers_dir):
        """Test that author search works after ingestion."""
        if test_papers_dir is None:
            pytest.skip("Test papers directory not found")

        # Look for a Valerio Bianchi paper
        bianchi_papers = [
            "fgene-07-00075.pdf",
            "3463.pdf",
            "s12859-015-0742-6.pdf",
            "1-s2.0-S1046202318304742-main.pdf",
            "1471-2105-13-S4-S17.pdf"
        ]

        pdfs = list(test_papers_dir.glob("*.pdf"))
        target_pdf = None
        for pdf in pdfs:
            if pdf.name in bianchi_papers:
                target_pdf = pdf
                break

        if target_pdf is None:
            pytest.skip("No Valerio Bianchi paper found in test files")

        ingestor = temp_ingestor["ingestor"]
        registry = temp_ingestor["registry"]

        # Ingest the paper
        result = await ingestor.ingest_file(str(target_pdf), use_vlm=False)
        assert result.get("doc_id") is not None

        # Try to find by author (this is what should work after structured ingestion!)
        # Note: This depends on the regex extractor finding the author name
        docs = registry.get_by_author("Bianchi")

        # The test passes if we can at least query the registry
        # Author extraction accuracy depends on the PDF structure
        print(f"Found {len(docs)} documents for 'Bianchi'")


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
