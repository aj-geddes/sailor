"""Test: Diagram Editing and Live Preview."""
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/main"


def test_edit_code_updates_preview(sailor_page: Page):
    """Verify editing code triggers a preview re-render."""
    preview = sailor_page.locator("#mermaidPreview")
    # Wait for initial render
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    # Change the code via CodeMirror API
    sailor_page.evaluate("""() => {
        editor.setValue('graph LR\\n    X[Hello] --> Y[World]');
    }""")

    # Wait for debounced re-render (500ms + render time)
    sailor_page.wait_for_timeout(1500)

    # Verify SVG updated
    svg = preview.locator("svg")
    expect(svg).to_be_visible()

    # Check the new content is in the SVG
    svg_text = preview.inner_text()
    assert "Hello" in svg_text
    assert "World" in svg_text
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/03-edited-diagram.png")


def test_invalid_code_shows_error(sailor_page: Page):
    """Verify invalid Mermaid code shows an error message."""
    sailor_page.evaluate("""() => {
        editor.setValue('this is not valid mermaid code');
    }""")
    sailor_page.wait_for_timeout(1500)

    preview = sailor_page.locator("#mermaidPreview")
    # Should show error text
    error_text = preview.inner_text()
    assert "Error" in error_text or "error" in error_text or len(error_text) == 0
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/04-invalid-code-error.png")


def test_empty_code_clears_preview(sailor_page: Page):
    """Verify empty code clears or shows error in preview."""
    sailor_page.evaluate("() => editor.setValue('')")
    sailor_page.wait_for_timeout(1500)

    preview = sailor_page.locator("#mermaidPreview")
    # Preview should have no SVG or show an error
    svg_count = preview.locator("svg").count()
    # Either no SVG or there's an error message
    assert svg_count == 0 or "Error" in preview.inner_text() or "error" in preview.inner_text()


def test_direction_change_updates_editor_content(sailor_page: Page):
    """Verify changing direction updates the editor code, not just the render (UX-2)."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    # Change direction to LR
    sailor_page.select_option("#direction", "LR")
    sailor_page.wait_for_timeout(1500)

    # Editor content should now contain "graph LR"
    editor_value = sailor_page.evaluate("() => editor.getValue()")
    assert "graph LR" in editor_value, f"Expected 'graph LR' in editor, got: {editor_value}"
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/05-direction-updates-editor.png")


def test_error_overlays_do_not_accumulate(sailor_page: Page):
    """Verify rendering invalid code multiple times doesn't leave orphaned error elements (BUG-3)."""
    # Render invalid code 3 times
    for i in range(3):
        sailor_page.evaluate("() => editor.setValue('this is invalid mermaid code attempt " + str(i) + "')")
        sailor_page.wait_for_timeout(1500)

    # Check for orphaned Mermaid error elements outside the preview container
    orphaned_count = sailor_page.evaluate("""() => {
        const preview = document.getElementById('mermaidPreview');
        let count = 0;
        document.querySelectorAll('div[id^="d"]').forEach(el => {
            if (!preview.contains(el) && (el.textContent.includes('Syntax error') || el.querySelector('svg'))) {
                count++;
            }
        });
        return count;
    }""")
    assert orphaned_count == 0, f"Found {orphaned_count} orphaned Mermaid error elements"
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/06-no-orphaned-errors.png")
