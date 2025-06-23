"""Minimal HTTP MCP server for Claude Desktop integration"""
import json
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .server import SailorMCPServer
from .logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MCP server instance
mcp_server = SailorMCPServer()
initialized = False


@app.post("/")
async def handle_root_post(request: Request):
    """Handle POST to root - redirect to MCP endpoint"""
    return await handle_mcp_message(request)


@app.post("/mcp")
async def handle_mcp_post(request: Request):
    """Handle POST to /mcp"""
    return await handle_mcp_message(request)


@app.post("/mcp/v1/message")
async def handle_mcp_message(request: Request):
    """Handle MCP JSON-RPC messages"""
    global initialized
    
    try:
        # Read request body
        body = await request.json()
        logger.info(f"Received request: {json.dumps(body, indent=2)}")
        
        # Extract JSON-RPC fields
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Handle notifications (no id field)
        if request_id is None:
            logger.info(f"Received notification: {method}")
            if method == "initialized":
                initialized = True
            # Return 204 No Content for notifications
            return Response(status_code=204)
        
        # Handle requests
        result = None
        
        if method == "initialize":
            initialized = True
            result = {
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
            
        elif method == "tools/list":
            if not initialized:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32002,
                            "message": "Not initialized"
                        }
                    }
                )
            
            tools = await mcp_server._list_tools()
            result = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
            
        elif method == "prompts/list":
            if not initialized:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32002,
                            "message": "Not initialized"
                        }
                    }
                )
            
            prompts = await mcp_server._list_prompts()
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
            
        elif method == "tools/call":
            if not initialized:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32002,
                            "message": "Not initialized"
                        }
                    }
                )
            
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            items = await mcp_server._call_tool(tool_name, tool_args)
            
            result = []
            for item in items:
                if hasattr(item, 'text'):
                    result.append({"type": item.type, "text": item.text})
                else:
                    result.append({
                        "type": item.type,
                        "data": item.data,
                        "mimeType": item.mimeType
                    })
                    
        elif method == "prompts/get":
            if not initialized:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32002,
                            "message": "Not initialized"
                        }
                    }
                )
            
            prompt_name = params.get("name")
            prompt_args = params.get("arguments", {})
            items = await mcp_server._get_prompt(prompt_name, prompt_args)
            result = [{"type": item.type, "text": item.text} for item in items]
            
        else:
            # Method not found
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )
        
        # Return success response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        logger.info(f"Sending response: {json.dumps(response, indent=2)}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if 'body' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        )


@app.get("/")
async def root():
    """Root endpoint with integration info"""
    return {
        "name": "Sailor MCP Server",
        "version": "1.0.0",
        "description": "Get a picture of your Mermaid!",
        "mcp": {
            "endpoint": "http://localhost:8081/mcp/v1/message",
            "transport": "http"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "initialized": initialized}


def run_server(host: str = "0.0.0.0", port: int = 8081):
    """Run the minimal HTTP server"""
    logger.info(f"Starting Sailor MCP minimal HTTP server on {host}:{port}")
    logger.info(f"Endpoint: http://{host}:{port}/mcp/v1/message")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()