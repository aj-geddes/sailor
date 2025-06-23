"""Stdio wrapper for Sailor MCP server to work with Claude Desktop"""
import asyncio
import json
import sys
import io
from typing import Optional

from .server import SailorMCPServer

# Configure logging to stderr before importing logger
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

from .logging_config import get_logger
logger = get_logger(__name__)


class StdioTransport:
    """Handle stdio communication for MCP"""
    
    def __init__(self):
        self.reader = None
        self.writer = None
    
    async def start(self):
        """Start reading from stdin and writing to stdout"""
        loop = asyncio.get_event_loop()
        self.reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(self.reader)
        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
        
        w_transport, w_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        self.writer = asyncio.StreamWriter(w_transport, w_protocol, self.reader, loop)
    
    async def read_message(self) -> Optional[str]:
        """Read a line from stdin"""
        try:
            line = await self.reader.readline()
            if not line:
                return None
            return line.decode('utf-8').strip()
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            return None
    
    async def write_message(self, message: dict):
        """Write a JSON message to stdout"""
        try:
            json_str = json.dumps(message)
            self.writer.write(f"{json_str}\n".encode('utf-8'))
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error writing message: {e}")


async def run_stdio_server():
    """Run the MCP server with stdio transport"""
    # Log to stderr only
    logger.info("Starting Sailor MCP stdio server")
    
    # Create server instance
    server = SailorMCPServer()
    transport = StdioTransport()
    
    try:
        # Start transport
        await transport.start()
        # Log to stderr only
        logger.info("Stdio transport started")
        
        # Main message loop
        while True:
            # Read message from stdin
            message_str = await transport.read_message()
            if not message_str:
                break
            
            try:
                # Parse JSON-RPC message
                message = json.loads(message_str)
                logger.debug(f"Received: {message}")
                
                # Handle the message
                method = message.get('method')
                params = message.get('params', {})
                request_id = message.get('id')
                
                if method == 'initialize':
                    # Use the protocol version requested by the client
                    requested_version = params.get('protocolVersion', '2024-11-05')
                    result = {
                        "protocolVersion": requested_version,
                        "capabilities": {
                            "tools": {},
                            "prompts": {}
                        },
                        "serverInfo": {
                            "name": "sailor-mcp",
                            "version": "1.0.0"
                        }
                    }
                elif method == 'tools/list':
                    tools = await server._list_tools()
                    result = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                elif method == 'tools/call':
                    tool_name = params.get('name')
                    tool_args = params.get('arguments', {})
                    items = await server._call_tool(tool_name, tool_args)
                    result = [
                        {"type": item.type, "text": item.text} if hasattr(item, 'text')
                        else {"type": item.type, "data": item.data, "mimeType": item.mimeType}
                        for item in items
                    ]
                elif method == 'prompts/list':
                    prompts = await server._list_prompts()
                    result = [
                        {
                            "name": prompt.name,
                            "description": prompt.description,
                            "arguments": [
                                {
                                    "name": arg.name,
                                    "description": arg.description,
                                    "required": arg.required
                                }
                                for arg in prompt.arguments
                            ]
                        }
                        for prompt in prompts
                    ]
                elif method == 'prompts/get':
                    prompt_name = params.get('name')
                    prompt_args = params.get('arguments', {})
                    items = await server._get_prompt(prompt_name, prompt_args)
                    result = [{"type": item.type, "text": item.text} for item in items]
                else:
                    # Unknown method
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    await transport.write_message(response)
                    continue
                
                # Send success response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                await transport.write_message(response)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                await transport.write_message(error_response)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": message.get('id') if 'message' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                await transport.write_message(error_response)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("Sailor MCP stdio server stopped")


def main():
    """Main entry point for stdio server"""
    # Set up logging to stderr so it doesn't interfere with stdio
    import logging
    import sys
    
    # Configure root logger to use stderr
    root_logger = logging.getLogger()
    root_logger.handlers = []
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Ensure no output goes to stdout except JSON-RPC messages
    sys.stdout = sys.stdout.detach()
    sys.stdout = io.TextIOWrapper(sys.stdout, encoding='utf-8', line_buffering=True)
    
    # Run the server
    asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()