"""
Sailor - Beautiful Mermaid Diagram Creation Tool

A dual-mode application that works as both an MCP server for AI assistants
and a web application for human users.
"""

__version__ = "2.0.0"
__author__ = "Sailor Team"
__license__ = "MIT"

from .core import MermaidValidator, MermaidRenderer, MermaidParser
from .mcp import SailorMCPServer

__all__ = [
    "MermaidValidator",
    "MermaidRenderer", 
    "MermaidParser",
    "SailorMCPServer",
]