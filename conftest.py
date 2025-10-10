"""Pytest configuration for Sailor MCP tests"""
import sys
import os
import pytest
import asyncio

# Add src to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mark integration tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )