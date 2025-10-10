"""FastMCP entry point for Sailor MCP server.

This module serves as the main entry point when running:
    python -m sailor_mcp

It replaces the complex stdio_wrapper.py with FastMCP's built-in transport handling.
"""

from .server_fastmcp import mcp

if __name__ == "__main__":
    # FastMCP handles all the stdio/HTTP transport complexity internally
    # Simply call run() and it will:
    # 1. Detect if running in stdio mode (for Claude Desktop)
    # 2. Start HTTP server if specified
    # 3. Handle all JSON-RPC protocol details
    mcp.run()