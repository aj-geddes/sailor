"""
FastAPI server for Sailor web frontend.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..core.validator import MermaidValidator
from ..core.renderer import MermaidRenderer, RenderConfig, OutputFormat
from ..core.generator import DiagramGenerator
from .models import (
    CreateDiagramRequest,
    CreateDiagramResponse,
    ValidateRequest,
    ValidateResponse,
    RenderRequest,
    RenderResponse,
    ValidationError as ValidationErrorModel,
    WebSocketMessage,
    WebSocketResponse
)
from .websocket import ConnectionManager

# Global instances
validator = MermaidValidator()
renderer = MermaidRenderer()
generator = DiagramGenerator()
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("Starting Sailor API server...")
    yield
    # Shutdown
    print("Shutting down Sailor API server...")
    await renderer.close()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Sailor API",
        description="API for creating and rendering Mermaid diagrams",
        version="1.0.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Sailor API", "version": "1.0.0"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.post("/api/v1/diagram/create", response_model=CreateDiagramResponse)
    async def create_diagram(request: CreateDiagramRequest):
        """Create a new diagram from description or enhance existing code."""
        try:
            if request.description:
                # Generate from description
                result = await generator.generate_from_description(
                    description=request.description,
                    diagram_type=request.diagram_type,
                    style=request.style or "default",
                    enhance_prompt=request.enhance_prompt
                )
                
                if not result.success:
                    raise HTTPException(400, result.error or "Generation failed")
                
                code = result.code
            elif request.code:
                # Use provided code
                code = request.code
                
                if request.enhance:
                    # Enhance existing code
                    result = await generator.enhance_diagram(
                        code=code,
                        enhancement_prompt=request.enhance_prompt or "Improve this diagram"
                    )
                    if result.success:
                        code = result.code
            else:
                raise HTTPException(400, "Either description or code must be provided")

            # Validate the code
            validation = validator.validate(code)
            
            # Generate diagram ID
            diagram_id = str(uuid.uuid4())
            
            return CreateDiagramResponse(
                diagram_id=diagram_id,
                code=code,
                valid=validation.is_valid,
                diagram_type=validation.diagram_type,
                errors=[e.message for e in validation.errors],
                suggestions=[s for s in validation.suggestions if s]
            )
            
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.post("/api/v1/diagram/validate", response_model=ValidateResponse)
    async def validate_diagram(request: ValidateRequest):
        """Validate Mermaid diagram code."""
        try:
            result = validator.validate(request.code)
            
            # Auto-fix if requested
            fixed_code = None
            if request.auto_fix and not result.is_valid:
                fixed_result = validator.auto_fix(request.code)
                if fixed_result.is_valid:
                    fixed_code = fixed_result.code
            
            return ValidateResponse(
                is_valid=result.is_valid,
                diagram_type=result.diagram_type,
                errors=[
                    ValidationErrorModel(
                        line=e.line,
                        column=e.column,
                        message=e.message,
                        severity=e.severity,
                        suggestion=e.suggestion
                    ) for e in result.errors
                ],
                warnings=[
                    ValidationErrorModel(
                        line=w.line,
                        column=w.column,
                        message=w.message,
                        severity="warning",
                        suggestion=w.suggestion
                    ) for w in result.warnings
                ],
                metadata=result.metadata,
                fixed_code=fixed_code
            )
            
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.post("/api/v1/diagram/render", response_model=RenderResponse)
    async def render_diagram(request: RenderRequest):
        """Render Mermaid diagram to image."""
        try:
            # Validate first
            validation = validator.validate(request.code)
            if not validation.is_valid:
                return RenderResponse(
                    success=False,
                    error="Invalid diagram code"
                )
            
            # Configure rendering
            config = RenderConfig(
                theme=request.theme or "default",
                width=request.width or 1920,
                height=request.height or 1080,
                background_color=request.background or "white",
                scale=request.scale or 1.0
            )
            
            # Render
            output_format = OutputFormat(request.format or "png")
            result = await renderer.render(request.code, config, output_format)
            
            if not result.success:
                return RenderResponse(
                    success=False,
                    error=result.error
                )
            
            return RenderResponse(
                success=True,
                format=request.format or "png",
                data=result.data,
                metadata=result.metadata
            )
            
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.get("/api/v1/diagram/{diagram_id}")
    async def get_diagram(diagram_id: str):
        """Get diagram by ID."""
        # In a real implementation, this would fetch from a database
        raise HTTPException(404, "Diagram storage not implemented")

    @app.get("/api/v1/templates")
    async def get_templates(type: Optional[str] = None):
        """Get available diagram templates."""
        templates = generator.list_templates()
        
        if type:
            templates = [t for t in templates if t.get("type") == type]
        
        return {"templates": templates}

    @app.get("/api/v1/diagram/types")
    async def get_diagram_types():
        """Get supported diagram types."""
        return {
            "types": [
                {"id": "flowchart", "name": "Flowchart", "description": "Flow diagrams and process charts"},
                {"id": "sequence", "name": "Sequence Diagram", "description": "Interaction sequences"},
                {"id": "class", "name": "Class Diagram", "description": "Object-oriented class structures"},
                {"id": "state", "name": "State Diagram", "description": "State machines and transitions"},
                {"id": "er", "name": "ER Diagram", "description": "Entity relationship diagrams"},
                {"id": "gantt", "name": "Gantt Chart", "description": "Project timelines"},
                {"id": "pie", "name": "Pie Chart", "description": "Statistical pie charts"},
                {"id": "git", "name": "Git Graph", "description": "Git commit history"},
                {"id": "journey", "name": "User Journey", "description": "User experience flows"},
                {"id": "mindmap", "name": "Mind Map", "description": "Hierarchical information"},
            ]
        }

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time features."""
        await manager.connect(websocket)
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                message = WebSocketMessage(**data)
                
                # Process message
                if message.action == "validate":
                    # Real-time validation
                    result = validator.validate(message.code)
                    response = WebSocketResponse(
                        action="validation",
                        valid=result.is_valid,
                        error=result.errors[0].message if result.errors else None
                    )
                    await manager.send_personal(response.dict(), websocket)
                    
                elif message.action == "render":
                    # Real-time render (preview)
                    validation = validator.validate(message.code)
                    if validation.is_valid:
                        # For preview, use smaller size and PNG
                        config = RenderConfig(
                            theme=message.config.get("theme", "default") if message.config else "default",
                            width=800,
                            height=600
                        )
                        result = await renderer.render(message.code, config, OutputFormat.PNG)
                        response = WebSocketResponse(
                            action="render",
                            data=result.data if result.success else None
                        )
                    else:
                        response = WebSocketResponse(
                            action="error",
                            message="Invalid diagram code"
                        )
                    await manager.send_personal(response.dict(), websocket)
                    
                elif message.action == "collaborate":
                    # Collaborative editing
                    room = message.room
                    if room:
                        await manager.join_room(websocket, room)
                        # Broadcast to room
                        await manager.broadcast_to_room(
                            {"action": "collaborate", "type": "update", "data": message.data},
                            room,
                            exclude=websocket
                        )
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket)


    return app


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    app = create_app()
    uvicorn.run(app, host=host, port=port)