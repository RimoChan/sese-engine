"""
Storage module for sese-engine.

This module provides efficient storage mechanisms for search engine data,
including compressed indexing and optimized data structures.
"""

import struct
import hashlib
from typing import MutableMapping, List, Tuple, Optional, Any, Iterator
from pathlib import Path

import orjson
import brotli
from rimo_storage import 超dict as SuperDict

from ..types import ScoredURL


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class DataCorruptionError(StorageError):
    """Exception raised when data corruption is detected."""
    pass


def serialize_scored_urls(data: ScoredURL) -> bytes:
    """
    Serialize scored URLs with optimized binary format.
    
    Args:
        data: List of (score, url) tuples
        
    Returns:
        Serialized binary data
    """
    if not data:
        return b'yn0001\x00\x00\x00\x00'
    
    # Transpose the data
    scores, urls = zip(*data) if data else ([], [])
    n = len(scores)
    
    # Serialize URLs with orjson
    urls_json = orjson.dumps(urls)
    
    # Pack binary data
    size_bytes = struct.pack('i', n)
    content_bytes = struct.pack(f'{n}e{len(urls_json)}s', *scores, urls_json)
    
    return b'yn0001' + size_bytes + content_bytes


def _load_legacy_format(data: bytes) -> ScoredURL:
    """
    Load data from legacy format (backward compatibility).
    
    Args:
        data: Legacy binary data
        
    Returns:
        List of (score, url) tuples
        
    Raises:
        DataCorruptionError: If data is corrupted
    """
    try:
        n = struct.unpack('i', data[:4])[0]
        string_lengths = struct.unpack(f'{n}h', data[4:4+n*2])
        scores = struct.unpack(f'{n}e', data[4+n*2:4+n*4])
        
        # Build format string for strings
        format_string = ''.join(f'{length}s' for length in string_lengths)
        packed_strings = struct.unpack(format_string, data[4+n*4:])
        
        # Decode strings
        urls = [s.decode('utf8') for s in packed_strings]
        
        return list(zip(scores, urls))
    except Exception as e:
        raise DataCorruptionError(f"Failed to load legacy format: {e}")


def _load_current_format(data: bytes) -> ScoredURL:
    """
    Load data from current format.
    
    Args:
        data: Binary data in current format
        
    Returns:
        List of (score, url) tuples
        
    Raises:
        DataCorruptionError: If data is corrupted
    """
    try:
        if not data.startswith(b'yn0001'):
            raise DataCorruptionError("Invalid format header")
        
        n = struct.unpack('i', data[6:10])[0]
        scores = struct.unpack(f'{n}e', data[10:10+n*2])
        urls = orjson.loads(data[10+n*2:])
        
        if len(scores) != len(urls):
            raise DataCorruptionError("Score and URL count mismatch")
        
        return list(zip(scores, urls))
    except Exception as e:
        raise DataCorruptionError(f"Failed to load current format: {e}")


def deserialize_scored_urls(data: bytes) -> ScoredURL:
    """
    Deserialize scored URLs from binary format.
    
    Args:
        data: Binary data to deserialize
        
    Returns:
        List of (score, url) tuples
    """
    if not data:
        return []
    
    if data.startswith(b'yn0001'):
        return _load_current_format(data)
    else:
        return _load_legacy_format(data)


# Compression functions
_empty_data = serialize_scored_urls([])


def compress_data(data: bytes) -> bytes:
    """Compress data using Brotli."""
    return brotli.compress(data, quality=6)


def decompress_data(data: bytes) -> bytes:
    """Decompress data using Brotli."""
    if data == b'':
        return _empty_data
    try:
        return brotli.decompress(data)
    except Exception:
        return _empty_data


class IndexSpace(MutableMapping[str, ScoredURL]):
    """
    Efficient storage space for keyword-to-URLs mapping.
    
    Uses compression and optimized serialization for memory efficiency.
    """
    
    def __init__(self, path: Path):
        """Initialize index space at given path."""
        self._storage = SuperDict(
            path,
            compress=(compress_data, decompress_data),
            serialize=(serialize_scored_urls, deserialize_scored_urls)
        )
    
    def __getitem__(self, key: str) -> ScoredURL:
        """Get URLs for a keyword."""
        return self._storage[key]
    
    def __setitem__(self, key: str, value: ScoredURL) -> None:
        """Set URLs for a keyword."""
        self._storage[key] = value
    
    def __delitem__(self, key: str) -> None:
        """Delete keyword entry."""
        del self._storage[key]
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over keywords."""
        return iter(self._storage)
    
    def __len__(self) -> int:
        """Get number of keywords."""
        return len(self._storage)
    
    def get_size_info(self) -> dict:
        """Get storage size information."""
        return {
            'key_count': len(self),
            'estimated_size_bytes': getattr(self._storage, 'estimated_size', 0)
        }


class FusionGate(MutableMapping[str, Any]):
    """
    High-performance key-value store with hash-based sharding.
    
    Uses SHA-224 hashing to distribute keys across shards for better performance.
    """
    
    def __init__(self, path: Path):
        """Initialize fusion gate at given path."""
        def safe_decompress(data: bytes) -> str:
            """Safely decompress data with fallback."""
            try:
                return brotli.decompress(data).decode('utf8')
            except Exception:
                return '[]'
        
        self._storage = SuperDict(
            path,
            compress=(compress_data, safe_decompress)
        )
    
    def _get_shard_key(self, key: str) -> str:
        """Get shard key for given key."""
        return hashlib.sha224(key.encode('utf8')).hexdigest()[:5]
    
    def __getitem__(self, key: str) -> Any:
        """Get value for key."""
        shard_key = self._get_shard_key(key)
        
        try:
            shard_data = self._storage[shard_key]
        except KeyError:
            raise KeyError(key)
        
        # Find the specific key within the shard
        for stored_key, value in shard_data:
            if stored_key == key:
                return value
        
        raise KeyError(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set value for key."""
        shard_key = self._get_shard_key(key)
        
        try:
            shard_data = self._storage[shard_key]
        except KeyError:
            # New shard
            self._storage[shard_key] = [(key, value)]
            return
        
        # Update existing shard
        updated = False
        for i, (stored_key, _) in enumerate(shard_data):
            if stored_key == key:
                shard_data[i] = (key, value)
                updated = True
                break
        
        if not updated:
            shard_data.append((key, value))
        
        self._storage[shard_key] = shard_data
    
    def __delitem__(self, key: str) -> None:
        """Delete key-value pair."""
        shard_key = self._get_shard_key(key)
        
        try:
            shard_data = self._storage[shard_key]
        except KeyError:
            raise KeyError(key)
        
        # Remove the key from the shard
        new_shard_data = [(k, v) for k, v in shard_data if k != key]
        
        if len(new_shard_data) == len(shard_data):
            raise KeyError(key)
        
        if new_shard_data:
            self._storage[shard_key] = new_shard_data
        else:
            del self._storage[shard_key]
    
    def items(self) -> Iterator[Tuple[str, Any]]:
        """Iterate over all key-value pairs."""
        for shard_data in self._storage.values():
            yield from shard_data
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over all keys."""
        for key, _ in self.items():
            yield key
    
    def __len__(self) -> int:
        """Get total number of keys."""
        return sum(len(shard_data) for shard_data in self._storage.values())
    
    def get_shard_count(self) -> int:
        """Get number of shards."""
        return len(self._storage)
    
    def get_shard_stats(self) -> dict:
        """Get statistics about shard distribution."""
        shard_sizes = [len(shard_data) for shard_data in self._storage.values()]
        return {
            'shard_count': len(shard_sizes),
            'total_keys': sum(shard_sizes),
            'min_shard_size': min(shard_sizes) if shard_sizes else 0,
            'max_shard_size': max(shard_sizes) if shard_sizes else 0,
            'avg_shard_size': sum(shard_sizes) / len(shard_sizes) if shard_sizes else 0,
        }


class StorageManager:
    """
    High-level storage management interface.
    
    Provides unified access to different storage components.
    """
    
    def __init__(self, base_path: Path):
        """Initialize storage manager."""
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage components
        self.keyword_index = IndexSpace(base_path / 'keywords')
        self.url_metadata = FusionGate(base_path / 'metadata')
        self.site_info = FusionGate(base_path / 'sites')
        self.link_data = FusionGate(base_path / 'links')
    
    def get_index_space(self, name: str) -> IndexSpace:
        """Get or create an index space."""
        path = self.base_path / name
        return IndexSpace(path)
    
    def get_fusion_gate(self, name: str) -> FusionGate:
        """Get or create a fusion gate."""
        path = self.base_path / name
        return FusionGate(path)
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up old data files."""
        # Implementation for cleaning up old data
        # This would involve checking file timestamps and removing old files
        pass
    
    def get_storage_stats(self) -> dict:
        """Get comprehensive storage statistics."""
        return {
            'keyword_index': self.keyword_index.get_size_info(),
            'url_metadata': self.url_metadata.get_shard_stats(),
            'site_info': self.site_info.get_shard_stats(),
            'link_data': self.link_data.get_shard_stats(),
        }