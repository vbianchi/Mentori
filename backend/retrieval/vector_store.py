"""
Vector Store for RAG

ChromaDB wrapper for document storage and retrieval.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
import logging
import uuid

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB wrapper for document vector storage.

    Features:
    - Task-scoped collections (isolation per task)
    - Automatic ID generation
    - Metadata support
    - Batch operations
    - Persistent or in-memory storage

    Collection Naming:
    - task_{task_id}: Isolated per task
    - global: Shared across all tasks (future use)
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "default"
    ):
        """
        Initialize vector store.

        Args:
            persist_directory: Path to persist data. None = in-memory.
            collection_name: Default collection name
        """
        # Initialize ChromaDB client
        from backend.config import settings

        # Default to settings if not provided
        target_dir = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        
        self.persist_directory = target_dir

        if target_dir:
            logger.info(f"Initializing ChromaDB with persistence: {target_dir}")
            self.client = chromadb.PersistentClient(path=target_dir)
        else:
            logger.info("Initializing ChromaDB in-memory")
            self.client = chromadb.Client()

        self.default_collection_name = collection_name  # Store default collection name
        self.collections = {}

    def get_collection(
        self,
        collection_name: Optional[str] = None,
        embedding_dimension: int = 384
    ):
        """
        Get or create a collection.

        Args:
            collection_name: Collection name. None = use default.
            embedding_dimension: Expected embedding dimension

        Returns:
            ChromaDB collection
        """
        name = collection_name or self.default_collection_name
        logger.debug(f"get_collection: requested='{collection_name}', resolved='{name}'")

        if name in self.collections:
            return self.collections[name]

        # Get or create collection
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Retrieved existing collection: {name}")
        except Exception:
            collection = self.client.create_collection(
                name=name,
                metadata={"dimension": embedding_dimension}
            )
            logger.info(f"Created new collection: {name}")

        self.collections[name] = collection
        return collection

    def add_documents(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        Add documents to vector store.

        Args:
            texts: Document texts
            embeddings: Document embeddings (N, dimension)
            metadatas: Optional metadata per document
            ids: Optional IDs. Auto-generated if not provided.
            collection_name: Target collection

        Returns:
            List of document IDs
        """
        collection = self.get_collection(
            collection_name,
            embedding_dimension=embeddings.shape[1]
        )

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        # Generate default metadata if not provided
        if metadatas is None:
            metadatas = [{"index": i} for i in range(len(texts))]

        # Add to collection
        collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(texts)} documents to {collection.name}")
        return ids

    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        collection_name: Optional[str] = None,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            collection_name: Target collection
            where: Metadata filter
            where_document: Document content filter

        Returns:
            Dictionary with:
            - ids: List of document IDs
            - documents: List of document texts
            - distances: List of distances (lower = more similar)
            - metadatas: List of metadata dicts
        """
        collection = self.get_collection(collection_name)

        # Ensure query_embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=where,
            where_document=where_document
        )

        return results

    def get_by_ids(
        self,
        ids: List[str],
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents by IDs.

        Args:
            ids: List of document IDs
            collection_name: Target collection

        Returns:
            Dictionary with documents, metadatas, embeddings
        """
        collection = self.get_collection(collection_name)
        results = collection.get(ids=ids)
        return results

    def delete_by_ids(
        self,
        ids: List[str],
        collection_name: Optional[str] = None
    ) -> None:
        """
        Delete documents by IDs.

        Args:
            ids: List of document IDs
            collection_name: Target collection
        """
        collection = self.get_collection(collection_name)
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from {collection.name}")

    def count(self, collection_name: Optional[str] = None) -> int:
        """
        Get document count in collection.

        Args:
            collection_name: Target collection

        Returns:
            Number of documents
        """
        collection = self.get_collection(collection_name)
        return collection.count()

    def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """
        Delete entire collection.

        Args:
            collection_name: Collection to delete. None = default.
        """
        name = collection_name or self.default_collection_name
        self.client.delete_collection(name=name)

        if name in self.collections:
            del self.collections[name]

        logger.info(f"Deleted collection: {name}")

    def list_collections(self) -> List[str]:
        """
        List all collection names.

        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [c.name for c in collections]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer

    # Initialize
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    store = VectorStore(collection_name="test_collection")

    # Documents
    documents = [
        "CRISPR-Cas9 is a genome editing tool.",
        "The polymerase chain reaction amplifies DNA.",
        "Deep learning models predict protein structures."
    ]

    # Embed and store
    embeddings = embedder.encode(documents, convert_to_numpy=True)
    ids = store.add_documents(
        texts=documents,
        embeddings=embeddings,
        metadatas=[{"source": f"doc_{i}"} for i in range(len(documents))]
    )

    print(f"Stored {len(ids)} documents")
    print(f"Collection count: {store.count()}")

    # Search
    query = "How does CRISPR work?"
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    results = store.search(query_embedding, n_results=2)

    print("\nSearch results:")
    for i, doc in enumerate(results['documents'][0]):
        distance = results['distances'][0][i]
        print(f"  {i+1}. [Distance: {distance:.3f}] {doc}")
