"""MCP Server implementation for Sailor Site"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool, 
        TextContent, 
        ImageContent,
        Prompt,
        PromptArgument
    )
except ImportError:
    # Fallback for testing without MCP package
    logging.warning("MCP package not found. Using mock implementations.")
    from .mocks import Server, stdio_server, Tool, TextContent, ImageContent, Prompt, PromptArgument

from .validators import MermaidValidator
from .renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer
from .prompts import PromptGenerator
from .mermaid_resources import MermaidResources
from .logging_config import get_logger

# Get logger
logger = get_logger(__name__)


class SailorMCPServer:
    """MCP Server for Sailor Site - Mermaid diagram generation"""
    
    def __init__(self):
        self.server = Server("sailor-mermaid")
        self.renderer = None
        self.resources = MermaidResources()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        self.server.list_tools()(self._list_tools)
        self.server.list_prompts()(self._list_prompts)
        self.server.get_prompt()(self._get_prompt)
        self.server.call_tool()(self._call_tool)
    
    async def _list_tools(self) -> List[Tool]:
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
                            "description": "Type of diagram",
                            "enum": [
                                "flowchart", "sequence", "gantt", "class", 
                                "state", "er", "pie", "mindmap", "journey", "timeline"
                            ],
                            "default": "flowchart"
                        },
                        "requirements": {
                            "type": "array",
                            "description": "Specific requirements for the diagram",
                            "items": {"type": "string"}
                        },
                        "style": {
                            "type": "object",
                            "description": "Style preferences",
                            "properties": {
                                "theme": {"type": "string", "enum": ["default", "dark", "forest", "neutral"]},
                                "look": {"type": "string", "enum": ["classic", "handDrawn"]},
                                "direction": {"type": "string", "enum": ["TB", "BT", "LR", "RL"]},
                                "background": {"type": "string", "enum": ["transparent", "white"]}
                            }
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
                            "default": True
                        },
                        "style": {
                            "type": "object",
                            "description": "Style configuration",
                            "properties": {
                                "theme": {"type": "string", "enum": ["default", "dark", "forest", "neutral"]},
                                "look": {"type": "string", "enum": ["classic", "handDrawn"]},
                                "background": {"type": "string", "enum": ["transparent", "white"]}
                            }
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
                            "enum": [
                                "flowchart", "sequence", "gantt", "class", 
                                "state", "er", "pie", "mindmap", "journey", "timeline", "all"
                            ],
                            "default": "all"
                        },
                        "complexity": {
                            "type": "string",
                            "description": "Filter by complexity level",
                            "enum": ["basic", "intermediate", "advanced", "all"],
                            "default": "all"
                        },
                        "search_keywords": {
                            "type": "string",
                            "description": "Search for examples containing specific keywords"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_diagram_template",
                description="Get a customizable template for quick diagram generation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template to retrieve"
                        },
                        "diagram_type": {
                            "type": "string",
                            "description": "Type of diagram template",
                            "enum": ["flowchart", "sequence", "class", "er", "state"],
                            "default": "flowchart"
                        },
                        "fill_variables": {
                            "type": "object",
                            "description": "Variables to fill in the template",
                            "additionalProperties": {"type": "string"}
                        }
                    },
                    "required": ["template_name"]
                }
            ),
            Tool(
                name="get_syntax_help",
                description="Get syntax reference and help for Mermaid diagram types",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "diagram_type": {
                            "type": "string",
                            "description": "Diagram type to get syntax help for",
                            "enum": ["flowchart", "sequence", "class", "er", "state", "gantt"]
                        },
                        "topic": {
                            "type": "string",
                            "description": "Specific syntax topic (e.g., 'node_shapes', 'relationships', 'styling')"
                        },
                        "generate_reference": {
                            "type": "boolean",
                            "description": "Generate a complete quick reference guide",
                            "default": false
                        }
                    },
                    "required": ["diagram_type"]
                }
            ),
            Tool(
                name="analyze_diagram_code",
                description="Analyze Mermaid code and provide improvement suggestions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Mermaid diagram code to analyze"
                        },
                        "focus_areas": {
                            "type": "array",
                            "description": "Areas to focus analysis on",
                            "items": {
                                "type": "string",
                                "enum": ["syntax", "best_practices", "styling", "readability", "performance"]
                            },
                            "default": ["syntax", "best_practices"]
                        }
                    },
                    "required": ["code"]
                }
            ),
            Tool(
                name="suggest_diagram_improvements",
                description="Get suggestions for improving an existing diagram",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_code": {
                            "type": "string",
                            "description": "Current Mermaid diagram code"
                        },
                        "improvement_goals": {
                            "type": "array",
                            "description": "What aspects to improve",
                            "items": {
                                "type": "string",
                                "enum": ["clarity", "visual_appeal", "completeness", "accuracy", "performance"]
                            }
                        },
                        "target_audience": {
                            "type": "string",
                            "description": "Target audience for the diagram",
                            "enum": ["technical", "business", "general", "presentation"]
                        }
                    },
                    "required": ["current_code"]
                }
            )
        ]
    
    async def _list_prompts(self) -> List[Prompt]:
        """List available prompts"""
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
            ),
            Prompt(
                name="state_diagram_wizard",
                description="Create state machine diagrams for system behavior",
                arguments=[
                    PromptArgument(
                        name="system_name",
                        description="Name of the system or component",
                        required=True
                    ),
                    PromptArgument(
                        name="initial_state",
                        description="Starting state of the system",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="er_diagram_wizard",
                description="Design entity-relationship diagrams for databases",
                arguments=[
                    PromptArgument(
                        name="domain",
                        description="Domain or subject area (e.g., 'e-commerce', 'library', 'blog')",
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
                name="class_diagram_wizard",
                description="Create class diagrams for object-oriented design",
                arguments=[
                    PromptArgument(
                        name="system_name",
                        description="Name of the system or module",
                        required=True
                    ),
                    PromptArgument(
                        name="design_pattern",
                        description="Design pattern to incorporate (optional)",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="mindmap_wizard",
                description="Create mindmaps for brainstorming and concept organization",
                arguments=[
                    PromptArgument(
                        name="central_topic",
                        description="Central topic or theme",
                        required=True
                    ),
                    PromptArgument(
                        name="purpose",
                        description="Purpose (brainstorming, planning, learning, presentation)",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="user_journey_wizard",
                description="Map customer or user journeys",
                arguments=[
                    PromptArgument(
                        name="journey_name",
                        description="Name of the journey (e.g., 'Customer Onboarding', 'Purchase Process')",
                        required=True
                    ),
                    PromptArgument(
                        name="user_type",
                        description="Type of user (customer, employee, admin, etc.)",
                        required=False
                    )
                ]
            ),
            Prompt(
                name="troubleshooting_flowchart",
                description="Create diagnostic and troubleshooting flowcharts",
                arguments=[
                    PromptArgument(
                        name="problem_area",
                        description="Area or system being diagnosed",
                        required=True
                    ),
                    PromptArgument(
                        name="complexity",
                        description="Diagnostic complexity (basic, intermediate, advanced)",
                        required=False
                    )
                ]
            )
        ]
    
    async def _get_prompt(self, name: str, arguments: Optional[Dict[str, str]] = None) -> List[TextContent]:
        """Generate guided prompts based on user input"""
        arguments = arguments or {}
        
        prompt_map = {
            "flowchart_wizard": lambda: PromptGenerator.get_flowchart_prompt(
                arguments.get('process_name', 'Process'),
                arguments.get('complexity', 'medium')
            ),
            "sequence_diagram_wizard": lambda: PromptGenerator.get_sequence_prompt(
                arguments.get('scenario', 'interaction'),
                arguments.get('participants', '3')
            ),
            "architecture_diagram": lambda: PromptGenerator.get_architecture_prompt(
                arguments.get('system_name', 'System'),
                arguments.get('components', '').split(',') if arguments.get('components') else []
            ),
            "data_visualization": lambda: PromptGenerator.get_data_viz_prompt(
                arguments.get('data_type', 'data'),
                arguments.get('title', 'Data Visualization')
            ),
            "project_timeline": lambda: PromptGenerator.get_gantt_prompt(
                arguments.get('project_name', 'Project'),
                arguments.get('duration', '3 months')
            ),
            "state_diagram_wizard": lambda: PromptGenerator.get_state_diagram_prompt(
                arguments.get('system_name', 'System')
            ),
            "er_diagram_wizard": lambda: PromptGenerator.get_er_diagram_prompt(
                arguments.get('domain', 'Database')
            ),
            "class_diagram_wizard": lambda: PromptGenerator.get_class_diagram_prompt(
                arguments.get('system_name', 'System')
            ),
            "mindmap_wizard": lambda: PromptGenerator.get_mindmap_prompt(
                arguments.get('central_topic', 'Topic')
            ),
            "user_journey_wizard": lambda: f"""Let's create a user journey map for "{arguments.get('journey_name', 'User Journey')}". Please provide:

1. **User Type**: Who is the user? ({arguments.get('user_type', 'customer, employee, admin, etc.')})

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

Share these details for a comprehensive journey map.""",
            "troubleshooting_flowchart": lambda: f"""Let's create a troubleshooting flowchart for "{arguments.get('problem_area', 'System Issue')}". Please provide:

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
        }
        
        if name in prompt_map:
            prompt_text = prompt_map[name]()
            return [TextContent(type="text", text=prompt_text)]
        else:
            return [TextContent(
                type="text",
                text=f"Unknown prompt: {name}. Available: {', '.join(prompt_map.keys())}"
            )]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent]:
        """Handle tool calls"""
        logger.info(f"Tool called: {name} with {len(arguments)} arguments")
        
        try:
            if name == "request_mermaid_generation":
                return await self._handle_generation_request(arguments)
            elif name == "validate_and_render_mermaid":
                return await self._handle_validate_and_render(arguments)
            elif name == "get_mermaid_examples":
                return await self._handle_get_examples(arguments)
            elif name == "get_diagram_template":
                return await self._handle_get_template(arguments)
            elif name == "get_syntax_help":
                return await self._handle_get_syntax_help(arguments)
            elif name == "analyze_diagram_code":
                return await self._handle_analyze_code(arguments)
            elif name == "suggest_diagram_improvements":
                return await self._handle_suggest_improvements(arguments)
            else:
                logger.warning(f"Unknown tool requested: {name}")
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except KeyError as e:
            logger.error(f"Missing required argument in {name}: {e}")
            return [TextContent(type="text", text=f"Missing required argument: {str(e)}")]
        except ValueError as e:
            logger.error(f"Invalid argument value in {name}: {e}")
            return [TextContent(type="text", text=f"Invalid argument: {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in {name}: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Internal error: {str(e)}\n\nPlease check the logs for details.")]
    
    async def _handle_generation_request(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle request for Mermaid generation"""
        description = arguments['description']
        diagram_type = arguments.get('diagram_type', 'flowchart')
        requirements = arguments.get('requirements', [])
        style_prefs = arguments.get('style', {})
        
        # Build the request for the calling LLM
        prompt = f"""Please generate Mermaid diagram code for the following request:

Description: {description}
Diagram Type: {diagram_type}
"""
        
        if requirements:
            prompt += f"\nSpecific Requirements:\n" + "\n".join(f"- {req}" for req in requirements)
        
        if style_prefs:
            prompt += f"\n\nStyle Preferences:\n"
            for key, value in style_prefs.items():
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
        examples = self._get_example_code()
        if diagram_type in examples:
            prompt += f"\n\nExample {diagram_type}:\n{examples[diagram_type]}"
        
        return [TextContent(type="text", text=prompt)]
    
    async def _handle_validate_and_render(self, arguments: Dict[str, Any]) -> List[TextContent | ImageContent]:
        """Handle validation and rendering of Mermaid code"""
        code = arguments['code'].strip()
        fix_errors = arguments.get('fix_errors', True)
        style = arguments.get('style', {})
        format = arguments.get('format', 'png')
        
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
            
            return [TextContent(type="text", text=error_msg)]
        
        # Create config from style
        config = MermaidConfig(
            theme=style.get('theme', 'default'),
            look=style.get('look', 'classic'),
            background=style.get('background', 'transparent')
        )
        
        # Render the diagram
        try:
            if not self.renderer:
                self.renderer = await get_renderer()
            
            images = await self.renderer.render(code, config, format)
            
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
            
            if 'svg' in images and format in ['svg', 'both']:
                content.append(TextContent(
                    type="text",
                    text=f"SVG also generated (base64 encoded, {len(images['svg'])} chars)"
                ))
            
            return content
            
        except Exception as e:
            logger.error(f"Rendering error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"Rendering failed: {str(e)}\n\nCode was valid but could not be rendered."
            )]
    
    async def _handle_get_examples(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle request for examples using comprehensive resource library"""
        diagram_type = arguments.get('diagram_type', 'all')
        complexity = arguments.get('complexity', 'all')
        search_keywords = arguments.get('search_keywords', '')
        
        # Use comprehensive resource library
        if search_keywords:
            examples = self.resources.search_examples(search_keywords)
            if not examples:
                return [TextContent(type="text", text=f"No examples found for keywords: {search_keywords}")]
        elif complexity != 'all':
            examples = self.resources.get_examples_by_complexity(complexity)
            if diagram_type != 'all':
                examples = [ex for ex in examples if ex.category == diagram_type]
        elif diagram_type == 'all':
            examples = []
            for category in self.resources.examples.keys():
                examples.extend(self.resources.get_examples_by_category(category))
        else:
            examples = self.resources.get_examples_by_category(diagram_type)
        
        if not examples:
            return [TextContent(type="text", text=f"No examples found for {diagram_type} with complexity {complexity}")]
        
        # Build comprehensive response
        content = f"# Mermaid Examples"
        if diagram_type != 'all':
            content += f" - {diagram_type.title()}"
        if complexity != 'all':
            content += f" ({complexity} complexity)"
        if search_keywords:
            content += f" (matching: {search_keywords})"
        content += "\n\n"
        
        for example in examples[:5]:  # Limit to 5 examples to avoid overwhelming
            content += f"## {example.name} ({example.complexity})\n"
            content += f"**Category**: {example.category.title()}\n"
            content += f"**Description**: {example.description}\n"
            
            if example.features:
                content += f"**Features**: {', '.join(example.features)}\n"
            
            if example.use_cases:
                content += f"**Use Cases**: {', '.join(example.use_cases)}\n"
            
            content += f"\n```mermaid\n{example.code}\n```\n\n"
        
        if len(examples) > 5:
            content += f"*Showing 5 of {len(examples)} examples. Use search or filter by complexity for more specific results.*\n"
        
        return [TextContent(type="text", text=content)]
    
    def _get_example_code(self) -> Dict[str, str]:
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
    
    async def _handle_get_template(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle request for diagram templates"""
        template_name = arguments['template_name']
        diagram_type = arguments.get('diagram_type', 'flowchart')
        fill_variables = arguments.get('fill_variables', {})
        
        # Get template from resources
        template = self.resources.get_template(template_name, diagram_type)
        
        if not template:
            # List available templates
            available = []
            for category, templates in self.resources.templates.items():
                for tmpl in templates:
                    available.append(f"{category}: {tmpl.name}")
            
            return [TextContent(
                type="text",
                text=f"Template '{template_name}' not found.\n\nAvailable templates:\n" + "\n".join(f"- {t}" for t in available)
            )]
        
        content = f"# Template: {template.name}\n\n"
        content += f"**Description**: {template.description}\n\n"
        content += f"**Variables**: {', '.join(template.variables)}\n\n"
        
        if fill_variables:
            # Fill template with provided variables
            filled_code = self.resources.fill_template(template, fill_variables)
            content += f"## Generated Code\n\n```mermaid\n{filled_code}\n```\n\n"
        else:
            # Show template with example variables
            if template.example_vars:
                example_code = self.resources.fill_template(template, template.example_vars)
                content += f"## Example with Sample Data\n\n```mermaid\n{example_code}\n```\n\n"
            
            content += f"## Template Code\n\n```mermaid\n{template.template}\n```\n\n"
            content += f"**To use**: Call this tool again with 'fill_variables' containing values for: {', '.join(template.variables)}"
        
        return [TextContent(type="text", text=content)]
    
    async def _handle_get_syntax_help(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle syntax help requests"""
        diagram_type = arguments['diagram_type']
        topic = arguments.get('topic')
        generate_reference = arguments.get('generate_reference', False)
        
        if generate_reference:
            # Generate complete quick reference
            reference = self.resources.generate_quick_reference(diagram_type)
            return [TextContent(type="text", text=reference)]
        
        # Get specific syntax help
        syntax_help = self.resources.get_syntax_help(diagram_type, topic)
        
        if not syntax_help:
            return [TextContent(
                type="text",
                text=f"No syntax help available for {diagram_type}" + (f" topic '{topic}'" if topic else "")
            )]
        
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
        practices = self.resources.get_best_practices(diagram_type)
        if practices:
            content += "\n## Best Practices\n"
            for practice in practices[:5]:  # Limit to 5 practices
                content += f"- {practice}\n"
        
        return [TextContent(type="text", text=content)]
    
    async def _handle_analyze_code(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze Mermaid code and provide suggestions"""
        code = arguments['code']
        focus_areas = arguments.get('focus_areas', ['syntax', 'best_practices'])
        
        content = f"# Code Analysis\n\n"
        
        # Validate syntax first
        validator = MermaidValidator()
        validation = validator.validate_mermaid_code(code)
        
        content += f"## Syntax Analysis\n"
        if validation['is_valid']:
            content += "✅ **Syntax is valid**\n"
        else:
            content += "❌ **Syntax errors found:**\n"
            for error in validation['errors']:
                content += f"- {error}\n"
        
        if validation['warnings']:
            content += "\n⚠️ **Warnings:**\n"
            for warning in validation['warnings']:
                content += f"- {warning}\n"
        
        content += f"\n**Diagram Type**: {validation['diagram_type']}\n"
        content += f"**Lines of Code**: {validation['line_count']}\n"
        
        # Detect diagram type for specific advice
        diagram_type = validation['diagram_type']
        
        if 'best_practices' in focus_areas:
            practices = self.resources.get_best_practices(diagram_type)
            if practices:
                content += f"\n## Best Practices for {diagram_type.title()}\n"
                for practice in practices[:7]:
                    content += f"- {practice}\n"
        
        if 'readability' in focus_areas:
            content += f"\n## Readability Suggestions\n"
            lines = code.split('\n')
            if len(lines) > 50:
                content += "- Consider breaking complex diagram into smaller sub-diagrams\n"
            if any(len(line) > 100 for line in lines):
                content += "- Some lines are very long - consider shorter labels\n"
            if code.count('-->') > 20:
                content += "- Many connections detected - ensure clear visual hierarchy\n"
            if not any(word in code.lower() for word in ['title', 'subgraph', 'section']):
                content += "- Consider adding title or grouping elements for clarity\n"
        
        if 'styling' in focus_areas:
            content += f"\n## Styling Recommendations\n"
            content += "- Use consistent naming conventions\n"
            content += "- Consider adding colors for different types of elements\n"
            if diagram_type == 'flowchart':
                content += "- Use subgraphs to group related processes\n"
            elif diagram_type == 'sequence':
                content += "- Use notes to explain complex interactions\n"
        
        return [TextContent(type="text", text=content)]
    
    async def _handle_suggest_improvements(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Suggest improvements for existing diagrams"""
        current_code = arguments['current_code']
        improvement_goals = arguments.get('improvement_goals', ['clarity'])
        target_audience = arguments.get('target_audience', 'general')
        
        # First analyze the current code
        validator = MermaidValidator()
        validation = validator.validate_mermaid_code(current_code)
        diagram_type = validation['diagram_type']
        
        content = f"# Improvement Suggestions\n\n"
        content += f"**Current Diagram**: {diagram_type.title()}\n"
        content += f"**Target Audience**: {target_audience.title()}\n"
        content += f"**Improvement Goals**: {', '.join(improvement_goals)}\n\n"
        
        # Get a better example of the same type
        examples = self.resources.get_examples_by_category(diagram_type)
        if examples:
            # Find a good example to reference
            suitable_example = None
            for example in examples:
                if example.complexity in ['intermediate', 'advanced']:
                    suitable_example = example
                    break
            
            if suitable_example:
                content += f"## Reference Example: {suitable_example.name}\n"
                content += f"{suitable_example.description}\n\n"
                content += f"**Features demonstrated**: {', '.join(suitable_example.features)}\n\n"
        
        if 'clarity' in improvement_goals:
            content += "## Clarity Improvements\n"
            content += "- Use descriptive, consistent naming\n"
            content += "- Add a title to explain the diagram's purpose\n"
            content += "- Group related elements using subgraphs or sections\n"
            content += "- Ensure logical flow from start to end\n\n"
        
        if 'visual_appeal' in improvement_goals:
            content += "## Visual Appeal\n"
            content += f"- Consider using the '{diagram_type}' theme for better visual hierarchy\n"
            content += "- Use consistent colors for similar elements\n"
            content += "- Balance the layout to avoid crowding\n"
            if diagram_type == 'flowchart':
                content += "- Try the hand-drawn look for informal presentations\n"
            content += "\n"
        
        if 'completeness' in improvement_goals:
            content += "## Completeness\n"
            if diagram_type == 'flowchart':
                content += "- Include error handling paths\n"
                content += "- Show all possible decision outcomes\n"
                content += "- Add start and end points\n"
            elif diagram_type == 'sequence':
                content += "- Show return messages\n"
                content += "- Include error scenarios\n"
                content += "- Add activation boxes for clarity\n"
            elif diagram_type == 'class':
                content += "- Include method parameters and return types\n"
                content += "- Show all important relationships\n"
                content += "- Add visibility modifiers\n"
            content += "\n"
        
        # Audience-specific suggestions
        content += f"## {target_audience.title()} Audience Considerations\n"
        if target_audience == 'technical':
            content += "- Include technical details and specific terms\n"
            content += "- Show implementation details where relevant\n"
            content += "- Use precise, unambiguous labels\n"
        elif target_audience == 'business':
            content += "- Focus on business processes and outcomes\n"
            content += "- Use business terminology, avoid technical jargon\n"
            content += "- Highlight decision points and approvals\n"
        elif target_audience == 'presentation':
            content += "- Simplify for high-level overview\n"
            content += "- Use larger, readable fonts\n"
            content += "- Minimize text, focus on visual flow\n"
            content += "- Consider hand-drawn style for engagement\n"
        else:  # general
            content += "- Balance detail with simplicity\n"
            content += "- Define any technical terms used\n"
            content += "- Use intuitive symbols and shapes\n"
        
        # Add a relevant template suggestion
        templates = self.resources.templates.get(diagram_type, [])
        if templates:
            content += f"\n## Template Suggestion\n"
            content += f"Consider using the '{templates[0].name}' template as a starting point:\n"
            content += f"- {templates[0].description}\n"
        
        return [TextContent(type="text", text=content)]
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Sailor MCP Server...")
        logger.info("Get a picture of your Mermaid! 🧜‍♀️")
        
        try:
            async with stdio_server() as streams:
                await self.server.run(
                    streams[0],  # stdin
                    streams[1],  # stdout
                    self.server.create_initialization_options()
                )
        finally:
            if self.renderer:
                await cleanup_renderer()
            logger.info("Sailor MCP Server stopped")


async def main():
    """Main entry point"""
    server = SailorMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())