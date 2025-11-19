"""
Pydantic models for API requests and responses.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class CreateDiagramRequest(BaseModel):
    """Request to create a new diagram."""
    description: Optional[str] = Field(None, description="Natural language description")
    code: Optional[str] = Field(None, description="Existing Mermaid code to enhance")
    diagram_type: Optional[str] = Field(None, description="Preferred diagram type")
    theme: Optional[str] = Field("default", description="Theme for the diagram")
    style: Optional[str] = Field("classic", description="Style (classic or handDrawn)")
    enhance: bool = Field(False, description="Whether to enhance existing code")
    enhance_prompt: Optional[str] = Field(None, description="Enhancement instructions")


class CreateDiagramResponse(BaseModel):
    """Response from diagram creation."""
    diagram_id: str
    code: str
    valid: bool
    diagram_type: Optional[str] = None
    share_url: Optional[str] = None
    errors: List[str] = []
    suggestions: List[str] = []


class ValidateRequest(BaseModel):
    """Request to validate Mermaid code."""
    code: str = Field(..., description="Mermaid diagram code to validate")
    auto_fix: bool = Field(False, description="Attempt to auto-fix errors")


class ValidationError(BaseModel):
    """Validation error details."""
    line: Optional[int] = None
    column: Optional[int] = None
    message: str
    severity: Literal["error", "warning", "info"]
    suggestion: Optional[str] = None


class ValidateResponse(BaseModel):
    """Response from validation."""
    is_valid: bool
    diagram_type: Optional[str] = None
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    metadata: Optional[Dict[str, Any]] = None
    fixed_code: Optional[str] = None


class RenderRequest(BaseModel):
    """Request to render a diagram."""
    code: str = Field(..., description="Mermaid code to render")
    format: Literal["png", "svg", "pdf", "webp"] = "png"
    theme: Optional[str] = None
    style: Optional[str] = None
    width: Optional[int] = Field(None, ge=100, le=4096)
    height: Optional[int] = Field(None, ge=100, le=4096)
    background: Optional[str] = None
    scale: Optional[float] = Field(None, ge=0.5, le=3.0)


class RenderResponse(BaseModel):
    """Response from rendering."""
    success: bool
    format: Optional[str] = None
    data: Optional[str] = Field(None, description="Base64 encoded image data")
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    action: Literal["validate", "render", "collaborate"]
    code: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    room: Optional[str] = None
    data: Optional[Any] = None


class WebSocketResponse(BaseModel):
    """WebSocket response format."""
    action: Literal["validation", "render", "collaborate", "error", "connected", "disconnected"]
    valid: Optional[bool] = None
    error: Optional[str] = None
    data: Optional[Any] = None
    message: Optional[str] = None
    type: Optional[str] = None