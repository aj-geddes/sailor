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
from .logging_config import get_logger

# Get logger
logger = get_logger(__name__)


class SailorMCPServer:
    """MCP Server for Sailor Site - Mermaid diagram generation"""
    
    def __init__(self):
        self.server = Server("sailor-mermaid")
        self.renderer = None
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
                                "state", "er", "pie", "mindmap", "all"
                            ],
                            "default": "all"
                        }
                    },
                    "required": []
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
            )
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
        """Handle request for examples"""
        diagram_type = arguments.get('diagram_type', 'all')
        examples = self._get_example_code()
        
        if diagram_type == "all":
            content = "# Mermaid Diagram Examples\n\n"
            for dtype, code in examples.items():
                content += f"## {dtype.title()}\n\n```mermaid\n{code}\n```\n\n"
        else:
            example = examples.get(diagram_type, examples["flowchart"])
            content = f"# {diagram_type.title()} Example\n\n```mermaid\n{example}\n```"
        
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