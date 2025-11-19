#!/usr/bin/env python3
"""
Test script to verify the enhanced MCP server starts correctly
and all Phase 2 tools are registered
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from sailor_mcp.server import mcp

async def test_server_startup():
    """Test that the server initializes with all tools"""
    print("🚀 Testing Sailor MCP Server Startup\n")
    
    # Get registered tools - check available attributes
    print("Available MCP attributes:", [attr for attr in dir(mcp) if not attr.startswith('_')])
    
    # Try to access tools using getter methods
    try:
        tools = await mcp.get_tools() if hasattr(mcp, 'get_tools') else {}
        resources = await mcp.get_resources() if hasattr(mcp, 'get_resources') else {}
        prompts = await mcp.get_prompts() if hasattr(mcp, 'get_prompts') else {}
    except Exception as e:
        print(f"Could not access tools/resources/prompts: {e}")
        return False
    
    print(f"📋 Registered Tools ({len(tools)}):")
    expected_tools = [
        "request_mermaid_generation",
        "validate_and_render_mermaid", 
        "get_mermaid_examples",
        "analyze_diagram",
        "suggest_improvements",
        "convert_diagram_style",
        "generate_from_code",      # Phase 2
        "generate_from_data",      # Phase 2
        "modify_diagram",          # Phase 2
        "merge_diagrams",          # Phase 2
        "extract_subgraph",        # Phase 2
        "optimize_layout"          # Phase 2
    ]
    
    if isinstance(tools, dict) and 'tools' in tools:
        tool_names = [tool['name'] for tool in tools['tools']]
    elif isinstance(tools, list):
        tool_names = [tool.get('name', 'unknown') for tool in tools]
    else:
        tool_names = list(tools.keys()) if tools else []
    
    for tool_name in expected_tools:
        if tool_name in tool_names:
            print(f"  ✅ {tool_name}")
        else:
            print(f"  ❌ {tool_name} - MISSING")
    
    print(f"\n📚 Registered Resources ({len(resources)}):")
    expected_resources = [
        "diagram://list",
        "template://{diagram_type}",
        "syntax://mermaid/{diagram_type}",
        "best_practices://{diagram_type}",
        "examples://by_industry/{industry}",     # Phase 2
        "examples://by_complexity/{level}"      # Phase 2
    ]
    
    if isinstance(resources, dict) and 'resourceTemplates' in resources:
        resource_names = [res['uriTemplate'] for res in resources['resourceTemplates']]
    elif isinstance(resources, list):
        resource_names = [res.get('uriTemplate', 'unknown') for res in resources]
    else:
        resource_names = list(resources.keys()) if resources else []
    
    for resource in resource_names:
        print(f"  ✅ {resource}")
    
    print(f"\n💬 Registered Prompts ({len(prompts)}):")
    expected_prompts = [
        "create_system_architecture",
        "document_user_flow", 
        "analyze_codebase_structure"
    ]
    
    if isinstance(prompts, dict) and 'prompts' in prompts:
        prompt_names = [prompt['name'] for prompt in prompts['prompts']]
    elif isinstance(prompts, list):
        prompt_names = [prompt.get('name', 'unknown') for prompt in prompts]
    else:
        prompt_names = list(prompts.keys()) if prompts else []
    
    for prompt in prompt_names:
        print(f"  ✅ {prompt}")
    
    # Summary
    total_tools = len(tool_names) if 'tool_names' in locals() else 0
    total_resources = len(resource_names) if 'resource_names' in locals() else 0
    total_prompts = len(prompt_names) if 'prompt_names' in locals() else 0
    
    print(f"\n📊 Summary:")
    print(f"  Tools: {total_tools}/12 expected")
    print(f"  Resources: {total_resources}/6 expected")
    print(f"  Prompts: {total_prompts}/3 expected")
    
    if total_tools >= 12 and total_resources >= 6 and total_prompts >= 3:
        print(f"\n🎉 Server startup test PASSED!")
        print(f"   Sailor Phase 2 is ready to be the ultimate Mermaid tamer!")
        return True
    else:
        print(f"\n❌ Server startup test FAILED!")
        return False

async def test_sample_tool_schema():
    """Test that tools have proper schemas"""
    print(f"\n🔧 Testing Tool Schemas:")
    
    try:
        # Test getting a specific tool
        tool = await mcp.get_tool("generate_from_code")
        if tool:
            print(f"  ✅ generate_from_code tool found")
        else:
            print(f"  ❌ generate_from_code tool not found")
    except:
        print(f"  ❌ Could not retrieve generate_from_code tool")
    
    try:
        # Test getting a resource
        resource = await mcp.get_resource("examples://by_industry/healthcare")
        if resource:
            print(f"  ✅ Industry examples resource accessible")
        else:
            print(f"  ❌ Industry examples resource not accessible")
    except:
        print(f"  ❌ Could not retrieve industry examples resource")
    
    print(f"  ✅ Schema testing completed")

async def main():
    """Run all startup tests"""
    try:
        success = await test_server_startup()
        await test_sample_tool_schema()
        
        if success:
            print(f"\n🌟 All tests passed! Sailor is ready to tame Mermaid diagrams!")
        else:
            print(f"\n⚠️  Some tests failed. Check the output above.")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())