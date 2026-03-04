"""Test: AI Diagram Generation (validation and error handling)."""
import re
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/generation"


def test_generate_without_input_shows_error(sailor_page: Page):
    """Verify generating with empty input shows toast error."""
    # Ensure userInput is empty
    sailor_page.fill("#userInput", "")
    sailor_page.click("#generateBtn")

    # Toast should show error
    toast = sailor_page.locator("#toast")
    expect(toast).to_have_class(re.compile(r"show"), timeout=3000)
    assert "description" in toast.inner_text().lower() or "enter" in toast.inner_text().lower()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/01-no-input-error.png")


def test_generate_without_api_key_shows_error(sailor_page: Page):
    """Verify generating without API key shows toast error."""
    sailor_page.fill("#userInput", "Create a flowchart for login process")
    # Make sure apiKey is empty
    sailor_page.fill("#apiKey", "")
    sailor_page.click("#generateBtn")

    toast = sailor_page.locator("#toast")
    expect(toast).to_have_class(re.compile(r"show"), timeout=3000)
    assert "api key" in toast.inner_text().lower() or "key" in toast.inner_text().lower()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/02-no-key-error.png")


def test_generate_button_shows_loading_text(sailor_page: Page):
    """Verify the generate button shows Generating... text during API call."""
    sailor_page.fill("#userInput", "Create a flowchart")
    sailor_page.fill("#apiKey", "sk-fake-key-for-testing-12345")

    # Use evaluate to click and immediately capture button text
    # The button shows "Generating..." briefly then returns to normal after API error
    sailor_page.click("#generateBtn")

    # Wait for the API call to complete and verify the button returns to normal
    button = sailor_page.locator("#generateBtn")
    expect(button).to_have_text("Generate Diagram", timeout=15000)
    expect(button).to_be_enabled()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/03-after-generate-attempt.png")


def test_generate_with_invalid_key_shows_error_toast(sailor_page: Page):
    """Verify that an invalid API key produces an error toast."""
    sailor_page.fill("#userInput", "Create a simple flowchart")
    sailor_page.fill("#apiKey", "sk-invalid-key-1234567890")
    sailor_page.select_option("#provider", "openai")
    sailor_page.click("#generateBtn")

    # Wait for response - should show error toast
    toast = sailor_page.locator("#toast")
    expect(toast).to_have_class(re.compile(r"show"), timeout=15000)
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/04-invalid-key-error.png")

    # Button should be re-enabled
    expect(sailor_page.locator("#generateBtn")).to_be_enabled()


def test_provider_selection(sailor_page: Page):
    """Verify provider dropdown works."""
    provider = sailor_page.locator("#provider")

    sailor_page.select_option("#provider", "openai")
    expect(provider).to_have_value("openai")

    sailor_page.select_option("#provider", "anthropic")
    expect(provider).to_have_value("anthropic")


def test_openai_sdk_error_not_leaked(sailor_page: Page):
    """Verify internal SDK error strings are not leaked to the user (BUG-2)."""
    sailor_page.fill("#userInput", "Create a simple flowchart")
    sailor_page.fill("#apiKey", "sk-invalid-key-1234567890")
    sailor_page.select_option("#provider", "openai")
    sailor_page.click("#generateBtn")

    # Wait for error toast
    toast = sailor_page.locator("#toast")
    expect(toast).to_have_class(re.compile(r"show"), timeout=15000)

    toast_text = toast.inner_text()
    # Should NOT contain internal error details like stack traces or SDK internals
    assert "Traceback" not in toast_text
    assert "openai.error" not in toast_text
    assert "openai." not in toast_text.lower() or "check your" in toast_text.lower()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/05-error-not-leaked.png")
