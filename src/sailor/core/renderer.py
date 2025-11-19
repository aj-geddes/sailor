"""
High-performance Mermaid diagram rendering with multiple output formats.
"""
import asyncio
import base64
import io
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import tempfile

from playwright.async_api import async_playwright, Browser, Page
from PIL import Image
import cairosvg


class Theme(Enum):
    """Available Mermaid themes."""
    DEFAULT = "default"
    DARK = "dark"
    FOREST = "forest"
    NEUTRAL = "neutral"


class RenderStyle(Enum):
    """Rendering styles."""
    CLASSIC = "classic"
    HAND_DRAWN = "handDrawn"


class OutputFormat(Enum):
    """Supported output formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    WEBP = "webp"


@dataclass
class RenderConfig:
    """Configuration for rendering."""
    theme: Theme = Theme.DEFAULT
    style: RenderStyle = RenderStyle.CLASSIC
    background: str = "white"
    width: int = 800
    height: int = 600
    scale: float = 2.0
    font_family: Optional[str] = None
    padding: int = 20
    
    def to_mermaid_config(self) -> Dict[str, Any]:
        """Convert to Mermaid configuration object."""
        config = {
            "theme": self.theme.value,
            "look": self.style.value,
            "themeVariables": {
                "background": self.background,
                "fontFamily": self.font_family or "Arial, sans-serif",
            }
        }
        return config


@dataclass
class RenderResult:
    """Result of rendering operation."""
    success: bool
    format: OutputFormat
    data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_bytes(self) -> Optional[bytes]:
        """Get raw bytes from base64 data."""
        if self.data:
            return base64.b64decode(self.data)
        return None


class MermaidRenderer:
    """
    High-performance Mermaid diagram renderer using Playwright.
    
    Supports multiple output formats and advanced styling options.
    """
    
    _instance: Optional['MermaidRenderer'] = None
    _browser: Optional[Browser] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize renderer."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._page_pool: List[Page] = []
            self._max_pool_size = 5
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Keep browser alive for reuse
        pass
    
    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        async with self._lock:
            if self._browser is None:
                playwright = await async_playwright().start()
                self._browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
    
    async def _get_page(self) -> Page:
        """Get a page from the pool or create new one."""
        await self._ensure_browser()
        
        if self._page_pool:
            return self._page_pool.pop()
        
        page = await self._browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        return page
    
    async def _return_page(self, page: Page):
        """Return page to pool or close if pool is full."""
        if len(self._page_pool) < self._max_pool_size:
            await page.goto("about:blank")  # Clear page
            self._page_pool.append(page)
        else:
            await page.close()
    
    async def render(
        self,
        code: str,
        config: RenderConfig = None,
        output_format: OutputFormat = OutputFormat.PNG
    ) -> RenderResult:
        """
        Render Mermaid diagram to specified format.
        
        Args:
            code: Mermaid diagram code
            config: Rendering configuration
            output_format: Desired output format
            
        Returns:
            RenderResult with base64 encoded data
        """
        if config is None:
            config = RenderConfig()
        
        page = None
        try:
            page = await self._get_page()
            
            # Create HTML with Mermaid
            html_content = self._create_html(code, config)
            
            # Load the HTML
            await page.set_content(html_content, wait_until="networkidle")
            
            # Wait for rendering
            await page.wait_for_selector("#diagram svg", timeout=10000)
            
            # Get diagram dimensions
            dimensions = await page.evaluate("""
                () => {
                    const svg = document.querySelector('#diagram svg');
                    const rect = svg.getBoundingClientRect();
                    return {
                        width: rect.width,
                        height: rect.height
                    };
                }
            """)
            
            # Render based on format
            if output_format == OutputFormat.PNG:
                result = await self._render_png(page, dimensions, config)
            elif output_format == OutputFormat.SVG:
                result = await self._render_svg(page)
            elif output_format == OutputFormat.PDF:
                result = await self._render_pdf(page, dimensions)
            elif output_format == OutputFormat.WEBP:
                result = await self._render_webp(page, dimensions, config)
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            return result
            
        except Exception as e:
            return RenderResult(
                success=False,
                format=output_format,
                error=str(e)
            )
        finally:
            if page:
                await self._return_page(page)
    
    def _create_html(self, code: str, config: RenderConfig) -> str:
        """Create HTML page with Mermaid diagram."""
        mermaid_config = json.dumps(config.to_mermaid_config())
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    margin: 0;
                    padding: {config.padding}px;
                    background: {config.background};
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    font-family: {config.font_family or 'Arial, sans-serif'};
                }}
                #diagram {{
                    transform: scale({config.scale});
                    transform-origin: center;
                }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        </head>
        <body>
            <div id="diagram" class="mermaid">
{code}
            </div>
            <script>
                mermaid.initialize({mermaid_config});
            </script>
        </body>
        </html>
        """
    
    async def _render_png(
        self,
        page: Page,
        dimensions: Dict[str, float],
        config: RenderConfig
    ) -> RenderResult:
        """Render to PNG format."""
        # Calculate viewport with padding
        width = int(dimensions['width'] * config.scale + config.padding * 2)
        height = int(dimensions['height'] * config.scale + config.padding * 2)
        
        # Take screenshot
        screenshot_bytes = await page.screenshot(
            clip={
                "x": 0,
                "y": 0,
                "width": width,
                "height": height
            },
            type="png",
            animations="disabled"
        )
        
        # Optimize PNG
        img = Image.open(io.BytesIO(screenshot_bytes))
        
        # Apply any post-processing
        if config.background == "transparent":
            img = img.convert("RGBA")
            # Make white background transparent
            datas = img.getdata()
            new_data = []
            for item in datas:
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            img.putdata(new_data)
        
        # Save optimized image
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        
        return RenderResult(
            success=True,
            format=OutputFormat.PNG,
            data=base64.b64encode(buffer.read()).decode(),
            metadata={
                "width": width,
                "height": height,
                "scale": config.scale
            }
        )
    
    async def _render_svg(self, page: Page) -> RenderResult:
        """Render to SVG format."""
        svg_content = await page.evaluate("""
            () => {
                const svg = document.querySelector('#diagram svg');
                return svg.outerHTML;
            }
        """)
        
        # Encode as base64
        svg_bytes = svg_content.encode('utf-8')
        
        return RenderResult(
            success=True,
            format=OutputFormat.SVG,
            data=base64.b64encode(svg_bytes).decode(),
            metadata={
                "raw_size": len(svg_content)
            }
        )
    
    async def _render_pdf(self, page: Page, dimensions: Dict[str, float]) -> RenderResult:
        """Render to PDF format."""
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={
                "top": "20px",
                "right": "20px",
                "bottom": "20px",
                "left": "20px"
            }
        )
        
        return RenderResult(
            success=True,
            format=OutputFormat.PDF,
            data=base64.b64encode(pdf_bytes).decode(),
            metadata={
                "page_format": "A4"
            }
        )
    
    async def _render_webp(
        self,
        page: Page,
        dimensions: Dict[str, float],
        config: RenderConfig
    ) -> RenderResult:
        """Render to WebP format."""
        # First get PNG
        png_result = await self._render_png(page, dimensions, config)
        
        if not png_result.success:
            return RenderResult(
                success=False,
                format=OutputFormat.WEBP,
                error="Failed to render base PNG"
            )
        
        # Convert PNG to WebP
        png_bytes = base64.b64decode(png_result.data)
        img = Image.open(io.BytesIO(png_bytes))
        
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=95, method=6)
        buffer.seek(0)
        
        return RenderResult(
            success=True,
            format=OutputFormat.WEBP,
            data=base64.b64encode(buffer.read()).decode(),
            metadata=png_result.metadata
        )
    
    async def render_batch(
        self,
        diagrams: List[tuple[str, RenderConfig]],
        output_format: OutputFormat = OutputFormat.PNG
    ) -> List[RenderResult]:
        """
        Render multiple diagrams efficiently.
        
        Args:
            diagrams: List of (code, config) tuples
            output_format: Output format for all diagrams
            
        Returns:
            List of RenderResults
        """
        tasks = [
            self.render(code, config, output_format)
            for code, config in diagrams
        ]
        
        return await asyncio.gather(*tasks)
    
    async def cleanup(self):
        """Clean up resources."""
        # Close all pages in pool
        for page in self._page_pool:
            await page.close()
        self._page_pool.clear()
        
        # Close browser
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    @classmethod
    async def get_instance(cls) -> 'MermaidRenderer':
        """Get or create renderer instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._ensure_browser()
        return cls._instance