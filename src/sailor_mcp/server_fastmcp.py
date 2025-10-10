"""FastMCP-based MCP Server implementation for Sailor Site"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

from fastmcp import FastMCP, Context
from fastmcp.resources import TextResource, FileResource

from .validators import MermaidValidator
from .renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer
from .prompts import PromptGenerator
from .mermaid_resources import MermaidResources
from .logging_config import get_logger

# Get logger
logger = get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="sailor-mermaid",
    instructions="MCP server for generating and rendering Mermaid diagrams with AI assistance",
    version="2.0.0"
)

# Initialize resources singleton
resources = MermaidResources()

# Global renderer instance
_renderer: Optional[MermaidRenderer] = None


# ============================================================================
# TOOLS - All 7 tools migrated to FastMCP pattern
# ============================================================================

@mcp.tool
async def request_mermaid_generation(
    description: str,
    diagram_type: str = "flowchart",
    requirements: Optional[List[str]] = None,
    style: Optional[Dict[str, Any]] = None,
    ctx: Optional[Context] = None
) -> str:
    """Request the calling LLM to generate Mermaid code based on requirements.

    Args:
        description: Detailed description of the diagram to generate
        diagram_type: Type of diagram (flowchart, sequence, gantt, class, state, er, pie, mindmap, journey, timeline)
        requirements: Specific requirements for the diagram
        style: Style preferences (theme, look, direction, background)
        ctx: MCP context for logging

    Returns:
        Formatted prompt for LLM to generate Mermaid code
    """
    if ctx:
        await ctx.info(f"Generating {diagram_type} diagram prompt")

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


@mcp.tool
async def validate_and_render_mermaid(
    code: str,
    fix_errors: bool = True,
    style: Optional[Dict[str, Any]] = None,
    format: str = "png",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Validate Mermaid code and render it as an image if valid.

    Args:
        code: Mermaid diagram code to validate and render
        fix_errors: Attempt to fix common errors automatically
        style: Style configuration (theme, look, background)
        format: Output format (png, svg, both)
        ctx: MCP context for logging

    Returns:
        Dictionary with validation results and rendered images
    """
    global _renderer

    if ctx:
        await ctx.info("Validating and rendering Mermaid diagram")

    # Remove markdown code blocks if present
    code = code.strip()
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
        code = MermaidValidator.fix_common_errors(code)
        validation = MermaidValidator.validate(code)

    if not validation['valid']:
        return {
            "success": False,
            "error": "Validation failed",
            "errors": validation['errors'],
            "warnings": validation['warnings'],
            "code": code
        }

    # Create config from style
    config = MermaidConfig(
        theme=style.get('theme', 'default') if style else 'default',
        look=style.get('look', 'classic') if style else 'classic',
        background=style.get('background', 'transparent') if style else 'transparent'
    )

    # Render the diagram
    try:
        if not _renderer:
            _renderer = await get_renderer()

        images = await _renderer.render(code, config, format)

        result = {
            "success": True,
            "validation": {
                "diagram_type": validation['diagram_type'],
                "line_count": validation['line_count'],
                "warnings": validation['warnings']
            },
            "config": {
                "theme": config.theme,
                "look": config.look,
                "background": config.background
            },
            "images": images
        }

        if ctx:
            await ctx.info(f"Successfully rendered {validation['diagram_type']} diagram")

        return result

    except Exception as e:
        logger.error(f"Rendering error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Rendering failed: {str(e)}",
            "validation": validation,
            "code": code
        }


@mcp.tool
async def get_mermaid_examples(
    diagram_type: str = "all",
    complexity: str = "all",
    search_keywords: Optional[str] = None,
    ctx: Optional[Context] = None
) -> List[Dict[str, Any]]:
    """Get examples of different Mermaid diagram types.

    Args:
        diagram_type: Type of diagram to get examples for (flowchart, sequence, gantt, etc., or 'all')
        complexity: Filter by complexity level (basic, intermediate, advanced, all)
        search_keywords: Search for examples containing specific keywords
        ctx: MCP context for logging

    Returns:
        List of example diagrams with metadata
    """
    if ctx:
        await ctx.info(f"Fetching {complexity} {diagram_type} examples")

    # Use comprehensive resource library
    if search_keywords:
        examples = resources.search_examples(search_keywords)
        if not examples:
            return []
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

    # Convert to dictionary format and limit to 5
    return [
        {
            "name": ex.name,
            "category": ex.category,
            "complexity": ex.complexity,
            "description": ex.description,
            "code": ex.code,
            "features": ex.features,
            "use_cases": ex.use_cases
        }
        for ex in examples[:5]
    ]


@mcp.tool
async def get_diagram_template(
    template_name: str,
    diagram_type: str = "flowchart",
    fill_variables: Optional[Dict[str, str]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Get a customizable template for quick diagram generation.

    Args:
        template_name: Name of the template to retrieve
        diagram_type: Type of diagram template (flowchart, sequence, class, er, state)
        fill_variables: Variables to fill in the template
        ctx: MCP context for logging

    Returns:
        Template information and optionally filled code
    """
    if ctx:
        await ctx.info(f"Fetching template: {template_name}")

    template = resources.get_template(template_name, diagram_type)

    if not template:
        # List available templates
        available = []
        for category, templates in resources.templates.items():
            for tmpl in templates:
                available.append(f"{category}: {tmpl.name}")

        return {
            "success": False,
            "error": f"Template '{template_name}' not found",
            "available_templates": available
        }

    result = {
        "success": True,
        "template": {
            "name": template.name,
            "description": template.description,
            "variables": template.variables,
            "template_code": template.template
        }
    }

    if fill_variables:
        filled_code = resources.fill_template(template, fill_variables)
        result["filled_code"] = filled_code
    elif template.example_vars:
        example_code = resources.fill_template(template, template.example_vars)
        result["example_code"] = example_code
        result["example_vars"] = template.example_vars

    return result


@mcp.tool
async def get_syntax_help(
    diagram_type: str,
    topic: Optional[str] = None,
    generate_reference: bool = False,
    ctx: Optional[Context] = None
) -> str:
    """Get syntax reference and help for Mermaid diagram types.

    Args:
        diagram_type: Diagram type to get syntax help for (flowchart, sequence, class, er, state, gantt)
        topic: Specific syntax topic (e.g., 'node_shapes', 'relationships', 'styling')
        generate_reference: Generate a complete quick reference guide
        ctx: MCP context for logging

    Returns:
        Formatted syntax help text
    """
    if ctx:
        await ctx.info(f"Getting syntax help for {diagram_type}")

    if generate_reference:
        return resources.generate_quick_reference(diagram_type)

    # Get specific syntax help
    syntax_help = resources.get_syntax_help(diagram_type, topic)

    if not syntax_help:
        return f"No syntax help available for {diagram_type}" + (f" topic '{topic}'" if topic else "")

    content = f"# {diagram_type.title()} Syntax Help"
    if topic:
        content += f" - {topic.replace('_', ' ').title()}"
    content += "\n\n"

    if isinstance(syntax_help, dict):
        for key, value in syntax_help.items():
            content += f"## {key.replace('_', ' ').title()}\n"
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    content += f"- `{subkey}`: {subvalue}\n"
            else:
                content += f"{value}\n"
            content += "\n"
    else:
        content += str(syntax_help)

    # Add best practices
    practices = resources.get_best_practices(diagram_type)
    if practices:
        content += "\n## Best Practices\n"
        for practice in practices[:5]:
            content += f"- {practice}\n"

    return content


@mcp.tool
async def analyze_diagram_code(
    code: str,
    focus_areas: Optional[List[str]] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Analyze Mermaid code and provide improvement suggestions.

    Args:
        code: Mermaid diagram code to analyze
        focus_areas: Areas to focus analysis on (syntax, best_practices, styling, readability, performance)
        ctx: MCP context for logging

    Returns:
        Analysis results with suggestions
    """
    if not focus_areas:
        focus_areas = ['syntax', 'best_practices']

    if ctx:
        await ctx.info(f"Analyzing diagram code, focus: {focus_areas}")

    # Validate syntax first
    validator = MermaidValidator()
    validation = validator.validate_mermaid_code(code)

    analysis = {
        "valid": validation['is_valid'],
        "diagram_type": validation['diagram_type'],
        "line_count": validation['line_count'],
        "errors": validation['errors'],
        "warnings": validation['warnings'],
        "analysis": {}
    }

    # Detect diagram type for specific advice
    diagram_type = validation['diagram_type']

    if 'best_practices' in focus_areas:
        practices = resources.get_best_practices(diagram_type)
        analysis['analysis']['best_practices'] = practices[:7] if practices else []

    if 'readability' in focus_areas:
        readability = []
        lines = code.split('\n')
        if len(lines) > 50:
            readability.append("Consider breaking complex diagram into smaller sub-diagrams")
        if any(len(line) > 100 for line in lines):
            readability.append("Some lines are very long - consider shorter labels")
        if code.count('-->') > 20:
            readability.append("Many connections detected - ensure clear visual hierarchy")
        if not any(word in code.lower() for word in ['title', 'subgraph', 'section']):
            readability.append("Consider adding title or grouping elements for clarity")
        analysis['analysis']['readability'] = readability

    if 'styling' in focus_areas:
        styling = [
            "Use consistent naming conventions",
            "Consider adding colors for different types of elements"
        ]
        if diagram_type == 'flowchart':
            styling.append("Use subgraphs to group related processes")
        elif diagram_type == 'sequence':
            styling.append("Use notes to explain complex interactions")
        analysis['analysis']['styling'] = styling

    return analysis


@mcp.tool
async def suggest_diagram_improvements(
    current_code: str,
    improvement_goals: Optional[List[str]] = None,
    target_audience: str = "general",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Get suggestions for improving an existing diagram.

    Args:
        current_code: Current Mermaid diagram code
        improvement_goals: What aspects to improve (clarity, visual_appeal, completeness, accuracy, performance)
        target_audience: Target audience for the diagram (technical, business, general, presentation)
        ctx: MCP context for logging

    Returns:
        Improvement suggestions organized by goal
    """
    if not improvement_goals:
        improvement_goals = ['clarity']

    if ctx:
        await ctx.info(f"Suggesting improvements for {target_audience} audience")

    # First analyze the current code
    validator = MermaidValidator()
    validation = validator.validate_mermaid_code(current_code)
    diagram_type = validation['diagram_type']

    suggestions = {
        "current_diagram_type": diagram_type,
        "target_audience": target_audience,
        "improvement_goals": improvement_goals,
        "suggestions": {}
    }

    # Get a reference example
    examples = resources.get_examples_by_category(diagram_type)
    if examples:
        suitable_example = next((ex for ex in examples if ex.complexity in ['intermediate', 'advanced']), None)
        if suitable_example:
            suggestions["reference_example"] = {
                "name": suitable_example.name,
                "description": suitable_example.description,
                "features": suitable_example.features
            }

    # Generate suggestions for each goal
    for goal in improvement_goals:
        if goal == 'clarity':
            suggestions['suggestions']['clarity'] = [
                "Use descriptive, consistent naming",
                "Add a title to explain the diagram's purpose",
                "Group related elements using subgraphs or sections",
                "Ensure logical flow from start to end"
            ]
        elif goal == 'visual_appeal':
            suggestions['suggestions']['visual_appeal'] = [
                f"Consider using the '{diagram_type}' theme for better visual hierarchy",
                "Use consistent colors for similar elements",
                "Balance the layout to avoid crowding",
                "Try the hand-drawn look for informal presentations" if diagram_type == 'flowchart' else "Use modern themes"
            ]
        elif goal == 'completeness':
            completeness = []
            if diagram_type == 'flowchart':
                completeness = [
                    "Include error handling paths",
                    "Show all possible decision outcomes",
                    "Add start and end points"
                ]
            elif diagram_type == 'sequence':
                completeness = [
                    "Show return messages",
                    "Include error scenarios",
                    "Add activation boxes for clarity"
                ]
            elif diagram_type == 'class':
                completeness = [
                    "Include method parameters and return types",
                    "Show all important relationships",
                    "Add visibility modifiers"
                ]
            suggestions['suggestions']['completeness'] = completeness

    # Audience-specific suggestions
    audience_tips = []
    if target_audience == 'technical':
        audience_tips = [
            "Include technical details and specific terms",
            "Show implementation details where relevant",
            "Use precise, unambiguous labels"
        ]
    elif target_audience == 'business':
        audience_tips = [
            "Focus on business processes and outcomes",
            "Use business terminology, avoid technical jargon",
            "Highlight decision points and approvals"
        ]
    elif target_audience == 'presentation':
        audience_tips = [
            "Simplify for high-level overview",
            "Use larger, readable fonts",
            "Minimize text, focus on visual flow",
            "Consider hand-drawn style for engagement"
        ]
    else:  # general
        audience_tips = [
            "Balance detail with simplicity",
            "Define any technical terms used",
            "Use intuitive symbols and shapes"
        ]

    suggestions['audience_considerations'] = audience_tips

    # Add template suggestion
    templates = resources.templates.get(diagram_type, [])
    if templates:
        suggestions['template_suggestion'] = {
            "name": templates[0].name,
            "description": templates[0].description
        }

    return suggestions


# ============================================================================
# PROMPTS - All 11 prompts migrated to FastMCP pattern
# ============================================================================

@mcp.prompt("flowchart_wizard")
async def flowchart_wizard(process_name: str, complexity: str = "medium") -> List[Dict[str, str]]:
    """Interactive wizard to create a flowchart diagram"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_flowchart_prompt(process_name, complexity)
        }
    ]


@mcp.prompt("sequence_diagram_wizard")
async def sequence_diagram_wizard(scenario: str, participants: str = "3") -> List[Dict[str, str]]:
    """Guide for creating sequence diagrams"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_sequence_prompt(scenario, participants)
        }
    ]


@mcp.prompt("architecture_diagram")
async def architecture_diagram(system_name: str, components: str) -> List[Dict[str, str]]:
    """Create system architecture diagrams"""
    component_list = components.split(',') if components else []
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_architecture_prompt(system_name, component_list)
        }
    ]


@mcp.prompt("data_visualization")
async def data_visualization(data_type: str, title: str) -> List[Dict[str, str]]:
    """Create charts and data visualizations"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_data_viz_prompt(data_type, title)
        }
    ]


@mcp.prompt("project_timeline")
async def project_timeline(project_name: str, duration: str) -> List[Dict[str, str]]:
    """Create Gantt charts for project planning"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_gantt_prompt(project_name, duration)
        }
    ]


@mcp.prompt("state_diagram_wizard")
async def state_diagram_wizard(system_name: str, initial_state: Optional[str] = None) -> List[Dict[str, str]]:
    """Create state machine diagrams for system behavior"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_state_diagram_prompt(system_name, initial_state)
        }
    ]


@mcp.prompt("er_diagram_wizard")
async def er_diagram_wizard(domain: str, complexity: str = "medium") -> List[Dict[str, str]]:
    """Design entity-relationship diagrams for databases"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_er_diagram_prompt(domain, complexity)
        }
    ]


@mcp.prompt("class_diagram_wizard")
async def class_diagram_wizard(system_name: str, design_pattern: Optional[str] = None) -> List[Dict[str, str]]:
    """Create class diagrams for object-oriented design"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_class_diagram_prompt(system_name, design_pattern)
        }
    ]


@mcp.prompt("mindmap_wizard")
async def mindmap_wizard(central_topic: str, purpose: Optional[str] = None) -> List[Dict[str, str]]:
    """Create mindmaps for brainstorming and concept organization"""
    return [
        {
            "role": "user",
            "content": PromptGenerator.get_mindmap_prompt(central_topic, purpose)
        }
    ]


@mcp.prompt("user_journey_wizard")
async def user_journey_wizard(journey_name: str, user_type: Optional[str] = None) -> List[Dict[str, str]]:
    """Map customer or user journeys"""
    prompt = f"""Let's create a user journey map for "{journey_name}". Please provide:

1. **User Type**: Who is the user? ({user_type or 'customer, employee, admin, etc.'})

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

    return [{"role": "user", "content": prompt}]


@mcp.prompt("troubleshooting_flowchart")
async def troubleshooting_flowchart(problem_area: str, complexity: str = "intermediate") -> List[Dict[str, str]]:
    """Create diagnostic and troubleshooting flowcharts"""
    prompt = f"""Let's create a troubleshooting flowchart for "{problem_area}". Please provide:

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

    return [{"role": "user", "content": prompt}]


# ============================================================================
# RESOURCES - Static and dynamic resources
# ============================================================================

@mcp.resource("resource://examples/{category}")
async def get_examples_resource(category: str) -> Dict[str, Any]:
    """Get examples for a specific diagram category"""
    examples = resources.get_examples_by_category(category)
    return {
        "category": category,
        "count": len(examples),
        "examples": [
            {
                "name": ex.name,
                "description": ex.description,
                "complexity": ex.complexity,
                "code": ex.code
            }
            for ex in examples
        ]
    }


@mcp.resource("resource://templates/{diagram_type}")
async def get_templates_resource(diagram_type: str) -> Dict[str, Any]:
    """Get all templates for a diagram type"""
    templates = resources.templates.get(diagram_type, [])
    return {
        "diagram_type": diagram_type,
        "count": len(templates),
        "templates": [
            {
                "name": t.name,
                "description": t.description,
                "variables": t.variables
            }
            for t in templates
        ]
    }


@mcp.resource("resource://syntax/{diagram_type}")
async def get_syntax_resource(diagram_type: str) -> str:
    """Get syntax help for a specific diagram type"""
    return resources.generate_quick_reference(diagram_type)


# Add static resources
best_practices = TextResource(
    uri="resource://best-practices/all",
    name="Complete Best Practices Guide",
    text=json.dumps({
        diagram_type: resources.get_best_practices(diagram_type)
        for diagram_type in ['flowchart', 'sequence', 'class', 'er', 'state', 'gantt']
    }, indent=2),
    mime_type="application/json"
)
mcp.add_resource(best_practices)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

# Note: FastMCP 2.11.3 doesn't have startup/shutdown decorators
# Initialization happens at module import
logger.info("Sailor MCP Server (FastMCP version) loaded")
logger.info("Get a picture of your Mermaid! 🧜‍♀️")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the server (handles stdio automatically)
    mcp.run()