"""Mock implementations for MCP types when package is not available"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock


@dataclass
class Tool:
    """Mock Tool type"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class TextContent:
    """Mock TextContent type"""
    type: str
    text: str


@dataclass
class ImageContent:
    """Mock ImageContent type"""
    type: str
    data: str
    mimeType: str


@dataclass
class PromptArgument:
    """Mock PromptArgument type"""
    name: str
    description: str
    required: bool


@dataclass
class Prompt:
    """Mock Prompt type"""
    name: str
    description: str
    arguments: List[PromptArgument]


class Server:
    """Mock MCP Server"""
    def __init__(self, name: str):
        self.name = name
        self._handlers = {}
    
    def list_tools(self):
        def decorator(func):
            self._handlers['list_tools'] = func
            return func
        return decorator
    
    def list_prompts(self):
        def decorator(func):
            self._handlers['list_prompts'] = func
            return func
        return decorator
    
    def get_prompt(self):
        def decorator(func):
            self._handlers['get_prompt'] = func
            return func
        return decorator
    
    def call_tool(self):
        def decorator(func):
            self._handlers['call_tool'] = func
            return func
        return decorator
    
    async def run(self, stdin, stdout, options):
        """Mock run method"""
        pass
    
    def create_initialization_options(self):
        """Mock initialization options"""
        return {}


class stdio_server:
    """Mock stdio_server context manager"""
    async def __aenter__(self):
        return (AsyncMock(), AsyncMock())  # stdin, stdout
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@dataclass
class JSONRPCMessage:
    """Mock JSON-RPC message"""
    jsonrpc: str = "2.0"


@dataclass
class JSONRPCRequest(JSONRPCMessage):
    """Mock JSON-RPC request"""
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


@dataclass
class JSONRPCResponse(JSONRPCMessage):
    """Mock JSON-RPC response"""
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None