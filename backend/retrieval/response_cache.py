"""
Semantic response cache for RAG queries.

Caches responses by hash of (query + index_name + retrieved doc IDs).
This avoids redundant LLM calls for identical queries against the same documents.

Thread-safe implementation using a simple dict with TTL eviction.
"""
import hashlib
import time
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached response with metadata."""
    response: str
    created_at: float
    doc_ids: List[str]
    hit_count: int = 0


@dataclass
class CacheStats:
    """Statistics for cache monitoring."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_entries: int = 0


class ResponseCache:
    """
    In-memory cache for RAG query responses.

    Features:
    - TTL-based expiration (default 1 hour)
    - LRU-style eviction when max entries reached
    - Thread-safe operations
    - Hit/miss statistics for monitoring
    """

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 1000):
        """
        Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
            max_entries: Maximum number of entries before eviction (default 1000)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._stats = CacheStats()

    def _make_key(self, query: str, index_name: str, doc_ids: List[str]) -> str:
        """
        Create a deterministic cache key from query parameters.

        The key is based on:
        - The query text (normalized to lowercase)
        - The index name
        - Sorted list of document IDs (order-independent)
        """
        normalized_query = query.strip().lower()
        sorted_doc_ids = sorted(doc_ids) if doc_ids else []
        content = f"{normalized_query}||{index_name}||{'|'.join(sorted_doc_ids)}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(self, query: str, index_name: str, doc_ids: List[str]) -> Optional[str]:
        """
        Retrieve a cached response if available and not expired.

        Args:
            query: The search query
            index_name: The RAG index name
            doc_ids: List of retrieved document IDs

        Returns:
            Cached response string, or None if not found/expired
        """
        key = self._make_key(query, index_name, doc_ids)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            # Check TTL expiration
            if time.time() - entry.created_at > self.ttl:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                self._stats.current_entries = len(self._cache)
                logger.debug(f"Cache entry expired for query: {query[:50]}...")
                return None

            # Cache hit
            entry.hit_count += 1
            self._stats.hits += 1
            logger.info(f"Cache hit for query: {query[:50]}... (hits: {entry.hit_count})")
            return entry.response

    def set(self, query: str, index_name: str, doc_ids: List[str], response: str):
        """
        Store a response in the cache.

        Args:
            query: The search query
            index_name: The RAG index name
            doc_ids: List of retrieved document IDs
            response: The response to cache
        """
        if not response:
            return

        key = self._make_key(query, index_name, doc_ids)

        with self._lock:
            # Evict oldest entry if at capacity
            if len(self._cache) >= self.max_entries:
                self._evict_oldest()

            self._cache[key] = CacheEntry(
                response=response,
                created_at=time.time(),
                doc_ids=doc_ids
            )
            self._stats.current_entries = len(self._cache)
            logger.debug(f"Cached response for query: {query[:50]}...")

    def _evict_oldest(self):
        """Evict the oldest cache entry (by creation time)."""
        if not self._cache:
            return

        oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]
        self._stats.evictions += 1
        logger.debug("Evicted oldest cache entry")

    def invalidate(self, index_name: str):
        """
        Invalidate all cache entries for a specific index.

        Call this when documents are added/removed from an index.

        Args:
            index_name: The index to invalidate
        """
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                # We can't easily check index_name from the hash,
                # so this is a simple clear-all approach
                # A more sophisticated implementation could store index_name in entry
                pass

            # For now, just clear the entire cache when invalidation is requested
            count = len(self._cache)
            self._cache.clear()
            self._stats.current_entries = 0
            self._stats.evictions += count
            logger.info(f"Invalidated cache for index {index_name} ({count} entries)")

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.current_entries = 0
            self._stats.evictions += count
            logger.info(f"Cleared cache ({count} entries)")

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            self._stats.current_entries = len(self._cache)
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                current_entries=self._stats.current_entries
            )

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._stats.hits + self._stats.misses
        return self._stats.hits / total if total > 0 else 0.0


# Global singleton instance
response_cache = ResponseCache()
