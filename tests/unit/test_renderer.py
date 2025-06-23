"""Unit tests for Mermaid renderer"""
import pytest
import base64
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.sailor_mcp.renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer


class TestMermaidConfig:
    """Test cases for MermaidConfig"""
    
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


class TestMermaidRenderer:
    """Test cases for MermaidRenderer"""
    
    @pytest.fixture
    def renderer(self):
        """Create a renderer instance for testing"""
        return MermaidRenderer()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test renderer as context manager"""
        with patch('src.sailor_mcp.renderer.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            async with MermaidRenderer() as renderer:
                assert renderer.browser is not None
                mock_playwright.return_value.start.assert_called_once()
            
            # After exiting context, browser should be closed
            mock_browser.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_stop(self, renderer):
        """Test starting and stopping the browser"""
        with patch('src.sailor_mcp.renderer.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            
            # Start browser
            await renderer.start()
            assert renderer.browser is not None
            mock_playwright.return_value.start.assert_called_once()
            
            # Stop browser
            await renderer.stop()
            assert renderer.browser is None
            mock_browser.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_render_png(self, renderer):
        """Test rendering to PNG"""
        with patch('src.sailor_mcp.renderer.async_playwright'):
            # Mock browser and page
            mock_page = AsyncMock()
            mock_element = AsyncMock()
            mock_screenshot_data = b"fake_png_data"
            
            renderer.browser = AsyncMock()
            renderer.browser.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_element.screenshot = AsyncMock(return_value=mock_screenshot_data)
            
            # Test render
            code = "graph TD\n    A --> B"
            config = MermaidConfig()
            
            with patch('tempfile.NamedTemporaryFile'), \
                 patch('os.unlink'):
                result = await renderer.render(code, config, "png")
            
            assert 'png' in result
            assert result['png'] == base64.b64encode(mock_screenshot_data).decode('utf-8')
            mock_element.screenshot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_render_svg(self, renderer):
        """Test rendering to SVG"""
        with patch('src.sailor_mcp.renderer.async_playwright'):
            # Mock browser and page
            mock_page = AsyncMock()
            mock_element = AsyncMock()
            mock_svg_content = '<svg>test</svg>'
            
            renderer.browser = AsyncMock()
            renderer.browser.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_page.evaluate = AsyncMock(return_value=mock_svg_content)
            
            # Test render
            code = "graph TD\n    A --> B"
            config = MermaidConfig()
            
            with patch('tempfile.NamedTemporaryFile'), \
                 patch('os.unlink'):
                result = await renderer.render(code, config, "svg")
            
            assert 'svg' in result
            assert result['svg'] == base64.b64encode(
                mock_svg_content.encode('utf-8')
            ).decode('utf-8')
    
    @pytest.mark.asyncio
    async def test_render_both_formats(self, renderer):
        """Test rendering to both PNG and SVG"""
        with patch('src.sailor_mcp.renderer.async_playwright'):
            # Mock browser and page
            mock_page = AsyncMock()
            mock_element = AsyncMock()
            mock_screenshot_data = b"fake_png_data"
            mock_svg_content = '<svg>test</svg>'
            
            renderer.browser = AsyncMock()
            renderer.browser.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_element.screenshot = AsyncMock(return_value=mock_screenshot_data)
            mock_page.evaluate = AsyncMock(return_value=mock_svg_content)
            
            # Test render
            code = "graph TD\n    A --> B"
            config = MermaidConfig()
            
            with patch('tempfile.NamedTemporaryFile'), \
                 patch('os.unlink'):
                result = await renderer.render(code, config, "both")
            
            assert 'png' in result
            assert 'svg' in result
    
    @pytest.mark.asyncio
    async def test_render_with_custom_config(self, renderer):
        """Test rendering with custom configuration"""
        with patch('src.sailor_mcp.renderer.async_playwright'):
            # Mock browser and page
            mock_page = AsyncMock()
            mock_element = AsyncMock()
            mock_screenshot_data = b"fake_png_data"
            
            renderer.browser = AsyncMock()
            renderer.browser.new_page = AsyncMock(return_value=mock_page)
            
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_element.screenshot = AsyncMock(return_value=mock_screenshot_data)
            
            # Test with custom config
            code = "graph LR\n    A --> B"
            config = MermaidConfig(
                theme="dark",
                look="handDrawn",
                background="white",
                scale=3
            )
            
            with patch('tempfile.NamedTemporaryFile'), \
                 patch('os.unlink'):
                result = await renderer.render(code, config, "png")
            
            # Verify screenshot was called with correct options
            mock_element.screenshot.assert_called_once_with(
                type='png',
                scale=3,
                omit_background=False
            )
    
    @pytest.mark.asyncio
    async def test_render_error_handling(self, renderer):
        """Test error handling during rendering"""
        with patch('src.sailor_mcp.renderer.async_playwright'):
            renderer.browser = AsyncMock()
            mock_page = AsyncMock()
            renderer.browser.new_page = AsyncMock(return_value=mock_page)
            
            # Mock page to raise an error
            mock_page.query_selector = AsyncMock(return_value=None)
            
            code = "graph TD\n    A --> B"
            config = MermaidConfig()
            
            with patch('tempfile.NamedTemporaryFile'), \
                 patch('os.unlink'), \
                 pytest.raises(RuntimeError, match="Failed to render diagram"):
                await renderer.render(code, config, "png")
    
    def test_create_html(self, renderer):
        """Test HTML generation"""
        code = "graph TD\n    A --> B"
        config = MermaidConfig(theme="dark", look="handDrawn")
        
        html = renderer._create_html(code, config)
        
        assert 'mermaid@11' in html
        assert code in html
        assert "theme: 'dark'" in html
        assert "look: 'handDrawn'" in html
        assert 'background-color: transparent' in html
    
    def test_create_html_with_white_background(self, renderer):
        """Test HTML generation with white background"""
        code = "graph TD\n    A --> B"
        config = MermaidConfig(background="white")
        
        html = renderer._create_html(code, config)
        
        assert 'background-color: white' in html


class TestRendererSingleton:
    """Test cases for renderer singleton functions"""
    
    @pytest.mark.asyncio
    async def test_get_renderer_singleton(self):
        """Test getting singleton renderer instance"""
        with patch('src.sailor_mcp.renderer.MermaidRenderer') as MockRenderer:
            mock_instance = AsyncMock()
            MockRenderer.return_value = mock_instance
            
            # First call should create instance
            renderer1 = await get_renderer()
            MockRenderer.assert_called_once()
            mock_instance.start.assert_called_once()
            
            # Second call should return same instance
            renderer2 = await get_renderer()
            assert renderer1 is renderer2
            assert MockRenderer.call_count == 1
        
        # Cleanup
        await cleanup_renderer()
    
    @pytest.mark.asyncio
    async def test_cleanup_renderer(self):
        """Test cleaning up singleton renderer"""
        with patch('src.sailor_mcp.renderer.MermaidRenderer') as MockRenderer:
            mock_instance = AsyncMock()
            MockRenderer.return_value = mock_instance
            
            # Create renderer
            await get_renderer()
            
            # Cleanup
            await cleanup_renderer()
            mock_instance.stop.assert_called_once()
            
            # Getting renderer again should create new instance
            await get_renderer()
            assert MockRenderer.call_count == 2