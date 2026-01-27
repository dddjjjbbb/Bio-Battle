"""Cache implementations for Bio Battle."""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Cache(ABC):
    """Abstract base class for cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Returns None if the key doesn't exist or has expired.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to store (must be JSON-serialisable).
            ttl: Time to live in seconds (default 1 hour).
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all values from the cache."""
        pass


class MemoryCache(Cache):
    """In-memory cache implementation."""

    def __init__(self) -> None:
        """Initialise the memory cache."""
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store a value in the cache."""
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all values from the cache."""
        self._cache.clear()


class FileCache(Cache):
    """File-based cache implementation."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialise the file cache.

        Args:
            cache_dir: Directory to store cache files.
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        if time.time() > data.get("expires_at", 0):
            cache_file.unlink(missing_ok=True)
            return None

        return data.get("value")

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store a value in the cache."""
        cache_file = self._get_cache_path(key)
        data = {
            "value": value,
            "expires_at": time.time() + ttl,
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")

    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        cache_file = self._get_cache_path(key)
        cache_file.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all values from the cache."""
        for cache_file in self._cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Generate a safe filename for the cache key."""
        # Use hash to ensure safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._cache_dir / f"{key_hash}.json"
