"""
Document Extractors Package

Provides type-specific metadata extractors for different document formats.
"""

from backend.retrieval.extractors.pdf_metadata import PDFMetadataExtractor

__all__ = [
    "PDFMetadataExtractor",
]
