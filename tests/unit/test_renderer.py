"""Unit tests for Mermaid renderer - REAL IMPLEMENTATIONS ONLY"""
import pytest
import base64
import tempfile
import os
from src.sailor_mcp.renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer

# Check if Playwright is available
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TestMermaidConfig:
    """Test cases for MermaidConfig - no mocking needed"""

    def test_default_config(self):
        """Test default configuration values"""
        config = MermaidConfig()
        assert config.theme == "default"
        assert config.look == "classic"
        assert config.direction == "TB"
        assert config.background == "transparent"
        assert config.scale == 2
        assert config.width is None
        assert config.height is None

    def test_custom_config(self):
        """Test custom configuration"""
        config = MermaidConfig(
            theme="dark",
            look="handDrawn",
            direction="LR",
            background="white",
            scale=3,
            width=800,
            height=600
        )
        assert config.theme == "dark"
        assert config.look == "handDrawn"
        assert config.direction == "LR"
        assert config.background == "white"
        assert config.scale == 3
        assert config.width == 800
        assert config.height == 600


@pytest.mark.requires_playwright
class TestMermaidRenderer:
    """Test cases for MermaidRenderer using REAL Playwright"""

    @pytest.fixture
    def renderer(self):
        """Create a renderer instance for testing"""
        return MermaidRenderer()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_context_manager_real(self):
        """Test renderer as context manager with REAL browser"""
        async with MermaidRenderer() as renderer:
            assert renderer.browser is not None
            # Browser should be running
            assert renderer.browser.is_connected()

        # After exiting context, browser should be closed
        assert renderer.browser is None

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_start_stop_real(self, renderer):
        """Test starting and stopping the REAL browser"""
        # Start browser
        await renderer.start()
        assert renderer.browser is not None
        assert renderer.browser.is_connected()

        # Stop browser
        await renderer.stop()
        assert renderer.browser is None

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_render_png_real(self):
        """Test rendering to PNG with REAL browser"""
        renderer = MermaidRenderer()
        await renderer.start()

        try:
            code = "graph TD\n    A --> B"
            config = MermaidConfig()

            result = await renderer.render(code, config, "png")

            assert 'png' in result
            # Check it's base64 encoded
            assert isinstance(result['png'], str)
            # Decode to verify it's valid base64
            decoded = base64.b64decode(result['png'])
            assert len(decoded) > 0
            # PNG magic bytes
            assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
        finally:
            await renderer.stop()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_render_svg_real(self):
        """Test rendering to SVG with REAL browser"""
        renderer = MermaidRenderer()
        await renderer.start()

        try:
            code = "graph TD\n    A --> B"
            config = MermaidConfig()

            result = await renderer.render(code, config, "svg")

            assert 'svg' in result
            # Check it's base64 encoded
            assert isinstance(result['svg'], str)
            # Decode to verify it's valid base64
            decoded = base64.b64decode(result['svg'])
            svg_str = decoded.decode('utf-8')
            assert '<svg' in svg_str
            assert '</svg>' in svg_str
        finally:
            await renderer.stop()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_render_both_formats_real(self):
        """Test rendering to both PNG and SVG with REAL browser"""
        renderer = MermaidRenderer()
        await renderer.start()

        try:
            code = "graph TD\n    A --> B"
            config = MermaidConfig()

            result = await renderer.render(code, config, "both")

            assert 'png' in result
            assert 'svg' in result

            # Verify PNG
            png_decoded = base64.b64decode(result['png'])
            assert png_decoded[:8] == b'\x89PNG\r\n\x1a\n'

            # Verify SVG
            svg_decoded = base64.b64decode(result['svg'])
            svg_str = svg_decoded.decode('utf-8')
            assert '<svg' in svg_str
        finally:
            await renderer.stop()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_render_with_custom_config_real(self):
        """Test rendering with custom configuration using REAL browser"""
        renderer = MermaidRenderer()
        await renderer.start()

        try:
            code = "graph LR\n    A --> B"
            config = MermaidConfig(
                theme="dark",
                look="handDrawn",
                background="white",
                scale=3
            )

            result = await renderer.render(code, config, "png")

            assert 'png' in result
            # Verify it's valid PNG
            png_decoded = base64.b64decode(result['png'])
            assert png_decoded[:8] == b'\x89PNG\r\n\x1a\n'
        finally:
            await renderer.stop()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_render_complex_diagram_real(self):
        """Test rendering complex diagram with REAL browser"""
        renderer = MermaidRenderer()
        await renderer.start()

        try:
            code = """graph TB
                subgraph "System"
                    A[Client] --> B[Server]
                    B --> C[(Database)]
                end
                D[External API] --> B
            """
            config = MermaidConfig(theme="forest")

            result = await renderer.render(code, config, "svg")

            assert 'svg' in result
            svg_decoded = base64.b64decode(result['svg'])
            svg_str = svg_decoded.decode('utf-8')
            # Check that nodes are rendered
            assert 'Client' in svg_str or 'text' in svg_str
        finally:
            await renderer.stop()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_render_error_handling_real(self):
        """Test error handling during rendering with REAL browser"""
        renderer = MermaidRenderer()
        await renderer.start()

        try:
            # Use malformed Mermaid that might cause rendering issues
            code = "graph TD\n    A --> "  # Incomplete
            config = MermaidConfig()

            # This might still render or might fail - test that we handle it
            try:
                result = await renderer.render(code, config, "png")
                # If it succeeds, check result is valid
                if 'png' in result:
                    assert isinstance(result['png'], str)
            except RuntimeError as e:
                # If it fails, check we get proper error
                assert "Failed to render" in str(e) or "rendering" in str(e).lower()
        finally:
            await renderer.stop()

    def test_create_html(self, renderer):
        """Test HTML generation - no browser needed"""
        code = "graph TD\n    A --> B"
        config = MermaidConfig(theme="dark", look="handDrawn")

        html = renderer._create_html(code, config)

        assert 'mermaid@11' in html
        assert code in html
        assert "theme: 'dark'" in html
        assert "look: 'handDrawn'" in html
        assert 'background-color: transparent' in html

    def test_create_html_with_white_background(self, renderer):
        """Test HTML generation with white background - no browser needed"""
        code = "graph TD\n    A --> B"
        config = MermaidConfig(background="white")

        html = renderer._create_html(code, config)

        assert 'background-color: white' in html


@pytest.mark.requires_playwright
class TestRendererSingleton:
    """Test cases for renderer singleton functions with REAL implementation"""

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_get_renderer_singleton_real(self):
        """Test getting singleton renderer instance with REAL browser"""
        # First call should create instance
        renderer1 = await get_renderer()
        assert renderer1 is not None
        assert renderer1.browser is not None
        assert renderer1.browser.is_connected()

        # Second call should return same instance
        renderer2 = await get_renderer()
        assert renderer1 is renderer2

        # Cleanup
        await cleanup_renderer()

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_cleanup_renderer_real(self):
        """Test cleaning up singleton renderer with REAL browser"""
        # Create renderer
        renderer = await get_renderer()
        assert renderer.browser is not None
        assert renderer.browser.is_connected()

        # Cleanup
        await cleanup_renderer()

        # Getting renderer again should create new instance
        new_renderer = await get_renderer()
        assert new_renderer is not renderer
        assert new_renderer.browser is not None

        # Final cleanup
        await cleanup_renderer()


# Tests that don't require Playwright
class TestRendererWithoutPlaywright:
    """Tests that can run without Playwright installed"""

    def test_config_creation(self):
        """Test that MermaidConfig can be created without Playwright"""
        config = MermaidConfig()
        assert config is not None
        assert config.theme == "default"

    def test_renderer_instantiation(self):
        """Test that renderer can be instantiated (but not started) without Playwright"""
        renderer = MermaidRenderer()
        assert renderer is not None
        assert renderer.browser is None
        assert renderer.playwright is None

    def test_html_generation_without_browser(self):
        """Test HTML generation works without browser"""
        renderer = MermaidRenderer()
        html = renderer._create_html(
            "graph TD\n    A --> B",
            MermaidConfig()
        )
        assert isinstance(html, str)
        assert 'mermaid' in html
        assert 'graph TD' in html


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestPlaywrightAvailability:
    """Test to verify Playwright is available when expected"""

    @pytest.mark.asyncio
    async def test_playwright_import(self):
        """Test that Playwright can be imported"""
        from playwright.async_api import async_playwright
        assert async_playwright is not None

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_browser_launch(self):
        """Test that browser can actually be launched"""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            assert browser is not None
            page = await browser.new_page()
            assert page is not None
            await browser.close()