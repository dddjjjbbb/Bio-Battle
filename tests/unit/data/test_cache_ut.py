"""Unit tests for cache implementations."""

import time
from pathlib import Path

from bio_battle.data.cache import Cache, FileCache, MemoryCache


class TestMemoryCache:
    """Tests for MemoryCache implementation."""

    def test_should_store_and_retrieve_value(self) -> None:
        """MemoryCache should store and retrieve values."""
        cache: Cache = MemoryCache()

        cache.set("key1", {"name": "Test"})
        result = cache.get("key1")

        assert result == {"name": "Test"}

    def test_should_return_none_for_missing_key(self) -> None:
        """MemoryCache should return None for missing keys."""
        cache: Cache = MemoryCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_should_expire_value_after_ttl(self) -> None:
        """MemoryCache should expire values after TTL."""
        cache: Cache = MemoryCache()

        cache.set("key1", {"name": "Test"}, ttl=1)
        time.sleep(1.1)
        result = cache.get("key1")

        assert result is None

    def test_should_delete_key(self) -> None:
        """MemoryCache should delete keys."""
        cache: Cache = MemoryCache()
        cache.set("key1", {"name": "Test"})

        cache.delete("key1")
        result = cache.get("key1")

        assert result is None

    def test_should_clear_all_values(self) -> None:
        """MemoryCache should clear all values."""
        cache: Cache = MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestFileCache:
    """Tests for FileCache implementation."""

    def test_should_store_and_retrieve_value(self, tmp_path: Path) -> None:
        """FileCache should store and retrieve values."""
        cache: Cache = FileCache(cache_dir=tmp_path)

        cache.set("key1", {"name": "Test"})
        result = cache.get("key1")

        assert result == {"name": "Test"}

    def test_should_create_cache_directory(self, tmp_path: Path) -> None:
        """FileCache should create cache directory if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        cache = FileCache(cache_dir=cache_dir)

        cache.set("key1", {"test": "data"})

        assert cache_dir.exists()

    def test_should_return_none_for_missing_key(self, tmp_path: Path) -> None:
        """FileCache should return None for missing keys."""
        cache: Cache = FileCache(cache_dir=tmp_path)

        result = cache.get("nonexistent")

        assert result is None

    def test_should_expire_value_after_ttl(self, tmp_path: Path) -> None:
        """FileCache should expire values after TTL."""
        cache: Cache = FileCache(cache_dir=tmp_path)

        cache.set("key1", {"name": "Test"}, ttl=1)
        time.sleep(1.1)
        result = cache.get("key1")

        assert result is None

    def test_should_persist_across_instances(self, tmp_path: Path) -> None:
        """FileCache should persist values across instances."""
        cache1: Cache = FileCache(cache_dir=tmp_path)
        cache1.set("key1", {"persisted": True}, ttl=3600)

        cache2: Cache = FileCache(cache_dir=tmp_path)
        result = cache2.get("key1")

        assert result == {"persisted": True}

    def test_should_delete_key(self, tmp_path: Path) -> None:
        """FileCache should delete keys."""
        cache: Cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", {"name": "Test"})

        cache.delete("key1")
        result = cache.get("key1")

        assert result is None

    def test_should_clear_all_values(self, tmp_path: Path) -> None:
        """FileCache should clear all values."""
        cache: Cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_should_sanitise_key_for_filename(self, tmp_path: Path) -> None:
        """FileCache should sanitise keys for use as filenames."""
        cache: Cache = FileCache(cache_dir=tmp_path)

        # Key with special characters
        cache.set("Albert_Einstein/wiki", {"name": "Einstein"})
        result = cache.get("Albert_Einstein/wiki")

        assert result == {"name": "Einstein"}

    def test_should_handle_complex_data_types(self, tmp_path: Path) -> None:
        """FileCache should handle complex data types."""
        cache: Cache = FileCache(cache_dir=tmp_path)
        complex_data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        cache.set("complex", complex_data)
        result = cache.get("complex")

        assert result == complex_data
