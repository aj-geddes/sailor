#!/usr/bin/env python3
"""
MCP Server for Sailor Site - Mermaid Diagram Generator
Allows LLMs to generate Mermaid diagrams and export them as images
"""

import json
import sys
import asyncio
import base64
import io
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent, 
    ImageContent,
    EmbeddedResource,
    SUPPORTED_IMAGE_TYPES,
    Prompt,
    PromptArgument
)

# For rendering Mermaid diagrams
from playwright.async_api import async_playwright
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MermaidConfig:
    """Configuration for Mermaid diagram rendering"""
    theme: str = "default"
    look: str = "classic"
    direction: str = "TB"
    background: str = "transparent"
    scale: int = 2

# Create the MCP server instance
mcp_server = Server("sailor-mermaid")

# Global browser instance
browser = None
playwright_instance = None

async def ensure_browser():
    """Ensure browser is initialized"""
    global browser, playwright_instance
    if not browser:
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
    return browser

async def validate_mermaid_code(code: str) -> Dict[str, Any]:
    """Validate Mermaid code syntax and structure"""
    errors = []
    warnings = []
    
    # Basic validation
    if not code or not code.strip():
        errors.append("Empty diagram code")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check for diagram type declaration
    diagram_types = {
        'graph': ['TD', 'TB', 'BT', 'LR', 'RL'],
        'flowchart': ['TD', 'TB', 'BT', 'LR', 'RL'],
        'sequenceDiagram': [],
        'classDiagram': [],
        'stateDiagram': [],
        'stateDiagram-v2': [],
        'erDiagram': [],
        'journey': [],
        'gantt': [],
        'pie': [],
        'quadrantChart': [],
        'requirementDiagram': [],
        'gitGraph': [],
        'mindmap': [],
        'timeline': [],
        'zenuml': [],
        'sankey-beta': [],
        'block-beta': [],
        'architecture-beta': []
    }
    
    lines = code.strip().split('\n')
    first_line = lines[0].strip()
    
    # Check if it starts with a valid diagram type
    valid_start = False
    for dtype, directions in diagram_types.items():
        if first_line.startswith(dtype):
            valid_start = True
            # Check direction for graph/flowchart
            if directions and dtype in ['graph', 'flowchart']:
                has_valid_direction = any(first_line.startswith(f"{dtype} {d}") for d in directions)
                if not has_valid_direction:
                    warnings.append(f"Missing or invalid direction for {dtype}. Use one of: {', '.join(directions)}")
            break
    
    if not valid_start:
        errors.append(f"Invalid diagram type. First line should start with one of: {', '.join(diagram_types.keys())}")
    
    # Check for common syntax errors
    open_brackets = code.count('{')
    close_brackets = code.count('}')
    if open_brackets != close_brackets:
        errors.append(f"Mismatched brackets: {open_brackets} opening, {close_brackets} closing")
    
    open_parens = code.count('(')
    close_parens = code.count(')')
    if open_parens != close_parens:
        errors.append(f"Mismatched parentheses: {open_parens} opening, {close_parens} closing")
    
    open_squares = code.count('[')
    close_squares = code.count(']')
    if open_squares != close_squares:
        errors.append(f"Mismatched square brackets: {open_squares} opening, {close_squares} closing")
    
    # Check for empty nodes in flowcharts
    if 'graph' in first_line or 'flowchart' in first_line:
        if '[]' in code or '{}' in code or '()' in code:
            warnings.append("Empty node labels detected")
    
    # Check for proper arrow syntax in flowcharts
    if 'graph' in first_line or 'flowchart' in first_line:
        if '-->' not in code and '---' not in code and '-.->':
            warnings.append("No connections found in flowchart")
    
    # Validate sequence diagrams
    if 'sequenceDiagram' in first_line:
        if 'participant' not in code:
            warnings.append("No participants defined in sequence diagram")
        if '->>' not in code and '-->>' not in code and '-)' not in code:
            warnings.append("No messages found in sequence diagram")
    
    # Check for unclosed strings
    quote_count = code.count('"')
    if quote_count % 2 != 0:
        errors.append("Unclosed string literal (odd number of quotes)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "line_count": len(lines),
        "diagram_type": first_line.split()[0] if lines else "unknown"
    }

async def render_diagram(mermaid_code: str, config: MermaidConfig, format: str = "png") -> Dict[str, str]:
    """Render Mermaid diagram to image"""
    browser = await ensure_browser()
    
    # Create HTML with Mermaid diagram
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {config.background if config.background == 'white' else 'transparent'};
            font-family: Arial, sans-serif;
        }}
        #diagram {{
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div id="diagram">
        <pre class="mermaid">
{mermaid_code}
        </pre>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{config.theme}',
            look: '{config.look}',
            flowchart: {{
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>
"""
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_html = f.name
    
    page = None
    try:
        # Create page and render
        page = await browser.new_page()
        await page.goto(f'file://{temp_html}')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(500)  # Give Mermaid time to render
        
        # Get the diagram element
        diagram = await page.query_selector('#diagram svg, #diagram .mermaid')
        if not diagram:
            raise Exception("Failed to render diagram")
        
        result = {}
        
        # Export as PNG
        if format in ["png", "both"]:
            png_buffer = await diagram.screenshot(
                type='png',
                scale=config.scale,
                omit_background=(config.background == "transparent")
            )
            result['png'] = base64.b64encode(png_buffer).decode('utf-8')
        
        # Export as SVG
        if format in ["svg", "both"]:
            svg_content = await page.evaluate('() => document.querySelector("#diagram svg")?.outerHTML || ""')
            if svg_content:
                result['svg'] = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        
        return result
        
    finally:
        # Clean up
        if page:
            await page.close()
        os.unlink(temp_html)

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="request_mermaid_generation",
            description="Request the calling LLM to generate Mermaid code based on requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the diagram to generate"
                    },
                    "diagram_type": {
                        "type": "string",
                        "description": "Type of diagram (flowchart, sequence, gantt, etc.)",
                        "enum": ["flowchart", "sequence", "gantt", "class", "state", "er", "pie", "mindmap", "journey", "timeline"],
                        "default": "flowchart"
                    },
                    "requirements": {
                        "type": "array",
                        "description": "Specific requirements for the diagram",
                        "items": {"type": "string"}
                    },
                    "examples": {
                        "type": "boolean",
                        "description": "Include examples for reference",
                        "default": true
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="validate_and_render_mermaid",
            description="Validate Mermaid code and render it as an image if valid",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Mermaid diagram code to validate and render"
                    },
                    "fix_errors": {
                        "type": "boolean",
                        "description": "Attempt to fix common errors automatically",
                        "default": true
                    },
                    "theme": {
                        "type": "string",
                        "description": "Mermaid theme",
                        "enum": ["default", "dark", "forest", "neutral"],
                        "default": "default"
                    },
                    "look": {
                        "type": "string",
                        "description": "Diagram style",
                        "enum": ["classic", "handDrawn"],
                        "default": "classic"
                    },
                    "background": {
                        "type": "string",
                        "description": "Image background",
                        "enum": ["transparent", "white"],
                        "default": "transparent"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format",
                        "enum": ["png", "svg", "both"],
                        "default": "png"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="render_mermaid_code",
            description="Render existing Mermaid code into an image",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Mermaid diagram code"
                    },
                    "theme": {
                        "type": "string",
                        "description": "Mermaid theme",
                        "enum": ["default", "dark", "forest", "neutral"],
                        "default": "default"
                    },
                    "look": {
                        "type": "string",
                        "description": "Diagram style",
                        "enum": ["classic", "handDrawn"],
                        "default": "classic"
                    },
                    "background": {
                        "type": "string",
                        "description": "Image background",
                        "enum": ["transparent", "white"],
                        "default": "transparent"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format",
                        "enum": ["png", "svg", "both"],
                        "default": "png"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="get_mermaid_examples",
            description="Get examples of different Mermaid diagram types",
            inputSchema={
                "type": "object",
                "properties": {
                    "diagram_type": {
                        "type": "string",
                        "description": "Type of diagram to get examples for",
                        "enum": ["flowchart", "sequence", "gantt", "class", "state", "er", "pie", "mindmap", "all"],
                        "default": "all"
                    }
                },
                "required": []
            }
        )
    ]

@mcp_server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts for guided diagram creation"""
    return [
        Prompt(
            name="flowchart_wizard",
            description="Interactive wizard to create a flowchart diagram",
            arguments=[
                PromptArgument(
                    name="process_name",
                    description="Name of the process or workflow",
                    required=True
                ),
                PromptArgument(
                    name="complexity",
                    description="Complexity level (simple, medium, complex)",
                    required=False
                )
            ]
        ),
        Prompt(
            name="sequence_diagram_wizard",
            description="Guide for creating sequence diagrams",
            arguments=[
                PromptArgument(
                    name="scenario",
                    description="The interaction scenario to diagram",
                    required=True
                ),
                PromptArgument(
                    name="participants",
                    description="Number of participants (2-10)",
                    required=False
                )
            ]
        ),
        Prompt(
            name="architecture_diagram",
            description="Create system architecture diagrams",
            arguments=[
                PromptArgument(
                    name="system_name",
                    description="Name of the system or application",
                    required=True
                ),
                PromptArgument(
                    name="components",
                    description="Key components (comma-separated)",
                    required=True
                )
            ]
        ),
        Prompt(
            name="data_visualization",
            description="Create charts and data visualizations",
            arguments=[
                PromptArgument(
                    name="data_type",
                    description="Type of data (percentages, timeline, comparison)",
                    required=True
                ),
                PromptArgument(
                    name="title",
                    description="Chart title",
                    required=True
                )
            ]
        ),
        Prompt(
            name="project_timeline",
            description="Create Gantt charts for project planning",
            arguments=[
                PromptArgument(
                    name="project_name",
                    description="Project name",
                    required=True
                ),
                PromptArgument(
                    name="duration",
                    description="Project duration (e.g., '3 months', '6 weeks')",
                    required=True
                )
            ]
        )
    ]

@mcp_server.get_prompt()
async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> List[TextContent]:
    """Generate guided prompts based on user input"""
    
    if name == "flowchart_wizard":
        process_name = arguments.get('process_name', 'Process')
        complexity = arguments.get('complexity', 'medium')
        
        questions = f"""Let's create a flowchart for "{process_name}". I'll guide you through the process:

1. **Starting Point**: What triggers or starts the {process_name}?
   Example: "User clicks submit button", "Customer places order", "System receives request"

2. **Main Steps**: List the main steps in order (3-7 steps for {complexity} complexity).
   Example: "Validate input → Process data → Save to database → Send notification"

3. **Decision Points**: Are there any decisions or conditions? (if/then scenarios)
   Example: "Is data valid? Yes → Continue, No → Show error"

4. **End Points**: How does the process complete? (Success/Failure/Multiple endings)
   Example: "Success: Show confirmation", "Failure: Display error message"

5. **Style Preferences**:
   - Theme: Default, Dark, Forest, or Neutral?
   - Look: Classic or Hand-drawn?
   - Direction: Top-to-bottom (TB), Left-to-right (LR)?

Please provide your answers, and I'll create a professional flowchart diagram."""
        
        return [TextContent(type="text", text=questions)]
    
    elif name == "sequence_diagram_wizard":
        scenario = arguments.get('scenario', 'interaction')
        participants = arguments.get('participants', '3')
        
        questions = f"""Let's create a sequence diagram for "{scenario}". Here's what I need:

1. **Participants**: Who or what are the {participants} main actors?
   Example: "User, Frontend, Backend, Database" or "Customer, Sales System, Payment Gateway"

2. **Initial Action**: What starts the {scenario}?
   Example: "User submits login form", "Customer initiates payment"

3. **Message Flow**: Describe the sequence of messages/actions between participants.
   Format: "A → B: Action/Message"
   Example: 
   - User → Frontend: Submit form
   - Frontend → Backend: Validate credentials
   - Backend → Database: Query user
   - Database → Backend: Return user data

4. **Response Types**: Are there any async operations or return messages?
   Example: "Backend -->> Frontend: Return token (dashed line for response)"

5. **Special Elements**: Any loops, alternatives, or parallel processes?
   Example: "Loop: Retry 3 times", "Alt: If authenticated / else show error"

6. **Visual Style**:
   - Theme preference?
   - Background: Transparent or white?

Share these details and I'll create your sequence diagram."""
        
        return [TextContent(type="text", text=questions)]
    
    elif name == "architecture_diagram":
        system_name = arguments.get('system_name', 'System')
        components = arguments.get('components', '').split(',')
        
        questions = f"""Let's design the architecture for "{system_name}". Please provide:

1. **Component Details** for each of: {', '.join(components) if components else 'your components'}
   - Type: (Service, Database, External API, User Interface, etc.)
   - Purpose: Brief description
   - Technology: (Optional - e.g., Python, PostgreSQL, React)

2. **Connections**: How do components communicate?
   Example: "Frontend → API Gateway → Microservices → Database"
   Include: Protocol (HTTP, gRPC, Message Queue, etc.)

3. **External Dependencies**: Any third-party services?
   Example: "Payment Gateway, Email Service, Cloud Storage"

4. **Architecture Pattern**: 
   - Monolithic, Microservices, Serverless, or Hybrid?
   - Any specific patterns? (MVC, Event-driven, etc.)

5. **Deployment Context**: 
   - Cloud provider? (AWS, Azure, GCP, On-premise)
   - Containerized? (Docker, Kubernetes)

6. **Diagram Preferences**:
   - Grouping: By layer, by domain, or by deployment?
   - Include icons/logos?
   - Style: Technical or presentation-friendly?

Provide these details for a comprehensive architecture diagram."""
        
        return [TextContent(type="text", text=questions)]
    
    elif name == "data_visualization":
        data_type = arguments.get('data_type', 'data')
        title = arguments.get('title', 'Data Visualization')
        
        if 'percentage' in data_type.lower() or 'pie' in data_type.lower():
            questions = f"""Creating a pie chart for "{title}". Please provide:

1. **Categories and Values**:
   Format: "Category: Value or Percentage"
   Example:
   - Desktop: 45%
   - Mobile: 35%
   - Tablet: 20%

2. **Color Preferences**: Any specific color scheme?

3. **Labels**: Show percentages, values, or both?

4. **Style**: Classic or hand-drawn look?"""
        
        elif 'timeline' in data_type.lower():
            questions = f"""Creating a timeline for "{title}". Please provide:

1. **Events with Dates**:
   Format: "YYYY-MM-DD: Event description"
   Example:
   - 2024-01: Project kickoff
   - 2024-03: Phase 1 complete
   - 2024-06: Launch

2. **Grouping**: Any categories or phases?

3. **Style**: Horizontal or vertical timeline?"""
        
        else:
            questions = f"""For your {data_type} visualization "{title}", please provide:

1. **Data Points**: List your data with labels and values

2. **Comparison Type**: What are you comparing?

3. **Visual Preference**: Bar chart, line graph, or other?"""
        
        return [TextContent(type="text", text=questions)]
    
    elif name == "project_timeline":
        project_name = arguments.get('project_name', 'Project')
        duration = arguments.get('duration', '3 months')
        
        questions = f"""Let's create a Gantt chart for "{project_name}" ({duration} duration):

1. **Project Phases**: List main phases or milestones
   Example: "Planning, Development, Testing, Deployment"

2. **Tasks per Phase**: Break down each phase into tasks
   Format: "Task name: Duration"
   Example:
   Planning:
   - Requirements gathering: 1 week
   - Design mockups: 2 weeks
   
3. **Dependencies**: Which tasks depend on others?
   Example: "Testing starts after Development"

4. **Resources**: Who's responsible? (Optional)
   Example: "Frontend: Team A, Backend: Team B"

5. **Critical Path**: Which tasks are critical for timeline?

6. **Visual Preferences**:
   - Show weekends?
   - Highlight critical tasks?
   - Color scheme?

Provide these details for your project timeline."""
        
        return [TextContent(type="text", text=questions)]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown prompt: {name}. Available prompts: flowchart_wizard, sequence_diagram_wizard, architecture_diagram, data_visualization, project_timeline"
        )]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent]:
    """Handle tool calls"""
    try:
        if name == "request_mermaid_generation":
            description = arguments['description']
            diagram_type = arguments.get('diagram_type', 'flowchart')
            requirements = arguments.get('requirements', [])
            include_examples = arguments.get('examples', True)
            
            # Build the request for the calling LLM
            prompt = f"""Please generate Mermaid diagram code for the following request:

Description: {description}
Diagram Type: {diagram_type}
"""
            
            if requirements:
                prompt += f"\nSpecific Requirements:\n" + "\n".join(f"- {req}" for req in requirements)
            
            # Add style guidance
            prompt += f"""

Style Guidelines:
- Use clear, descriptive labels for all nodes/elements
- Ensure proper syntax for {diagram_type} diagrams
- Include appropriate connections/relationships
- Consider using subgraphs or sections for complex diagrams
- For flowcharts/graphs, specify direction (TD, LR, etc.)
"""
            
            if include_examples:
                examples = {
                    "flowchart": """Example flowchart:
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[Alternative]
    C --> E[End]
    D --> E
```""",
                    "sequence": """Example sequence diagram:
```mermaid
sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System-->>User: Response
```""",
                    "gantt": """Example Gantt chart:
```mermaid
gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Task 1 :a1, 2024-01-01, 30d
    Task 2 :after a1, 20d
```""",
                    "class": """Example class diagram:
```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    Animal <|-- Dog
```""",
                    "state": """Example state diagram:
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Complete: Success
    Processing --> Error: Failure
    Error --> Idle: Reset
    Complete --> [*]
```"""
                }
                
                if diagram_type in examples:
                    prompt += f"\n\n{examples[diagram_type]}"
            
            prompt += "\n\nPlease respond with ONLY the Mermaid code, no explanations or markdown code blocks."
            
            return [TextContent(
                type="text",
                text=prompt
            )]
        
        elif name == "validate_and_render_mermaid":
            code = arguments['code'].strip()
            fix_errors = arguments.get('fix_errors', True)
            
            # Remove markdown code blocks if present
            if code.startswith('```'):
                lines = code.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines[-1] == '```':
                    lines = lines[:-1]
                code = '\n'.join(lines)
            
            # Validate the code
            validation = await validate_mermaid_code(code)
            
            if not validation['valid'] and fix_errors:
                # Attempt to fix common issues
                fixed_code = code
                
                # Fix missing direction
                if 'graph' in code and not any(d in code for d in ['TD', 'TB', 'BT', 'LR', 'RL']):
                    fixed_code = fixed_code.replace('graph', 'graph TD', 1)
                
                # Re-validate
                validation = await validate_mermaid_code(fixed_code)
                if validation['valid']:
                    code = fixed_code
            
            if not validation['valid']:
                error_msg = "## Mermaid Code Validation Failed\n\n"
                error_msg += "### Errors:\n" + "\n".join(f"- {e}" for e in validation['errors'])
                if validation['warnings']:
                    error_msg += "\n\n### Warnings:\n" + "\n".join(f"- {w}" for w in validation['warnings'])
                error_msg += f"\n\n### Code provided:\n```mermaid\n{code}\n```"
                error_msg += "\n\nPlease fix the errors and try again."
                
                return [TextContent(type="text", text=error_msg)]
            
            # Create config from arguments
            config = MermaidConfig(
                theme=arguments.get('theme', 'default'),
                look=arguments.get('look', 'classic'),
                background=arguments.get('background', 'transparent')
            )
            
            # Render the diagram
            format = arguments.get('format', 'png')
            images = await render_diagram(code, config, format)
            
            content = []
            
            # Add validation summary
            summary = f"✅ Mermaid code validated successfully!\n"
            summary += f"- Diagram type: {validation['diagram_type']}\n"
            summary += f"- Lines of code: {validation['line_count']}\n"
            summary += f"- Theme: {config.theme}\n"
            summary += f"- Style: {config.look}\n"
            summary += f"- Background: {config.background}\n"
            
            if validation['warnings']:
                summary += "\n⚠️ Warnings:\n" + "\n".join(f"- {w}" for w in validation['warnings'])
            
            content.append(TextContent(type="text", text=summary))
            
            # Add the rendered image
            if 'png' in images:
                content.append(ImageContent(
                    type="image",
                    data=images['png'],
                    mimeType="image/png"
                ))
            
            return content
            
        elif name == "generate_mermaid_diagram":
            description = arguments['description']
            diagram_type = arguments.get('diagram_type', 'flowchart')
            
            # Generate Mermaid code
            mermaid_code = await generate_mermaid_code(description, diagram_type)
            
            # Create config
            config = MermaidConfig(
                theme=arguments.get('theme', 'default'),
                look=arguments.get('look', 'classic'),
                direction=arguments.get('direction', 'TB'),
                background=arguments.get('background', 'transparent')
            )
            
            # Apply direction to flowchart code
            if diagram_type == 'flowchart' and config.direction != 'TB':
                mermaid_code = mermaid_code.replace('graph TD', f'graph {config.direction}')
            
            # Render diagram
            format = arguments.get('format', 'png')
            images = await render_diagram(mermaid_code, config, format)
            
            content = [
                TextContent(
                    type="text",
                    text=f"Generated {diagram_type} diagram:\n\n```mermaid\n{mermaid_code}\n```"
                )
            ]
            
            if 'png' in images:
                content.append(ImageContent(
                    type="image",
                    data=images['png'],
                    mimeType="image/png"
                ))
            
            return content
            
        elif name == "render_mermaid_code":
            mermaid_code = arguments['code']
            
            # Create config
            config = MermaidConfig(
                theme=arguments.get('theme', 'default'),
                look=arguments.get('look', 'classic'),
                background=arguments.get('background', 'transparent')
            )
            
            # Render diagram
            format = arguments.get('format', 'png')
            images = await render_diagram(mermaid_code, config, format)
            
            content = []
            
            if 'png' in images:
                content.append(ImageContent(
                    type="image",
                    data=images['png'],
                    mimeType="image/png"
                ))
            
            if 'svg' in images and format in ['svg', 'both']:
                content.append(TextContent(
                    type="text",
                    text=f"SVG also generated (base64 encoded, {len(images['svg'])} chars)"
                ))
            
            return content
            
        elif name == "get_mermaid_examples":
            diagram_type = arguments.get('diagram_type', 'all')
            
            examples = {
                "flowchart": """graph TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    B -->|No| D[End]
    C --> E[Process]
    E --> F[Complete]""",
                "sequence": """sequenceDiagram
    participant Alice
    participant Bob
    Alice->>John: Hello John, how are you?
    John-->>Alice: Great!
    Alice-)Bob: How about you?
    Bob--)Alice: Also good!""",
                "gantt": """gantt
    title A Gantt Diagram
    dateFormat YYYY-MM-DD
    section Section
    A task :a1, 2024-01-01, 30d
    Another task :after a1, 20d
    section Another
    Task in sec :2024-01-12, 12d""",
                "class": """classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()
    Duck : +String beakColor
    Duck : +swim()
    Fish : -int sizeInFeet
    Fish : -canEat()""",
                "state": """stateDiagram-v2
    [*] --> Still
    Still --> [*]
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]""",
                "er": """erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER {
        string name
        string custNumber
        string sector
    }
    ORDER {
        int orderNumber
        string deliveryAddress
    }""",
                "pie": """pie title Pets adopted by volunteers
    "Dogs" : 386
    "Cats" : 85
    "Rats" : 15
    "Ferrets" : 25""",
                "mindmap": """mindmap
  root((Mermaid))
    Diagrams
      Flowchart
      Sequence
      Class
    Features
      Themes
      Looks
        Classic
        HandDrawn
    Export
      PNG
      SVG"""
            }
            
            if diagram_type == "all":
                content = "# Mermaid Diagram Examples\n\n"
                for dtype, code in examples.items():
                    content += f"## {dtype.title()}\n\n```mermaid\n{code}\n```\n\n"
            else:
                example = examples.get(diagram_type, examples["flowchart"])
                content = f"# {diagram_type.title()} Example\n\n```mermaid\n{example}\n```"
            
            return [TextContent(type="text", text=content)]
        
        else:
            return [TextContent(
                type="text", 
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def cleanup():
    """Cleanup resources"""
    global browser, playwright_instance
    if browser:
        await browser.close()
    if playwright_instance:
        await playwright_instance.stop()

async def main():
    """Run the MCP server"""
    logger.info("Starting Sailor Mermaid MCP Server...")
    
    try:
        # Run the server using stdio transport
        async with stdio_server() as streams:
            await mcp_server.run(
                streams[0],  # stdin
                streams[1],  # stdout
                mcp_server.create_initialization_options()
            )
    finally:
        await cleanup()

if __name__ == "__main__":
    asyncio.run(main())