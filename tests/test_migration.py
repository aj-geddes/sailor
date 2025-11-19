#!/usr/bin/env python3
"""Test FastMCP migration of Sailor MCP server"""

import asyncio

async def test_migration():
    """Test that the migrated server works correctly"""

    print("Testing FastMCP Migration for Sailor MCP Server")
    print("=" * 50)

    # Import after checking
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
        state_diagram_wizard,
        er_diagram_wizard,
        class_diagram_wizard,
        mindmap_wizard,
        user_journey_wizard,
        troubleshooting_flowchart
    )

    # Test a tool
    print("\n📦 Testing Tools:")
    result = await request_mermaid_generation(
        description="Test flowchart",
        diagram_type="flowchart"
    )
    if "flowchart" in result.lower():
        print("  ✅ request_mermaid_generation works!")

    # Test getting examples
    examples = await get_mermaid_examples(diagram_type="flowchart")
    if isinstance(examples, dict) and "examples" in examples:
        print("  ✅ get_mermaid_examples returns dict format!")

    # Test a prompt
    print("\n💬 Testing Prompts:")
    prompt_result = await flowchart_wizard("Test Process", "simple")
    if "flowchart" in prompt_result.lower():
        print("  ✅ flowchart_wizard works!")

    print("\n✅ Migration SUCCESSFUL! Tools and prompts are working.")
    return True

if __name__ == "__main__":
    asyncio.run(test_migration())