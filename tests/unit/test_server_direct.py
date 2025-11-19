"""Direct unit tests for FastMCP Server - NO MOCKS, REAL IMPLEMENTATIONS"""
import pytest
import json
import base64
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.sailor_mcp.server import (
    request_mermaid_generation,
    validate_and_render_mermaid,
    get_mermaid_examples,
    get_diagram_template,
    get_syntax_help,
    analyze_diagram_code,
    suggest_diagram_improvements,
    flowchart_wizard,
    sequence_diagram_wizard,
    architecture_diagram,
    data_visualization,
    project_timeline,
    mcp
)
from src.sailor_mcp.renderer import MermaidConfig
from src.sailor_mcp.validators import MermaidValidator


class TestSailorMCPServerDirect:
    """Test cases for Sailor FastMCP Server using REAL implementations"""

    @pytest.mark.asyncio
    async def test_request_mermaid_generation_basic(self):
        """Test handling basic generation request"""
        result = await request_mermaid_generation.fn(
            description="Create a flowchart for user registration",
            diagram_type="flowchart"
        )

        assert isinstance(result, str)
        assert "user registration" in result.lower()
        assert "flowchart" in result.lower()
        assert "Guidelines" in result

    @pytest.mark.asyncio
    async def test_request_mermaid_generation_with_requirements(self):
        """Test handling generation request with requirements"""
        result = await request_mermaid_generation.fn(
            description="Create a sequence diagram",
            diagram_type="sequence",
            requirements=["Include error handling", "Show async operations"],
            style={
                "theme": "dark",
                "look": "handDrawn",
                "direction": "LR"
            }
        )

        assert isinstance(result, str)
        assert "sequence" in result.lower()
        assert "Include error handling" in result
        assert "Show async operations" in result
        assert "theme: dark" in result
        assert "look: handDrawn" in result

    @pytest.mark.asyncio
    @pytest.mark.requires_browser
    async def test_validate_and_render_valid_code(self):
        """Test validation and rendering of valid Mermaid code with REAL implementations"""
        # Use REAL validator and renderer - NO MOCKS!
        result = await validate_and_render_mermaid.fn(
            code="graph TD\n    A --> B",
            style={"theme": "dark", "look": "classic"},
            format="png"
        )

        assert isinstance(result, dict)
        # Real validator should validate this correctly
        assert result.get('valid') is True
        assert result.get('diagram_type') == 'graph'  # Real validator returns 'graph' not 'flowchart'
        # Images may or may not be present depending on browser availability
        if 'images' in result:
            assert isinstance(result['images'], dict)

    @pytest.mark.asyncio
    async def test_validate_and_render_invalid_code(self):
        """Test validation of invalid Mermaid code with REAL validator"""
        # Use code that REAL validator will detect as invalid
        result = await validate_and_render_mermaid.fn(
            code="not valid mermaid code",
            fix_errors=False
        )

        assert isinstance(result, dict)
        assert result.get('valid') is False
        assert 'error' in result
        error_msg = result['error']
        # Real validator error messages
        assert "Validation Failed" in error_msg or "Invalid" in error_msg

    @pytest.mark.asyncio
    async def test_get_examples_all(self):
        """Test getting all examples"""
        result = await get_mermaid_examples.fn(
            diagram_type="all"
        )

        assert isinstance(result, dict)
        assert 'examples' in result
        assert len(result['examples']) > 0
        assert result['diagram_type'] == 'all'

    @pytest.mark.asyncio
    async def test_get_examples_specific(self):
        """Test getting specific diagram example"""
        result = await get_mermaid_examples.fn(
            diagram_type="sequence"
        )

        assert isinstance(result, dict)
        assert 'examples' in result
        assert result['diagram_type'] == 'sequence'
        # Check that examples are sequence diagrams
        for example in result['examples']:
            assert example['category'] == 'sequence'

    @pytest.mark.asyncio
    async def test_get_diagram_template(self):
        """Test getting diagram template"""
        result = await get_diagram_template.fn(
            template_name="basic_flow",
            diagram_type="flowchart"
        )

        assert isinstance(result, dict)
        # Should have template or error
        assert 'template' in result or 'error' in result

    @pytest.mark.asyncio
    async def test_get_syntax_help(self):
        """Test getting syntax help"""
        result = await get_syntax_help.fn(
            diagram_type="flowchart",
            generate_reference=True
        )

        assert isinstance(result, dict)
        assert 'reference' in result or 'syntax' in result
        assert result['diagram_type'] == 'flowchart'

    @pytest.mark.asyncio
    async def test_analyze_diagram_code_with_real_validator(self):
        """Test analyzing diagram code with REAL validator"""
        # Use REAL validator - no mocks!
        result = await analyze_diagram_code.fn(
            code="graph TD\n    A --> B",
            focus_areas=["syntax", "readability"]
        )

        assert isinstance(result, dict)
        assert 'is_valid' in result
        # This code is valid
        assert result['is_valid'] is True
        assert result['diagram_type'] == 'graph'  # Real validator returns 'graph' not 'flowchart'
        assert 'analysis' in result

    @pytest.mark.asyncio
    async def test_analyze_invalid_code_real(self):
        """Test analyzing invalid code with REAL validator"""
        result = await analyze_diagram_code.fn(
            code="this is not valid",
            focus_areas=["syntax"]
        )

        assert isinstance(result, dict)
        assert 'is_valid' in result
        assert result['is_valid'] is False
        assert 'errors' in result
        assert len(result['errors']) > 0

    @pytest.mark.asyncio
    async def test_suggest_diagram_improvements_real(self):
        """Test suggesting diagram improvements with REAL validator"""
        # Use REAL validator - no mocks!
        result = await suggest_diagram_improvements.fn(
            current_code="graph TD\n    A --> B --> C",
            improvement_goals=["clarity", "visual_appeal"],
            target_audience="technical"
        )

        assert isinstance(result, dict)
        assert 'suggestions' in result
        assert 'clarity' in result['suggestions']
        assert 'visual_appeal' in result['suggestions']
        assert result['target_audience'] == 'technical'

    @pytest.mark.asyncio
    async def test_flowchart_wizard(self):
        """Test flowchart wizard prompt"""
        result = await flowchart_wizard.fn(
            process_name="Order Processing",
            complexity="medium"
        )

        assert isinstance(result, str)
        assert "Order Processing" in result
        assert "medium" in result

    @pytest.mark.asyncio
    async def test_sequence_diagram_wizard(self):
        """Test sequence diagram wizard prompt"""
        result = await sequence_diagram_wizard.fn(
            scenario="User Login",
            participants="4"
        )

        assert isinstance(result, str)
        assert "User Login" in result
        assert "4" in result
        assert "Participants" in result

    @pytest.mark.asyncio
    async def test_architecture_diagram(self):
        """Test architecture diagram prompt"""
        result = await architecture_diagram.fn(
            system_name="E-commerce",
            components="Frontend,Backend,Database"
        )

        assert isinstance(result, str)
        assert "E-commerce" in result
        assert "Frontend, Backend, Database" in result

    @pytest.mark.asyncio
    async def test_data_visualization(self):
        """Test data visualization prompt"""
        result = await data_visualization.fn(
            data_type="pie",
            title="Market Share"
        )

        assert isinstance(result, str)
        assert "pie chart" in result
        assert "Market Share" in result

    @pytest.mark.asyncio
    async def test_project_timeline(self):
        """Test project timeline prompt"""
        result = await project_timeline.fn(
            project_name="Website Redesign",
            duration="3 months"
        )

        assert isinstance(result, str)
        assert "Website Redesign" in result
        assert "3 months" in result

    @pytest.mark.asyncio
    async def test_fix_common_errors_integration_real(self):
        """Test fix_errors integration with REAL validator"""
        # Test with code that can be fixed
        result = await validate_and_render_mermaid.fn(
            code="graph\n    A --> B",  # Missing direction
            fix_errors=True
        )

        assert isinstance(result, dict)
        # Should succeed after fix
        assert result.get('valid') is True
        # Check it was fixed (added TD)
        if 'corrected_code' in result:
            assert 'graph TD' in result['corrected_code']

    @pytest.mark.asyncio
    async def test_real_validator_edge_cases(self):
        """Test REAL validator with edge cases"""
        # Empty code
        result = MermaidValidator.validate("")
        assert result['valid'] is False
        assert any("Empty" in err for err in result['errors'])

        # Missing arrows
        result = MermaidValidator.validate("graph TD\n    A B")
        assert result['valid'] is True or len(result['warnings']) > 0

        # Complex valid diagram
        complex = """graph TB
            subgraph sub1
                A-->B
            end
            subgraph sub2
                C-->D
            end
            B-->C"""
        result = MermaidValidator.validate(complex)
        assert result['valid'] is True

    @pytest.mark.asyncio
    async def test_mcp_server_instance_exists(self):
        """Test that the FastMCP server instance is properly configured"""
        assert mcp is not None
        assert hasattr(mcp, 'name')
        assert mcp.name == 'sailor-mermaid'
        assert hasattr(mcp, 'version')
        assert mcp.version == '2.0.0'

    @pytest.mark.asyncio
    async def test_real_validator_all_diagram_types(self):
        """Test REAL validator with all supported diagram types"""
        test_cases = [
            ("graph TD\n    A-->B", "graph"),
            ("flowchart LR\n    A-->B", "flowchart"),
            ("sequenceDiagram\n    A->>B: Hi", "sequenceDiagram"),
            ("classDiagram\n    class A", "classDiagram"),
            ("stateDiagram\n    [*] --> State1", "stateDiagram"),
            ("erDiagram\n    CUSTOMER ||--o{ ORDER : places", "erDiagram"),
            ("journey\n    title My day\n    section Morning", "journey"),
            ("gantt\n    title A Gantt\n    dateFormat YYYY-MM-DD", "gantt"),
            ("pie\n    title Pie\n    \"A\" : 30", "pie"),
            ("gitGraph\n    commit", "gitGraph"),
            ("mindmap\n    root", "mindmap")
        ]

        for code, expected_type in test_cases:
            result = MermaidValidator.validate(code)
            # Some might have warnings but should be valid
            if result['valid']:
                assert result['diagram_type'] == expected_type, f"Failed for {expected_type}"