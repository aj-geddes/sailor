"""
Mermaid Renderer Component
As specified in /docs/index.md Core Components architecture
Connects to Playwright Browser Engine as documented
"""

import asyncio
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page
import logging

logger = logging.getLogger(__name__)


@dataclass
class RenderConfig:
    """Configuration for rendering."""
    theme: str = "default"
    width: int = 1920
    height: int = 1080
    background_color: str = "white"
    scale: float = 1.0
    transparent_background: bool = False


@dataclass
class RenderResult:
    """Result of diagram rendering."""
    success: bool
    data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MermaidRenderer:
    """
    Mermaid diagram renderer using Playwright.
    As documented in /docs/index.md architecture - connects to Browser Engine.
    Follows singleton pattern for efficient browser management.
    """
    
    _instance = None
    _browser: Optional[Browser] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._browser = None
            self._playwright = None
    
    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            logger.info("Browser initialized for rendering")
    
    async def render(self, code: str, theme: str = "default", 
                    output_format: str = "png", 
                    transparent_background: bool = False) -> RenderResult:
        """
        Render Mermaid diagram to image.
        Follows architecture documented in /docs/index.md
        """
        try:
            await self._ensure_browser()
            
            # Create new page for rendering
            page = await self._browser.new_page()
            
            try:
                # Set viewport size
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Create HTML content with Mermaid
                html_content = self._create_html_content(code, theme, transparent_background)
                
                # Load HTML content
                await page.set_content(html_content)
                
                # Wait for Mermaid to render
                await page.wait_for_selector('#mermaid-diagram svg', timeout=10000)
                
                # Get the SVG element
                svg_element = await page.query_selector('#mermaid-diagram svg')
                
                if not svg_element:
                    return RenderResult(
                        success=False,
                        error="Failed to find rendered SVG element"
                    )
                
                # Get SVG dimensions for proper cropping
                svg_box = await svg_element.bounding_box()
                
                if output_format.lower() == 'svg':
                    # Return SVG directly
                    svg_content = await svg_element.inner_html()
                    svg_data = base64.b64encode(svg_content.encode()).decode()
                    
                    return RenderResult(
                        success=True,
                        data=svg_data,
                        metadata={
                            'format': 'svg',
                            'width': svg_box['width'] if svg_box else 0,
                            'height': svg_box['height'] if svg_box else 0
                        }
                    )
                
                # For other formats, take screenshot
                screenshot_options = {
                    'type': output_format.lower(),
                    'omit_background': transparent_background
                }
                
                # Remove None values from options
                screenshot_options = {k: v for k, v in screenshot_options.items() if v is not None}
                
                screenshot_bytes = await svg_element.screenshot(**screenshot_options)
                screenshot_data = base64.b64encode(screenshot_bytes).decode()
                
                return RenderResult(
                    success=True,
                    data=screenshot_data,
                    metadata={
                        'format': output_format.lower(),
                        'width': svg_box['width'] if svg_box else 0,
                        'height': svg_box['height'] if svg_box else 0,
                        'theme': theme,
                        'transparent': transparent_background
                    }
                )
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Rendering error: {e}")
            return RenderResult(
                success=False,
                error=str(e)
            )
    
    def _create_html_content(self, mermaid_code: str, theme: str, transparent: bool) -> str:
        """Create HTML content for rendering Mermaid diagram."""
        background_style = "background: transparent;" if transparent else "background: white;"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    {background_style}
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                #mermaid-diagram {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
            </style>
        </head>
        <body>
            <div id="mermaid-diagram">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: '{theme}',
                    themeVariables: {{
                        primaryColor: '#3b82f6',
                        primaryTextColor: '#1f2937',
                        primaryBorderColor: '#2563eb',
                        lineColor: '#6b7280',
                        secondaryColor: '#f3f4f6',
                        tertiaryColor: '#ffffff'
                    }},
                    flowchart: {{
                        htmlLabels: true,
                        curve: 'linear'
                    }},
                    sequence: {{
                        diagramMarginX: 50,
                        diagramMarginY: 10,
                        actorMargin: 50,
                        width: 150,
                        height: 65,
                        boxMargin: 10,
                        boxTextMargin: 5,
                        noteMargin: 10,
                        messageMargin: 35
                    }}
                }});
            </script>
        </body>
        </html>
        """
    
    async def close(self):
        """Close browser and cleanup resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("Browser closed and resources cleaned up")