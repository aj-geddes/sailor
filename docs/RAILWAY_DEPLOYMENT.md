# Railway Deployment Guide for Sailor MCP Server

This guide explains how to deploy the Sailor MCP Server as a remote/public MCP server on Railway.

## Overview

Sailor MCP Server can be deployed as a remote MCP server using **Streamable HTTP transport**. This enables:

- **Remote Access**: Use the MCP server from anywhere without local installation
- **Shared Service**: Multiple clients can use the same server instance
- **Always On**: Server runs 24/7 without requiring local resources

## Quick Deploy

### Option 1: Deploy from GitHub

1. **Fork or connect your repo** to Railway
2. **Create a new project** in Railway
3. **Add a new service** from your GitHub repo
4. Railway will auto-detect the `railway.toml` or `Dockerfile.railway`
5. **Set environment variables** (optional, defaults are provided):
   ```
   SAILOR_LOG_LEVEL=INFO
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_RENDER=20
   ```
6. **Deploy** - Railway will build and deploy automatically

### Option 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (in sailor directory)
railway init

# Deploy
railway up
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | (set by Railway) | Server port - Railway sets this automatically |
| `HOST` | `0.0.0.0` | Server host |
| `SAILOR_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per client per minute |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `RATE_LIMIT_RENDER` | `20` | Max render requests per client per minute |
| `MCP_TRANSPORT` | `http` | Transport type (http for Railway) |

### Rate Limiting

The server includes built-in rate limiting to prevent abuse:

- **General requests**: 100 per minute per client (configurable)
- **Render requests**: 20 per minute per client (rendering is resource-intensive)

Rate limits are applied per client ID. If no client ID is provided, requests use a default bucket.

## Transport Types

| Deployment | Transport | Use Case |
|------------|-----------|----------|
| **Railway (Remote)** | Streamable HTTP | Public MCP server, HTTP-based clients |
| **Local (Claude Desktop)** | stdio | Direct integration with Claude Desktop |
| **Local (Development)** | SSE | Local testing with web clients |

**Railway uses Streamable HTTP exclusively** - this is the standard HTTP-based MCP transport that works well with load balancers, proxies, and serverless environments.

## Connecting to the Remote Server

Once deployed, Railway will provide a URL like:
```
https://sailor-mcp-production-xxxx.up.railway.app
```

### Claude Desktop Configuration

Add to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sailor-remote": {
      "transport": {
        "type": "streamable-http",
        "url": "https://your-railway-url.up.railway.app/mcp"
      }
    }
  }
}
```

### Programmatic Access

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def connect_to_sailor():
    async with streamablehttp_client("https://your-railway-url.up.railway.app/mcp") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Use a tool
            result = await session.call_tool(
                "validate_and_render_mermaid",
                arguments={
                    "code": "graph TD\n    A[Start] --> B[End]",
                    "client_id": "my-app"
                }
            )
            print(result)
```

## Available Tools

The remote server exposes these MCP tools:

| Tool | Description |
|------|-------------|
| `health_check` | Server health and metrics |
| `server_status` | Detailed server status |
| `request_mermaid_generation` | Request diagram generation |
| `validate_and_render_mermaid` | Validate and render Mermaid code |
| `get_mermaid_examples` | Get example diagrams |
| `get_diagram_template` | Get customizable templates |
| `get_syntax_help` | Get syntax reference |
| `analyze_diagram_code` | Analyze existing code |
| `suggest_diagram_improvements` | Get improvement suggestions |

## Monitoring

### Health Check

The server provides a health check tool that returns:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "metrics": {
    "total_requests": 1250,
    "successful_renders": 890,
    "failed_renders": 12,
    "rate_limited": 5
  },
  "rate_limiter": {
    "active_clients": 15,
    "total_requests_in_window": 230
  }
}
```

### Logs

View logs in Railway dashboard or via CLI:

```bash
railway logs
```

## Scaling

Railway automatically handles scaling based on your plan. For high traffic:

1. **Increase rate limits** if needed
2. **Monitor metrics** via the `health_check` tool
3. **Upgrade Railway plan** for more resources

## Troubleshooting

### Server Not Starting

1. Check logs: `railway logs`
2. Verify `PORT` environment variable is being used
3. Ensure Playwright dependencies are installed (handled in Dockerfile)

### Rate Limit Errors

If clients receive rate limit errors:

1. Increase `RATE_LIMIT_REQUESTS` or `RATE_LIMIT_RENDER`
2. Implement client-side retry with backoff
3. Ensure clients pass unique `client_id` values

### Rendering Failures

Playwright requires specific system dependencies. The `Dockerfile.railway` includes all necessary dependencies. If rendering fails:

1. Check memory limits (Playwright needs ~512MB minimum)
2. Verify Chromium is installed correctly
3. Check for timeout issues (default 30s)

## Security Considerations

- **No Authentication**: The server is public by default
- **Rate Limiting**: Protects against abuse
- **HTTPS**: Railway provides automatic HTTPS
- **No Secrets**: Don't pass sensitive data through the MCP server

For private deployments, consider:
- Using Railway's private networking
- Adding API key authentication (modify `server.py`)
- Using a VPN or private network

## Cost Estimation

Railway pricing depends on usage:

- **Hobby Plan**: $5/month, suitable for light usage
- **Pro Plan**: Pay-as-you-go, scales automatically

Typical resource usage:
- Memory: 512MB - 1GB (due to Playwright/Chromium)
- CPU: Low unless rendering frequently
- Bandwidth: Varies with image output size

## Support

- **Issues**: [GitHub Issues](https://github.com/aj-geddes/sailor/issues)
- **Railway Docs**: [Railway Documentation](https://docs.railway.app)
- **MCP Protocol**: [MCP Specification](https://modelcontextprotocol.io)
