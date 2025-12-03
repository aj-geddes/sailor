"""FastMCP entry point for Sailor MCP server.

This module serves as the main entry point when running:
    python -m sailor_mcp
    python -m sailor_mcp --http  (for HTTP/Streamable HTTP transport)

Transport modes:
- stdio (default): For Claude Desktop integration
- Streamable HTTP: For remote deployment (Railway, etc.)
- SSE: For local development/testing
"""

import sys
import os

from .server import mcp, main_stdio, main_http

if __name__ == "__main__":
    # Determine transport mode based on args or environment
    if "--http" in sys.argv or os.environ.get("MCP_TRANSPORT") == "http":
        # Run with HTTP transport (Streamable HTTP by default)
        main_http()
    else:
        # Run with stdio transport (default for Claude Desktop)
        main_stdio()