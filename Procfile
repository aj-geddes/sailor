# Procfile for Railway deployment
# Railway will use this if no Dockerfile is specified, or as a reference
# Uses Streamable HTTP transport for remote MCP server

web: python -m sailor_mcp.server --http --host 0.0.0.0 --port $PORT --transport streamable-http
