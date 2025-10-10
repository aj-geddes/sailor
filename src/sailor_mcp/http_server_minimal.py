"""Minimal HTTP MCP server using FastMCP - simplest possible implementation"""
from .server import mcp


def main():
    """Minimal HTTP server - just run FastMCP with SSE transport"""
    print("Starting Sailor MCP Minimal HTTP Server on http://localhost:8081")
    print("SSE endpoint: http://localhost:8081/sse")
    print("Get a picture of your Mermaid! 🧜‍♀️")

    # Simplest possible: Just run with default SSE transport
    # FastMCP handles everything:
    # - SSE endpoint at /sse
    # - CORS headers
    # - JSON-RPC message handling
    # - Tool and prompt registration
    mcp.run(transport="sse", port=8081)


if __name__ == "__main__":
    main()