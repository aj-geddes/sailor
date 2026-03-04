"""Test: Page Load and Initial State."""
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/main"


def test_page_loads_successfully(sailor_page: Page):
    """Verify the main page loads with 200 status."""
    # Title check
    expect(sailor_page).to_have_title("Sailor Site - Get a picture of your Mermaid")
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/01-initial-load.png", full_page=True)


def test_header_elements_present(sailor_page: Page):
    """Verify header contains logo, provider selector, and API key input."""
    expect(sailor_page.locator("h1")).to_have_text("Sailor Site")
    expect(sailor_page.locator(".slogan")).to_have_text("Get a picture of your Mermaid")
    expect(sailor_page.locator("#provider")).to_be_visible()
    expect(sailor_page.locator("#apiKey")).to_be_visible()
    expect(sailor_page.locator("#keyStatus")).to_be_attached()


def test_editor_panel_present(sailor_page: Page):
    """Verify the code editor panel loads with CodeMirror."""
    # CodeMirror wraps the textarea
    expect(sailor_page.locator(".CodeMirror")).to_be_visible()
    expect(sailor_page.locator("#copyCodeBtn")).to_be_visible()
    # Check default code is loaded
    editor_content = sailor_page.evaluate("() => editor.getValue()")
    assert "graph TD" in editor_content
    assert "Start" in editor_content


def test_preview_panel_present(sailor_page: Page):
    """Verify the preview panel shows a rendered diagram."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview).to_be_visible()
    # Wait for Mermaid to render an SVG
    expect(preview.locator("svg")).to_be_visible(timeout=10000)
    expect(sailor_page.locator("#copyImageBtn")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/02-default-diagram.png")


def test_controls_panel_present(sailor_page: Page):
    """Verify all style controls are visible."""
    expect(sailor_page.locator("#theme")).to_be_visible()
    expect(sailor_page.locator("#direction")).to_be_visible()
    expect(sailor_page.locator("#look")).to_be_visible()
    expect(sailor_page.locator("#exportBg")).to_be_visible()


def test_example_buttons_present(sailor_page: Page):
    """Verify example diagram buttons exist."""
    buttons = sailor_page.locator(".example-btn")
    expect(buttons).to_have_count(3)
    expect(buttons.nth(0)).to_have_text("Flowchart")
    expect(buttons.nth(1)).to_have_text("Sequence")
    expect(buttons.nth(2)).to_have_text("Gantt Chart")


def test_generate_section_present(sailor_page: Page):
    """Verify the AI generation section is visible."""
    expect(sailor_page.locator("#userInput")).to_be_visible()
    expect(sailor_page.locator("#generateBtn")).to_be_visible()
    expect(sailor_page.locator("#generateBtn")).to_have_text("Generate Diagram")


def test_toast_element_exists(sailor_page: Page):
    """Verify the toast notification element exists (hidden by default)."""
    toast = sailor_page.locator("#toast")
    expect(toast).to_be_attached()
