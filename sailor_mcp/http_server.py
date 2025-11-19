"""
HTTP Server for MCP Server
As specified in /docs/index.md Application Layer architecture
Provides HTTP transport for MCP protocol
"""

import asyncio
import logging
from typing import Optional
import argparse

# Import MCP components following documented architecture
import os
import sys
sys.path.append(os.path.dirname(__file__))
from server import mcp

logger = logging.getLogger(__name__)


class HttpServer:
    """
    HTTP server for MCP protocol.
    As documented in /docs/index.md Application Layer - provides HTTP transport.
    Implements Model Context Protocol over HTTP/SSE transport.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.server = mcp
    
    async def run(self):
        """
        Run MCP server with HTTP transport.
        Follows documented architecture for HTTP-based MCP access.
        """
        try:
            logger.info(f"Starting MCP HTTP server on {self.host}:{self.port}")
            
            # Configure server for HTTP transport (Streamable HTTP)
            await self.server.run(
                transport="http",
                host=self.host,
                port=self.port
            )
            
        except KeyboardInterrupt:
            logger.info("HTTP server stopped by user")
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
            raise


async def main():
    """
    Main entry point for HTTP MCP server.
    Supports command-line arguments for host and port configuration.
    """
    parser = argparse.ArgumentParser(description="Sailor MCP HTTP Server")
    parser.add_argument(
        "--host", 
        default="localhost", 
        help="Host to bind to (default: localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080, 
        help="Port to bind to (default: 8080)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = HttpServer(host=args.host, port=args.port)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())