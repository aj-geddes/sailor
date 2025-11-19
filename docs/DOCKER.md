# Docker Deployment Guide - Sailor MCP v2.0

## Overview

Sailor MCP v2.0 has been fully migrated to FastMCP with optimized Docker configurations for production deployment.

## Docker Images

### 1. STDIO Container (`sailor-mcp:2.0`)
- **Purpose**: Claude Desktop integration via stdio transport
- **Size**: 1.57GB
- **Base**: Python 3.11-slim with Playwright
- **Security**: Non-root user (`sailor`)
- **Entry Point**: `sailor-mcp` (FastMCP stdio)

### 2. HTTP/SSE Container (`sailor-mcp-http:2.0`)
- **Purpose**: Web server with SSE transport
- **Size**: 1.57GB
- **Base**: Python 3.11-slim with Playwright
- **Security**: Non-root user (`sailor`)
- **Port**: 8000 (configurable)
- **Entry Point**: `sailor-mcp-http` (FastMCP HTTP/SSE)

### 3. Backend Container (`sailor-backend:2.0`)
- **Purpose**: Flask web UI
- **Size**: 386MB
- **Base**: Python 3.11-slim
- **Security**: Non-root user (`flask`)
- **Port**: 5000
- **Server**: Gunicorn (production) or Flask dev server

## Quick Start

### Build Images

```bash
# Build all images
docker-compose build

# Or build individually
docker build -f Dockerfile.mcp-stdio -t sailor-mcp:2.0 .
docker build -f Dockerfile.mcp-http -t sailor-mcp-http:2.0 .
cd backend && docker build -t sailor-backend:2.0 .
```

### Run with Docker Compose

```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Run Individual Containers

```bash
# STDIO (for Claude Desktop)
docker run -i --rm \
  -v ./output:/home/sailor/output \
  sailor-mcp:2.0

# HTTP Server
docker run -d \
  -p 8000:8000 \
  -v ./output:/home/sailor/output \
  sailor-mcp-http:2.0

# Backend Web UI
docker run -d \
  -p 5000:5000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  sailor-backend:2.0
```

## Configuration

### Environment Variables

```bash
# MCP Server
SAILOR_LOG_LEVEL=INFO         # Logging level
MCP_PORT=8000                  # HTTP server port

# Backend
FLASK_ENV=production           # Flask environment
SECRET_KEY=your-secret-key    # Flask session secret
OPENAI_API_KEY=sk-...         # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...  # Anthropic API key
MCP_SERVER_URL=http://mcp:8000 # MCP server URL
```

### Volume Mounts

- `/home/sailor/output`: Rendered diagram output directory
- `/app`: Application code (read-only in production)

## Claude Desktop Integration

### Using Docker Container

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sailor": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/path/to/output:/home/sailor/output",
        "sailor-mcp:2.0"
      ]
    }
  }
}
```

## Production Deployment

### Using docker-compose.prod.yml

Features:
- Load balancing with multiple replicas
- Resource limits and reservations
- Health checks with auto-restart
- Nginx reverse proxy support
- Persistent volumes

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale mcp=3 --scale backend=2

# Monitor health
docker-compose -f docker-compose.prod.yml ps

# View resource usage
docker stats
```

### Security Features

1. **Non-root Users**: All containers run as non-privileged users
2. **Read-only Filesystems**: Application code mounted read-only in production
3. **Resource Limits**: CPU and memory constraints configured
4. **Health Checks**: Automatic container health monitoring
5. **Network Isolation**: Services communicate over internal network

## Optimization Results

### Build Performance
- **Multi-stage builds**: Reduced image size by ~30%
- **Layer caching**: Subsequent builds complete in 2-3 seconds
- **Optimized dependencies**: Only production packages installed

### Runtime Performance
- **FastMCP 2.0**: Lower overhead, faster startup
- **Uvicorn ASGI**: High-performance async server
- **Gunicorn**: Multi-worker production server for Flask

### Image Sizes
- **Before**: ~2.1GB (monolithic builds)
- **After**: 1.57GB (optimized multi-stage)
- **Backend**: 386MB (minimal Flask container)

## Health Checks

All containers include health checks:

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Manual health check
docker exec sailor_mcp_1 python -c "import socket; s=socket.socket(); s.connect(('localhost', 8000)); s.close()"
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs container_name

# Inspect container
docker inspect container_name

# Run interactive debug
docker run -it --rm --entrypoint /bin/bash sailor-mcp:2.0
```

### Port conflicts
```bash
# Check port usage
netstat -tulpn | grep :8000

# Use alternative ports
docker run -p 8001:8000 sailor-mcp-http:2.0
```

### Permission issues
```bash
# Fix output directory permissions
chmod 777 ./output

# Or run with user mapping
docker run --user $(id -u):$(id -g) ...
```

## Metrics Script

Run the metrics script to verify everything is working:

```bash
./scripts/docker-build-metrics.sh
```

This will:
- Build all images with timing
- Report image sizes
- Test container health
- Verify FastMCP integration

## Migration Notes

### Changes from v1.x to v2.0
1. **Entry Points**: Updated to use FastMCP commands
   - Old: `python -m sailor_mcp.stdio_wrapper`
   - New: `sailor-mcp` (stdio) or `sailor-mcp-http` (HTTP)

2. **Dependencies**: Simplified with FastMCP
   - Removed: Manual MCP implementation
   - Added: `fastmcp>=0.5.0` with SSE support

3. **Health Checks**: Updated for FastMCP endpoints
   - Uses socket connection test instead of HTTP endpoints
   - More reliable for SSE connections

4. **Security**: Enhanced with non-root users
   - All containers run as unprivileged users
   - Follows Docker security best practices

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Run health checks: `docker-compose ps`
- Verify metrics: `./scripts/docker-build-metrics.sh`
- Review configuration: Environment variables and volumes