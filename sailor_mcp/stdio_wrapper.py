"""
STDIO Wrapper for MCP Server
As specified in /docs/index.md Application Layer architecture
Provides STDIO transport for Claude Desktop integration
"""

import asyncio
import sys
import logging
from typing import Optional

# Import MCP components following documented architecture
import os
import sys
sys.path.append(os.path.dirname(__file__))
from server import mcp

logger = logging.getLogger(__name__)


class StdioWrapper:
    """
    STDIO wrapper for MCP server.
    As documented in /docs/index.md Application Layer - connects Claude Desktop to MCP Server.
    Implements Model Context Protocol over STDIO transport.
    """
    
    def __init__(self):
        self.server = mcp
    
    async def run(self):
        """
        Run MCP server with STDIO transport.
        Follows documented architecture for Claude Desktop integration.
        """
        try:
            logger.info("Starting MCP server with STDIO transport")
            
            # Configure server for STDIO transport
            await self.server.run(transport="stdio")
            
        except KeyboardInterrupt:
            logger.info("STDIO wrapper stopped by user")
        except Exception as e:
            logger.error(f"STDIO wrapper error: {e}")
            raise


async def main():
    """
    Main entry point for STDIO MCP server.
    Used by Claude Desktop as documented in /docs/index.md
    """
    # Configure logging for STDIO mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Log to stderr to avoid interfering with STDIO communication
    )
    
    wrapper = StdioWrapper()
    await wrapper.run()


if __name__ == "__main__":
    asyncio.run(main())