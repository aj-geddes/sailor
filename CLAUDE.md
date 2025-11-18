# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview (v2.0 - FastMCP Migration)

Sailor is a Mermaid diagram generator that combines a web interface with an MCP (Model Context Protocol) server for generating and rendering Mermaid diagrams. **Version 2.0 migrates from mcp-python to FastMCP** for a simpler, more maintainable codebase.

### Key Components:
- **Web UI**: Flask-based web application for interactive diagram creation
- **MCP Server**: FastMCP-powered server with decorator-based tools and prompts
- **Architecture Benefits**: 70% code reduction, eliminated stdio_wrapper complexity

## Development Commands

### Installation & Setup

```bash
# Install FastMCP framework
pip install fastmcp>=0.5.0

# Install development dependencies
pip install -r requirements-dev.txt

# Install MCP server in development mode
pip install -e .

# Install Playwright browsers (required for rendering)
playwright install chromium

# Install backend dependencies
cd backend && pip install -r requirements.txt
```

### Testing

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_server.py -v

# Run with coverage
pytest --cov=sailor_mcp tests/

# Quick test runner
python scripts/run_tests.py

# Run integration tests (requires browser)
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code with Black
black src/ tests/ backend/

# Lint with flake8
flake8 src/ tests/ backend/

# Type checking with mypy
mypy src/sailor_mcp/

# Sort imports
isort src/ tests/ backend/
```

### Running Services

```bash
# Run web UI development server
cd backend && python app.py

# Run MCP server with stdio (Claude Desktop)
python -m sailor_mcp.server

# Run MCP server with HTTP/SSE (Web clients)
python -m sailor_mcp.server --http --port 8000

# Run everything with Docker
docker-compose up --build

# Build MCP Docker image for Claude Desktop
docker build -f Dockerfile.mcp-stdio -t sailor-mcp .
```

## FastMCP Architecture (v2.0+)

Sailor now uses FastMCP for a simpler, more maintainable codebase:

### Component Structure

The project follows a dual-server architecture:

1. **Web Interface (`backend/`)**
   - `app.py`: Flask server handling web UI and API endpoints
   - `static/`: Frontend HTML/CSS/JS files
   - Integrates with OpenAI and Anthropic APIs for diagram generation

2. **FastMCP Server (`src/sailor_mcp/`)**
   - `server.py`: Main FastMCP server with decorated tools and prompts
   - `renderer.py`: Playwright-based Mermaid rendering engine
   - `validators.py`: Mermaid syntax validation logic
   - `prompts.py`: AI prompt templates for diagram generation
   - `mermaid_resources.py`: Example diagrams and documentation
   - **Note**: stdio_wrapper.py eliminated - FastMCP handles transports natively

### Key Integration Points

- **MCP Protocol**: The server implements MCP tools that Claude Desktop can invoke:
  - `request_mermaid_generation`: Generate Mermaid code from descriptions
  - `validate_and_render_mermaid`: Validate and render existing Mermaid code
  - `get_mermaid_examples`: Retrieve example diagrams

- **Rendering Pipeline**: 
  1. Mermaid code validation (`validators.py`)
  2. Browser-based rendering via Playwright (`renderer.py`)
  3. Image output as PNG with configurable themes

- **Docker Architecture**:
  - `Dockerfile.mcp-stdio`: Claude Desktop integration container
  - `Dockerfile.mcp-http`: HTTP server container
  - `docker-compose.yml`: Multi-service orchestration

### Configuration

- **Environment Variables** (backend/.env):
  - `OPENAI_API_KEY`: OpenAI API key for generation
  - `ANTHROPIC_API_KEY`: Anthropic API key for generation
  - `SECRET_KEY`: Flask session secret

- **MCP Configuration** (claude_desktop_config.json):
  - Output directory mapping for rendered images
  - Docker container arguments

### Error Handling

The codebase implements comprehensive error handling:
- Custom exceptions in `exceptions.py`
- Validation errors return detailed feedback
- Rendering failures include troubleshooting suggestions
- Async timeout handling for browser operations

## Development Patterns

### FastMCP Patterns (New in v2.0)

#### Tool Definition
```python
# Simple decorator-based tool definition
@mcp.tool(description="Validate and render Mermaid code")
async def validate_and_render_mermaid(
    code: str,
    fix_errors: bool = True,
    style: Dict[str, str] = None,
    format: str = "png"
) -> Dict[str, Any]:
    # Tool implementation
    pass
```

#### Prompt Definition
```python
# Decorator-based prompt templates
@mcp.prompt(description="Interactive wizard to create a flowchart")
async def flowchart_wizard(process_name: str = "Process") -> str:
    return PromptGenerator.get_flowchart_prompt(process_name)
```

#### Entry Points
```python
# Main entry points for different transports
def main_stdio():
    """Entry point for stdio transport (Claude Desktop)"""
    mcp.run()  # Default transport is stdio

def main_http():
    """Entry point for HTTP/SSE transport (Web clients)"""
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
```

### General Patterns

- **Async/Await**: All MCP server operations are async
- **Resource Management**: Playwright browser instances are managed with proper cleanup
- **Logging**: Structured logging throughout with configurable levels
- **Type Hints**: Extensive use of type annotations for better IDE support
- **Mock Support**: Fallback mocks for testing without MCP dependencies