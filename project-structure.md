# Sailor - Project Structure

```
sailor/
├── src/                      # Core library code
│   └── sailor/
│       ├── __init__.py
│       ├── core/            # Core business logic
│       │   ├── __init__.py
│       │   ├── validator.py
│       │   ├── renderer.py
│       │   ├── parser.py
│       │   └── generator.py
│       ├── mcp/             # MCP server implementation
│       │   ├── __init__.py
│       │   ├── server.py
│       │   ├── tools.py
│       │   └── resources.py
│       └── api/             # REST API implementation
│           ├── __init__.py
│           ├── app.py
│           ├── routes.py
│           └── websocket.py
│
├── frontend/                # Svelte frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   ├── stores/
│   │   │   └── services/
│   │   ├── routes/
│   │   └── app.html
│   ├── static/
│   ├── package.json
│   └── vite.config.js
│
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/                  # Docker configurations
│   ├── Dockerfile.mcp
│   ├── Dockerfile.api
│   └── Dockerfile.frontend
│
├── docs/                    # Documentation
│   ├── api/
│   ├── architecture/
│   └── user-guide/
│
├── scripts/                 # Utility scripts
│   ├── setup.py
│   ├── lint.py
│   └── deploy.py
│
├── .github/                 # GitHub configurations
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── docker-compose.yml       # Full stack composition
├── pyproject.toml          # Python project config
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── LICENSE                # License file
```