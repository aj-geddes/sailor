"""Integration tests for MCP server functionality"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.sailor_mcp.server import SailorMCPServer
from src.sailor_mcp.renderer import MermaidConfig


class TestMCPIntegration:
    """Integration tests for the MCP server"""
    
    @pytest.fixture
    def server(self):
        """Create server instance"""
        return SailorMCPServer()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_generation_flow(self, server):
        """Test complete flow from generation request to rendered image"""
        # Step 1: Request generation
        gen_arguments = {
            "description": "Create a flowchart showing user login process",
            "diagram_type": "flowchart",
            "requirements": ["Include error handling", "Show success path"],
            "style": {"theme": "dark", "look": "classic"}
        }
        
        gen_result = await server._handle_generation_request(gen_arguments)
        assert len(gen_result) == 1
        assert "flowchart" in gen_result[0].text
        assert "user login process" in gen_result[0].text
        
        # Step 2: Simulate LLM response with Mermaid code
        mermaid_code = """flowchart TD
    A[User enters credentials] --> B{Valid?}
    B -->|Yes| C[Login successful]
    B -->|No| D[Show error]
    D --> A
    C --> E[Redirect to dashboard]"""
        
        # Step 3: Validate and render
        render_arguments = {
            "code": mermaid_code,
            "style": {"theme": "dark", "look": "classic"},
            "format": "png"
        }
        
        with patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'test_image_data'})
            mock_get_renderer.return_value = mock_renderer
            
            render_result = await server._handle_validate_and_render(render_arguments)
            
            assert len(render_result) == 2
            assert "✅ Mermaid code validated successfully!" in render_result[0].text
            assert render_result[1].type == "image"
            assert render_result[1].data == "test_image_data"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_prompt_to_diagram_flow(self, server):
        """Test flow from prompt selection to diagram generation"""
        # Step 1: Get flowchart prompt
        prompt_result = await server._get_prompt(
            "flowchart_wizard",
            {"process_name": "Order Processing", "complexity": "medium"}
        )
        
        assert len(prompt_result) == 1
        assert "Order Processing" in prompt_result[0].text
        assert "Starting Point" in prompt_result[0].text
        
        # Step 2: Simulate user answering the prompt
        user_response = """
        1. Starting Point: Customer places order
        2. Main Steps: Validate order -> Process payment -> Ship order -> Send confirmation
        3. Decision Points: Is payment valid? If yes continue, if no cancel order
        4. End Points: Success: Order delivered, Failure: Order cancelled
        5. Style: Dark theme with hand-drawn look, top-to-bottom flow
        """
        
        # Step 3: Generate based on response
        gen_arguments = {
            "description": user_response,
            "diagram_type": "flowchart",
            "style": {"theme": "dark", "look": "handDrawn", "direction": "TB"}
        }
        
        gen_result = await server._handle_generation_request(gen_arguments)
        assert "Customer places order" in gen_result[0].text
        assert "theme: dark" in gen_result[0].text
        assert "look: handDrawn" in gen_result[0].text
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_correction_flow(self, server):
        """Test automatic error correction during validation"""
        # Invalid Mermaid code
        invalid_code = """graph TD
    A[Start] -- B[Process]
    B -> C[End]"""  # Mixed arrow syntax
        
        with patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'corrected_image'})
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {
                "code": invalid_code,
                "fix_errors": True,
                "format": "png"
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            # Should succeed after fixing
            assert any("validated successfully" in str(item) for item in result)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_tools_integration(self, server):
        """Test integration of all three tools"""
        # Tool 1: Get examples
        examples_result = await server._call_tool(
            "get_mermaid_examples",
            {"diagram_type": "sequence"}
        )
        assert len(examples_result) == 1
        assert "sequenceDiagram" in examples_result[0].text
        
        # Tool 2: Request generation
        gen_result = await server._call_tool(
            "request_mermaid_generation",
            {
                "description": "API authentication flow",
                "diagram_type": "sequence"
            }
        )
        assert len(gen_result) == 1
        assert "sequence" in gen_result[0].text
        
        # Tool 3: Validate and render
        with patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'image_data'})
            mock_get_renderer.return_value = mock_renderer
            
            render_result = await server._call_tool(
                "validate_and_render_mermaid",
                {
                    "code": "sequenceDiagram\n    A->>B: Test",
                    "format": "png"
                }
            )
            assert any("validated successfully" in str(item) for item in render_result)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_style_preferences_flow(self, server):
        """Test that style preferences are properly handled through the flow"""
        # Request with specific style
        arguments = {
            "description": "System architecture",
            "diagram_type": "flowchart",
            "style": {
                "theme": "forest",
                "look": "handDrawn",
                "direction": "LR",
                "background": "transparent"
            }
        }
        
        # Generate request
        gen_result = await server._handle_generation_request(arguments)
        prompt_text = gen_result[0].text
        
        assert "theme: forest" in prompt_text
        assert "look: handDrawn" in prompt_text
        assert "direction: LR" in prompt_text
        assert "background: transparent" in prompt_text
        
        # Validate and render with same style
        code = "flowchart LR\n    A --> B --> C"
        
        with patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'styled_image'})
            mock_get_renderer.return_value = mock_renderer
            
            render_arguments = {
                "code": code,
                "style": arguments["style"],
                "format": "png"
            }
            
            render_result = await server._handle_validate_and_render(render_arguments)
            
            # Verify style was applied
            mock_renderer.render.assert_called_once()
            call_args = mock_renderer.render.call_args[0]
            config = call_args[1]
            
            assert config.theme == "forest"
            assert config.look == "handDrawn"
            assert config.background == "transparent"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_prompt_types(self, server):
        """Test different prompt types produce appropriate content"""
        prompt_tests = [
            ("flowchart_wizard", {"process_name": "Test"}, "Starting Point"),
            ("sequence_diagram_wizard", {"scenario": "Test"}, "Participants"),
            ("architecture_diagram", {"system_name": "Test", "components": "A,B"}, "Component Details"),
            ("data_visualization", {"data_type": "pie", "title": "Test"}, "Categories and Values"),
            ("project_timeline", {"project_name": "Test", "duration": "1 month"}, "Project Phases")
        ]
        
        for prompt_name, args, expected_text in prompt_tests:
            result = await server._get_prompt(prompt_name, args)
            assert len(result) == 1
            assert expected_text in result[0].text
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complex_diagram_validation_and_rendering(self, server):
        """Test validation and rendering of complex diagrams"""
        complex_code = """graph TB
    subgraph "User Interface"
        A[Web App] --> B[Mobile App]
    end
    
    subgraph "API Layer"
        C[REST API] --> D[GraphQL]
        C --> E[WebSocket]
    end
    
    subgraph "Services"
        F[Auth Service] --> G[User Service]
        H[Order Service] --> I[Payment Service]
    end
    
    subgraph "Data Layer"
        J[(PostgreSQL)] --> K[(Redis)]
        L[(MongoDB)] --> M[(Elasticsearch)]
    end
    
    A --> C
    B --> C
    C --> F
    C --> H
    F --> J
    G --> J
    H --> L
    I --> K"""
        
        with patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={
                'png': 'complex_diagram_image',
                'svg': 'complex_diagram_svg'
            })
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {
                "code": complex_code,
                "style": {"theme": "dark", "look": "classic"},
                "format": "both"
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            # Should validate successfully
            assert any("validated successfully" in str(item) for item in result)
            # Should have both PNG and SVG mentions
            assert any(item.type == "image" for item in result)
            assert any("SVG also generated" in str(item) for item in result)