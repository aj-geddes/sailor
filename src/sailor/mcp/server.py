"""
Sailor MCP Server - Clean, production-ready implementation.
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

from ..core import MermaidValidator, MermaidRenderer, DiagramGenerator
from ..core.validator import ValidationResult, DiagramType
from ..core.renderer import RenderConfig, RenderResult, OutputFormat, Theme, RenderStyle
from .tools import create_diagram_tool, validate_mermaid_tool, render_diagram_tool
from .resources import DiagramResource, TemplateResource


class DiagramMetadata(BaseModel):
    """Metadata for a diagram."""
    id: str
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    diagram_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: int = 1


class SailorMCPServer:
    """
    Production-ready MCP server for Mermaid diagram creation.
    
    Features:
    - Natural language diagram generation
    - Syntax validation with detailed errors
    - Multiple output formats
    - Template library
    - Diagram storage and retrieval
    """
    
    def __init__(self, name: str = "Sailor", version: str = "2.0.0"):
        """Initialize the MCP server."""
        self.mcp = FastMCP(name, version=version)
        self.validator = MermaidValidator()
        self.renderer: Optional[MermaidRenderer] = None
        self.generator = DiagramGenerator()
        
        # Storage (in-memory for now, could be Redis/DB)
        self.diagrams: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Any] = {}
        
        # Register handlers
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    async def initialize(self):
        """Initialize async components."""
        self.renderer = await MermaidRenderer.get_instance()
        await self.generator.initialize()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        async def create_diagram(
            description: str = Field(..., description="Natural language description of the diagram"),
            diagram_type: Optional[str] = Field(None, description="Preferred diagram type (flowchart, sequence, etc.)"),
            style: Optional[Dict[str, str]] = Field(None, description="Style preferences"),
            enhance: bool = Field(True, description="Use AI to enhance the diagram"),
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Create a Mermaid diagram from natural language description.
            
            This tool uses AI to generate appropriate Mermaid code based on your description.
            It automatically selects the best diagram type and creates well-structured diagrams.
            """
            try:
                # Generate diagram code
                result = await self.generator.generate_from_description(
                    description=description,
                    diagram_type=diagram_type,
                    enhance=enhance
                )
                
                # Validate the generated code
                validation = self.validator.validate(result.code)
                
                if not validation.is_valid:
                    # Try to fix common errors
                    fixed_code = self.validator.fix_common_errors(result.code)
                    validation = self.validator.validate(fixed_code)
                    if validation.is_valid:
                        result.code = fixed_code
                
                # Create metadata
                diagram_id = str(uuid.uuid4())
                metadata = DiagramMetadata(
                    id=diagram_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    title=description[:50] + "..." if len(description) > 50 else description,
                    description=description,
                    diagram_type=validation.diagram_type.value if validation.diagram_type else None
                )
                
                # Store diagram
                self.diagrams[diagram_id] = {
                    "code": result.code,
                    "metadata": metadata.dict(),
                    "validation": {
                        "is_valid": validation.is_valid,
                        "errors": [e.__dict__ for e in validation.errors],
                        "warnings": [w.__dict__ for w in validation.warnings]
                    }
                }
                
                return {
                    "success": True,
                    "diagram_id": diagram_id,
                    "code": result.code,
                    "diagram_type": validation.diagram_type.value if validation.diagram_type else None,
                    "validation": {
                        "is_valid": validation.is_valid,
                        "errors": [e.message for e in validation.errors],
                        "warnings": [w.message for w in validation.warnings]
                    },
                    "suggestions": result.suggestions,
                    "share_url": f"/diagram/{diagram_id}"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def validate_mermaid(
            code: str = Field(..., description="Mermaid diagram code to validate"),
            auto_fix: bool = Field(False, description="Attempt to fix common errors"),
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Validate Mermaid diagram syntax with detailed error reporting.
            
            Returns comprehensive validation results including:
            - Syntax errors with line numbers
            - Warnings for best practices
            - Diagram metadata (type, complexity, etc.)
            - Suggestions for improvements
            """
            # Sanitize input
            code = self.validator.sanitize(code)
            
            # Validate
            validation = self.validator.validate(code)
            
            result = {
                "is_valid": validation.is_valid,
                "diagram_type": validation.diagram_type.value if validation.diagram_type else None,
                "errors": [
                    {
                        "line": e.line,
                        "column": e.column,
                        "message": e.message,
                        "severity": e.severity,
                        "suggestion": e.suggestion
                    }
                    for e in validation.errors
                ],
                "warnings": [
                    {
                        "line": w.line,
                        "column": w.column,
                        "message": w.message,
                        "severity": w.severity,
                        "suggestion": w.suggestion
                    }
                    for w in validation.warnings
                ],
                "metadata": validation.metadata
            }
            
            # Auto-fix if requested
            if auto_fix and not validation.is_valid:
                fixed_code = self.validator.fix_common_errors(code)
                fixed_validation = self.validator.validate(fixed_code)
                
                if fixed_validation.is_valid:
                    result["fixed_code"] = fixed_code
                    result["fix_applied"] = True
            
            return result
        
        @self.mcp.tool()
        async def render_diagram(
            code: str = Field(..., description="Mermaid code to render"),
            format: str = Field("png", description="Output format: png, svg, pdf, webp"),
            theme: str = Field("default", description="Theme: default, dark, forest, neutral"),
            style: str = Field("classic", description="Style: classic or handDrawn"),
            width: int = Field(800, description="Width in pixels"),
            height: int = Field(600, description="Height in pixels"),
            background: str = Field("white", description="Background color"),
            scale: float = Field(2.0, description="Scale factor for rendering"),
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Render a Mermaid diagram to an image.
            
            Supports multiple output formats and styling options.
            Returns base64-encoded image data.
            """
            try:
                # Validate first
                validation = self.validator.validate(code)
                if not validation.is_valid:
                    return {
                        "success": False,
                        "error": "Invalid diagram syntax",
                        "validation_errors": [e.message for e in validation.errors]
                    }
                
                # Create render config
                config = RenderConfig(
                    theme=Theme(theme),
                    style=RenderStyle(style),
                    background=background,
                    width=width,
                    height=height,
                    scale=scale
                )
                
                # Render
                output_format = OutputFormat(format.lower())
                result = await self.renderer.render(code, config, output_format)
                
                if result.success:
                    return {
                        "success": True,
                        "format": result.format.value,
                        "data": result.data,
                        "metadata": result.metadata
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def list_diagram_types(ctx: Context = None) -> Dict[str, Any]:
            """
            List all supported Mermaid diagram types with descriptions.
            """
            types = []
            for diagram_type in DiagramType:
                types.append({
                    "type": diagram_type.value,
                    "name": diagram_type.name.title(),
                    "description": self._get_type_description(diagram_type)
                })
            
            return {
                "diagram_types": types,
                "total": len(types)
            }
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.mcp.resource("diagram://list")
        async def list_diagrams() -> str:
            """List all stored diagrams."""
            diagrams = []
            for diagram_id, data in self.diagrams.items():
                diagrams.append({
                    "id": diagram_id,
                    "title": data["metadata"]["title"],
                    "created_at": data["metadata"]["created_at"],
                    "diagram_type": data["metadata"]["diagram_type"]
                })
            
            return json.dumps({
                "diagrams": diagrams,
                "count": len(diagrams)
            }, indent=2)
        
        @self.mcp.resource("diagram://{diagram_id}")
        async def get_diagram(diagram_id: str) -> str:
            """Get a specific diagram by ID."""
            if diagram_id in self.diagrams:
                return json.dumps(self.diagrams[diagram_id], indent=2)
            else:
                return json.dumps({"error": "Diagram not found"})
        
        @self.mcp.resource("template://list")
        async def list_templates() -> str:
            """List available diagram templates."""
            templates = self.generator.get_templates()
            return json.dumps({
                "templates": [t.dict() for t in templates],
                "count": len(templates)
            }, indent=2)
        
        @self.mcp.resource("template://{template_type}")
        async def get_template(template_type: str) -> str:
            """Get templates for a specific diagram type."""
            templates = self.generator.get_templates(template_type)
            if templates:
                return json.dumps({
                    "type": template_type,
                    "templates": [t.dict() for t in templates]
                }, indent=2)
            else:
                return json.dumps({"error": "No templates found for type"})
    
    def _register_prompts(self):
        """Register MCP prompts."""
        
        @self.mcp.prompt()
        async def diagram_assistant(
            topic: str = Field(..., description="Topic or domain for the diagram"),
            complexity: str = Field("medium", description="Complexity: simple, medium, complex"),
            audience: str = Field("technical", description="Target audience: technical, business, general")
        ) -> str:
            """
            Get AI assistance for creating diagrams on a specific topic.
            
            Provides tailored suggestions and examples based on the topic,
            complexity level, and target audience.
            """
            prompt = f"""You are a Mermaid diagram expert. Help create a {complexity} diagram about {topic} 
            for a {audience} audience. Provide:
            
            1. Recommended diagram type
            2. Key elements to include
            3. Example Mermaid code
            4. Best practices for this type of diagram
            """
            
            return prompt
    
    def _get_type_description(self, diagram_type: DiagramType) -> str:
        """Get description for a diagram type."""
        descriptions = {
            DiagramType.FLOWCHART: "Flowcharts for processes and workflows",
            DiagramType.SEQUENCE: "Sequence diagrams for interactions over time",
            DiagramType.CLASS: "Class diagrams for object-oriented design",
            DiagramType.STATE: "State diagrams for state machines",
            DiagramType.ER: "Entity-relationship diagrams for databases",
            DiagramType.GANTT: "Gantt charts for project timelines",
            DiagramType.PIE: "Pie charts for proportional data",
            DiagramType.JOURNEY: "User journey maps",
            DiagramType.GITGRAPH: "Git branch and commit visualization",
            DiagramType.MINDMAP: "Mind maps for brainstorming",
            DiagramType.TIMELINE: "Timeline diagrams for chronological events",
            DiagramType.QUADRANT: "Quadrant charts for 2D analysis",
            DiagramType.REQUIREMENT: "Requirement diagrams for specifications",
            DiagramType.C4CONTEXT: "C4 context diagrams for system architecture"
        }
        return descriptions.get(diagram_type, "Diagram type for specialized use cases")
    
    async def run(self, transport: str = "stdio"):
        """Run the MCP server."""
        await self.initialize()
        self.mcp.run(transport=transport)
    
    async def cleanup(self):
        """Clean up resources."""
        if self.renderer:
            await self.renderer.cleanup()