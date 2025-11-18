---
layout: default
title: "Setup Guide"
description: "Complete installation and setup instructions for Sailor"
---

# Setup Guide 🚀

This guide will help you install and configure Sailor for your first use. Follow these steps to get your Mermaid diagram generator up and running.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Web Interface Setup](#web-interface-setup)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Verification](#verification)
- [First Diagram](#first-diagram)
- [Next Steps](#next-steps)

---

## Prerequisites

Before installing Sailor, ensure you have the following:

### System Requirements

```mermaid
graph TD
    A[System Requirements] --> B[Docker Desktop]
    A --> C[Operating System]
    A --> D[Resources]
    A --> E[Optional]

    B --> B1[Version 20.10+]
    C --> C1[Windows 10/11]
    C --> C2[macOS 11+]
    C --> C3[Linux Kernel 4+]
    D --> D1[2GB RAM minimum]
    D --> D2[4GB RAM recommended]
    D --> D3[1GB disk space]
    E --> E1[Claude Desktop]
    E --> E2[AI API Keys]

    style A fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style B fill:#1e90ff,stroke:#003366,stroke-width:2px,color:#fff
    style E fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
```

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Docker Desktop** | 20.10+ | Container runtime |
| **Docker Compose** | 2.0+ | Multi-container orchestration |
| **Git** | 2.0+ | Source code management |

### Optional Components

| Component | Purpose |
|-----------|---------|
| **Claude Desktop** | MCP integration for AI-powered diagram generation |
| **OpenAI API Key** | GPT-powered diagram generation in Web UI |
| **Anthropic API Key** | Claude-powered diagram generation in Web UI |

> **Note**: API keys are optional but required for AI-powered diagram generation. You can still use Sailor to render existing Mermaid code without them.

---

## Installation Methods

Sailor can be deployed in two primary modes:

```mermaid
graph LR
    A[Choose Deployment] --> B[Web Interface Only]
    A --> C[Claude Desktop Integration]
    A --> D[Both]

    B --> E[docker-compose up]
    C --> F[Docker build + Claude config]
    D --> G[Full deployment]

    E --> H[Access via Browser]
    F --> I[Use via Claude Desktop]
    G --> J[Both interfaces available]

    style A fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style B fill:#1e90ff,stroke:#003366,stroke-width:2px,color:#fff
    style C fill:#1e90ff,stroke:#003366,stroke-width:2px,color:#fff
    style D fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
```

---

## Web Interface Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/aj-geddes/sailor.git
cd sailor
```

### Step 2: Configure Environment

Create the environment file in the `backend` directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your preferred editor:

```bash
# .env configuration
SECRET_KEY=your-secret-key-here-change-this
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional settings
FLASK_ENV=production
FLASK_DEBUG=0
```

> **Security Note**: Generate a strong SECRET_KEY using:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### Step 3: Launch with Docker Compose

From the project root directory:

```bash
docker-compose up -d
```

This command will:
1. Build the Flask web application container
2. Start the service on port 5000
3. Set up networking between services

### Step 4: Verify Web Interface

Open your browser and navigate to:

```
http://localhost:5000
```

You should see the Sailor web interface:

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Flask
    participant Renderer

    User->>Browser: Open localhost:5000
    Browser->>Flask: HTTP GET /
    Flask->>Browser: Return HTML
    Browser->>User: Display Interface

    User->>Browser: Enter diagram description
    Browser->>Flask: POST /generate
    Flask->>Renderer: Render Mermaid
    Renderer->>Flask: Return PNG
    Flask->>Browser: Display diagram
    Browser->>User: Show result

    Note over User,Renderer: Web Interface Flow
```

---

## Claude Desktop Integration

### Step 1: Build the MCP Docker Image

```bash
cd sailor
docker build -f Dockerfile.mcp-stdio -t sailor-mcp .
```

Verify the image was created:

```bash
docker images | grep sailor-mcp
```

### Step 2: Locate Claude Desktop Config

Find your Claude Desktop configuration file:

| Operating System | Configuration Path |
|-----------------|-------------------|
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

### Step 3: Configure MCP Server

Edit the configuration file and add the Sailor MCP server:

**Windows Example:**
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

**macOS/Linux Example:**
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
        "/Users/yourname/Pictures:/output",
        "sailor-mcp"
      ]
    }
  }
}
```

> **Important**: Replace the volume path with your desired output directory for generated diagrams.

### Step 4: Restart Claude Desktop

Completely close and restart Claude Desktop to load the new MCP server configuration.

### Step 5: Verify MCP Connection

The MCP integration flow:

```mermaid
sequenceDiagram
    participant User
    participant Claude Desktop
    participant Docker
    participant MCP Server
    participant Renderer

    User->>Claude Desktop: Request diagram
    Claude Desktop->>Docker: Start container
    Docker->>MCP Server: Initialize
    MCP Server->>Claude Desktop: Ready

    Claude Desktop->>MCP Server: Call tool
    MCP Server->>Renderer: Render diagram
    Renderer->>MCP Server: Return PNG
    MCP Server->>Docker: Write to /output
    Docker->>User: Save to local directory

    Note over User,Renderer: Claude Desktop Integration Flow
```

In Claude Desktop, try:
```
Use sailor-mermaid to create a simple flowchart showing a login process
```

---

## Verification

### Health Check Commands

Verify your installation with these commands:

```bash
# Check Docker containers
docker ps

# Check web interface
curl -I http://localhost:5000

# Check MCP image
docker images | grep sailor-mcp

# View logs
docker-compose logs -f
```

### Expected Results

```mermaid
graph TD
    A[Health Checks] --> B{Web Interface}
    A --> C{MCP Server}

    B -->|Port 5000| B1[✅ Running]
    B -->|Logs| B2[✅ No errors]
    B -->|Browser| B3[✅ Accessible]

    C -->|Image| C1[✅ Built]
    C -->|Claude| C2[✅ Connected]
    C -->|Output| C3[✅ Directory mounted]

    style A fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style B1 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
    style B2 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
    style B3 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
    style C1 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
    style C2 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
    style C3 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
```

---

## First Diagram

### Via Web Interface

1. Open `http://localhost:5000`
2. Enter an API key (OpenAI or Anthropic)
3. Describe your diagram: "Create a flowchart showing user authentication"
4. Click "Generate Diagram"
5. View and download your diagram!

### Via Claude Desktop

In Claude Desktop, use natural language:

```
Use sailor-mermaid to create a sequence diagram showing
a REST API call with request, processing, and response
```

Claude will:
1. Generate Mermaid code based on your description
2. Validate the syntax
3. Render the diagram
4. Save it to your configured output directory

---

## Next Steps

Now that Sailor is installed, explore these guides:

<div class="guide-card">

### 👨‍💼 Admin Guide
Learn about configuration, security, and API key management.

[Configure Sailor →](admin-guide)

</div>

<div class="guide-card">

### ⚙️ Operations Guide
Deploy to production with Docker, monitoring, and maintenance.

[Deploy to Production →](operations-guide)

</div>

<div class="guide-card">

### 🔧 Troubleshooting
Having issues? Find solutions to common problems.

[Get Help →](troubleshooting-guide)

</div>

---

## Quick Reference

### Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up -d --build

# Check status
docker-compose ps
```

### Port Reference

| Service | Port | Access |
|---------|------|--------|
| Web Interface | 5000 | http://localhost:5000 |
| MCP Server | stdio | Via Claude Desktop |

### Configuration Files

| File | Purpose |
|------|---------|
| `backend/.env` | Environment variables and API keys |
| `docker-compose.yml` | Service orchestration |
| `claude_desktop_config.json` | Claude Desktop MCP configuration |

---

<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #0066cc 0%, #1e90ff 100%); border-radius: 8px; color: white;">
  <h2 style="color: white; border: none;">🎉 Setup Complete!</h2>
  <p>Your Sailor instance is ready to generate beautiful diagrams.</p>
</div>

---

[← Back to Home](index) | [Admin Guide →](admin-guide)
