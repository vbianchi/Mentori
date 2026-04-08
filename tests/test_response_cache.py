"""Tests for the response cache module."""

import pytest
import time
from backend.retrieval.response_cache import ResponseCache, CacheEntry


class TestResponseCache:
    """Tests for the ResponseCache class."""

    def test_cache_miss(self):
        """Query not in cache should return None."""
        cache = ResponseCache()
        result = cache.get("test query", "test_index", ["doc1", "doc2"])
        assert result is None

    def test_cache_hit(self):
        """Cached response should be retrievable."""
        cache = ResponseCache()
        cache.set("test query", "test_index", ["doc1", "doc2"], "cached response")
        result = cache.get("test query", "test_index", ["doc1", "doc2"])
        assert result == "cached response"

    def test_cache_key_normalization(self):
        """Query should be normalized (lowercase, trimmed)."""
        cache = ResponseCache()
        cache.set("TEST QUERY", "test_index", ["doc1"], "response1")

        # Same query with different case should hit cache
        result = cache.get("test query", "test_index", ["doc1"])
        assert result == "response1"

    def test_cache_key_doc_order_independent(self):
        """Doc IDs should be sorted for consistent cache key."""
        cache = ResponseCache()
        cache.set("query", "index", ["doc2", "doc1", "doc3"], "response")

        # Different doc order should still hit cache
        result = cache.get("query", "index", ["doc1", "doc2", "doc3"])
        assert result == "response"

        result = cache.get("query", "index", ["doc3", "doc2", "doc1"])
        assert result == "response"

    def test_cache_different_queries(self):
        """Different queries should not collide."""
        cache = ResponseCache()
        cache.set("query1", "index", ["doc1"], "response1")
        cache.set("query2", "index", ["doc1"], "response2")

        assert cache.get("query1", "index", ["doc1"]) == "response1"
        assert cache.get("query2", "index", ["doc1"]) == "response2"

    def test_cache_different_indexes(self):
        """Same query on different indexes should not collide."""
        cache = ResponseCache()
        cache.set("query", "index1", ["doc1"], "response1")
        cache.set("query", "index2", ["doc1"], "response2")

        assert cache.get("query", "index1", ["doc1"]) == "response1"
        assert cache.get("query", "index2", ["doc1"]) == "response2"

    def test_ttl_expiration(self):
        """Expired entries should return None."""
        cache = ResponseCache(ttl_seconds=1)  # 1 second TTL
        cache.set("query", "index", ["doc1"], "response")

        # Should hit immediately
        assert cache.get("query", "index", ["doc1"]) == "response"

        # Wait for expiration
        time.sleep(1.1)

        # Should miss after expiration
        assert cache.get("query", "index", ["doc1"]) is None

    def test_max_entries_eviction(self):
        """Oldest entry should be evicted when max reached."""
        cache = ResponseCache(max_entries=3)

        cache.set("query1", "index", ["doc1"], "response1")
        time.sleep(0.01)  # Ensure different timestamps
        cache.set("query2", "index", ["doc1"], "response2")
        time.sleep(0.01)
        cache.set("query3", "index", ["doc1"], "response3")

        # All should be present
        assert cache.get("query1", "index", ["doc1"]) == "response1"
        assert cache.get("query2", "index", ["doc1"]) == "response2"
        assert cache.get("query3", "index", ["doc1"]) == "response3"

        # Add fourth entry - should evict query1 (oldest)
        cache.set("query4", "index", ["doc1"], "response4")

        assert cache.get("query1", "index", ["doc1"]) is None  # Evicted
        assert cache.get("query4", "index", ["doc1"]) == "response4"

    def test_clear_cache(self):
        """Clear should remove all entries."""
        cache = ResponseCache()
        cache.set("query1", "index", ["doc1"], "response1")
        cache.set("query2", "index", ["doc1"], "response2")

        cache.clear()

        assert cache.get("query1", "index", ["doc1"]) is None
        assert cache.get("query2", "index", ["doc1"]) is None

    def test_stats_tracking(self):
        """Cache should track hits and misses."""
        cache = ResponseCache()

        # Miss
        cache.get("query", "index", ["doc1"])
        stats = cache.get_stats()
        assert stats.misses == 1
        assert stats.hits == 0

        # Set and hit
        cache.set("query", "index", ["doc1"], "response")
        cache.get("query", "index", ["doc1"])
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.current_entries == 1

    def test_hit_rate(self):
        """Hit rate should be calculated correctly."""
        cache = ResponseCache()

        # No requests yet
        assert cache.hit_rate == 0.0

        # 1 miss
        cache.get("query1", "index", ["doc1"])
        assert cache.hit_rate == 0.0

        # Add entry and 1 hit
        cache.set("query1", "index", ["doc1"], "response")
        cache.get("query1", "index", ["doc1"])
        assert cache.hit_rate == 0.5  # 1 hit, 1 miss

    def test_empty_response_not_cached(self):
        """Empty responses should not be cached."""
        cache = ResponseCache()
        cache.set("query", "index", ["doc1"], "")

        assert cache.get("query", "index", ["doc1"]) is None

    def test_hit_count_incremented(self):
        """Hit count should increment on each access."""
        cache = ResponseCache()
        cache.set("query", "index", ["doc1"], "response")

        cache.get("query", "index", ["doc1"])
        cache.get("query", "index", ["doc1"])
        cache.get("query", "index", ["doc1"])

        # Access internal state to verify
        key = cache._make_key("query", "index", ["doc1"])
        assert cache._cache[key].hit_count == 3
