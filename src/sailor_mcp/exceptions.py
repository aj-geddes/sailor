"""Custom exceptions for Sailor MCP"""


class SailorMCPError(Exception):
    """Base exception for all Sailor MCP errors"""
    pass


class ValidationError(SailorMCPError):
    """Raised when Mermaid code validation fails"""
    def __init__(self, message: str, errors: list = None, warnings: list = None):
        super().__init__(message)
        self.errors = errors or []
        self.warnings = warnings or []


class RenderingError(SailorMCPError):
    """Raised when diagram rendering fails"""
    pass


class BrowserError(RenderingError):
    """Raised when browser-related operations fail"""
    pass


class ConfigurationError(SailorMCPError):
    """Raised when configuration is invalid"""
    pass


class PromptError(SailorMCPError):
    """Raised when prompt generation fails"""
    pass


class ToolError(SailorMCPError):
    """Raised when MCP tool execution fails"""
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Tool '{tool_name}' failed: {message}")
        self.tool_name = tool_name