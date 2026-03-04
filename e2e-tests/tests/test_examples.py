"""Test: Loading Example Diagrams."""
import pytest
from playwright.sync_api import Page, expect

SCREENSHOT_DIR = "e2e-screenshots/main"


def test_load_flowchart_example(sailor_page: Page):
    """Verify loading the flowchart example."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.locator(".example-btn", has_text="Flowchart").click()
    sailor_page.wait_for_timeout(1500)

    code = sailor_page.evaluate("() => editor.getValue()")
    assert "Christmas" in code
    assert "Go shopping" in code

    expect(preview.locator("svg")).to_be_visible(timeout=10000)
    svg_text = preview.inner_text()
    assert "Christmas" in svg_text
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/05-flowchart-example.png")


def test_load_sequence_example(sailor_page: Page):
    """Verify loading the sequence diagram example."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.locator(".example-btn", has_text="Sequence").click()
    sailor_page.wait_for_timeout(1500)

    code = sailor_page.evaluate("() => editor.getValue()")
    assert "sequenceDiagram" in code
    assert "Alice" in code

    expect(preview.locator("svg")).to_be_visible(timeout=10000)
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/06-sequence-example.png")


def test_load_gantt_example(sailor_page: Page):
    """Verify loading the Gantt chart example."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    sailor_page.locator(".example-btn", has_text="Gantt Chart").click()
    sailor_page.wait_for_timeout(1500)

    code = sailor_page.evaluate("() => editor.getValue()")
    assert "gantt" in code
    assert "A Gantt Diagram" in code

    expect(preview.locator("svg")).to_be_visible(timeout=10000)
    sailor_page.screenshot(path=f"{SCREENSHOT_DIR}/07-gantt-example.png")


def test_switch_between_examples(sailor_page: Page):
    """Verify switching between examples updates both editor and preview."""
    preview = sailor_page.locator("#mermaidPreview")
    expect(preview.locator("svg")).to_be_visible(timeout=10000)

    # Load flowchart
    sailor_page.locator(".example-btn", has_text="Flowchart").click()
    sailor_page.wait_for_timeout(1500)
    code1 = sailor_page.evaluate("() => editor.getValue()")
    assert "Christmas" in code1

    # Switch to sequence
    sailor_page.locator(".example-btn", has_text="Sequence").click()
    sailor_page.wait_for_timeout(1500)
    code2 = sailor_page.evaluate("() => editor.getValue()")
    assert "sequenceDiagram" in code2
    assert "Christmas" not in code2

    # Switch to gantt
    sailor_page.locator(".example-btn", has_text="Gantt Chart").click()
    sailor_page.wait_for_timeout(1500)
    code3 = sailor_page.evaluate("() => editor.getValue()")
    assert "gantt" in code3
    assert "sequenceDiagram" not in code3
