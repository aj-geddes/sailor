---
layout: default
title: "Sailor Documentation"
description: "Get a picture of your Mermaid! 🎨"
---

# Welcome Aboard! 🧜‍♀️

Welcome to the **Sailor Documentation** - your comprehensive guide to navigating the Mermaid diagram generator. Whether you're setting up your first instance or managing a production deployment, we've got you covered.

## What is Sailor?

Sailor is a powerful Mermaid diagram generator that combines a beautiful web interface with an MCP (Model Context Protocol) server. It enables you to:

- 🎨 Generate diagrams using AI (OpenAI or Anthropic)
- 🔄 Render Mermaid diagrams in real-time
- 🤖 Integrate with Claude Desktop for natural language diagram creation
- ☁️ Connect to remote MCP servers - no local installation required
- 🐳 Deploy anywhere with Docker
- ⚡ Leverage FastMCP's modern architecture

```mermaid
graph LR
    A[User Request] --> B{Interface}
    B -->|Web UI| C[Flask Server]
    B -->|Claude Desktop| D[Local MCP]
    B -->|Claude Desktop| R[Remote MCP]
    C --> E[AI Generation]
    D --> E
    R --> E
    E --> F[Mermaid Renderer]
    F --> G[Beautiful Diagram]

    style A fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style B fill:#1e90ff,stroke:#003366,stroke-width:2px,color:#fff
    style R fill:#ff6b6b,stroke:#003366,stroke-width:2px,color:#fff
    style G fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
```

## 🗺️ Documentation Navigator

<div class="guide-card" markdown="1">

### 🚀 Setup Guide
**New to Sailor?** Start here for installation and initial configuration.

[Get Started →](setup-guide)

Topics covered:
- Prerequisites and system requirements
- Docker installation
- Web UI setup
- Claude Desktop integration
- First diagram generation

</div>

<div class="guide-card" markdown="1">

### 👨‍💼 Admin Guide
**Managing Sailor?** Configuration, security, and user management.

[Learn More →](admin-guide)

Topics covered:
- Configuration management
- API key management
- Security best practices
- Multi-user setups
- Environment variables

</div>

<div class="guide-card" markdown="1">

### ⚙️ Operations Guide
**Running in production?** Deployment, monitoring, and maintenance.

[Explore →](operations-guide)

Topics covered:
- Production deployment
- Docker orchestration
- Health monitoring
- Backup and recovery
- Performance tuning
- Update procedures

</div>

<div class="guide-card" markdown="1">

### 🔧 Troubleshooting Guide
**Having issues?** Common problems and solutions.

[Get Help →](troubleshooting-guide)

Topics covered:
- Common error messages
- Docker issues
- Rendering problems
- API connectivity
- Performance issues
- Debug procedures

</div>

## 🎯 Quick Links

| Resource | Description |
|----------|-------------|
| [GitHub Repository](https://github.com/aj-geddes/sailor) | Source code and issue tracking |
| [Main README](https://github.com/aj-geddes/sailor/blob/main/README.md) | Project overview and quick start |
| [Docker Guide](DOCKER.html) | Docker-specific documentation |
| [Production Guide](PRODUCTION.html) | Production deployment checklist |

## 🆕 Version 2.0 Highlights

Sailor v2.0 brings major improvements with the FastMCP migration:

```mermaid
graph TB
    subgraph "v1.x Architecture"
        A1[Manual MCP] --> B1[stdio_wrapper]
        B1 --> C1[Complex Setup]
    end

    subgraph "v2.0 Architecture"
        A2[FastMCP] --> B2[Native Transports]
        B2 --> C2[Simple Setup]
    end

    C1 -.->|Migration| A2

    style A2 fill:#20b2aa,stroke:#003366,stroke-width:3px,color:#fff
    style B2 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
    style C2 fill:#20b2aa,stroke:#003366,stroke-width:2px,color:#fff
```

**Key improvements:**
- ✨ 70% less boilerplate code
- 🚀 50% faster startup time
- 🎯 Decorator-based tools and prompts
- 🔄 Built-in stdio and HTTP/SSE support
- 🛡️ Better type safety with native Python hints

## 📊 System Architecture

```mermaid
C4Context
    title Sailor System Architecture

    Person(user, "User", "Creates diagrams")
    Person(claude_user, "Claude User", "Uses AI assistance")

    System_Boundary(sailor, "Sailor System") {
        Container(web, "Web Interface", "Flask", "Interactive UI")
        Container(mcp, "MCP Server", "FastMCP", "AI Integration")
        Container(renderer, "Renderer", "Playwright", "Diagram Engine")
    }

    System_Ext(openai, "OpenAI API", "GPT models")
    System_Ext(anthropic, "Anthropic API", "Claude models")
    System_Ext(claude_desktop, "Claude Desktop", "MCP client")

    Rel(user, web, "Uses", "HTTPS")
    Rel(claude_user, claude_desktop, "Uses")
    Rel(claude_desktop, mcp, "Connects via", "MCP Protocol")
    Rel(web, openai, "Calls")
    Rel(web, anthropic, "Calls")
    Rel(web, renderer, "Renders")
    Rel(mcp, renderer, "Renders")
```

## 🌊 Next Steps

1. **First Time Setup**: Head to the [Setup Guide](setup-guide) to get Sailor running
2. **Configuration**: Check the [Admin Guide](admin-guide) for detailed configuration
3. **Production Ready**: Follow the [Operations Guide](operations-guide) for deployment
4. **Need Help?** Visit the [Troubleshooting Guide](troubleshooting-guide)

---

<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #0066cc 0%, #1e90ff 100%); border-radius: 8px; color: white; margin: 2rem 0;">
  <h2 style="color: white; border: none; margin-bottom: 1rem;">⚓ Ready to Set Sail?</h2>
  <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">Start your journey with Sailor today!</p>
  <a href="setup-guide" style="display: inline-block; background: white; color: #0066cc; padding: 0.75rem 2rem; border-radius: 4px; text-decoration: none; font-weight: bold; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
    Begin Setup →
  </a>
</div>

---

**Questions or feedback?** [Open an issue](https://github.com/aj-geddes/sailor/issues) on GitHub!
