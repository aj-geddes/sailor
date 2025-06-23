"""HTTP transport for Sailor MCP server - Claude Desktop compatible version"""
import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any, List
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Response, WebSocket
from fastapi.responses import StreamingResponse, JSONResponse
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


class MCPSession:
    """Represents an MCP session"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.initialized = False
        self.client_info = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        

class MCPHTTPTransport:
    """HTTP transport handler for MCP JSON-RPC messages with Claude Desktop support"""
    
    def __init__(self, mcp_server: SailorMCPServer):
        self.mcp_server = mcp_server
        self.sessions: Dict[str, MCPSession] = {}
        
    def get_or_create_session(self, session_id: Optional[str] = None) -> MCPSession:
        """Get existing session or create new one"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            logger.info(f"Creating new session: {session_id}")
            self.sessions[session_id] = MCPSession(session_id)
        else:
            self.sessions[session_id].last_activity = datetime.now()
            
        return self.sessions[session_id]
        
    async def handle_request(self, request_data: dict, session_id: Optional[str] = None) -> dict:
        """Handle a single JSON-RPC request with session support"""
        try:
            # Get or create session
            session = self.get_or_create_session(session_id)
            
            # Extract JSON-RPC fields
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            logger.info(f"[Session {session.session_id}] Handling request: {method}")
            logger.debug(f"Request params: {json.dumps(params, indent=2)}")
            
            # Handle notifications (no ID)
            if request_id is None:
                logger.info(f"Received notification: {method}")
                # Process notification but don't return response
                await self._process_notification(method, params, session)
                return None
            
            # Route to appropriate handler
            if method == "initialize":
                result = await self._handle_initialize(params, session)
            elif method == "initialized":
                # Client notification that initialization is complete
                session.initialized = True
                logger.info(f"Session {session.session_id} initialization confirmed")
                return None
            elif method == "tools/list":
                if not session.initialized:
                    raise ValueError("Session not initialized")
                result = await self.mcp_server._list_tools()
            elif method == "tools/call":
                if not session.initialized:
                    raise ValueError("Session not initialized")
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await self.mcp_server._call_tool(tool_name, tool_args)
            elif method == "prompts/list":
                if not session.initialized:
                    raise ValueError("Session not initialized")
                result = await self.mcp_server._list_prompts()
            elif method == "prompts/get":
                if not session.initialized:
                    raise ValueError("Session not initialized")
                prompt_name = params.get("name")
                prompt_args = params.get("arguments", {})
                result = await self.mcp_server._get_prompt(prompt_name, prompt_args)
            elif method == "completion/complete":
                # Handle completion requests if needed
                result = {"completions": []}
            else:
                logger.warning(f"Unknown method: {method}")
                raise ValueError(f"Method not found: {method}")
            
            # Format response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": self._serialize_result(result)
            }
            
            logger.debug(f"Response: {json.dumps(response, indent=2)}")
            return response
            
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": {
                        "type": type(e).__name__,
                        "details": str(e)
                    }
                }
            }
            if request_data.get("id") is None:
                return None  # Don't respond to notifications
            return error_response
    
    async def _process_notification(self, method: str, params: dict, session: MCPSession):
        """Process notification messages (no response expected)"""
        logger.info(f"Processing notification: {method}")
        if method == "initialized":
            session.initialized = True
        elif method == "$/cancelRequest":
            # Handle request cancellation
            request_id = params.get("id")
            logger.info(f"Cancellation requested for: {request_id}")
        # Add other notification handlers as needed
    
    async def _handle_initialize(self, params: dict, session: MCPSession) -> dict:
        """Handle initialization request with Claude Desktop compatibility"""
        # Store client info
        session.client_info = params.get("clientInfo", {})
        logger.info(f"Initializing session for client: {session.client_info}")
        
        # Get protocol version
        protocol_version = params.get("protocolVersion", "0.1.0")
        
        # Initialize response
        response = {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {},
                "prompts": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "sailor-mcp",
                "version": "1.0.0"
            }
        }
        
        # Mark session as initialized
        session.initialized = True
        
        return response
    
    def _serialize_result(self, result):
        """Serialize MCP objects to JSON-compatible format"""
        if isinstance(result, list):
            return [self._serialize_item(item) for item in result]
        elif isinstance(result, dict):
            return result
        elif hasattr(result, '__dict__'):
            return self._serialize_item(result)
        return result
    
    def _serialize_item(self, item):
        """Serialize a single MCP object"""
        if hasattr(item, '__dict__'):
            # Convert MCP objects to dicts
            serialized = {}
            for k, v in item.__dict__.items():
                if not k.startswith('_'):
                    if isinstance(v, (list, dict)):
                        serialized[k] = self._serialize_result(v)
                    else:
                        serialized[k] = v
            return serialized
        return item


class SailorHTTPServer:
    """HTTP server for Sailor MCP with Claude Desktop support"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.mcp_server = SailorMCPServer()
        self.transport = MCPHTTPTransport(self.mcp_server)
        self.app = None
        self._setup_app()
    
    def _setup_app(self):
        """Set up FastAPI application with all required endpoints"""
        self.app = FastAPI(
            title="Sailor MCP Server",
            description="MCP server for generating and rendering Mermaid diagrams",
            version="1.0.0"
        )
        
        # Add CORS middleware with permissive settings for Claude Desktop
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"]
        )
        
        # Add middleware to log all requests
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            logger.info(f"Incoming {request.method} request to {request.url.path}")
            logger.debug(f"Headers: {dict(request.headers)}")
            response = await call_next(request)
            logger.info(f"Response status: {response.status_code}")
            return response
        
        # Add routes
        self.app.get("/health")(self.health_check)
        self.app.get("/")(self.root)
        
        # Main MCP endpoints
        self.app.post("/mcp/v1/message")(self.handle_message)
        self.app.post("/message")(self.handle_message)  # Alternative path
        self.app.post("/")(self.handle_message)  # Root POST for compatibility
        
        # Streaming endpoint
        self.app.post("/mcp/v1/stream")(self.handle_stream)
        
        # WebSocket support (optional)
        self.app.websocket("/mcp/v1/websocket")(self.websocket_endpoint)
        
        # Add CORS preflight handling
        self.app.options("/mcp/v1/message")(self.handle_options)
        self.app.options("/mcp/v1/stream")(self.handle_options)
        self.app.options("/message")(self.handle_options)
        self.app.options("/")(self.handle_options)
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "sailor-mcp",
            "version": "1.0.0",
            "sessions": len(self.transport.sessions)
        }
    
    async def root(self):
        """Root endpoint with MCP integration info"""
        base_url = f"http://{self.host}:{self.port}"
        return {
            "name": "Sailor MCP Server",
            "description": "Get a picture of your Mermaid!",
            "mcp_version": "0.1.0",
            "endpoints": {
                "message": f"{base_url}/mcp/v1/message",
                "stream": f"{base_url}/mcp/v1/stream",
                "websocket": f"ws://{self.host}:{self.port}/mcp/v1/websocket"
            },
            "transport": ["http+jsonrpc", "ws+jsonrpc"],
            "features": ["tools", "prompts"],
            "integration": {
                "claude_desktop": {
                    "url": f"{base_url}/mcp/v1/message",
                    "transport": "http"
                }
            }
        }
    
    async def handle_options(self):
        """Handle OPTIONS request for CORS"""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "3600",
            }
        )
    
    async def handle_message(self, request: Request):
        """Handle single JSON-RPC message with extensive logging"""
        try:
            # Get session ID from headers if available
            session_id = request.headers.get("X-Session-ID")
            
            # Read raw body for debugging
            body_bytes = await request.body()
            body_str = body_bytes.decode('utf-8')
            
            logger.info("=" * 50)
            logger.info("Incoming request")
            logger.info(f"Path: {request.url.path}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Raw body: {body_str}")
            logger.info("=" * 50)
            
            # Parse JSON
            if not body_str:
                logger.warning("Empty request body")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error: empty request body"
                        },
                        "id": None
                    }
                )
            
            try:
                body = json.loads(body_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        },
                        "id": None
                    }
                )
            
            logger.debug(f"Parsed request: {json.dumps(body, indent=2)}")
            
            # Handle single or batch requests
            if isinstance(body, list):
                # Batch request
                logger.info(f"Processing batch request with {len(body)} items")
                responses = []
                for req in body:
                    resp = await self.transport.handle_request(req, session_id)
                    if resp is not None:  # Don't include responses for notifications
                        responses.append(resp)
                return JSONResponse(content=responses)
            else:
                # Single request
                response = await self.transport.handle_request(body, session_id)
                if response is None:
                    # Notification - return 204 No Content
                    return Response(status_code=204)
                return JSONResponse(content=response)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": None
                }
            )
    
    async def handle_stream(self, request: Request):
        """Handle streaming JSON-RPC messages"""
        session_id = request.headers.get("X-Session-ID")
        
        async def stream_generator():
            try:
                # Read the initial request
                body = await request.json()
                logger.debug(f"Stream request: {body}")
                
                # Send initial response
                response = await self.transport.handle_request(body, session_id)
                if response:
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
            media_type="application/x-ndjson",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-cache",
            }
        )
    
    async def websocket_endpoint(self, websocket: WebSocket):
        """WebSocket endpoint for bidirectional communication"""
        await websocket.accept()
        session_id = str(uuid.uuid4())
        logger.info(f"WebSocket connection established: {session_id}")
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                request = json.loads(data)
                
                # Process request
                response = await self.transport.handle_request(request, session_id)
                
                # Send response if not a notification
                if response:
                    await websocket.send_text(json.dumps(response))
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            logger.info(f"WebSocket connection closed: {session_id}")
    
    def run(self):
        """Run the HTTP server"""
        logger.info("=" * 60)
        logger.info(f"Starting Sailor MCP HTTP server on {self.host}:{self.port}")
        logger.info(f"MCP endpoint: http://{self.host}:{self.port}/mcp/v1/message")
        logger.info(f"Alternative endpoints:")
        logger.info(f"  - http://{self.host}:{self.port}/message")
        logger.info(f"  - http://{self.host}:{self.port}/ (POST)")
        logger.info("Get a picture of your Mermaid! 🧜‍♀️")
        logger.info("=" * 60)
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True
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