"""
Test configuration for pytest.
"""

import pytest
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_storage():
    """Create mock storage for testing."""
    from unittest.mock import Mock
    from src.storage import StorageManager
    
    mock_manager = Mock(spec=StorageManager)
    mock_manager.keyword_index = Mock()
    mock_manager.url_metadata = Mock()
    mock_manager.site_info = Mock()
    mock_manager.link_data = Mock()
    
    return mock_manager