import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_CACHE_SIZE: int = 10_000


@dataclass
class CacheStats:
    """Running counters for cache effectiveness.

    Attributes:
        hits: Number of lookups that found a cached embedding.
        misses: Number of lookups that found nothing cached.
        evictions: Number of entries removed to stay within capacity.
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Return the cache hit rate as a fraction between 0.0 and 1.0."""
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


class EmbeddingCache:
    """Fixed-capacity, in-memory LRU cache mapping text -> embedding vector."""

    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE) -> None:
        """Initialize the cache.

        Args:
            max_size: Maximum number of entries retained. The
                least-recently-used entry is evicted once this limit is
                exceeded.
        """
        self._max_size = max_size
        self._store: OrderedDict[str, list[float]] = OrderedDict()
        self.stats = CacheStats()

    @staticmethod
    def _make_key(text: str, model_name: str) -> str:
        """Compute a stable cache key from text and model name.

        Args:
            text: The text that was (or will be) embedded.
            model_name: The embedding model identifier, included so the
                same text cached under different models never collides.

        Returns:
            A SHA-256 hex digest uniquely identifying this (model, text)
            pair.
        """
        payload = f"{model_name}\x00{text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get(self, text: str, model_name: str) -> list[float] | None:
        """Look up a cached embedding, marking it as recently used on hit.

        Args:
            text: The text to look up.
            model_name: The embedding model identifier.

        Returns:
            The cached embedding vector, or None if not cached.
        """
        key = self._make_key(text, model_name)
        if key in self._store:
            self._store.move_to_end(key)
            self.stats.hits += 1
            logger.debug("Cache hit (key=%s...)", key[:12])
            return self._store[key]

        self.stats.misses += 1
        logger.debug("Cache miss (key=%s...)", key[:12])
        return None

    def set(self, text: str, model_name: str, embedding: list[float]) -> None:
        """Store an embedding, evicting the least-recently-used entry if full.

        Args:
            text: The text that was embedded.
            model_name: The embedding model identifier.
            embedding: The embedding vector to cache.
        """
        key = self._make_key(text, model_name)
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = embedding

        if len(self._store) > self._max_size:
            evicted_key, _ = self._store.popitem(last=False)
            self.stats.evictions += 1
            logger.debug("Cache eviction (key=%s...)", evicted_key[:12])

    def clear(self) -> None:
        """Remove all cached entries and reset statistics."""
        self._store.clear()
        self.stats = CacheStats()

    def __len__(self) -> int:
        """Return the current number of cached entries."""
        return len(self._store)