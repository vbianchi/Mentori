"""
RAG Retrieval Infrastructure for Mentori

Provides document ingestion, embedding generation, and semantic search
capabilities for scientific document analysis.
"""

from backend.retrieval.embeddings import EmbeddingEngine
from backend.retrieval.vector_store import VectorStore
from backend.retrieval.chunking import SimpleChunker, MarkdownChunker
from backend.retrieval.ingestor import SimpleIngestor
from backend.retrieval.retriever import SimpleRetriever
from backend.retrieval.hybrid_search import HybridSearchEngine, AdaptiveHybridSearch

__all__ = [
    "EmbeddingEngine",
    "VectorStore",
    "SimpleChunker",
    "MarkdownChunker",
    "SimpleIngestor",
    "SimpleRetriever",
    "HybridSearchEngine",
    "AdaptiveHybridSearch",
]
