"""HTTP transport for Sailor MCP server using FastMCP's built-in SSE transport"""
import argparse
import logging
from .server import mcp
from .logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point for HTTP server with SSE transport"""
    parser = argparse.ArgumentParser(description="Sailor MCP HTTP Server (SSE)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"Starting Sailor MCP HTTP/SSE server on {args.host}:{args.port}")
    logger.info(f"SSE endpoint: http://{args.host}:{args.port}/sse")
    logger.info("Get a picture of your Mermaid! 🧜‍♀️")
    logger.info("=" * 60)

    # Use FastMCP's built-in SSE transport
    # This automatically creates a FastAPI app with:
    # - GET /sse for SSE connections
    # - CORS middleware configured
    # - Proper error handling
    mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()