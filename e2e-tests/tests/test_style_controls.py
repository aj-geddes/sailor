"""Test: Style Controls (Theme, Direction, Look)."""
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/main"


def test_theme_change_default(sailor_page: Page):
    """Verify changing theme to Default re-renders the diagram."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#theme", "default")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/08-theme-default.png")


def test_theme_change_dark(sailor_page: Page):
    """Verify changing theme to Dark."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#theme", "dark")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/09-theme-dark.png")


def test_theme_change_forest(sailor_page: Page):
    """Verify changing theme to Forest."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#theme", "forest")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/10-theme-forest.png")


def test_theme_change_neutral(sailor_page: Page):
    """Verify changing theme to Neutral."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#theme", "neutral")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/11-theme-neutral.png")


def test_direction_change_lr(sailor_page: Page):
    """Verify changing direction to Left-to-Right."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#direction", "LR")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/12-direction-lr.png")


def test_direction_change_bt(sailor_page: Page):
    """Verify changing direction to Bottom-to-Top."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#direction", "BT")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/13-direction-bt.png")


def test_direction_change_rl(sailor_page: Page):
    """Verify changing direction to Right-to-Left."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#direction", "RL")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/14-direction-rl.png")


def test_look_change_hand_drawn(sailor_page: Page):
    """Verify changing look to Hand-Drawn and description updates."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#look", "handDrawn")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    expect(sailor_page.locator("#lookDescription")).to_have_text("Sketch-like, personal touch")
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/15-look-hand-drawn.png")


def test_look_change_classic(sailor_page: Page):
    """Verify changing look back to Classic."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    # First switch to hand-drawn, then back
    sailor_page.select_option("#look", "handDrawn")
    sailor_page.wait_for_timeout(1000)
    sailor_page.select_option("#look", "classic")
    sailor_page.wait_for_timeout(1500)

    expect(preview.locator("svg")).to_be_visible()
    expect(sailor_page.locator("#lookDescription")).to_have_text("Traditional Mermaid style")


def test_combined_style_changes(sailor_page: Page):
    """Verify applying multiple style changes together."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.select_option("#theme", "forest")
    sailor_page.select_option("#direction", "LR")
    sailor_page.select_option("#look", "handDrawn")
    sailor_page.wait_for_timeout(2000)

    expect(preview.locator("svg")).to_be_visible()
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/16-combined-styles.png")


def test_theme_default_matches_js_initial(sailor_page: Page):
    """Verify JS currentTheme starts as 'default', matching the first <option> (BUG-4)."""
    theme_value = sailor_page.evaluate("() => currentTheme")
    assert theme_value == "default", f"Expected currentTheme='default', got '{theme_value}'"

    # The theme dropdown should also show 'default' as selected
    select_value = sailor_page.locator("#theme").input_value()
    assert select_value == "default", f"Expected theme select='default', got '{select_value}'"


def test_theme_changes_preview_background(sailor_page: Page):
    """Verify preview background changes with theme (UX-1)."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    # Default theme should have light background class
    assert "theme-default" in preview.get_attribute("class")

    # Switch to dark
    sailor_page.select_option("#theme", "dark")
    sailor_page.wait_for_timeout(500)
    assert "theme-dark" in preview.get_attribute("class")

    # Switch to forest
    sailor_page.select_option("#theme", "forest")
    sailor_page.wait_for_timeout(500)
    assert "theme-forest" in preview.get_attribute("class")
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/17-theme-preview-bg.png")
