"""Test: Responsive Layout at Different Viewports."""
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/responsive"

VIEWPORTS = {
    "mobile": {"width": 375, "height": 812},
    "tablet": {"width": 768, "height": 1024},
    "desktop": {"width": 1440, "height": 900},
}


@pytest.mark.parametrize("viewport_name", VIEWPORTS.keys())
def test_responsive_layout(page: Page, viewport_name: str):
    """Verify page renders at different viewport sizes without crash."""
    vp = VIEWPORTS[viewport_name]
    page.set_viewport_size(vp)
    page.goto("http://192.168.86.94:30501")
    page.wait_for_load_state("networkidle")

    # Page should load without errors
    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("#mermaidPreview")).to_be_visible()

    page.screenshot(
        path=f"{SCREENSHOT_DIR}/layout-{viewport_name}.png",
        full_page=True
    )


@pytest.mark.parametrize("viewport_name", VIEWPORTS.keys())
def test_editor_visible_all_viewports(page: Page, viewport_name: str):
    """Verify the editor is accessible at all viewports."""
    vp = VIEWPORTS[viewport_name]
    page.set_viewport_size(vp)
    page.goto("http://192.168.86.94:30501")
    page.wait_for_load_state("networkidle")

    # CodeMirror editor should be present
    expect(page.locator(".CodeMirror")).to_be_attached()


@pytest.mark.parametrize("viewport_name", VIEWPORTS.keys())
def test_controls_accessible_all_viewports(page: Page, viewport_name: str):
    """Verify controls are present at all viewports."""
    vp = VIEWPORTS[viewport_name]
    page.set_viewport_size(vp)
    page.goto("http://192.168.86.94:30501")
    page.wait_for_load_state("networkidle")

    # Controls should exist in DOM even if overflow
    expect(page.locator("#theme")).to_be_attached()
    expect(page.locator("#generateBtn")).to_be_attached()


def test_mobile_panels_stack_vertically(page: Page):
    """Verify panels stack vertically at mobile width (375px)."""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("http://192.168.86.94:30501")
    page.wait_for_load_state("networkidle")

    # Check that main-content uses column direction at mobile
    direction = page.evaluate("""() => {
        const el = document.querySelector('.main-content');
        return window.getComputedStyle(el).flexDirection;
    }""")
    assert direction == "column", f"Expected flex-direction: column at 375px, got '{direction}'"
    page.screenshot(path=f"{SCREENSHOT_DIR}/mobile-stacked.png", full_page=True)


def test_mobile_page_scrollable(page: Page):
    """Verify content is accessible via scrolling at mobile width (375px)."""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("http://192.168.86.94:30501")
    page.wait_for_load_state("networkidle")

    # Body should allow scrolling (overflow not hidden)
    overflow = page.evaluate("""() => {
        return window.getComputedStyle(document.body).overflow;
    }""")
    assert overflow != "hidden", f"Body overflow is 'hidden' at mobile width, content is not scrollable"

    # The generate button at the bottom should be reachable by scrolling
    page.locator("#generateBtn").scroll_into_view_if_needed()
    expect(page.locator("#generateBtn")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/mobile-scrolled.png", full_page=True)
