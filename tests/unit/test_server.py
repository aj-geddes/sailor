"""Unit tests for MCP Server"""
import pytest
import json
import base64
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.sailor_mcp.server import SailorMCPServer
from src.sailor_mcp.renderer import MermaidConfig


class TestSailorMCPServer:
    """Test cases for SailorMCPServer"""
    
    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        return SailorMCPServer()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test listing available tools"""
        tools = await server._list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "request_mermaid_generation" in tool_names
        assert "validate_and_render_mermaid" in tool_names
        assert "get_mermaid_examples" in tool_names
        
        # Check tool schemas
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
    
    @pytest.mark.asyncio
    async def test_list_prompts(self, server):
        """Test listing available prompts"""
        prompts = await server._list_prompts()
        
        assert len(prompts) == 5
        prompt_names = [prompt.name for prompt in prompts]
        assert "flowchart_wizard" in prompt_names
        assert "sequence_diagram_wizard" in prompt_names
        assert "architecture_diagram" in prompt_names
        assert "data_visualization" in prompt_names
        assert "project_timeline" in prompt_names
        
        # Check prompt structure
        for prompt in prompts:
            assert hasattr(prompt, 'name')
            assert hasattr(prompt, 'description')
            assert hasattr(prompt, 'arguments')
            assert isinstance(prompt.arguments, list)
    
    @pytest.mark.asyncio
    async def test_get_prompt_flowchart(self, server):
        """Test getting flowchart wizard prompt"""
        result = await server._get_prompt(
            "flowchart_wizard",
            {"process_name": "Order Processing", "complexity": "medium"}
        )
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Order Processing" in result[0].text
        assert "medium" in result[0].text
        assert "Starting Point" in result[0].text
        assert "Main Steps" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_prompt_sequence(self, server):
        """Test getting sequence diagram prompt"""
        result = await server._get_prompt(
            "sequence_diagram_wizard",
            {"scenario": "User Login", "participants": "4"}
        )
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "User Login" in result[0].text
        assert "4" in result[0].text
        assert "Participants" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_prompt_unknown(self, server):
        """Test getting unknown prompt"""
        result = await server._get_prompt("unknown_prompt")
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Unknown prompt" in result[0].text
        assert "Available:" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_generation_request_basic(self, server):
        """Test handling basic generation request"""
        arguments = {
            "description": "Create a flowchart for user registration",
            "diagram_type": "flowchart"
        }
        
        result = await server._handle_generation_request(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "user registration" in result[0].text
        assert "flowchart" in result[0].text
        assert "Guidelines for flowchart" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_generation_request_with_requirements(self, server):
        """Test handling generation request with requirements"""
        arguments = {
            "description": "Create a sequence diagram",
            "diagram_type": "sequence",
            "requirements": ["Include error handling", "Show async operations"],
            "style": {
                "theme": "dark",
                "look": "handDrawn",
                "direction": "LR"
            }
        }
        
        result = await server._handle_generation_request(arguments)
        
        assert len(result) == 1
        text = result[0].text
        assert "sequence diagram" in text
        assert "Include error handling" in text
        assert "Show async operations" in text
        assert "theme: dark" in text
        assert "look: handDrawn" in text
        assert "Example sequence:" in text
    
    @pytest.mark.asyncio
    async def test_handle_validate_and_render_valid_code(self, server):
        """Test validation and rendering of valid Mermaid code"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator, \
             patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            
            # Mock validation success
            MockValidator.validate.return_value = {
                'valid': True,
                'diagram_type': 'flowchart',
                'line_count': 5,
                'errors': [],
                'warnings': []
            }
            
            # Mock renderer
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={
                'png': 'base64_png_data'
            })
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {
                "code": "graph TD\n    A --> B",
                "style": {"theme": "dark", "look": "classic"},
                "format": "png"
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            assert len(result) == 2
            assert result[0].type == "text"
            assert "✅ Mermaid code validated successfully!" in result[0].text
            assert "Diagram type: flowchart" in result[0].text
            assert result[1].type == "image"
            assert result[1].data == "base64_png_data"
            assert result[1].mimeType == "image/png"
    
    @pytest.mark.asyncio
    async def test_handle_validate_and_render_invalid_code(self, server):
        """Test validation of invalid Mermaid code"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator:
            
            # Mock validation failure
            MockValidator.validate.return_value = {
                'valid': False,
                'errors': ['Syntax error: Missing arrow', 'Invalid node definition'],
                'warnings': ['Consider using descriptive labels']
            }
            MockValidator.fix_common_errors.return_value = "graph TD\n    A --> B"
            
            arguments = {
                "code": "graph TD\n    A - B",
                "fix_errors": False
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Validation Failed" in result[0].text
            assert "Syntax error: Missing arrow" in result[0].text
            assert "Invalid node definition" in result[0].text
            assert "Consider using descriptive labels" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_validate_and_render_with_markdown(self, server):
        """Test handling code with markdown blocks"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator, \
             patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            
            MockValidator.validate.return_value = {
                'valid': True,
                'diagram_type': 'flowchart',
                'line_count': 3,
                'errors': [],
                'warnings': []
            }
            
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'data'})
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {
                "code": "```mermaid\ngraph TD\n    A --> B\n```"
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            # Verify markdown was stripped
            MockValidator.validate.assert_called_with("graph TD\n    A --> B")
    
    @pytest.mark.asyncio
    async def test_handle_validate_and_render_both_formats(self, server):
        """Test rendering both PNG and SVG formats"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator, \
             patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            
            MockValidator.validate.return_value = {
                'valid': True,
                'diagram_type': 'sequence',
                'line_count': 10,
                'errors': [],
                'warnings': []
            }
            
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={
                'png': 'png_data',
                'svg': 'svg_data'
            })
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {
                "code": "sequenceDiagram\n    A->>B: Hello",
                "format": "both"
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            assert len(result) == 3
            assert result[0].type == "text"
            assert result[1].type == "image"
            assert result[2].type == "text"
            assert "SVG also generated" in result[2].text
    
    @pytest.mark.asyncio
    async def test_handle_validate_and_render_with_warnings(self, server):
        """Test rendering with validation warnings"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator, \
             patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            
            MockValidator.validate.return_value = {
                'valid': True,
                'diagram_type': 'flowchart',
                'line_count': 5,
                'errors': [],
                'warnings': ['Node A has no label', 'Consider using subgraphs']
            }
            
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'data'})
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {"code": "graph TD\n    A --> B"}
            
            result = await server._handle_validate_and_render(arguments)
            
            assert "⚠️ Warnings:" in result[0].text
            assert "Node A has no label" in result[0].text
            assert "Consider using subgraphs" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_validate_and_render_error(self, server):
        """Test handling rendering errors"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator, \
             patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            
            MockValidator.validate.return_value = {
                'valid': True,
                'diagram_type': 'flowchart',
                'line_count': 5,
                'errors': [],
                'warnings': []
            }
            
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(side_effect=Exception("Browser crashed"))
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {"code": "graph TD\n    A --> B"}
            
            result = await server._handle_validate_and_render(arguments)
            
            assert len(result) == 1
            assert "Rendering failed: Browser crashed" in result[0].text
            assert "Code was valid but could not be rendered" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_get_examples_all(self, server):
        """Test getting all examples"""
        result = await server._handle_get_examples({"diagram_type": "all"})
        
        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text
        assert "# Mermaid Diagram Examples" in text
        assert "## Flowchart" in text
        assert "## Sequence" in text
        assert "## Gantt" in text
        assert "## Class" in text
        assert "graph TD" in text
        assert "sequenceDiagram" in text
    
    @pytest.mark.asyncio
    async def test_handle_get_examples_specific(self, server):
        """Test getting specific diagram example"""
        result = await server._handle_get_examples({"diagram_type": "sequence"})
        
        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text
        assert "# Sequence Example" in text
        assert "sequenceDiagram" in text
        assert "participant" in text
    
    @pytest.mark.asyncio
    async def test_call_tool_unknown(self, server):
        """Test calling unknown tool"""
        result = await server._call_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Unknown tool: unknown_tool" in result[0].text
    
    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self, server):
        """Test error handling in tool calls"""
        with patch.object(server, '_handle_generation_request', 
                         side_effect=Exception("Test error")):
            
            result = await server._call_tool("request_mermaid_generation", 
                                           {"description": "test"})
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Error: Test error" in result[0].text
    
    def test_get_example_code(self, server):
        """Test getting example code"""
        examples = server._get_example_code()
        
        expected_types = ["flowchart", "sequence", "gantt", "class", 
                         "state", "er", "pie", "mindmap"]
        
        for dtype in expected_types:
            assert dtype in examples
            assert isinstance(examples[dtype], str)
            assert len(examples[dtype]) > 0
    
    @pytest.mark.asyncio
    async def test_run_server(self, server):
        """Test running the server"""
        with patch('src.sailor_mcp.server.stdio_server') as mock_stdio, \
             patch.object(server, 'renderer', AsyncMock()) as mock_renderer:
            
            # Mock stdio streams
            mock_streams = (AsyncMock(), AsyncMock())
            mock_stdio.return_value.__aenter__.return_value = mock_streams
            mock_stdio.return_value.__aexit__.return_value = None
            
            # Mock server run to complete immediately
            server.server.run = AsyncMock()
            
            await server.run()
            
            # Verify server was run with correct streams
            server.server.run.assert_called_once()
            call_args = server.server.run.call_args[0]
            assert call_args[0] == mock_streams[0]  # stdin
            assert call_args[1] == mock_streams[1]  # stdout
    
    @pytest.mark.asyncio
    async def test_fix_common_errors_integration(self, server):
        """Test fix_errors integration in validate_and_render"""
        with patch('src.sailor_mcp.server.MermaidValidator') as MockValidator, \
             patch('src.sailor_mcp.server.get_renderer') as mock_get_renderer:
            
            # First validation fails
            first_validation = {
                'valid': False,
                'errors': ['Missing arrow syntax'],
                'warnings': []
            }
            
            # After fix, validation succeeds
            second_validation = {
                'valid': True,
                'diagram_type': 'flowchart',
                'line_count': 3,
                'errors': [],
                'warnings': []
            }
            
            MockValidator.validate.side_effect = [first_validation, second_validation]
            MockValidator.fix_common_errors.return_value = "graph TD\n    A --> B"
            
            mock_renderer = AsyncMock()
            mock_renderer.render = AsyncMock(return_value={'png': 'data'})
            mock_get_renderer.return_value = mock_renderer
            
            arguments = {
                "code": "graph TD\n    A - B",
                "fix_errors": True
            }
            
            result = await server._handle_validate_and_render(arguments)
            
            # Should have succeeded after fix
            assert len(result) == 2
            assert "✅ Mermaid code validated successfully!" in result[0].text
            
            # Verify fix was called
            MockValidator.fix_common_errors.assert_called_once_with("graph TD\n    A - B")
            assert MockValidator.validate.call_count == 2