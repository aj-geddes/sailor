"""HTTP transport for Sailor MCP server following MCP standards"""
import asyncio
import json
import logging
from typing import AsyncIterator, Optional
import uuid

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import JSONRPCMessage, JSONRPCRequest, JSONRPCResponse
except ImportError:
    # Fallback for testing
    from .mocks import Server, JSONRPCMessage, JSONRPCRequest, JSONRPCResponse
    InitializationOptions = dict

from .server import SailorMCPServer
from .logging_config import get_logger

logger = get_logger(__name__)


class MCPHTTPTransport:
    """HTTP transport handler for MCP JSON-RPC messages"""
    
    def __init__(self, mcp_server: SailorMCPServer):
        self.mcp_server = mcp_server
        self.sessions = {}
        
    async def handle_request(self, request_data: dict) -> dict:
        """Handle a single JSON-RPC request"""
        try:
            # Extract JSON-RPC fields
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            logger.debug(f"Handling JSON-RPC request: {method}")
            
            # Route to appropriate handler
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self.mcp_server._list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await self.mcp_server._call_tool(tool_name, tool_args)
            elif method == "prompts/list":
                result = await self.mcp_server._list_prompts()
            elif method == "prompts/get":
                prompt_name = params.get("name")
                prompt_args = params.get("arguments", {})
                result = await self.mcp_server._get_prompt(prompt_name, prompt_args)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Format response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": self._serialize_result(result)
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialization request"""
        return {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "tools": {},
                "prompts": {}
            },
            "serverInfo": {
                "name": "sailor-mcp",
                "version": "1.0.0"
            }
        }
    
    def _serialize_result(self, result):
        """Serialize MCP objects to JSON-compatible format"""
        if isinstance(result, list):
            return [self._serialize_item(item) for item in result]
        return result
    
    def _serialize_item(self, item):
        """Serialize a single MCP object"""
        if hasattr(item, '__dict__'):
            # Convert MCP objects to dicts
            return {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
        return item


class SailorHTTPServer:
    """HTTP server for Sailor MCP following MCP standards"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.mcp_server = SailorMCPServer()
        self.transport = MCPHTTPTransport(self.mcp_server)
        self.app = None
        self._setup_app()
    
    def _setup_app(self):
        """Set up FastAPI application"""
        self.app = FastAPI(
            title="Sailor MCP Server",
            description="MCP server for generating and rendering Mermaid diagrams",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self.app.get("/health")(self.health_check)
        self.app.get("/")(self.root)
        self.app.post("/mcp/v1/message")(self.handle_message)
        self.app.post("/mcp/v1/stream")(self.handle_stream)
        
        # Add CORS preflight handling
        self.app.options("/mcp/v1/message")(self.handle_options)
        self.app.options("/mcp/v1/stream")(self.handle_options)
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "sailor-mcp",
            "version": "1.0.0"
        }
    
    async def root(self):
        """Root endpoint with MCP integration info"""
        base_url = f"http://{self.host}:{self.port}"
        return {
            "name": "Sailor MCP Server",
            "description": "Get a picture of your Mermaid!",
            "mcp": {
                "version": "0.1.0",
                "endpoints": {
                    "message": f"{base_url}/mcp/v1/message",
                    "stream": f"{base_url}/mcp/v1/stream"
                },
                "transport": "http+jsonrpc"
            },
            "integration": {
                "url": f"{base_url}/mcp/v1/message",
                "transport": "http"
            }
        }
    
    async def handle_options(self):
        """Handle OPTIONS request for CORS"""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600",
            }
        )
    
    async def handle_message(self, request: Request):
        """Handle single JSON-RPC message"""
        try:
            # Read raw body for debugging
            body_bytes = await request.body()
            body_str = body_bytes.decode('utf-8')
            logger.info(f"Raw request body: {body_str}")
            
            # Parse JSON
            body = json.loads(body_str) if body_str else {}
            logger.debug(f"Parsed message: {body}")
            
            # Handle single or batch requests
            if isinstance(body, list):
                # Batch request
                responses = []
                for req in body:
                    resp = await self.transport.handle_request(req)
                    responses.append(resp)
                return responses
            else:
                # Single request
                return await self.transport.handle_request(body)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": None
            }
    
    async def handle_stream(self, request: Request):
        """Handle streaming JSON-RPC messages"""
        async def stream_generator():
            try:
                # Read the initial request
                body = await request.json()
                logger.debug(f"Stream request: {body}")
                
                # Send initial response
                response = await self.transport.handle_request(body)
                yield json.dumps(response).encode() + b'\n'
                
                # For long-running operations (like rendering), we could stream progress
                # This is where we'd implement streaming updates if needed
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                yield json.dumps(error_response).encode() + b'\n'
        
        return StreamingResponse(
            stream_generator(),
            media_type="application/json-rpc",
            headers={
                "X-Content-Type-Options": "nosniff",
            }
        )
    
    def run(self):
        """Run the HTTP server"""
        logger.info(f"Starting Sailor MCP HTTP server on {self.host}:{self.port}")
        logger.info(f"MCP endpoint: http://{self.host}:{self.port}/mcp/v1/message")
        logger.info("Get a picture of your Mermaid! 🧜‍♀️")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


def main():
    """Main entry point for HTTP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sailor MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = SailorHTTPServer(host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main()