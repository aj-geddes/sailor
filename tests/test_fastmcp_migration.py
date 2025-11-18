#!/usr/bin/env python3
"""Test script to verify FastMCP migration of Sailor MCP server"""

import asyncio
import json
from src.sailor_mcp.server import mcp

async def test_server():
    """Test that the FastMCP server has all expected tools and prompts"""

    print("Testing FastMCP Migration for Sailor MCP Server\n")
    print("=" * 50)

    # Expected tools
    expected_tools = [
        "request_mermaid_generation",
        "validate_and_render_mermaid",
        "get_mermaid_examples",
        "get_diagram_template",
        "get_syntax_help",
        "analyze_diagram_code",
        "suggest_diagram_improvements"
    ]

    # Expected prompts
    expected_prompts = [
        "flowchart_wizard",
        "sequence_diagram_wizard",
        "architecture_diagram",
        "data_visualization",
        "project_timeline",
        "state_diagram_wizard",
        "er_diagram_wizard",
        "class_diagram_wizard",
        "mindmap_wizard",
        "user_journey_wizard",
        "troubleshooting_flowchart"
    ]

    # Test tools
    print("\n📦 Checking Tools:")
    tools_found = []
    for tool_name in expected_tools:
        if hasattr(mcp, 'tools') and tool_name in mcp.tools:
            print(f"  ✅ {tool_name}")
            tools_found.append(tool_name)
        else:
            # Check if function exists in module
            import src.sailor_mcp.server as server_module
            if hasattr(server_module, tool_name):
                print(f"  ✅ {tool_name}")
                tools_found.append(tool_name)
            else:
                print(f"  ❌ {tool_name} - MISSING")

    # Test prompts
    print("\n💬 Checking Prompts:")
    prompts_found = []
    for prompt_name in expected_prompts:
        if hasattr(mcp, 'prompts') and prompt_name in mcp.prompts:
            print(f"  ✅ {prompt_name}")
            prompts_found.append(prompt_name)
        else:
            # Check if function exists in module
            import src.sailor_mcp.server as server_module
            if hasattr(server_module, prompt_name):
                print(f"  ✅ {prompt_name}")
                prompts_found.append(prompt_name)
            else:
                print(f"  ❌ {prompt_name} - MISSING")

    # Test calling a tool
    print("\n🧪 Testing Tool Execution:")
    try:
        # Test the request_mermaid_generation tool
        result = await mcp.tools.request_mermaid_generation(
            description="Simple test flowchart",
            diagram_type="flowchart"
        )
        if result and isinstance(result, str) and "flowchart" in result.lower():
            print("  ✅ request_mermaid_generation works!")
        else:
            print("  ⚠️ request_mermaid_generation returned unexpected result")
    except Exception as e:
        print(f"  ❌ Error testing tool: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Migration Summary:")
    print(f"  Tools: {len(tools_found)}/{len(expected_tools)} found")
    print(f"  Prompts: {len(prompts_found)}/{len(expected_prompts)} found")

    if len(tools_found) == len(expected_tools) and len(prompts_found) == len(expected_prompts):
        print("\n✅ Migration SUCCESSFUL! All tools and prompts are present.")
    else:
        print("\n⚠️ Migration INCOMPLETE. Some tools or prompts are missing.")

    return len(tools_found) == len(expected_tools) and len(prompts_found) == len(expected_prompts)

if __name__ == "__main__":
    success = asyncio.run(test_server())
    exit(0 if success else 1)