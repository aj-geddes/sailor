"""Pytest configuration and fixtures for all tests"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check if Playwright is available
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Check if real browser can be launched (for integration tests)
BROWSER_AVAILABLE = False
if PLAYWRIGHT_AVAILABLE:
    import asyncio
    async def check_browser():
        global BROWSER_AVAILABLE
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                await browser.close()
                BROWSER_AVAILABLE = True
        except Exception:
            BROWSER_AVAILABLE = False

    # Run the check once at test collection time
    try:
        asyncio.run(check_browser())
    except:
        pass

@pytest.fixture
def playwright_available():
    """Fixture to check if Playwright is available"""
    return PLAYWRIGHT_AVAILABLE

@pytest.fixture
def browser_available():
    """Fixture to check if real browser can be launched"""
    return BROWSER_AVAILABLE

# Markers for different test types
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "requires_playwright: mark test as requiring Playwright"
    )
    config.addinivalue_line(
        "markers", "requires_browser: mark test as requiring real browser"
    )

# Skip tests based on availability
def pytest_collection_modifyitems(config, items):
    """Skip tests based on availability of dependencies"""
    for item in items:
        # Skip Playwright tests if not available
        if "requires_playwright" in item.keywords and not PLAYWRIGHT_AVAILABLE:
            skip_marker = pytest.mark.skip(reason="Playwright not available")
            item.add_marker(skip_marker)

        # Skip browser tests if browser not available
        if "requires_browser" in item.keywords and not BROWSER_AVAILABLE:
            skip_marker = pytest.mark.skip(reason="Browser not available")
            item.add_marker(skip_marker)