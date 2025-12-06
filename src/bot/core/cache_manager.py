"""Cache manager for embeddings and RAG responses."""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from rich.console import Console

console = Console()


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if entry has expired."""
        if ttl_seconds <= 0:  # 0 or negative = no expiration
            return False
        return (time.time() - self.created_at) > ttl_seconds

    def access(self):
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "hit_rate": self.hit_rate
        }


class CacheManager:
    """
    Manages caching for embeddings and RAG responses.

    Features:
    - Embedding cache: Store expensive OpenAI embedding API calls
    - Response cache: Store complete RAG query responses
    - TTL support: Automatic expiration
    - Size limits: LRU eviction when cache is full
    - Persistence: Save/load from disk
    - Statistics: Track hit/miss rates
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        embedding_ttl: float = 86400 * 7,  # 7 days
        response_ttl: float = 3600,  # 1 hour
        max_embedding_cache_size: int = 10000,
        max_response_cache_size: int = 1000,
        enable_persistence: bool = True
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
            embedding_ttl: Time-to-live for embeddings (seconds, 0 = no expiration)
            response_ttl: Time-to-live for responses (seconds, 0 = no expiration)
            max_embedding_cache_size: Max number of embeddings to cache
            max_response_cache_size: Max number of responses to cache
            enable_persistence: Whether to persist cache to disk
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "legal_bot"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.embedding_ttl = embedding_ttl
        self.response_ttl = response_ttl
        self.max_embedding_cache_size = max_embedding_cache_size
        self.max_response_cache_size = max_response_cache_size
        self.enable_persistence = enable_persistence

        # In-memory caches
        self._embedding_cache: Dict[str, CacheEntry] = {}
        self._response_cache: Dict[str, CacheEntry] = {}

        # Statistics
        self.embedding_stats = CacheStats()
        self.response_stats = CacheStats()

        # Load from disk if persistence enabled
        if self.enable_persistence:
            self._load_from_disk()

    def _hash_text(self, text: str) -> str:
        """Generate hash key for text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _evict_lru(self, cache: Dict[str, CacheEntry], max_size: int, stats: CacheStats):
        """Evict least recently used entries when cache is full."""
        while len(cache) >= max_size:
            # Find LRU entry
            lru_key = min(cache.keys(), key=lambda k: cache[k].last_accessed)
            del cache[lru_key]
            stats.evictions += 1

    def _clean_expired(self, cache: Dict[str, CacheEntry], ttl: float):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in cache.items()
            if entry.is_expired(ttl)
        ]
        for key in expired_keys:
            del cache[key]

    # ===== EMBEDDING CACHE =====

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding for text.

        Args:
            text: Text to get embedding for

        Returns:
            Cached embedding or None if not found
        """
        key = self._hash_text(text)

        # Clean expired entries
        self._clean_expired(self._embedding_cache, self.embedding_ttl)

        if key in self._embedding_cache:
            entry = self._embedding_cache[key]
            if not entry.is_expired(self.embedding_ttl):
                entry.access()
                self.embedding_stats.hits += 1
                return entry.value
            else:
                # Expired, remove it
                del self._embedding_cache[key]

        self.embedding_stats.misses += 1
        return None

    def set_embedding(self, text: str, embedding: List[float]):
        """
        Cache embedding for text.

        Args:
            text: Text that was embedded
            embedding: The embedding vector
        """
        key = self._hash_text(text)

        # Evict if needed
        self._evict_lru(
            self._embedding_cache,
            self.max_embedding_cache_size,
            self.embedding_stats
        )

        # Store entry
        self._embedding_cache[key] = CacheEntry(
            value=embedding,
            created_at=time.time(),
            last_accessed=time.time()
        )

        self.embedding_stats.size = len(self._embedding_cache)

    # ===== RESPONSE CACHE =====

    def get_response(self, query: str, context_hash: Optional[str] = None) -> Optional[Dict]:
        """
        Get cached RAG response.

        Args:
            query: User query
            context_hash: Optional hash of context documents (for more precise caching)

        Returns:
            Cached response or None if not found
        """
        # Create cache key from query (and optionally context)
        cache_text = f"{query}|{context_hash}" if context_hash else query
        key = self._hash_text(cache_text)

        # Clean expired entries
        self._clean_expired(self._response_cache, self.response_ttl)

        if key in self._response_cache:
            entry = self._response_cache[key]
            if not entry.is_expired(self.response_ttl):
                entry.access()
                self.response_stats.hits += 1
                return entry.value
            else:
                del self._response_cache[key]

        self.response_stats.misses += 1
        return None

    def set_response(self, query: str, response: Dict, context_hash: Optional[str] = None):
        """
        Cache RAG response.

        Args:
            query: User query
            response: RAG response dict
            context_hash: Optional hash of context documents
        """
        cache_text = f"{query}|{context_hash}" if context_hash else query
        key = self._hash_text(cache_text)

        # Evict if needed
        self._evict_lru(
            self._response_cache,
            self.max_response_cache_size,
            self.response_stats
        )

        # Store entry
        self._response_cache[key] = CacheEntry(
            value=response,
            created_at=time.time(),
            last_accessed=time.time()
        )

        self.response_stats.size = len(self._response_cache)

    # ===== UTILITIES =====

    def clear_embeddings(self):
        """Clear all cached embeddings."""
        count = len(self._embedding_cache)
        self._embedding_cache.clear()
        self.embedding_stats = CacheStats()
        console.print(f"[yellow]🗑️  Cleared {count} cached embeddings[/yellow]")

    def clear_responses(self):
        """Clear all cached responses."""
        count = len(self._response_cache)
        self._response_cache.clear()
        self.response_stats = CacheStats()
        console.print(f"[yellow]🗑️  Cleared {count} cached responses[/yellow]")

    def clear_all(self):
        """Clear all caches."""
        self.clear_embeddings()
        self.clear_responses()

    def get_stats(self) -> Dict:
        """
        Get comprehensive cache statistics.

        Returns:
            Dict with stats for both caches
        """
        return {
            "embeddings": self.embedding_stats.to_dict(),
            "responses": self.response_stats.to_dict(),
            "total_size_bytes": self._estimate_size()
        }

    def _estimate_size(self) -> int:
        """Estimate total cache size in bytes."""
        # Rough estimate: embedding = 1536 floats * 8 bytes = ~12KB each
        embedding_bytes = len(self._embedding_cache) * 1536 * 8
        # Response: average ~2KB (text + metadata)
        response_bytes = len(self._response_cache) * 2048
        return embedding_bytes + response_bytes

    # ===== PERSISTENCE =====

    def _serialize_cache(self, cache: Dict[str, CacheEntry]) -> Dict:
        """Serialize cache to JSON-compatible format."""
        return {
            key: {
                "value": entry.value,
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "access_count": entry.access_count
            }
            for key, entry in cache.items()
        }

    def _deserialize_cache(self, data: Dict) -> Dict[str, CacheEntry]:
        """Deserialize cache from JSON format."""
        return {
            key: CacheEntry(**entry_data)
            for key, entry_data in data.items()
        }

    def save_to_disk(self):
        """Save caches to disk."""
        if not self.enable_persistence:
            return

        try:
            # Save embeddings
            embedding_file = self.cache_dir / "embeddings.json"
            with open(embedding_file, 'w') as f:
                json.dump(self._serialize_cache(self._embedding_cache), f)

            # Save responses
            response_file = self.cache_dir / "responses.json"
            with open(response_file, 'w') as f:
                json.dump(self._serialize_cache(self._response_cache), f)

            # Save stats
            stats_file = self.cache_dir / "stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.get_stats(), f, indent=2)

            console.print(f"[green]✓ Cache saved to {self.cache_dir}[/green]")

        except Exception as e:
            console.print(f"[red]✗ Error saving cache: {e}[/red]")

    def _load_from_disk(self):
        """Load caches from disk."""
        try:
            # Load embeddings
            embedding_file = self.cache_dir / "embeddings.json"
            if embedding_file.exists():
                with open(embedding_file, 'r') as f:
                    data = json.load(f)
                    self._embedding_cache = self._deserialize_cache(data)
                    self.embedding_stats.size = len(self._embedding_cache)
                console.print(f"[green]✓ Loaded {len(self._embedding_cache)} cached embeddings[/green]")

            # Load responses
            response_file = self.cache_dir / "responses.json"
            if response_file.exists():
                with open(response_file, 'r') as f:
                    data = json.load(f)
                    self._response_cache = self._deserialize_cache(data)
                    self.response_stats.size = len(self._response_cache)
                console.print(f"[green]✓ Loaded {len(self._response_cache)} cached responses[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠ Error loading cache: {e}[/yellow]")

    def __del__(self):
        """Save cache on cleanup."""
        if self.enable_persistence:
            self.save_to_disk()
