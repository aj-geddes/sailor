"""MCP Server implementation for Sailor Site using FastMCP"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json

from fastmcp import FastMCP

from .validators import MermaidValidator
from .renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer
from .prompts import PromptGenerator
from .mermaid_resources import MermaidResources
from .logging_config import get_logger

# Get logger
logger = get_logger(__name__)

# Create FastMCP server instance
mcp = FastMCP("sailor-mermaid", version="2.0.0")

# Global resources
resources = MermaidResources()
renderer = None

# ==================== TOOLS ====================

# Tool: Request Mermaid Generation
@mcp.tool(description="Request the calling LLM to generate Mermaid code based on requirements")
async def request_mermaid_generation(
    description: str,
    diagram_type: str = "flowchart",
    requirements: List[str] = None,
    style: Dict[str, str] = None
) -> str:
    """Handle request for Mermaid generation"""
    requirements = requirements or []
    style = style or {}

    # Build the request for the calling LLM
    prompt = f"""Please generate Mermaid diagram code for the following request:

Description: {description}
Diagram Type: {diagram_type}
"""

    if requirements:
        prompt += f"\nSpecific Requirements:\n" + "\n".join(f"- {req}" for req in requirements)

    if style:
        prompt += f"\n\nStyle Preferences:\n"
        for key, value in style.items():
            prompt += f"- {key}: {value}\n"

    # Add guidelines
    prompt += f"""

Guidelines for {diagram_type} diagrams:
- Use clear, descriptive labels
- Ensure proper syntax for {diagram_type}
- Include appropriate connections/relationships
- For flowcharts/graphs, specify direction (TD, LR, etc.)
- Keep the diagram well-organized and readable

Please respond with ONLY the Mermaid code, no explanations or markdown blocks."""

    # Add example
    examples = _get_example_code()
    if diagram_type in examples:
        prompt += f"\n\nExample {diagram_type}:\n{examples[diagram_type]}"

    return prompt


# Tool: Validate and Render Mermaid
@mcp.tool(description="Validate Mermaid code and render it as an image if valid")
async def validate_and_render_mermaid(
    code: str,
    fix_errors: bool = True,
    style: Dict[str, str] = None,
    format: str = "png"
) -> Dict[str, Any]:
    """Handle validation and rendering of Mermaid code"""
    global renderer

    code = code.strip()
    style = style or {}

    # Remove markdown code blocks if present
    if code.startswith('```'):
        lines = code.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1] == '```':
            lines = lines[:-1]
        code = '\n'.join(lines)

    # Validate the code
    validation = MermaidValidator.validate(code)

    if not validation['valid'] and fix_errors:
        # Attempt to fix common issues
        code = MermaidValidator.fix_common_errors(code)
        validation = MermaidValidator.validate(code)

    if not validation['valid']:
        error_msg = "## Mermaid Code Validation Failed\n\n"
        error_msg += "### Errors:\n" + "\n".join(f"- {e}" for e in validation['errors'])
        if validation['warnings']:
            error_msg += "\n\n### Warnings:\n" + "\n".join(f"- {w}" for w in validation['warnings'])
        error_msg += f"\n\n### Code provided:\n```mermaid\n{code}\n```"

        return {"error": error_msg, "valid": False}

    # Create config from style
    config = MermaidConfig(
        theme=style.get('theme', 'default'),
        look=style.get('look', 'classic'),
        background=style.get('background', 'transparent')
    )

    # Render the diagram
    try:
        global renderer
        if not renderer:
            logger.info("Initializing renderer on first use...")
            renderer = await get_renderer()

        images = await renderer.render(code, config, format)

        # Create response
        result = {
            "valid": True,
            "diagram_type": validation['diagram_type'],
            "line_count": validation['line_count'],
            "theme": config.theme,
            "style": config.look,
            "background": config.background,
            "images": images
        }

        if validation['warnings']:
            result["warnings"] = validation['warnings']

        return result

    except Exception as e:
        logger.error(f"Rendering error: {e}", exc_info=True)
        return {
            "error": f"Rendering failed: {str(e)}\n\nCode was valid but could not be rendered.",
            "valid": True,
            "rendering_failed": True
        }


# Tool: Get Mermaid Examples
@mcp.tool(description="Get examples of different Mermaid diagram types")
async def get_mermaid_examples(
    diagram_type: str = "all",
    complexity: str = "all",
    search_keywords: str = ""
) -> Dict[str, Any]:
    """Handle request for examples using comprehensive resource library"""

    # Use comprehensive resource library
    if search_keywords:
        examples = resources.search_examples(search_keywords)
        if not examples:
            return {"error": f"No examples found for keywords: {search_keywords}"}
    elif complexity != 'all':
        examples = resources.get_examples_by_complexity(complexity)
        if diagram_type != 'all':
            examples = [ex for ex in examples if ex.category == diagram_type]
    elif diagram_type == 'all':
        examples = []
        for category in resources.examples.keys():
            examples.extend(resources.get_examples_by_category(category))
    else:
        examples = resources.get_examples_by_category(diagram_type)

    if not examples:
        return {"error": f"No examples found for {diagram_type} with complexity {complexity}"}

    # Build comprehensive response
    result = {
        "diagram_type": diagram_type,
        "complexity": complexity,
        "search_keywords": search_keywords,
        "count": len(examples),
        "examples": []
    }

    for example in examples[:5]:  # Limit to 5 examples
        result["examples"].append({
            "name": example.name,
            "category": example.category,
            "complexity": example.complexity,
            "description": example.description,
            "features": example.features,
            "use_cases": example.use_cases,
            "code": example.code
        })

    return result


# Tool: Get Diagram Template
@mcp.tool(description="Get a customizable template for quick diagram generation")
async def get_diagram_template(
    template_name: str,
    diagram_type: str = "flowchart",
    fill_variables: Dict[str, str] = None
) -> Dict[str, Any]:
    """Handle request for diagram templates"""
    fill_variables = fill_variables or {}

    # Get template from resources
    template = resources.get_template(template_name, diagram_type)

    if not template:
        # List available templates
        available = []
        for category, templates in resources.templates.items():
            for tmpl in templates:
                available.append(f"{category}: {tmpl.name}")

        return {
            "error": f"Template '{template_name}' not found",
            "available_templates": available
        }

    result = {
        "name": template.name,
        "description": template.description,
        "variables": template.variables,
        "template": template.template
    }

    if fill_variables:
        # Fill template with provided variables
        filled_code = resources.fill_template(template, fill_variables)
        result["filled_code"] = filled_code
    elif template.example_vars:
        # Show template with example variables
        example_code = resources.fill_template(template, template.example_vars)
        result["example_code"] = example_code
        result["example_vars"] = template.example_vars

    return result


# Tool: Get Syntax Help
@mcp.tool(description="Get syntax reference and help for Mermaid diagram types")
async def get_syntax_help(
    diagram_type: str,
    topic: str = None,
    generate_reference: bool = False
) -> Dict[str, Any]:
    """Handle syntax help requests"""

    if generate_reference:
        # Generate complete quick reference
        reference = resources.generate_quick_reference(diagram_type)
        return {"diagram_type": diagram_type, "reference": reference}

    # Get specific syntax help
    syntax_help = resources.get_syntax_help(diagram_type, topic)

    if not syntax_help:
        return {
            "error": f"No syntax help available for {diagram_type}" +
                    (f" topic '{topic}'" if topic else "")
        }

    result = {
        "diagram_type": diagram_type,
        "topic": topic,
        "syntax": syntax_help
    }

    # Add best practices
    practices = resources.get_best_practices(diagram_type)
    if practices:
        result["best_practices"] = practices[:5]  # Limit to 5 practices

    return result


# Tool: Analyze Diagram Code
@mcp.tool(description="Analyze Mermaid code and provide improvement suggestions")
async def analyze_diagram_code(
    code: str,
    focus_areas: List[str] = None
) -> Dict[str, Any]:
    """Analyze Mermaid code and provide suggestions"""
    focus_areas = focus_areas or ['syntax', 'best_practices']

    # Validate syntax first
    validation = MermaidValidator.validate(code)

    result = {
        "is_valid": validation.get('valid', False),
        "diagram_type": validation.get('diagram_type', 'unknown'),
        "line_count": validation['line_count'],
        "errors": validation.get('errors', []),
        "warnings": validation.get('warnings', []),
        "analysis": {}
    }

    # Detect diagram type for specific advice
    diagram_type = validation['diagram_type']

    if 'best_practices' in focus_areas:
        practices = resources.get_best_practices(diagram_type)
        if practices:
            result["analysis"]["best_practices"] = practices[:7]

    if 'readability' in focus_areas:
        readability_issues = []
        lines = code.split('\n')
        if len(lines) > 50:
            readability_issues.append("Consider breaking complex diagram into smaller sub-diagrams")
        if any(len(line) > 100 for line in lines):
            readability_issues.append("Some lines are very long - consider shorter labels")
        if code.count('-->') > 20:
            readability_issues.append("Many connections detected - ensure clear visual hierarchy")
        if not any(word in code.lower() for word in ['title', 'subgraph', 'section']):
            readability_issues.append("Consider adding title or grouping elements for clarity")
        result["analysis"]["readability"] = readability_issues

    if 'styling' in focus_areas:
        styling_recommendations = [
            "Use consistent naming conventions",
            "Consider adding colors for different types of elements"
        ]
        if diagram_type == 'flowchart':
            styling_recommendations.append("Use subgraphs to group related processes")
        elif diagram_type == 'sequence':
            styling_recommendations.append("Use notes to explain complex interactions")
        result["analysis"]["styling"] = styling_recommendations

    return result


# Tool: Suggest Diagram Improvements
@mcp.tool(description="Get suggestions for improving an existing diagram")
async def suggest_diagram_improvements(
    current_code: str,
    improvement_goals: List[str] = None,
    target_audience: str = "general"
) -> Dict[str, Any]:
    """Suggest improvements for existing diagrams"""
    improvement_goals = improvement_goals or ['clarity']

    # First analyze the current code
    validation = MermaidValidator.validate(current_code)
    diagram_type = validation['diagram_type']

    result = {
        "diagram_type": diagram_type,
        "target_audience": target_audience,
        "improvement_goals": improvement_goals,
        "suggestions": {}
    }

    # Get a better example of the same type
    examples = resources.get_examples_by_category(diagram_type)
    if examples:
        # Find a good example to reference
        for example in examples:
            if example.complexity in ['intermediate', 'advanced']:
                result["reference_example"] = {
                    "name": example.name,
                    "description": example.description,
                    "features": example.features
                }
                break

    if 'clarity' in improvement_goals:
        result["suggestions"]["clarity"] = [
            "Use descriptive, consistent naming",
            "Add a title to explain the diagram's purpose",
            "Group related elements using subgraphs or sections",
            "Ensure logical flow from start to end"
        ]

    if 'visual_appeal' in improvement_goals:
        result["suggestions"]["visual_appeal"] = [
            f"Consider using the '{diagram_type}' theme for better visual hierarchy",
            "Use consistent colors for similar elements",
            "Balance the layout to avoid crowding"
        ]
        if diagram_type == 'flowchart':
            result["suggestions"]["visual_appeal"].append("Try the hand-drawn look for informal presentations")

    if 'completeness' in improvement_goals:
        completeness_suggestions = []
        if diagram_type == 'flowchart':
            completeness_suggestions.extend([
                "Include error handling paths",
                "Show all possible decision outcomes",
                "Add start and end points"
            ])
        elif diagram_type == 'sequence':
            completeness_suggestions.extend([
                "Show return messages",
                "Include error scenarios",
                "Add activation boxes for clarity"
            ])
        elif diagram_type == 'class':
            completeness_suggestions.extend([
                "Include method parameters and return types",
                "Show all important relationships",
                "Add visibility modifiers"
            ])
        result["suggestions"]["completeness"] = completeness_suggestions

    # Audience-specific suggestions
    audience_suggestions = []
    if target_audience == 'technical':
        audience_suggestions.extend([
            "Include technical details and specific terms",
            "Show implementation details where relevant",
            "Use precise, unambiguous labels"
        ])
    elif target_audience == 'business':
        audience_suggestions.extend([
            "Focus on business processes and outcomes",
            "Use business terminology, avoid technical jargon",
            "Highlight decision points and approvals"
        ])
    elif target_audience == 'presentation':
        audience_suggestions.extend([
            "Simplify for high-level overview",
            "Use larger, readable fonts",
            "Minimize text, focus on visual flow",
            "Consider hand-drawn style for engagement"
        ])
    else:  # general
        audience_suggestions.extend([
            "Balance detail with simplicity",
            "Define any technical terms used",
            "Use intuitive symbols and shapes"
        ])
    result["suggestions"]["audience"] = audience_suggestions

    # Add a relevant template suggestion
    templates = resources.templates.get(diagram_type, [])
    if templates:
        result["template_suggestion"] = {
            "name": templates[0].name,
            "description": templates[0].description
        }

    return result


# Prompt: Flowchart Wizard
@mcp.prompt(description="Interactive wizard to create a flowchart diagram")
async def flowchart_wizard(process_name: str = "Process", complexity: str = "medium") -> str:
    """Generate flowchart wizard prompt"""
    return PromptGenerator.get_flowchart_prompt(process_name, complexity)


# Prompt: Sequence Diagram Wizard
@mcp.prompt(description="Guide for creating sequence diagrams")
async def sequence_diagram_wizard(scenario: str = "interaction", participants: str = "3") -> str:
    """Generate sequence diagram wizard prompt"""
    return PromptGenerator.get_sequence_prompt(scenario, participants)


# Prompt: Architecture Diagram
@mcp.prompt(description="Create system architecture diagrams")
async def architecture_diagram(system_name: str = "System", components: str = "") -> str:
    """Generate architecture diagram prompt"""
    component_list = components.split(',') if components else []
    return PromptGenerator.get_architecture_prompt(system_name, component_list)


# Prompt: Data Visualization
@mcp.prompt(description="Create charts and data visualizations")
async def data_visualization(data_type: str = "data", title: str = "Data Visualization") -> str:
    """Generate data visualization prompt"""
    return PromptGenerator.get_data_viz_prompt(data_type, title)


# Prompt: Project Timeline
@mcp.prompt(description="Create Gantt charts for project planning")
async def project_timeline(project_name: str = "Project", duration: str = "3 months") -> str:
    """Generate project timeline prompt"""
    return PromptGenerator.get_gantt_prompt(project_name, duration)


# Prompt: State Diagram Wizard
@mcp.prompt(description="Create state machine diagrams for system behavior")
async def state_diagram_wizard(system_name: str = "System", initial_state: str = None) -> str:
    """Generate state diagram wizard prompt"""
    return PromptGenerator.get_state_diagram_prompt(system_name)


# Prompt: ER Diagram Wizard
@mcp.prompt(description="Design entity-relationship diagrams for databases")
async def er_diagram_wizard(domain: str = "Database", complexity: str = "medium") -> str:
    """Generate ER diagram wizard prompt"""
    return PromptGenerator.get_er_diagram_prompt(domain)


# Prompt: Class Diagram Wizard
@mcp.prompt(description="Create class diagrams for object-oriented design")
async def class_diagram_wizard(system_name: str = "System", design_pattern: str = None) -> str:
    """Generate class diagram wizard prompt"""
    return PromptGenerator.get_class_diagram_prompt(system_name)


# Prompt: Mindmap Wizard
@mcp.prompt(description="Create mindmaps for brainstorming and concept organization")
async def mindmap_wizard(central_topic: str = "Topic", purpose: str = "brainstorming") -> str:
    """Generate mindmap wizard prompt"""
    return PromptGenerator.get_mindmap_prompt(central_topic)


# Prompt: User Journey Wizard
@mcp.prompt(description="Map customer or user journeys")
async def user_journey_wizard(journey_name: str = "User Journey", user_type: str = "customer") -> str:
    """Generate user journey wizard prompt"""
    return f"""Let's create a user journey map for "{journey_name}". Please provide:

1. **User Type**: Who is the user? ({user_type})

2. **Journey Stages**: What are the main phases?
   Example: "Awareness → Consideration → Purchase → Onboarding → Usage → Support"

3. **Touchpoints**: Where does the user interact with your system/service?
   Example: "Website, Mobile app, Email, Phone support, Physical store"

4. **User Actions**: What does the user do at each stage?
   Example: "Research options, Compare features, Read reviews, Make purchase"

5. **Emotions**: How does the user feel? (1-5 scale)
   Example: "Excited: 5, Confused: 2, Satisfied: 4"

6. **Pain Points**: What frustrates the user?
   Example: "Complex registration, Slow loading, Unclear pricing"

7. **Opportunities**: Where can you improve the experience?

Share these details for a comprehensive journey map."""


# Prompt: Troubleshooting Flowchart
@mcp.prompt(description="Create diagnostic and troubleshooting flowcharts")
async def troubleshooting_flowchart(problem_area: str = "System Issue", complexity: str = "basic") -> str:
    """Generate troubleshooting flowchart prompt"""
    return f"""Let's create a troubleshooting flowchart for "{problem_area}". Please provide:

1. **Initial Problem**: What issue are users experiencing?
   Example: "System won't start", "App crashes", "Login fails"

2. **Diagnostic Questions**: What should be checked first?
   Example: "Is the power on?", "Is network connected?", "Are credentials correct?"

3. **Common Causes**: List the most frequent root causes
   Example: "Network timeout", "Invalid credentials", "Server overload"

4. **Quick Fixes**: Simple solutions to try first
   Example: "Restart application", "Clear cache", "Check connection"

5. **Escalation Points**: When should it go to next level support?
   Example: "After 3 failed attempts", "If hardware issue suspected"

6. **Resolution Steps**: Detailed fix procedures
   Example: "Reset password → Verify email → Login again"

Provide these details for a comprehensive troubleshooting guide."""


# ==================== HELPER FUNCTIONS ====================

def _get_example_code() -> Dict[str, str]:
    """Get example Mermaid code for different diagram types"""
    return {
        "flowchart": """graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> E[Fix issues]
    E --> B
    C --> F[Deploy]""",

        "sequence": """sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database

    User->>Frontend: Submit form
    Frontend->>Backend: POST /api/data
    Backend->>Database: INSERT query
    Database-->>Backend: Success
    Backend-->>Frontend: 200 OK
    Frontend-->>User: Show success""",

        "gantt": """gantt
    title Project Schedule
    dateFormat YYYY-MM-DD
    section Planning
    Requirements :done, req, 2024-01-01, 7d
    Design :done, design, after req, 10d
    section Development
    Backend :active, backend, 2024-01-20, 20d
    Frontend :frontend, after backend, 15d
    section Testing
    Unit tests :test1, 2024-02-15, 10d
    Integration :test2, after test1, 7d""",

        "class": """classDiagram
    class User {
        -String id
        -String email
        +String name
        +login(password)
        +logout()
    }
    class Admin {
        +String role
        +manageUsers()
    }
    class Customer {
        -String customerId
        +placeOrder()
        +viewOrders()
    }
    User <|-- Admin
    User <|-- Customer""",

        "state": """stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : Start
    Processing --> Success : Complete
    Processing --> Error : Fail
    Success --> [*]
    Error --> Idle : Retry
    Error --> [*] : Give up""",

        "er": """erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER {
        string id PK
        string name
        string email UK
    }
    ORDER {
        string id PK
        date orderDate
        string customerId FK
    }
    LINE-ITEM {
        string id PK
        number quantity
        number price
        string orderId FK
        string productId FK
    }""",

        "pie": """pie title Browser Usage Stats
    "Chrome" : 65
    "Firefox" : 20
    "Safari" : 10
    "Edge" : 5""",

        "mindmap": """mindmap
  root((Sailor Site))
    Features
      AI Generation
        OpenAI
        Anthropic
      Live Preview
      Style Controls
        Themes
        Looks
          Classic
          HandDrawn
    Benefits
      No API needed
      Professional diagrams
      Easy to use
    Use Cases
      Documentation
      Architecture
      Planning"""
    }


# ==================== ENTRY POINTS ====================

def main_stdio():
    """Entry point for stdio transport (for setup.py console_scripts)"""
    logger.info("Starting Sailor MCP Server (stdio)...")
    logger.info("Get a picture of your Mermaid! 🧜‍♀️")
    mcp.run()  # Default transport is stdio


def main_http():
    """Entry point for HTTP/SSE transport (for setup.py console_scripts)"""
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    logger.info(f"Starting Sailor MCP Server (HTTP/SSE) on {args.host}:{args.port}...")
    logger.info("Get a picture of your Mermaid! 🧜‍♀️")
    mcp.run(transport="sse", host=args.host, port=args.port)


# ==================== MAIN ====================

if __name__ == "__main__":
    import sys

    # FastMCP handles both stdio and HTTP/SSE transports
    if "--http" in sys.argv:
        # Run with HTTP transport
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--http", action="store_true")
        parser.add_argument("--host", default="0.0.0.0")
        parser.add_argument("--port", type=int, default=8000)
        args = parser.parse_args()

        logger.info(f"Starting Sailor MCP Server (HTTP/SSE) on {args.host}:{args.port}...")
        logger.info("Get a picture of your Mermaid! 🧜‍♀️")
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        # Run with stdio transport (default)
        logger.info("Starting Sailor MCP Server (stdio)...")
        logger.info("Get a picture of your Mermaid! 🧜‍♀️")
        mcp.run()