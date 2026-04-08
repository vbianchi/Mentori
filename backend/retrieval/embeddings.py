"""
Embedding Generation for RAG

Handles text-to-vector conversion using sentence-transformers.
"""

from typing import List, Dict, Any, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


# ── Embedding Model Registry ────────────────────────────────────────────────
# Entries are ordered from lightweight → heavyweight.
# "dimension" is informational; the actual value comes from the loaded model.

EMBEDDING_MODELS: Dict[str, Dict[str, Any]] = {
    "all-MiniLM-L6-v2": {
        "dimension": 384,
        "description": "Fast, general-purpose (default for dev/testing)",
        "category": "general",
    },
    "allenai/specter2": {
        "dimension": 768,
        "description": "Trained on scientific papers — best for research corpora",
        "category": "scientific",
    },
    "BAAI/bge-m3": {
        "dimension": 1024,
        "description": "Multilingual, high quality, larger model",
        "category": "multilingual",
    },
    "all-mpnet-base-v2": {
        "dimension": 768,
        "description": "High-quality general-purpose (production grade)",
        "category": "general",
    },
}


def get_available_models() -> List[Dict[str, Any]]:
    """Return the list of supported embedding models for frontend display."""
    return [
        {"name": name, **info}
        for name, info in EMBEDDING_MODELS.items()
    ]


_embedding_cache: Dict[str, "EmbeddingEngine"] = {}


class EmbeddingEngine:
    """
    Generates embeddings for text using sentence-transformers.

    Features:
    - Batched encoding for efficiency
    - Automatic normalization
    - Dimension introspection
    - Support for queries and documents
    - Singleton per model_name to prevent MPS memory leaks

    Model Recommendations (from V2-1 experiment, 30-paper scientific corpus):
    - Production/Default: BAAI/bge-m3 (1024 dim, MRR=0.918 — best at all scales)
    - Lightweight: all-MiniLM-L6-v2 (384 dim, MRR=0.863 — dev/testing only)
    - Avoid: allenai/specter2 (MRR collapses from 0.793→0.406 at 30 papers)
    """

    def __new__(cls, model_name: str = "BAAI/bge-m3", normalize: bool = True, device: str = "auto"):
        if model_name in _embedding_cache:
            logger.debug(f"Reusing cached EmbeddingEngine for {model_name}")
            return _embedding_cache[model_name]
        instance = super().__new__(cls)
        instance._initialized = False
        return instance

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        normalize: bool = True,
        device: str = "auto"
    ):
        """
        Initialize embedding engine.

        Args:
            model_name: HuggingFace model identifier
            normalize: Whether to L2-normalize embeddings
            device: Device to run on ('cpu', 'cuda', 'mps', 'auto').
                    'auto' picks the best available GPU backend.
        """
        if self._initialized:
            return
        self.model_name = model_name
        self.normalize = normalize
        self.model = None  # Lazy-loaded on first embed call
        self._device_setting = device  # Resolved when model loads
        self.device = None
        self.dimension = None
        self._initialized = True
        _embedding_cache[model_name] = self

    def _ensure_model(self):
        """Load the SentenceTransformer model on first use (lazy loading).

        This avoids allocating ~1.7 GB of GPU/CPU memory at import time,
        which caused kernel panics when multiple experiment processes
        each loaded the model during __init__.
        """
        if self.model is not None:
            return

        device = self._device_setting
        if device == "auto":
            import os
            import torch
            env_device = os.environ.get("MENTORI_EMBED_DEVICE")
            if env_device:
                device = env_device
            elif torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device

        logger.info(f"Loading embedding model: {self.model_name} (device={device})")
        try:
            self.model = SentenceTransformer(self.model_name, device=device, local_files_only=True)
            logger.info(f"Loaded {self.model_name} from local cache")
        except Exception:
            logger.info(f"Downloading {self.model_name} (first time)...")
            self.model = SentenceTransformer(self.model_name, device=device)
            logger.info(f"Downloaded and loaded {self.model_name}")
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_documents(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Embed a batch of documents.

        Args:
            texts: List of document texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Array of embeddings, shape (N, dimension)
        """
        if not texts:
            return np.array([])

        self._ensure_model()
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True
        )

        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query.

        Args:
            query: Query text

        Returns:
            Embedding vector, shape (dimension,)
        """
        self._ensure_model()
        embedding = self.model.encode(
            query,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True
        )

        return embedding

    def embed_batch(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Unified interface for embedding single or multiple texts.

        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Embeddings array
        """
        if isinstance(texts, str):
            return self.embed_query(texts)
        else:
            return self.embed_documents(texts, batch_size, show_progress)

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        self._ensure_model()
        return self.dimension

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize engine
    embedder = EmbeddingEngine(model_name="all-MiniLM-L6-v2")

    # Test documents
    documents = [
        "CRISPR-Cas9 is a genome editing tool.",
        "The system uses guide RNA to target DNA sequences.",
        "Off-target effects remain a significant challenge."
    ]

    # Embed documents
    doc_embeddings = embedder.embed_documents(documents, show_progress=True)
    print(f"Document embeddings shape: {doc_embeddings.shape}")

    # Embed query
    query = "How does CRISPR work?"
    query_embedding = embedder.embed_query(query)
    print(f"Query embedding shape: {query_embedding.shape}")

    # Compute similarities
    from numpy.linalg import norm
    similarities = doc_embeddings @ query_embedding / (
        norm(doc_embeddings, axis=1) * norm(query_embedding)
    )

    print("\nSimilarities:")
    for i, (doc, sim) in enumerate(zip(documents, similarities)):
        print(f"  {i+1}. [{sim:.3f}] {doc}")
