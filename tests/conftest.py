import pytest
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def setup_test_env():
    """Setup test environment variables"""
    os.environ['TOGETHER_API_KEY'] = 'test_key_123'
    yield
    # Cleanup if needed
