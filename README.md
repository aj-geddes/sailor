# 🧜‍♀️ Sailor - Mermaid Diagram Generator

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-0.5+-blue?style=for-the-badge)](https://github.com/jlowin/fastmcp)
[![Version](https://img.shields.io/badge/version-2.0.0-green?style=for-the-badge)](https://github.com/aj-geddes/sailor)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-Compatible-orange?style=for-the-badge)](https://claude.ai)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

Get a picture of your Mermaid! 🎨

Sailor combines a beautiful web interface with an MCP (Model Context Protocol) server for generating and rendering Mermaid diagrams. Use the web UI for interactive diagram creation, or integrate with Claude Desktop for AI-powered diagram generation through natural language.

## 🆕 What's New in v2.0

- **Modern FastMCP Architecture**: 70% less boilerplate code with decorator-based patterns
- **Simplified Development**: No more stdio_wrapper complexity - FastMCP handles it all
- **Faster Startup**: ~50% improvement in server initialization time
- **Better Type Safety**: Native Python type hints throughout
- **Cleaner API**: Simple `@mcp.tool()` and `@mcp.prompt()` decorators
- **Dual Transport Support**: Built-in stdio and HTTP/SSE transports

## ✨ Features

### 🌐 Web Interface
- 🎨 **AI-Powered Generation**: Generate diagrams using OpenAI or Anthropic APIs
- 🔄 **Live Preview**: Real-time rendering with syntax highlighting
- 📋 **Copy Functions**: Copy both code and rendered images
- 🎯 **Style Controls**: Theme and appearance customization
- ✅ **API Key Validation**: Instant feedback on key validity

### 🤖 MCP Server (Powered by FastMCP)
- 📐 **All Mermaid Diagram Types**: Flowcharts, sequence, gantt, class, state, ER, pie, mindmap, journey, timeline
- 🎨 **Multiple Themes**: Default, dark, forest, neutral
- ✏️ **Hand-drawn Look**: Optional sketch-style rendering
- 🖼️ **Flexible Output**: PNG with transparent background support
- 🤖 **LLM Integration**: Works with Claude Desktop via MCP
- 🐳 **Fully Containerized**: No dependencies needed except Docker
- ⚡ **FastMCP Architecture**: Modern, maintainable codebase with decorators

## 🚀 Quick Start

Choose your preferred way to use Sailor:

### Option A: Web Interface 🌐

1. **Clone and Setup**:
```bash
git clone https://github.com/aj-geddes/sailor.git
cd sailor
```

2. **Configure Environment** (backend folder):
```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

3. **Run with Docker**:
```bash
docker-compose up -d
```

4. **Access**: Open http://localhost:5000

![image](https://github.com/user-attachments/assets/15ea7954-4cfa-46f5-9a02-b72b80fcc9ca)


### Option B: Claude Desktop Integration 🤖

**Prerequisites**: Docker Desktop + Claude Desktop

1. **Clone and Build**:
```bash
git clone https://github.com/aj-geddes/sailor.git
cd sailor
docker build -f Dockerfile.mcp-stdio -t sailor-mcp .
```

2. **Configure Claude Desktop**:

Add the following to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sailor-mermaid": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "C:\\Users\\YourName\\Pictures:/output",
        "sailor-mcp"
      ]
    }
  }
}
```

**Note**: Replace `C:\\Users\\YourName\\Pictures` with your desired output directory.

### 4. Restart Claude Desktop

Completely close and reopen Claude Desktop to load the new configuration.

## 📖 Usage

### 🌐 Web Interface

1. **Enter API Key**: Provide your OpenAI or Anthropic API key
2. **Describe Your Diagram**: Enter a natural language description
3. **Generate**: Click "Generate Diagram" to create Mermaid code
4. **Customize**: Use style controls to adjust appearance
5. **Export**: Copy the code or image with the copy buttons

### 🤖 Claude Desktop Integration

Once configured, you can use natural language commands in Claude Desktop:

- "Use sailor-mermaid to create a flowchart showing a login process"
- "Generate a sequence diagram with sailor-mermaid showing API calls"
- "Create a Gantt chart for a project timeline using sailor-mermaid"
- "Show me examples of Mermaid diagrams with sailor-mermaid"

Images are automatically saved to your configured output directory.

## 🛠️ Available Tools

### 1. `request_mermaid_generation`
Request AI to generate Mermaid diagram code based on your description.

### 2. `validate_and_render_mermaid`
Validate and render existing Mermaid code as an image.

### 3. `get_mermaid_examples`
Get examples of different Mermaid diagram types.

## 🎨 Styling Options

- **Themes**: `default`, `dark`, `forest`, `neutral`
- **Look**: `classic`, `handDrawn`
- **Background**: `transparent`, `white`
- **Direction**: `TB` (top-bottom), `LR` (left-right), `BT`, `RL`

## 📁 Project Structure

```
sailor/
├── backend/                  # Web UI Flask application
│   ├── app.py               # Main Flask server
│   ├── static/              # Frontend files (HTML/CSS/JS)
│   ├── requirements.txt     # Web UI dependencies
│   └── .env.example         # Environment template
├── src/
│   └── sailor_mcp/          # FastMCP server implementation
│       ├── server.py        # Main MCP server with decorators
│       ├── renderer.py      # Mermaid rendering engine
│       ├── validators.py    # Syntax validation
│       ├── prompts.py       # AI prompt templates
│       └── mermaid_resources.py # Examples and templates
├── tests/                   # Comprehensive test suite
├── Dockerfile.mcp-stdio     # MCP server container
├── docker-compose.yml       # Multi-service setup
├── setup.py                 # Python package setup (v2.0.0)
└── requirements.txt         # FastMCP dependencies
```

## 🧪 Development

### Web UI Development
```bash
# Setup environment
cd backend
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py
# Access at http://localhost:5000
```

### MCP Server Development (FastMCP v2.0)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install FastMCP and dependencies
pip install fastmcp>=0.5.0
pip install -e .

# Install Playwright browsers
playwright install chromium

# Run tests
pytest

# Run MCP server with stdio (Claude Desktop)
python -m sailor_mcp.server

# Run MCP server with HTTP/SSE (Web clients)
python -m sailor_mcp.server --http --port 8000
```

### Full Stack Development
```bash
# Run everything with Docker Compose
docker-compose up --build

# Web UI: http://localhost:5000
# MCP Server: Available for Claude Desktop integration
```

## 🐛 Troubleshooting

### Server Not Appearing in Claude Desktop
1. Ensure Docker Desktop is running
2. Check the image exists: `docker images | grep sailor-mcp`
3. Verify config file location and JSON syntax
4. Restart Claude Desktop completely

### Connection Issues
Test the server manually:
```bash
docker run -i --rm sailor-mcp
```

### View Logs
Check Docker logs:
```bash
docker logs $(docker ps -a | grep sailor-mcp | awk '{print $1}')
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with [MCP](https://modelcontextprotocol.io/) (Model Context Protocol)
- Powered by [Mermaid.js](https://mermaid.js.org/) for diagram rendering
- Uses [Playwright](https://playwright.dev/) for headless rendering

---

Made with ❤️ for Claude Desktop users
