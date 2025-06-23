# 🧜‍♀️ Sailor - Mermaid Diagram MCP Server

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-Compatible-orange?style=for-the-badge)](https://claude.ai)

Get a picture of your Mermaid! 🎨

Sailor is an MCP (Model Context Protocol) server that enables LLMs to generate and render Mermaid diagrams as images. It integrates seamlessly with Claude Desktop, allowing you to create flowcharts, sequence diagrams, and more through natural language.

## ✨ Features

- 📐 **All Mermaid Diagram Types**: Flowcharts, sequence, gantt, class, state, ER, pie, mindmap, journey, timeline
- 🎨 **Multiple Themes**: Default, dark, forest, neutral
- ✏️ **Hand-drawn Look**: Optional sketch-style rendering
- 🖼️ **Flexible Output**: PNG with transparent background support
- 🤖 **LLM Integration**: Works with Claude Desktop via MCP
- 🐳 **Fully Containerized**: No dependencies needed except Docker

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Claude Desktop application

### 1. Clone the Repository
```bash
git clone https://github.com/aj-geddes/sailor.git
cd sailor
```

### 2. Build the Docker Image
```bash
docker build -f Dockerfile.mcp-stdio -t sailor-mcp .
```

### 3. Configure Claude Desktop

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
├── Dockerfile.mcp-stdio      # Docker configuration
├── setup.py                  # Python package setup
├── requirements.txt          # Python dependencies
├── src/
│   └── sailor_mcp/
│       ├── __init__.py
│       ├── server.py         # Main MCP server
│       ├── stdio_wrapper.py  # Claude Desktop communication
│       ├── renderer.py       # Mermaid rendering engine
│       ├── validators.py     # Syntax validation
│       └── prompts.py        # AI prompt templates
└── tests/                    # Test suite
```

## 🧪 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium

# Run tests
pytest
```

### Running Without Docker
```bash
python -m sailor_mcp.stdio_wrapper
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