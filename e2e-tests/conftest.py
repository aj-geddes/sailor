"""Shared fixtures for Sailor E2E tests."""
import pytest
from playwright.sync_api import Page, BrowserContext

BASE_URL = "http://192.168.86.94:30501"

VIEWPORTS = {
    "mobile": {"width": 375, "height": 812},
    "tablet": {"width": 768, "height": 1024},
    "desktop": {"width": 1440, "height": 900},
}


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def sailor_page(page: Page) -> Page:
    """Navigate to the main Sailor page and wait for it to load."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    return page
