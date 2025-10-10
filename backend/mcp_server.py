#!/usr/bin/env python3
"""
MCP Server for Sailor Site - Mermaid Diagram Generator using FastMCP
Allows LLMs to generate Mermaid diagrams and export them as images
"""

import sys
import os
import asyncio

# Add parent directory to path to import from sailor_mcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sailor_mcp.server import mcp, main_stdio


def main():
    """Main entry point that uses the FastMCP server from sailor_mcp"""
    print("Starting Sailor Mermaid MCP Server (FastMCP)...")
    print("This server is now using FastMCP for improved performance and features")
    print("Get a picture of your Mermaid! 🧜‍♀️")

    # Run the FastMCP server with stdio transport (default for Claude Desktop)
    asyncio.run(main_stdio())


if __name__ == "__main__":
    main()