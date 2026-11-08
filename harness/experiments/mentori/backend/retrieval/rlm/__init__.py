"""
RLM - Recursive Language Model for Scientific Document Analysis

This module implements a true RLM approach where:
1. Documents are treated as external environment (not fed directly to LLM)
2. LLM writes code to navigate, filter, and extract from documents
3. Recursive sub-LLM calls process specific content chunks
4. All synthesis is grounded with mandatory citation tracking
"""

from .context import RLMContext, Citation, CitationType, ChunkResult, DocumentInfo
from .executor import RLMExecutor
from .orchestrator import RLMOrchestrator
from .summarizer import CitationGroundedSummarizer

__all__ = [
    "RLMContext",
    "RLMExecutor",
    "RLMOrchestrator",
    "CitationGroundedSummarizer",
    "Citation",
    "CitationType",
    "ChunkResult",
    "DocumentInfo",
]
