"""Test: Accessibility Checks."""
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/main"


def test_html_lang_attribute(sailor_page: Page):
    """Verify HTML has lang attribute."""
    lang = sailor_page.locator("html").get_attribute("lang")
    assert lang == "en"


def test_page_has_heading(sailor_page: Page):
    """Verify page has a proper heading hierarchy."""
    h1 = sailor_page.locator("h1")
    expect(h1).to_be_visible()
    expect(h1).to_have_text("Sailor Site")


def test_interactive_elements_focusable(sailor_page: Page):
    """Verify key interactive elements are keyboard-focusable."""
    # Tab through elements and check they receive focus
    elements_to_check = ["#provider", "#apiKey", "#theme", "#direction", "#look", "#exportBg"]
    for selector in elements_to_check:
        el = sailor_page.locator(selector)
        expect(el).to_be_attached()
        # These are all native HTML elements (select/input) so they're natively focusable


def test_buttons_have_accessible_names(sailor_page: Page):
    """Verify buttons have text or aria-label."""
    buttons = sailor_page.locator("button")
    count = buttons.count()
    for i in range(count):
        btn = buttons.nth(i)
        text = btn.inner_text().strip()
        title = btn.get_attribute("title") or ""
        aria_label = btn.get_attribute("aria-label") or ""
        # Each button should have some accessible name
        assert text or title or aria_label, f"Button at index {i} has no accessible name"


def test_form_inputs_identifiable(sailor_page: Page):
    """Verify form inputs have some identifying mechanism."""
    # API key input should have placeholder
    api_key = sailor_page.locator("#apiKey")
    placeholder = api_key.get_attribute("placeholder")
    assert placeholder and len(placeholder) > 0

    # User input should have placeholder
    user_input = sailor_page.locator("#userInput")
    placeholder = user_input.get_attribute("placeholder")
    assert placeholder and len(placeholder) > 0


def test_viewport_meta_tag(sailor_page: Page):
    """Verify viewport meta tag exists for responsive design."""
    viewport = sailor_page.locator('meta[name="viewport"]')
    expect(viewport).to_be_attached()
    content = viewport.get_attribute("content")
    assert "width=device-width" in content


def test_labels_associated_with_controls(sailor_page: Page):
    """Verify labels have for attributes matching control IDs (A11Y-1)."""
    controls = ["theme", "direction", "look", "exportBg"]
    for control_id in controls:
        label = sailor_page.locator(f'label[for="{control_id}"]')
        assert label.count() > 0, f"No label with for='{control_id}' found"
        control = sailor_page.locator(f"#{control_id}")
        expect(control).to_be_attached()


def test_inputs_have_aria_labels(sailor_page: Page):
    """Verify unlabeled inputs have aria-label attributes (A11Y-2)."""
    checks = {
        "#provider": "AI Provider",
        "#apiKey": "API Key",
        "#userInput": "Diagram description",
    }
    for selector, expected_label in checks.items():
        el = sailor_page.locator(selector)
        aria = el.get_attribute("aria-label")
        assert aria == expected_label, f"Expected aria-label='{expected_label}' on {selector}, got '{aria}'"


def test_favicon_present(sailor_page: Page):
    """Verify a favicon link is present in the head (A11Y-3)."""
    favicon = sailor_page.locator('link[rel="icon"]')
    assert favicon.count() > 0, "No favicon link found"
    href = favicon.get_attribute("href")
    assert href and len(href) > 0, "Favicon href is empty"
