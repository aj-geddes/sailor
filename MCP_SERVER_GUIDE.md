# Sailor MCP Server Guide - The Ultimate Mermaid Tamer for LLMs

## Overview

Sailor is a powerful MCP (Model Context Protocol) server designed to make working with Mermaid diagrams effortless for AI assistants. It provides comprehensive tools, resources, and prompts to generate, validate, analyze, and improve diagrams through natural conversation.

## Available MCP Tools

### 1. **request_mermaid_generation**
Generate Mermaid diagrams from natural language descriptions.

```python
# Example usage
result = await mcp.call_tool("request_mermaid_generation", {
    "description": "Create a flowchart showing user login process with email validation",
    "diagram_type": "flowchart",
    "theme": "default"
})
```

### 2. **validate_and_render_mermaid**
Validate Mermaid code and optionally render to image.

```python
# Example usage
result = await mcp.call_tool("validate_and_render_mermaid", {
    "code": "flowchart TD\n    A[Start] --> B[End]",
    "theme": "forest",
    "format": "png",
    "transparent": false
})
```

### 3. **get_mermaid_examples**
Get example diagrams for learning and reference.

```python
# Example usage
examples = await mcp.call_tool("get_mermaid_examples", {
    "diagram_type": "sequence"  # Optional, returns all types if not specified
})
```

### 4. **analyze_diagram** 🆕
Analyze a Mermaid diagram to extract structure, relationships, and meaning.

```python
# Example usage
analysis = await mcp.call_tool("analyze_diagram", {
    "code": "flowchart TD\n    A[Login] --> B{Valid?}\n    B -->|Yes| C[Dashboard]\n    B -->|No| D[Error]"
})
# Returns: node count, relationships, complexity analysis, and summary
```

### 5. **suggest_improvements** 🆕
Get AI-powered suggestions for improving diagram clarity and following best practices.

```python
# Example usage
suggestions = await mcp.call_tool("suggest_improvements", {
    "code": "flowchart TD\n    A --> B\n    B --> C",
    "focus": "clarity"  # Optional: clarity, structure, documentation
})
```

### 6. **convert_diagram_style** 🆕
Convert diagrams between different Mermaid styles.

```python
# Example usage
converted = await mcp.call_tool("convert_diagram_style", {
    "code": "graph TD\n    A --> B",
    "target_style": "flowchart"  # Options: flowchart, graph, dotted, thick, normal
})
```

### 7. **generate_from_code** 🆕 (Phase 2)
Generate Mermaid diagrams from source code analysis.

```python
# Example usage - Python to Class Diagram
python_code = '''
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self._id = None
    
    def login(self):
        pass
    
    def _validate_email(self):
        pass

class Admin(User):
    def __init__(self, name, email, role):
        super().__init__(name, email)
        self.role = role
    
    def manage_users(self):
        pass
'''

result = await mcp.call_tool("generate_from_code", {
    "code": python_code,
    "language": "python",
    "diagram_type": "class"
})
# Generates a class diagram with inheritance, attributes, and methods
```

### 8. **generate_from_data** 🆕 (Phase 2)
Create diagrams from structured data (JSON/CSV).

```python
# Example usage - JSON to ER Diagram
json_data = '''
{
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "orders": [101, 102]},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "orders": [103]}
    ],
    "orders": [
        {"id": 101, "total": 99.99, "items": ["A", "B"]},
        {"id": 102, "total": 149.99, "items": ["C"]}
    ]
}
'''

result = await mcp.call_tool("generate_from_data", {
    "data": json_data,
    "data_format": "json",
    "diagram_type": "er"
})
# Creates an ER diagram showing entities and relationships
```

### 9. **modify_diagram** 🆕 (Phase 2)
Apply specific modifications to existing diagrams.

```python
# Example usage
modifications = [
    {"action": "add_node", "target": "Auth", "value": "Authentication Service"},
    {"action": "add_relationship", "target": "User->Auth", "value": ""},
    {"action": "modify_label", "target": "Process", "value": "Process Order"},
    {"action": "add_subgraph", "target": "Security", "value": "Auth[Authentication]\n        AuthZ[Authorization]"}
]

result = await mcp.call_tool("modify_diagram", {
    "code": existing_diagram_code,
    "modifications": modifications
})
```

### 10. **merge_diagrams** 🆕 (Phase 2)
Intelligently merge multiple diagrams.

```python
# Example usage
merged = await mcp.call_tool("merge_diagrams", {
    "diagram1": first_diagram_code,
    "diagram2": second_diagram_code,
    "merge_strategy": "deduplicate"  # Options: combine, deduplicate, overlay
})
```

### 11. **extract_subgraph** 🆕 (Phase 2)
Extract a portion of a larger diagram.

```python
# Example usage
extracted = await mcp.call_tool("extract_subgraph", {
    "code": large_diagram_code,
    "target": "Payment",  # Extract Payment subgraph or nodes containing "Payment"
    "include_connections": true  # Include all connections to/from extracted nodes
})
```

### 12. **optimize_layout** 🆕 (Phase 2)
Optimize diagram layout for better readability.

```python
# Example usage
optimized = await mcp.call_tool("optimize_layout", {
    "code": messy_diagram_code,
    "optimization_goal": "clarity"  # Options: clarity, compact, hierarchical
})
```

## Available MCP Resources

### Diagram Resources
- `diagram://list` - List all available diagram types and their descriptions
- `template://{diagram_type}` - Get a template for specific diagram type (flowchart, sequence, class, etc.)

### Knowledge Resources 🆕
- `syntax://mermaid/{diagram_type}` - Complete syntax reference for any diagram type
- `best_practices://{diagram_type}` - Best practices and design patterns

### Enhanced Resources 🚀 (Phase 2)
- `examples://by_industry/{industry}` - Industry-specific examples (healthcare, finance, ecommerce)
- `examples://by_complexity/{level}` - Complexity-based examples (beginner, intermediate, advanced)

### Example Usage
```python
# Get syntax reference
syntax = await mcp.read_resource("syntax://mermaid/flowchart")

# Get best practices
practices = await mcp.read_resource("best_practices://sequence")

# Get template
template = await mcp.read_resource("template://class")

# Get industry-specific examples
healthcare_examples = await mcp.read_resource("examples://by_industry/healthcare")
finance_examples = await mcp.read_resource("examples://by_industry/finance")

# Get complexity-based examples
beginner_examples = await mcp.read_resource("examples://by_complexity/beginner")
advanced_examples = await mcp.read_resource("examples://by_complexity/advanced")
```

## Available MCP Prompts 🆕

### 1. **create_system_architecture**
Guided creation of system architecture diagrams.

```python
prompt = await mcp.get_prompt("create_system_architecture", {
    "system_name": "E-commerce Platform",
    "components": ["Frontend", "API Gateway", "Auth Service", "Order Service", "Database"],
    "style": "modern"  # Optional: modern, classic, minimal
})
```

### 2. **document_user_flow**
Create user journey and flow diagrams.

```python
prompt = await mcp.get_prompt("document_user_flow", {
    "process_name": "Online Purchase",
    "user_type": "Customer", 
    "steps": ["Browse Products", "Add to Cart", "Checkout", "Payment", "Confirmation"]
})
```

### 3. **analyze_codebase_structure**
Visualize code/project structure.

```python
prompt = await mcp.get_prompt("analyze_codebase_structure", {
    "project_type": "REST API",
    "main_components": ["Controllers", "Services", "Repositories", "Models", "Middleware"],
    "show_dependencies": true
})
```

## Common Use Cases

### 1. Document API Flow
```python
# Step 1: Generate the diagram
diagram = await mcp.call_tool("request_mermaid_generation", {
    "description": "REST API flow for user registration with email verification",
    "diagram_type": "sequence"
})

# Step 2: Analyze complexity
analysis = await mcp.call_tool("analyze_diagram", {
    "code": diagram["code"]
})

# Step 3: Get improvement suggestions
improvements = await mcp.call_tool("suggest_improvements", {
    "code": diagram["code"]
})
```

### 2. Create System Architecture
```python
# Step 1: Get guided prompt
prompt = await mcp.get_prompt("create_system_architecture", {
    "system_name": "Microservices Platform",
    "components": ["API Gateway", "User Service", "Order Service", "Payment Service"],
    "style": "modern"
})

# Step 2: Generate based on prompt guidance
diagram = await mcp.call_tool("request_mermaid_generation", {
    "description": prompt,
    "diagram_type": "flowchart"
})

# Step 3: Validate and render
result = await mcp.call_tool("validate_and_render_mermaid", {
    "code": diagram["code"],
    "theme": "default",
    "format": "png"
})
```

### 3. Convert Legacy Diagrams
```python
# Convert old graph syntax to modern flowchart
modern = await mcp.call_tool("convert_diagram_style", {
    "code": old_diagram_code,
    "target_style": "flowchart"
})

# Apply modern arrow styles
styled = await mcp.call_tool("convert_diagram_style", {
    "code": modern["converted_code"],
    "target_style": "thick"
})
```

## Best Practices for LLMs

1. **Start with Templates**: Use `template://{type}` resources to start with correct syntax
2. **Validate Early**: Always validate before rendering to catch syntax errors
3. **Analyze Complexity**: Use `analyze_diagram` to ensure diagrams aren't too complex
4. **Iterate with Suggestions**: Use `suggest_improvements` to refine diagrams
5. **Use Prompts for Guidance**: Leverage structured prompts for consistent results

## Integration with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "sailor": {
      "command": "python",
      "args": ["/path/to/sailor/sailor_mcp/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

## Advanced Features

### Multi-Diagram Management
```python
# Compare two versions of a diagram
original = "flowchart TD\n    A --> B"
updated = "flowchart TD\n    A[Start] --> B[Process] --> C[End]"

# Analyze both
analysis1 = await mcp.call_tool("analyze_diagram", {"code": original})
analysis2 = await mcp.call_tool("analyze_diagram", {"code": updated})

# Compare complexity
print(f"Complexity increased from {analysis1['analysis']['complexity']} to {analysis2['analysis']['complexity']}")
```

### Style Consistency
```python
# Ensure consistent styling across multiple diagrams
diagrams = [diagram1, diagram2, diagram3]

for diagram in diagrams:
    # Convert all to consistent style
    consistent = await mcp.call_tool("convert_diagram_style", {
        "code": diagram,
        "target_style": "flowchart"
    })
    
    # Apply consistent arrow style
    final = await mcp.call_tool("convert_diagram_style", {
        "code": consistent["converted_code"],
        "target_style": "thick"
    })
```

## Troubleshooting

### Common Issues

1. **Validation Errors**: Use `syntax://mermaid/{type}` to check syntax
2. **Rendering Failures**: Ensure diagram validates before rendering
3. **Complex Diagrams**: Break into subgraphs or multiple diagrams
4. **Style Issues**: Use `convert_diagram_style` for consistency

### Debug Mode
```python
# Get detailed validation info
validation = await mcp.call_tool("validate_and_render_mermaid", {
    "code": diagram_code,
    "format": "png"
})

if not validation["success"]:
    print(f"Error: {validation['error']}")
    # Get syntax help
    syntax = await mcp.read_resource(f"syntax://mermaid/{diagram_type}")
```

## Future Enhancements

- Code-to-diagram generation
- PlantUML/Graphviz conversion
- Git integration for diagram versioning
- Collaborative diagram editing
- Custom style templates

## Support

- GitHub: https://github.com/aj-geddes/sailor
- Documentation: See `/docs` directory
- MCP Protocol: https://modelcontextprotocol.io

With Sailor MCP Server, creating and managing Mermaid diagrams becomes as natural as having a conversation. Let Sailor tame the complexity of diagram creation for you!