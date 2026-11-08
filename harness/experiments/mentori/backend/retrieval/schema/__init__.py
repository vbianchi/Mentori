"""
Document Schema Package

Provides universal document schema and SQLite registry for metadata storage.
"""

from backend.retrieval.schema.document import (
    DocumentType,
    DocumentMetadata,
    PaperMetadata,
    GrantMetadata,
    MeetingMetadata,
    SpreadsheetMetadata,
    CodeMetadata,
)
from backend.retrieval.schema.registry import DocumentRegistry

__all__ = [
    "DocumentType",
    "DocumentMetadata",
    "PaperMetadata",
    "GrantMetadata",
    "MeetingMetadata",
    "SpreadsheetMetadata",
    "CodeMetadata",
    "DocumentRegistry",
]
