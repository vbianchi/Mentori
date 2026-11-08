"""
File Router - Detects file type and routes to appropriate extractor.

Supports scientific documents, spreadsheets, code, and bioinformatics formats.
"""

import mimetypes
import logging
from pathlib import Path
from typing import Tuple, Optional, Type

from backend.retrieval.schema.document import DocumentType

logger = logging.getLogger(__name__)


class FileRouter:
    """
    Detect file type and route to appropriate extractor.

    Uses extension mapping and MIME type detection to classify files.
    """

    EXTENSION_MAP = {
        # Documents
        '.pdf': DocumentType.PAPER,  # Default, may be refined by content
        '.doc': DocumentType.TEXT,
        '.docx': DocumentType.TEXT,
        '.txt': DocumentType.TEXT,
        '.md': DocumentType.TEXT,
        '.rtf': DocumentType.TEXT,
        '.odt': DocumentType.TEXT,

        # Spreadsheets
        '.xlsx': DocumentType.SPREADSHEET,
        '.xls': DocumentType.SPREADSHEET,
        '.csv': DocumentType.SPREADSHEET,
        '.tsv': DocumentType.SPREADSHEET,
        '.ods': DocumentType.SPREADSHEET,

        # Code
        '.py': DocumentType.CODE,
        '.js': DocumentType.CODE,
        '.ts': DocumentType.CODE,
        '.jsx': DocumentType.CODE,
        '.tsx': DocumentType.CODE,
        '.r': DocumentType.CODE,
        '.R': DocumentType.CODE,
        '.sh': DocumentType.CODE,
        '.bash': DocumentType.CODE,
        '.sql': DocumentType.CODE,
        '.java': DocumentType.CODE,
        '.cpp': DocumentType.CODE,
        '.c': DocumentType.CODE,
        '.go': DocumentType.CODE,
        '.rs': DocumentType.CODE,
        '.rb': DocumentType.CODE,
        '.pl': DocumentType.CODE,
        '.ipynb': DocumentType.NOTEBOOK,

        # Bioinformatics
        '.fasta': DocumentType.SEQUENCE,
        '.fa': DocumentType.SEQUENCE,
        '.fna': DocumentType.SEQUENCE,
        '.faa': DocumentType.SEQUENCE,
        '.fastq': DocumentType.SEQUENCE,
        '.fq': DocumentType.SEQUENCE,
        '.vcf': DocumentType.VARIANTS,
        '.vcf.gz': DocumentType.VARIANTS,
        '.bam': DocumentType.ALIGNMENT,
        '.sam': DocumentType.ALIGNMENT,
        '.cram': DocumentType.ALIGNMENT,
        '.gff': DocumentType.SEQUENCE,
        '.gff3': DocumentType.SEQUENCE,
        '.gtf': DocumentType.SEQUENCE,
        '.bed': DocumentType.SEQUENCE,
        '.gb': DocumentType.SEQUENCE,
        '.gbk': DocumentType.SEQUENCE,

        # Presentations
        '.pptx': DocumentType.PRESENTATION,
        '.ppt': DocumentType.PRESENTATION,
        '.odp': DocumentType.PRESENTATION,

        # Database
        '.sqlite': DocumentType.DATABASE,
        '.db': DocumentType.DATABASE,
        '.sqlite3': DocumentType.DATABASE,
    }

    # MIME type fallback mapping
    MIME_MAP = {
        'application/pdf': DocumentType.PAPER,
        'text/plain': DocumentType.TEXT,
        'text/markdown': DocumentType.TEXT,
        'text/csv': DocumentType.SPREADSHEET,
        'application/vnd.ms-excel': DocumentType.SPREADSHEET,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': DocumentType.SPREADSHEET,
        'application/json': DocumentType.TEXT,
        'text/x-python': DocumentType.CODE,
        'application/x-ipynb+json': DocumentType.NOTEBOOK,
    }

    @classmethod
    def detect_type(cls, file_path: str) -> Tuple[DocumentType, str]:
        """
        Detect document type from file.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (DocumentType, mime_type)
        """
        path = Path(file_path)

        # Handle compound extensions (e.g., .vcf.gz)
        full_suffix = ''.join(path.suffixes).lower()
        ext = path.suffix.lower()

        # Check compound extension first
        if full_suffix in cls.EXTENSION_MAP:
            doc_type = cls.EXTENSION_MAP[full_suffix]
        elif ext in cls.EXTENSION_MAP:
            doc_type = cls.EXTENSION_MAP[ext]
        else:
            doc_type = DocumentType.UNKNOWN

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'

        # If extension didn't match, try MIME type
        if doc_type == DocumentType.UNKNOWN and mime_type in cls.MIME_MAP:
            doc_type = cls.MIME_MAP[mime_type]

        logger.debug(f"Detected type for {path.name}: {doc_type.value} (MIME: {mime_type})")

        return doc_type, mime_type

    @classmethod
    def get_extractor_class(cls, doc_type: DocumentType):
        """
        Get the appropriate extractor class for a document type.

        Args:
            doc_type: The document type

        Returns:
            Extractor class or None if not supported
        """
        # Import here to avoid circular imports
        from backend.retrieval.extractors.pdf_metadata import PDFMetadataExtractor

        # Future extractors would be imported here:
        # from backend.retrieval.extractors.spreadsheet import SpreadsheetExtractor
        # from backend.retrieval.extractors.code import CodeExtractor
        # from backend.retrieval.extractors.bioinformatics import SequenceExtractor

        extractors = {
            DocumentType.PAPER: PDFMetadataExtractor,
            DocumentType.REPORT: PDFMetadataExtractor,
            DocumentType.GRANT: PDFMetadataExtractor,
            DocumentType.MEETING: PDFMetadataExtractor,  # PDFs of meeting notes
            DocumentType.PRESENTATION: PDFMetadataExtractor,  # Exported as PDF
            # Future:
            # DocumentType.SPREADSHEET: SpreadsheetExtractor,
            # DocumentType.CODE: CodeExtractor,
            # DocumentType.NOTEBOOK: CodeExtractor,
            # DocumentType.SEQUENCE: SequenceExtractor,
            # DocumentType.VARIANTS: SequenceExtractor,
        }

        return extractors.get(doc_type)

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        Check if a file type is supported for ingestion.

        Args:
            file_path: Path to file

        Returns:
            True if file type is supported
        """
        doc_type, _ = cls.detect_type(file_path)
        return cls.get_extractor_class(doc_type) is not None

    @classmethod
    def get_supported_extensions(cls) -> list:
        """Get list of all supported file extensions."""
        return list(cls.EXTENSION_MAP.keys())

    @classmethod
    def classify_by_content(cls, file_path: str, text_sample: str) -> DocumentType:
        """
        Refine document type classification based on content analysis.

        For PDFs, this can distinguish between papers, grants, meeting notes, etc.

        Args:
            file_path: Path to file
            text_sample: Sample of document text (first ~2000 chars)

        Returns:
            Refined DocumentType
        """
        text_lower = text_sample.lower()

        # Check for grant-specific indicators
        grant_indicators = [
            'specific aims', 'budget justification', 'research strategy',
            'nih', 'nsf', 'grant proposal', 'funding', 'principal investigator',
            'co-investigator', 'subcontract'
        ]
        if sum(1 for ind in grant_indicators if ind in text_lower) >= 2:
            return DocumentType.GRANT

        # Check for meeting notes indicators
        meeting_indicators = [
            'meeting notes', 'minutes', 'attendees', 'action items',
            'agenda', 'next meeting', 'discussed'
        ]
        if sum(1 for ind in meeting_indicators if ind in text_lower) >= 2:
            return DocumentType.MEETING

        # Check for technical report indicators
        report_indicators = [
            'technical report', 'white paper', 'internal report',
            'confidential', 'version', 'revision'
        ]
        if sum(1 for ind in report_indicators if ind in text_lower) >= 2:
            return DocumentType.REPORT

        # Check for paper indicators
        paper_indicators = [
            'abstract', 'introduction', 'methods', 'results', 'discussion',
            'references', 'doi', 'journal', 'volume', 'issue'
        ]
        if sum(1 for ind in paper_indicators if ind in text_lower) >= 3:
            return DocumentType.PAPER

        # Default based on extension
        doc_type, _ = cls.detect_type(file_path)
        return doc_type
