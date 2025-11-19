# FastMCP Migration Plan for Sailor MCP Server

## Executive Summary

This document outlines the comprehensive migration strategy from the legacy `mcp-python` implementation to the modern `FastMCP` framework for the Sailor Mermaid diagram generator. The migration will reduce codebase complexity by ~70%, improve maintainability, and align with modern MCP standards.

## 1. FastMCP Migration Architecture

### Current Architecture (mcp-python)
```python
# Complex, manual setup
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, Prompt

class SailorMCPServer:
    def __init__(self):
        self.server = Server("sailor-mermaid")
        self._setup_handlers()

    def _setup_handlers(self):
        self.server.list_tools()(self._list_tools)
        self.server.call_tool()(self._call_tool)
        # ... more manual registration
```

### Target Architecture (FastMCP)
```python
# Simple, declarative setup
from fastmcp import FastMCP

mcp = FastMCP(name="sailor-mermaid")

@mcp.tool
async def request_mermaid_generation(description: str, ...) -> str:
    """Direct tool implementation"""
    return result
```

## 2. API Mapping Guide

### Core Server Patterns

| Old mcp-python | FastMCP Equivalent | Migration Notes |
|----------------|-------------------|-----------------|
| `Server("name")` | `FastMCP(name="name")` | Direct replacement |
| `server.list_tools()(handler)` | Automatic with `@mcp.tool` | No manual registration needed |
| `server.call_tool()(handler)` | Direct function calls | FastMCP handles routing |
| `server.list_prompts()(handler)` | Automatic with `@mcp.prompt` | Declarative registration |
| `server.get_prompt()(handler)` | Prompt functions return messages | Simplified pattern |
| Manual stdio handling | `mcp.run()` | Built-in transport support |

### Tool Migration Patterns

#### Old Pattern (mcp-python)
```python
async def _list_tools(self) -> List[Tool]:
    return [
        Tool(
            name="request_mermaid_generation",
            description="...",
            inputSchema={...}
        )
    ]

async def _call_tool(self, name: str, arguments: Dict) -> List[TextContent]:
    if name == "request_mermaid_generation":
        return await self._handle_generation_request(arguments)
    # ... more string matching
```

#### New Pattern (FastMCP)
```python
@mcp.tool
async def request_mermaid_generation(
    description: str,
    diagram_type: str = "flowchart",
    requirements: list[str] = None,
    style: dict = None,
    ctx: Context = None  # Optional context injection
) -> str:
    """Request the calling LLM to generate Mermaid code based on requirements"""
    # Direct implementation, no routing needed
    prompt = generate_prompt(description, diagram_type, requirements, style)
    return prompt
```

### Prompt Migration Patterns

#### Old Pattern
```python
async def _list_prompts(self) -> List[Prompt]:
    return [
        Prompt(
            name="flowchart_wizard",
            description="...",
            arguments=[PromptArgument(...)]
        )
    ]

async def _get_prompt(self, name: str, arguments: Dict) -> List[TextContent]:
    if name == "flowchart_wizard":
        return [TextContent(type="text", text=prompt_text)]
```

#### New Pattern
```python
@mcp.prompt("flowchart_wizard")
async def flowchart_wizard(process_name: str, complexity: str = "medium") -> list:
    """Interactive wizard to create a flowchart diagram"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_flowchart_prompt(process_name, complexity)
        }
    ]
```

### Resource Migration Patterns

#### Old Pattern
```python
# Resources handled separately in MermaidResources class
self.resources = MermaidResources()
examples = self.resources.get_examples_by_category(diagram_type)
```

#### New Pattern
```python
@mcp.resource("resource://examples/{diagram_type}")
async def get_examples(diagram_type: str) -> dict:
    """Get examples for a specific diagram type"""
    return resources.get_examples_by_category(diagram_type)

# Static resources
mcp.add_resource(TextResource(
    uri="resource://syntax-help",
    text=resources.get_syntax_help_text()
))
```

## 3. Dependency Updates

### setup.py Changes
```python
# Old dependencies
install_requires = [
    "mcp-python>=0.1.0",  # REMOVE
    # ... other deps
]

# New dependencies
install_requires = [
    "fastmcp>=0.5.0",  # ADD
    "playwright>=1.40.0",  # KEEP
    "asyncio",  # KEEP
    # FastAPI/uvicorn optional for HTTP transport
]
```

### Requirements Files
```bash
# requirements.txt
fastmcp>=0.5.0
playwright>=1.40.0

# requirements-dev.txt (unchanged)
pytest>=7.0.0
pytest-asyncio>=0.21.0
# ...
```

## 4. File Structure Reorganization

### Current Structure
```
src/sailor_mcp/
├── server.py          # 1114 lines - complex class
├── stdio_wrapper.py   # 226 lines - manual JSON-RPC
├── http_server.py     # HTTP variant
├── renderer.py        # KEEP AS-IS
├── validators.py      # KEEP AS-IS
├── prompts.py         # KEEP AS-IS
├── mermaid_resources.py  # ADAPT for resources
└── mocks.py          # REMOVE - FastMCP has better testing
```

### New Structure
```
src/sailor_mcp/
├── server.py          # ~400 lines - FastMCP server with decorators
├── __main__.py        # Entry point: from .server import mcp; mcp.run()
├── tools.py           # Optional: Separate tool implementations
├── prompts.py         # KEEP AS-IS with decorator updates
├── resources.py       # Adapted from mermaid_resources.py
├── renderer.py        # KEEP AS-IS
├── validators.py      # KEEP AS-IS
└── config.py          # Configuration management
```

## 5. Detailed Component Migration

### 5.1 Tool Migration (7 Tools)

```python
# server.py - FastMCP version
from fastmcp import FastMCP, Context
from .validators import MermaidValidator
from .renderer import get_renderer, MermaidConfig
from .prompts import PromptGenerator
from .resources import mermaid_resources

mcp = FastMCP(name="sailor-mermaid")

# Tool 1: request_mermaid_generation
@mcp.tool
async def request_mermaid_generation(
    description: str,
    diagram_type: str = "flowchart",
    requirements: list[str] = None,
    style: dict = None
) -> str:
    """Request the calling LLM to generate Mermaid code based on requirements"""
    prompt = f"Please generate Mermaid diagram code for the following request:\n\n"
    prompt += f"Description: {description}\nDiagram Type: {diagram_type}\n"

    if requirements:
        prompt += "\nSpecific Requirements:\n" + "\n".join(f"- {req}" for req in requirements)

    if style:
        prompt += "\n\nStyle Preferences:\n"
        for key, value in style.items():
            prompt += f"- {key}: {value}\n"

    # Add guidelines and examples
    prompt += get_diagram_guidelines(diagram_type)

    return prompt

# Tool 2: validate_and_render_mermaid
@mcp.tool
async def validate_and_render_mermaid(
    code: str,
    fix_errors: bool = True,
    style: dict = None,
    format: str = "png",
    ctx: Context = None
) -> dict:
    """Validate Mermaid code and render it as an image if valid"""
    # Clean code
    code = clean_mermaid_code(code)

    # Validate
    validation = MermaidValidator.validate(code)

    if not validation['valid'] and fix_errors:
        code = MermaidValidator.fix_common_errors(code)
        validation = MermaidValidator.validate(code)

    if not validation['valid']:
        return {
            "type": "error",
            "errors": validation['errors'],
            "warnings": validation['warnings']
        }

    # Render
    config = MermaidConfig(
        theme=style.get('theme', 'default') if style else 'default',
        look=style.get('look', 'classic') if style else 'classic',
        background=style.get('background', 'transparent') if style else 'transparent'
    )

    renderer = await get_renderer()
    images = await renderer.render(code, config, format)

    # Return both text summary and image data
    return {
        "type": "success",
        "validation": validation,
        "images": images,
        "config": config.__dict__
    }

# Tool 3-7: Similar pattern for other tools
@mcp.tool
async def get_mermaid_examples(
    diagram_type: str = "all",
    complexity: str = "all",
    search_keywords: str = None
) -> list[dict]:
    """Get examples of different Mermaid diagram types"""
    examples = mermaid_resources.search_examples(
        diagram_type, complexity, search_keywords
    )
    return [ex.to_dict() for ex in examples[:5]]

@mcp.tool
async def get_diagram_template(
    template_name: str,
    diagram_type: str = "flowchart",
    fill_variables: dict = None
) -> dict:
    """Get a customizable template for quick diagram generation"""
    template = mermaid_resources.get_template(template_name, diagram_type)
    if not template:
        return {"error": f"Template '{template_name}' not found"}

    result = {"template": template.to_dict()}
    if fill_variables:
        result["filled_code"] = mermaid_resources.fill_template(template, fill_variables)

    return result

@mcp.tool
async def get_syntax_help(
    diagram_type: str,
    topic: str = None,
    generate_reference: bool = False
) -> str:
    """Get syntax reference and help for Mermaid diagram types"""
    if generate_reference:
        return mermaid_resources.generate_quick_reference(diagram_type)

    help_text = mermaid_resources.get_syntax_help(diagram_type, topic)
    practices = mermaid_resources.get_best_practices(diagram_type)

    return format_help_response(help_text, practices)

@mcp.tool
async def analyze_diagram_code(
    code: str,
    focus_areas: list[str] = None
) -> dict:
    """Analyze Mermaid code and provide improvement suggestions"""
    if not focus_areas:
        focus_areas = ['syntax', 'best_practices']

    validator = MermaidValidator()
    validation = validator.validate_mermaid_code(code)

    analysis = {
        "validation": validation,
        "focus_areas": {}
    }

    for area in focus_areas:
        analysis["focus_areas"][area] = analyze_area(code, area, validation)

    return analysis

@mcp.tool
async def suggest_diagram_improvements(
    current_code: str,
    improvement_goals: list[str] = None,
    target_audience: str = "general"
) -> dict:
    """Get suggestions for improving an existing diagram"""
    if not improvement_goals:
        improvement_goals = ['clarity']

    validator = MermaidValidator()
    validation = validator.validate_mermaid_code(current_code)

    suggestions = {
        "current_analysis": validation,
        "improvements": {},
        "audience_tips": get_audience_tips(target_audience),
        "reference_examples": mermaid_resources.get_improvement_examples(
            validation['diagram_type']
        )
    }

    for goal in improvement_goals:
        suggestions["improvements"][goal] = generate_improvements(
            current_code, goal, validation['diagram_type']
        )

    return suggestions
```

### 5.2 Prompt Migration (11 Prompts)

```python
# prompts.py - Updated with FastMCP decorators
from fastmcp import mcp

@mcp.prompt("flowchart_wizard")
async def flowchart_wizard(process_name: str, complexity: str = "medium") -> list:
    """Interactive wizard to create a flowchart diagram"""
    return [{
        "role": "user",
        "content": PromptGenerator.get_flowchart_prompt(process_name, complexity)
    }]

@mcp.prompt("sequence_diagram_wizard")
async def sequence_diagram_wizard(scenario: str, participants: str = "3") -> list:
    """Guide for creating sequence diagrams"""
    return [{
        "role": "user",
        "content": PromptGenerator.get_sequence_prompt(scenario, participants)
    }]

@mcp.prompt("architecture_diagram")
async def architecture_diagram(system_name: str, components: str) -> list:
    """Create system architecture diagrams"""
    component_list = components.split(',') if components else []
    return [{
        "role": "user",
        "content": PromptGenerator.get_architecture_prompt(system_name, component_list)
    }]

# ... Continue for all 11 prompts
```

### 5.3 Entry Point Simplification

```python
# __main__.py - New simplified entry point
from .server import mcp

if __name__ == "__main__":
    mcp.run()  # Handles stdio automatically

# For HTTP transport
# mcp.run(transport="http", port=8000)
```

### 5.4 Resource Integration

```python
# resources.py - Adapted from mermaid_resources.py
from fastmcp import mcp
from fastmcp.resources import TextResource, FileResource

# Dynamic resources
@mcp.resource("resource://examples/{category}")
async def get_category_examples(category: str) -> dict:
    """Get examples for a specific category"""
    examples = MermaidResources().get_examples_by_category(category)
    return {"examples": [ex.to_dict() for ex in examples]}

@mcp.resource("resource://templates/{name}")
async def get_template(name: str) -> dict:
    """Get a specific template"""
    template = MermaidResources().get_template(name)
    return template.to_dict() if template else {"error": "Not found"}

# Static resources
syntax_resource = TextResource(
    uri="resource://syntax/all",
    text=MermaidResources().get_all_syntax_help(),
    name="Complete Syntax Reference",
    mime_type="text/markdown"
)
mcp.add_resource(syntax_resource)

# Best practices as static resource
practices_resource = TextResource(
    uri="resource://best-practices",
    text=MermaidResources().get_all_best_practices(),
    name="Mermaid Best Practices Guide"
)
mcp.add_resource(practices_resource)
```

## 6. Backwards Compatibility Strategy

### 6.1 Dual Mode Support (Optional)
```python
# config.py
import os

USE_LEGACY_MODE = os.getenv("SAILOR_LEGACY_MODE", "false").lower() == "true"

if USE_LEGACY_MODE:
    from .legacy_server import SailorMCPServer
    server = SailorMCPServer()
else:
    from .server import mcp
    server = mcp
```

### 6.2 Response Format Compatibility
```python
# FastMCP returns native Python types, but we can wrap if needed
@mcp.tool
async def validate_and_render_mermaid(...) -> dict:
    # Modern response format
    result = {"validation": ..., "images": ...}

    # If legacy mode needed, convert to TextContent/ImageContent
    if LEGACY_RESPONSE_FORMAT:
        return convert_to_legacy_format(result)

    return result
```

### 6.3 Configuration Compatibility
```json
// claude_desktop_config.json remains the same
{
  "mcpServers": {
    "sailor-mermaid": {
      "command": "python",
      "args": ["-m", "sailor_mcp"]
    }
  }
}
```

## 7. Testing Strategy

### 7.1 Unit Test Migration
```python
# test_server.py - Updated for FastMCP
import pytest
from fastmcp.testing import FastMCPTestClient
from sailor_mcp.server import mcp

@pytest.fixture
def client():
    return FastMCPTestClient(mcp)

async def test_mermaid_generation(client):
    result = await client.call_tool(
        "request_mermaid_generation",
        {"description": "User login flow"}
    )
    assert "flowchart" in result.lower()

async def test_validation(client):
    result = await client.call_tool(
        "validate_and_render_mermaid",
        {"code": "graph TD\nA-->B"}
    )
    assert result["type"] == "success"
```

### 7.2 Integration Tests
```python
# test_integration.py
async def test_full_workflow(client):
    # Generate
    prompt = await client.call_tool(
        "request_mermaid_generation",
        {"description": "API workflow"}
    )

    # Validate and render
    result = await client.call_tool(
        "validate_and_render_mermaid",
        {"code": "graph TD\nA[Start]-->B[End]"}
    )

    assert result["type"] == "success"
    assert "png" in result["images"]
```

### 7.3 Compatibility Tests
```python
# test_compatibility.py
async def test_legacy_format_compatibility():
    """Ensure responses work with old clients"""
    # Test that responses can be consumed by legacy clients
    pass
```

## 8. Migration Phases

### Phase 1: Core Server Setup (Week 1)
- [ ] Install FastMCP dependency
- [ ] Create new server.py with FastMCP instance
- [ ] Set up basic tool structure
- [ ] Verify basic functionality

### Phase 2: Component Migration (Week 2)
- [ ] Migrate all 7 tools
- [ ] Migrate all 11 prompts
- [ ] Integrate resources
- [ ] Update renderer/validator integration

### Phase 3: Transport Simplification (Week 3)
- [ ] Replace stdio_wrapper with FastMCP.run()
- [ ] Update HTTP server if needed
- [ ] Update entry points in setup.py
- [ ] Test with Claude Desktop

### Phase 4: Testing & Documentation (Week 4)
- [ ] Update all unit tests
- [ ] Add integration tests
- [ ] Update README and documentation
- [ ] Performance testing
- [ ] Final validation

## 9. Performance Improvements

### Expected Benefits
- **Startup Time**: ~50% faster (less initialization code)
- **Memory Usage**: ~30% reduction (fewer abstractions)
- **Response Time**: ~20% faster (direct routing)
- **Code Maintenance**: ~70% less boilerplate

### Benchmarking Plan
```python
# benchmark.py
import time
import asyncio
from fastmcp.testing import FastMCPTestClient

async def benchmark_tool_calls():
    client = FastMCPTestClient(mcp)

    start = time.time()
    for _ in range(100):
        await client.call_tool("get_mermaid_examples")

    elapsed = time.time() - start
    print(f"100 calls in {elapsed:.2f}s")
```

## 10. Risk Mitigation

### Identified Risks
1. **Breaking Changes**: Client compatibility
   - Mitigation: Dual-mode support during transition

2. **Feature Gaps**: FastMCP missing features
   - Mitigation: Contribute to FastMCP or maintain wrapper

3. **Performance Regression**: Unexpected slowdowns
   - Mitigation: Comprehensive benchmarking before deployment

4. **Testing Coverage**: Missing edge cases
   - Mitigation: Maintain 100% test coverage

## Conclusion

The migration from mcp-python to FastMCP will result in:
- **70% reduction** in boilerplate code
- **Improved maintainability** through declarative patterns
- **Better type safety** with native Python types
- **Simplified deployment** with built-in transports
- **Enhanced developer experience** with cleaner APIs

The migration can be completed in 4 weeks with minimal disruption to existing functionality.