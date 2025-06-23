"""Integration tests for Mermaid diagram rendering"""
import pytest
import asyncio
import base64
from src.sailor_mcp.renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer
from src.sailor_mcp.validators import MermaidValidator


class TestRenderingIntegration:
    """Integration tests for the rendering pipeline"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_basic_flowchart_rendering(self):
        """Test rendering a basic flowchart"""
        code = """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[End]
    C --> D"""
        
        # Validate first
        validation = MermaidValidator.validate(code)
        assert validation['valid']
        
        # Render
        renderer = await get_renderer()
        try:
            config = MermaidConfig(theme="default", look="classic")
            result = await renderer.render(code, config, "png")
            
            assert 'png' in result
            assert len(result['png']) > 0
            
            # Verify it's valid base64
            decoded = base64.b64decode(result['png'])
            assert len(decoded) > 0
            
            # PNG magic number check
            assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hand_drawn_rendering(self):
        """Test rendering with hand-drawn look"""
        code = """flowchart LR
    A[Input] --> B[Process]
    B --> C[Output]"""
        
        renderer = await get_renderer()
        try:
            config = MermaidConfig(
                theme="neutral",
                look="handDrawn",
                background="white"
            )
            result = await renderer.render(code, config, "png")
            
            assert 'png' in result
            # Hand-drawn diagrams should still produce valid images
            decoded = base64.b64decode(result['png'])
            assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_svg_rendering(self):
        """Test SVG output format"""
        code = """sequenceDiagram
    participant User
    participant API
    User->>API: Request
    API-->>User: Response"""
        
        renderer = await get_renderer()
        try:
            config = MermaidConfig()
            result = await renderer.render(code, config, "svg")
            
            assert 'svg' in result
            svg_content = base64.b64decode(result['svg']).decode('utf-8')
            assert svg_content.startswith('<svg')
            assert '</svg>' in svg_content
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_both_formats_rendering(self):
        """Test rendering both PNG and SVG"""
        code = """pie title Pet Adoption
    "Dogs" : 45
    "Cats" : 35
    "Birds" : 20"""
        
        renderer = await get_renderer()
        try:
            config = MermaidConfig()
            result = await renderer.render(code, config, "both")
            
            assert 'png' in result
            assert 'svg' in result
            
            # Verify PNG
            png_decoded = base64.b64decode(result['png'])
            assert png_decoded[:8] == b'\x89PNG\r\n\x1a\n'
            
            # Verify SVG
            svg_decoded = base64.b64decode(result['svg']).decode('utf-8')
            assert '<svg' in svg_decoded
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_transparent_background(self):
        """Test rendering with transparent background"""
        code = """mindmap
  root((Sailor Site))
    Features
      AI Generation
      Live Preview
    Benefits
      Easy to use
      Professional"""
        
        renderer = await get_renderer()
        try:
            config = MermaidConfig(background="transparent")
            result = await renderer.render(code, config, "png")
            
            assert 'png' in result
            # Transparent PNGs are still valid PNGs
            decoded = base64.b64decode(result['png'])
            assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration 
    async def test_complex_diagram_rendering(self):
        """Test rendering a complex diagram with subgraphs"""
        code = """graph TB
    subgraph Frontend
        A[React App] --> B[API Client]
    end
    
    subgraph Backend
        C[REST API] --> D[Database]
        C --> E[Cache]
    end
    
    B -->|HTTP| C
    
    subgraph Infrastructure
        F[Load Balancer] --> C
        G[CDN] --> A
    end"""
        
        renderer = await get_renderer()
        try:
            config = MermaidConfig(theme="dark", scale=3)
            result = await renderer.render(code, config, "png")
            
            assert 'png' in result
            decoded = base64.b64decode(result['png'])
            assert len(decoded) > 1000  # Complex diagrams should be larger
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_diagram_types_rendering(self):
        """Test rendering different diagram types"""
        test_cases = [
            ("graph TD\n    A --> B", "flowchart"),
            ("sequenceDiagram\n    A->>B: Hello", "sequence"),
            ("classDiagram\n    class Animal", "class"),
            ("stateDiagram-v2\n    [*] --> State1", "state"),
            ("erDiagram\n    CUSTOMER ||--o{ ORDER : places", "er"),
            ("gantt\n    title Project\n    section Phase1\n    Task1 :a1, 2024-01-01, 30d", "gantt"),
            ("pie\n    title Sales\n    \"Q1\" : 30\n    \"Q2\" : 40", "pie"),
            ("journey\n    title My day\n    section Morning\n    Wake up: 5: Me", "journey"),
        ]
        
        renderer = await get_renderer()
        try:
            for code, diagram_type in test_cases:
                config = MermaidConfig()
                result = await renderer.render(code, config, "png")
                
                assert 'png' in result, f"Failed to render {diagram_type}"
                decoded = base64.b64decode(result['png'])
                assert decoded[:8] == b'\x89PNG\r\n\x1a\n', f"Invalid PNG for {diagram_type}"
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_recovery(self):
        """Test that renderer can recover from errors"""
        renderer = await get_renderer()
        try:
            # First, try invalid code
            invalid_code = "invalid mermaid code"
            
            # This should raise an error but not crash the renderer
            with pytest.raises(Exception):
                await renderer.render(invalid_code, MermaidConfig(), "png")
            
            # Renderer should still work for valid code
            valid_code = "graph TD\n    A --> B"
            result = await renderer.render(valid_code, MermaidConfig(), "png")
            
            assert 'png' in result
            assert len(result['png']) > 0
        finally:
            await cleanup_renderer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_rendering(self):
        """Test concurrent rendering requests"""
        codes = [
            "graph TD\n    A --> B",
            "sequenceDiagram\n    A->>B: Test",
            "pie\n    \"A\" : 50\n    \"B\" : 50"
        ]
        
        renderer = await get_renderer()
        try:
            # Create multiple rendering tasks
            tasks = []
            for code in codes:
                config = MermaidConfig()
                task = renderer.render(code, config, "png")
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks)
            
            # Verify all succeeded
            assert len(results) == len(codes)
            for result in results:
                assert 'png' in result
                decoded = base64.b64decode(result['png'])
                assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
        finally:
            await cleanup_renderer()