"""HTTP transport for Sailor MCP server - Enhanced version with custom middleware using FastMCP"""
import argparse
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastmcp.server.sse import create_sse_server
import uvicorn

from .server import mcp
from .logging_config import get_logger

logger = get_logger(__name__)


def create_enhanced_server(host: str = "0.0.0.0", port: int = 8080) -> FastAPI:
    """Create enhanced HTTP server with custom middleware and routes"""

    # Create SSE server from FastMCP
    app = create_sse_server(mcp)

    # Add enhanced CORS middleware with more permissive settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests for debugging"""
        logger.info(f"Incoming {request.method} request to {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "sailor-mcp",
            "version": "2.0.0",
            "transport": "sse"
        }

    # Add root endpoint with service info
    @app.get("/")
    async def root():
        """Root endpoint with MCP integration info"""
        base_url = f"http://{host}:{port}"
        return {
            "name": "Sailor MCP Server",
            "description": "Get a picture of your Mermaid! 🧜‍♀️",
            "version": "2.0.0",
            "mcp": {
                "version": "1.0.0",
                "transport": "sse",
                "endpoint": f"{base_url}/sse"
            },
            "endpoints": {
                "sse": f"{base_url}/sse",
                "health": f"{base_url}/health"
            },
            "features": [
                "Server-Sent Events (SSE) transport",
                "Enhanced CORS support",
                "Request logging",
                "Health monitoring"
            ]
        }

    # Add metrics endpoint (simple version)
    @app.get("/metrics")
    async def metrics():
        """Simple metrics endpoint"""
        return {
            "uptime": "running",
            "requests_total": 0,  # Could be tracked with middleware
            "active_connections": 0  # Could be tracked with SSE connections
        }

    return app


def main():
    """Main entry point for enhanced HTTP server"""
    parser = argparse.ArgumentParser(description="Sailor MCP HTTP Server V2 (Enhanced)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", help="Logging level")

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"Starting Sailor MCP HTTP server V2 on {args.host}:{args.port}")
    logger.info(f"SSE endpoint: http://{args.host}:{args.port}/sse")
    logger.info("Enhanced features: CORS, logging, health checks, metrics")
    logger.info("Get a picture of your Mermaid! 🧜‍♀️")
    logger.info("=" * 60)

    # Create and run the enhanced server
    app = create_enhanced_server(args.host, args.port)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
        access_log=True
    )


if __name__ == "__main__":
    main()