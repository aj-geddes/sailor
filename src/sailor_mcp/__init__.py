"""Sailor MCP Server - Model Context Protocol for Mermaid diagram generation

This package provides an MCP server for generating and rendering Mermaid diagrams.

Transport modes:
- stdio: For Claude Desktop integration (default)
- streamable-http: For remote deployment (Railway, etc.)
- sse: For local development/testing

Usage:
    # As a module (stdio mode)
    python -m sailor_mcp

    # HTTP mode (Streamable HTTP)
    python -m sailor_mcp --http --port 8000

    # Via console scripts
    sailor-mcp          # stdio mode
    sailor-mcp-http     # HTTP mode
"""

__version__ = "2.0.0"

# Export main components
from .server import (
    mcp,
    main_stdio,
    main_http,
    health_check,
    server_status,
    validate_and_render_mermaid,
    get_mermaid_examples,
    request_mermaid_generation,
)

from .validators import MermaidValidator
from .renderer import MermaidRenderer, MermaidConfig
from .prompts import PromptGenerator
from .mermaid_resources import MermaidResources

__all__ = [
    "mcp",
    "main_stdio",
    "main_http",
    "health_check",
    "server_status",
    "validate_and_render_mermaid",
    "get_mermaid_examples",
    "request_mermaid_generation",
    "MermaidValidator",
    "MermaidRenderer",
    "MermaidConfig",
    "PromptGenerator",
    "MermaidResources",
]