"""Mermaid diagram rendering module"""
import asyncio
import base64
import os
import tempfile
from typing import Dict, Optional
from dataclasses import dataclass
import logging

from playwright.async_api import async_playwright, Browser, Page
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MermaidConfig:
    """Configuration for Mermaid diagram rendering"""
    theme: str = "default"
    look: str = "classic"
    direction: str = "TB"
    background: str = "transparent"
    scale: int = 2
    width: Optional[int] = None
    height: Optional[int] = None


class MermaidRenderer:
    """Renders Mermaid diagrams to images using Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    async def start(self):
        """Start the browser instance"""
        async with self._lock:
            if not self.browser:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                logger.info("Browser started successfully")
    
    async def stop(self):
        """Stop the browser instance"""
        async with self._lock:
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                logger.info("Browser stopped successfully")
    
    async def render(
        self, 
        mermaid_code: str, 
        config: MermaidConfig, 
        output_format: str = "png"
    ) -> Dict[str, str]:
        """
        Render Mermaid diagram to image
        
        Args:
            mermaid_code: The Mermaid diagram code
            config: Rendering configuration
            output_format: Output format ('png', 'svg', or 'both')
            
        Returns:
            Dictionary with base64-encoded images
        
        Raises:
            ValueError: If invalid output format or empty code
            RuntimeError: If rendering fails
        """
        if not mermaid_code or not mermaid_code.strip():
            raise ValueError("Empty Mermaid code provided")
        
        if output_format not in ["png", "svg", "both"]:
            raise ValueError(f"Invalid output format: {output_format}. Use 'png', 'svg', or 'both'")
        
        logger.info(f"Rendering {output_format} with theme={config.theme}, look={config.look}")
        
        if not self.browser:
            await self.start()
        
        # Create HTML with Mermaid diagram
        html_content = self._create_html(mermaid_code, config)
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.html', 
            delete=False
        ) as f:
            f.write(html_content)
            temp_html = f.name
        
        page: Optional[Page] = None
        try:
            # Create page and render
            page = await self.browser.new_page()
            await page.goto(f'file://{temp_html}')
            await page.wait_for_load_state('networkidle')
            
            # Wait for Mermaid to render
            await page.wait_for_selector('#diagram svg, #diagram .mermaid', 
                                        timeout=5000)
            await page.wait_for_timeout(500)  # Additional time for rendering
            
            # Get the diagram element
            diagram = await page.query_selector('#diagram svg, #diagram .mermaid')
            if not diagram:
                raise RuntimeError("Failed to render diagram - no SVG element found")
            
            result = {}
            
            # Export as PNG
            if output_format in ["png", "both"]:
                png_options = {
                    'type': 'png',
                    'omit_background': (config.background == "transparent")
                }
                
                # Only add scale if it's 'css' or 'device'
                if hasattr(config, 'scale_type'):
                    png_options['scale'] = config.scale_type
                else:
                    # Use default screenshot without scale parameter
                    pass
                
                # Add dimensions if specified
                if config.width:
                    png_options['clip'] = {
                        'x': 0,
                        'y': 0,
                        'width': config.width,
                        'height': config.height or config.width
                    }
                
                png_buffer = await diagram.screenshot(**png_options)
                result['png'] = base64.b64encode(png_buffer).decode('utf-8')
                logger.info(f"PNG rendered successfully ({len(png_buffer)} bytes)")
            
            # Export as SVG
            if output_format in ["svg", "both"]:
                svg_content = await page.evaluate(
                    '() => document.querySelector("#diagram svg")?.outerHTML || ""'
                )
                if svg_content:
                    result['svg'] = base64.b64encode(
                        svg_content.encode('utf-8')
                    ).decode('utf-8')
                    logger.info(f"SVG rendered successfully ({len(svg_content)} chars)")
                else:
                    logger.warning("SVG content not found")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error("Rendering timeout - diagram may be too complex")
            raise RuntimeError("Rendering timeout - the diagram may be too complex or contain syntax errors")
        except Exception as e:
            logger.error(f"Rendering error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to render diagram: {str(e)}")
        finally:
            # Clean up
            if page:
                await page.close()
            try:
                os.unlink(temp_html)
            except Exception:
                pass
    
    def _create_html(self, mermaid_code: str, config: MermaidConfig) -> str:
        """Create HTML page with Mermaid diagram"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {
                config.background if config.background == 'white' 
                else 'transparent'
            };
            font-family: Arial, sans-serif;
        }}
        #diagram {{
            display: inline-block;
        }}
        /* Ensure proper sizing */
        #diagram svg {{
            max-width: none !important;
            height: auto !important;
        }}
    </style>
</head>
<body>
    <div id="diagram">
        <pre class="mermaid">
{mermaid_code}
        </pre>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{config.theme}',
            look: '{config.look}',
            flowchart: {{
                curve: 'basis',
                useMaxWidth: false
            }},
            sequence: {{
                useMaxWidth: false
            }},
            gantt: {{
                useMaxWidth: false
            }}
        }});
    </script>
</body>
</html>"""


# Singleton instance for reuse
_renderer_instance: Optional[MermaidRenderer] = None


async def get_renderer() -> MermaidRenderer:
    """Get or create singleton renderer instance"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = MermaidRenderer()
        await _renderer_instance.start()
    return _renderer_instance


async def cleanup_renderer():
    """Clean up the singleton renderer"""
    global _renderer_instance
    if _renderer_instance:
        await _renderer_instance.stop()
        _renderer_instance = None