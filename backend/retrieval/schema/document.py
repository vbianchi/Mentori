"""
Universal Document Schema for all document types.

Handles: papers, grants, meeting notes, spreadsheets, code, notebooks, etc.
This schema provides a unified way to store and query metadata across all document types.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class DocumentType(str, Enum):
    """All supported document types."""
    # Scientific
    PAPER = "paper"           # Journal articles, preprints
    REPORT = "report"         # Technical reports, white papers
    GRANT = "grant"           # Grant proposals, applications

    # Meeting/Communication
    MEETING = "meeting"       # Meeting notes, minutes
    PRESENTATION = "presentation"  # Slides, posters

    # Data
    SPREADSHEET = "spreadsheet"   # Excel, CSV
    DATABASE = "database"         # SQLite dumps, etc.

    # Code
    CODE = "code"             # Scripts, modules
    NOTEBOOK = "notebook"     # Jupyter notebooks

    # Bioinformatics-specific
    SEQUENCE = "sequence"     # FASTA, GenBank
    VARIANTS = "variants"     # VCF files
    ALIGNMENT = "alignment"   # BAM/SAM metadata

    # General
    TEXT = "text"             # Plain text, markdown
    UNKNOWN = "unknown"       # Fallback


class PaperMetadata(BaseModel):
    """Paper/manuscript-specific metadata."""
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    publication_date: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None


class GrantMetadata(BaseModel):
    """Grant proposal metadata."""
    funding_agency: Optional[str] = None
    grant_number: Optional[str] = None
    principal_investigator: Optional[str] = None
    budget: Optional[float] = None
    status: Optional[str] = None  # submitted, funded, rejected


class MeetingMetadata(BaseModel):
    """Meeting notes metadata."""
    attendees: List[str] = Field(default_factory=list)
    meeting_date: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)


class SpreadsheetMetadata(BaseModel):
    """Spreadsheet metadata."""
    sheet_names: List[str] = Field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    column_names: List[str] = Field(default_factory=list)
    data_types: Dict[str, str] = Field(default_factory=dict)


class CodeMetadata(BaseModel):
    """Code/notebook metadata."""
    language: Optional[str] = None
    functions: List[str] = Field(default_factory=list)
    classes: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    cell_count: Optional[int] = None  # For notebooks


# =============================================================================
# VLM-Extracted Structured Data
# =============================================================================

class Reference(BaseModel):
    """A parsed bibliographic reference from the References section."""
    ref_id: str  # "[1]", "[14]", "Smith2023", etc.
    authors: List[str] = Field(default_factory=list)
    title: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    raw_text: str = ""  # Original reference text as fallback


class FigureDescription(BaseModel):
    """A figure extracted and described by VLM."""
    figure_id: str  # "Figure 1", "Fig. 2a", etc.
    page: int
    caption: Optional[str] = None  # Caption text if present
    description: str = ""  # VLM-generated description of what it shows
    figure_type: Optional[str] = None  # "plot", "heatmap", "diagram", "microscopy", etc.


class TableDescription(BaseModel):
    """A table extracted and described by VLM."""
    table_id: str  # "Table 1", etc.
    page: int
    caption: Optional[str] = None
    description: str = ""  # VLM-generated description of data/findings
    columns: List[str] = Field(default_factory=list)  # Column headers if extractable
    row_count: Optional[int] = None


class EquationDescription(BaseModel):
    """A notable equation extracted by VLM."""
    equation_id: str  # "Eq. 1", "(1)", etc.
    page: int
    latex: Optional[str] = None  # LaTeX representation if possible
    description: str = ""  # What the equation represents


class PageAnalysisResult(BaseModel):
    """Result of VLM analysis on a single page."""
    page_number: int
    page_type: str = "content"  # "title", "content", "figures", "tables", "references", "appendix", "mixed"

    # Metadata (typically from title pages)
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    doi: Optional[str] = None
    date: Optional[str] = None

    # Content elements found on this page
    figures: List[FigureDescription] = Field(default_factory=list)
    tables: List[TableDescription] = Field(default_factory=list)
    equations: List[EquationDescription] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)

    # Section headings found
    section_headings: List[str] = Field(default_factory=list)

    # Raw text from this page (for validation)
    ocr_text: Optional[str] = None


class ExtractionConfidence(BaseModel):
    """Confidence scores for extracted fields based on OCR validation."""
    title: float = 0.0
    authors: float = 0.0
    abstract: float = 0.0
    figures: float = 1.0  # VLM-only, no validation
    tables: float = 1.0
    references: float = 0.0
    overall: float = 0.0


class DocumentMetadata(BaseModel):
    """
    Universal document metadata schema.

    All fields are optional except doc_id and file_path.
    Type-specific metadata is stored in nested objects.
    """
    # Core identifiers
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    file_name: str
    file_hash: Optional[str] = None  # For deduplication

    # Classification
    doc_type: DocumentType = DocumentType.UNKNOWN

    # Common metadata (applicable to most types)
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    author_variants: List[str] = Field(default_factory=list)  # "V. Bianchi", "Bianchi, V", etc.
    date: Optional[str] = None

    # Structure
    page_count: int = 0
    sections: List[str] = Field(default_factory=list)  # Section headings
    has_abstract: bool = False
    has_tables: bool = False
    has_figures: bool = False

    # Full-text search fields
    searchable_text: Optional[str] = None  # Summary for embedding

    # Type-specific nested metadata
    paper_metadata: Optional[PaperMetadata] = None
    grant_metadata: Optional[GrantMetadata] = None
    meeting_metadata: Optional[MeetingMetadata] = None
    spreadsheet_metadata: Optional[SpreadsheetMetadata] = None
    code_metadata: Optional[CodeMetadata] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # User/collection context
    user_id: Optional[str] = None
    collection_name: Optional[str] = None

    # VLM-extracted structured content
    figures: List[FigureDescription] = Field(default_factory=list)
    tables: List[TableDescription] = Field(default_factory=list)
    equations: List[EquationDescription] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)

    # Extraction metadata
    vlm_model: Optional[str] = None  # e.g., "deepseek-ocr:3b"
    extraction_confidence: Optional[ExtractionConfidence] = None
    page_analyses: List[PageAnalysisResult] = Field(default_factory=list)  # Raw per-page results

    def get_author_search_variants(self) -> List[str]:
        """
        Generate all searchable author name variants.

        For "Valerio Bianchi", generates:
        - V. Bianchi
        - V Bianchi
        - Bianchi V
        - Bianchi, V.
        - Bianchi (just last name)
        """
        variants = set(self.authors)
        variants.update(self.author_variants)

        # Auto-generate variants from full names
        for author in self.authors:
            parts = author.split()
            if len(parts) >= 2:
                first = parts[0]
                last = parts[-1]

                # V. Bianchi
                variants.add(f"{first[0]}. {last}")
                # V Bianchi
                variants.add(f"{first[0]} {last}")
                # Bianchi V
                variants.add(f"{last} {first[0]}")
                # Bianchi, V.
                variants.add(f"{last}, {first[0]}.")
                # Just last name
                variants.add(last)

                # Handle middle names if present
                if len(parts) > 2:
                    middle_initials = "".join(p[0] for p in parts[1:-1])
                    # V.M. Bianchi format
                    variants.add(f"{first[0]}.{middle_initials}. {last}")

        return list(variants)

    def to_search_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary optimized for search indexing.

        Flattens nested metadata and includes all author variants.
        """
        result = {
            "doc_id": self.doc_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "doc_type": self.doc_type.value,
            "title": self.title or "",
            "authors": self.authors,
            "author_variants": self.get_author_search_variants(),
            "date": self.date,
            "page_count": self.page_count,
            "has_abstract": self.has_abstract,
            "has_tables": self.has_tables,
            "has_figures": self.has_figures,
        }

        # Add type-specific metadata if present
        if self.paper_metadata:
            result["journal"] = self.paper_metadata.journal
            result["doi"] = self.paper_metadata.doi
            result["abstract"] = self.paper_metadata.abstract
            result["keywords"] = self.paper_metadata.keywords

        if self.grant_metadata:
            result["funding_agency"] = self.grant_metadata.funding_agency
            result["grant_number"] = self.grant_metadata.grant_number
            result["pi"] = self.grant_metadata.principal_investigator

        if self.meeting_metadata:
            result["attendees"] = self.meeting_metadata.attendees
            result["action_items"] = self.meeting_metadata.action_items

        # Add VLM-extracted content counts
        result["figure_count"] = len(self.figures)
        result["table_count"] = len(self.tables)
        result["reference_count"] = len(self.references)
        result["vlm_model"] = self.vlm_model

        return result

    def get_reference(self, ref_id: str) -> Optional[Reference]:
        """
        Look up a reference by its ID (e.g., "[1]", "[14]").

        Useful for resolving citations in retrieved chunks.
        """
        # Normalize ref_id (handle "[1]" vs "1" vs "[1].")
        normalized = ref_id.strip().strip("[]().").strip()

        for ref in self.references:
            ref_normalized = ref.ref_id.strip().strip("[]().").strip()
            if ref_normalized == normalized:
                return ref

        return None

    def resolve_citations(self, text: str) -> str:
        """
        Replace citation markers in text with full reference info.

        Example:
            "as shown in [1]" -> "as shown in [1: Smith et al. (2023) 'Title']"
        """
        import re

        # Find all citation patterns like [1], [14], [1,2,3], [1-3]
        citation_pattern = r'\[(\d+(?:[-,]\d+)*)\]'

        def replace_citation(match):
            citation_text = match.group(0)
            ref_ids = match.group(1)

            # Handle ranges like "1-3" and lists like "1,2,3"
            expanded_refs = []
            for part in ref_ids.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-')
                    expanded_refs.extend(str(i) for i in range(int(start), int(end) + 1))
                else:
                    expanded_refs.append(part)

            # Look up each reference
            ref_summaries = []
            for ref_id in expanded_refs:
                ref = self.get_reference(ref_id)
                if ref:
                    # Build short summary
                    authors_str = ref.authors[0] if ref.authors else "Unknown"
                    if len(ref.authors) > 1:
                        authors_str += " et al."
                    year = ref.year or "n.d."
                    ref_summaries.append(f"{authors_str} ({year})")

            if ref_summaries:
                return f"{citation_text}: {'; '.join(ref_summaries)}"
            return citation_text

        return re.sub(citation_pattern, replace_citation, text)
