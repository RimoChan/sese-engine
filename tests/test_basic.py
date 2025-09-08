"""
Basic unit tests for sese-engine.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import config
from src.storage import StorageManager, IndexSpace, FusionGate
from src.utils import (
    extract_netloc, tokenize_text, calculate_url_penalty, 
    decompose_url, serialize_scored_urls, deserialize_scored_urls
)
from src.types import ScoredURL


class TestUtils:
    """Test utility functions."""
    
    def test_extract_netloc(self):
        """Test netloc extraction."""
        assert extract_netloc("https://example.com/path") == "example.com"
        assert extract_netloc("http://sub.example.com/page") == "sub.example.com"
        assert extract_netloc("https://example.com:8080/path") == "example.com:8080"
    
    def test_tokenize_text(self):
        """Test text tokenization."""
        # Test English text
        result = tokenize_text("hello world", search_mode=False)
        assert "hello" in result
        assert "world" in result
        
        # Test Chinese text
        result = tokenize_text("你好世界", search_mode=False)
        assert len(result) > 0
    
    def test_calculate_url_penalty(self):
        """Test URL penalty calculation."""
        penalty1 = calculate_url_penalty("https://example.com/")
        penalty2 = calculate_url_penalty("https://example.com/very/long/path/with/many/segments/file.php")
        
        assert 0 <= penalty1 <= 0.9
        assert 0 <= penalty2 <= 0.9
        assert penalty2 > penalty1  # Longer URL should have higher penalty
    
    def test_decompose_url(self):
        """Test URL decomposition."""
        result = list(decompose_url("https://example.com/path/to/page"))
        expected = ["example.com", "example.com/path", "example.com/path/to", "example.com/path/to/page"]
        assert list(result) == expected
    
    def test_serialize_deserialize(self):
        """Test serialization and deserialization of scored URLs."""
        original = [(0.8, "https://example.com"), (0.6, "https://test.com")]
        
        serialized = serialize_scored_urls(original)
        deserialized = deserialize_scored_urls(serialized)
        
        assert deserialized == original


class TestStorage:
    """Test storage components."""
    
    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """Create temporary storage path."""
        return tmp_path / "test_storage"
    
    def test_index_space(self, temp_storage_path):
        """Test index space functionality."""
        index_space = IndexSpace(temp_storage_path / "index")
        
        # Test basic operations
        test_urls = [(0.8, "https://example.com"), (0.6, "https://test.com")]
        index_space["test"] = test_urls
        
        retrieved = index_space["test"]
        assert retrieved == test_urls
        
        # Test deletion
        del index_space["test"]
        with pytest.raises(KeyError):
            _ = index_space["test"]
    
    def test_fusion_gate(self, temp_storage_path):
        """Test fusion gate functionality."""
        gate = FusionGate(temp_storage_path / "fusion")
        
        # Test basic operations
        gate["key1"] = "value1"
        assert gate["key1"] == "value1"
        
        # Test multiple keys in same shard
        gate["key2"] = "value2"
        assert gate["key2"] == "value2"
        
        # Test overwriting
        gate["key1"] = "new_value1"
        assert gate["key1"] == "new_value1"
        
        # Test deletion
        del gate["key1"]
        with pytest.raises(KeyError):
            _ = gate["key1"]
    
    def test_storage_manager(self, temp_storage_path):
        """Test storage manager."""
        manager = StorageManager(temp_storage_path)
        
        # Test that all components are initialized
        assert manager.keyword_index is not None
        assert manager.url_metadata is not None
        assert manager.site_info is not None
        assert manager.link_data is not None
        
        # Test stats
        stats = manager.get_storage_stats()
        assert isinstance(stats, dict)


class TestConfig:
    """Test configuration."""
    
    def test_config_values(self):
        """Test that configuration values are properly set."""
        assert config.MAX_URLS_PER_KEYWORD > 0
        assert config.CRAWLER_THREADS > 0
        assert config.SERVER_PORT > 0
        assert config.STORAGE_PATH is not None
    
    def test_config_getters(self):
        """Test configuration getter methods."""
        crawler_config = config.get_crawler_config()
        assert isinstance(crawler_config, dict)
        assert "threads" in crawler_config
        
        search_config = config.get_search_config()
        assert isinstance(search_config, dict)
        assert "use_online_summary" in search_config
        
        index_config = config.get_index_config()
        assert isinstance(index_config, dict)
        assert "max_urls_per_keyword" in index_config


class TestAPI:
    """Test API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_search_endpoint_validation(self, client):
        """Test search endpoint validation."""
        # Test missing query parameter
        response = client.get("/search")
        assert response.status_code == 422  # Validation error
        
        # Test empty query
        response = client.get("/search?q=")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
    
    def test_search_endpoint_with_params(self, client):
        """Test search endpoint with parameters."""
        response = client.get("/search?q=test&offset=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert data["offset"] == 0
        assert data["limit"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])