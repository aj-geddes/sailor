"""Setup configuration for Sailor MCP - FastMCP version"""
from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Base requirements - Updated for FastMCP
install_requires = [
    # MCP Framework (replaced mcp-python with fastmcp)
    "fastmcp>=0.5.0",

    # Rendering dependencies (unchanged)
    "playwright>=1.40.0",

    # Async support
    "asyncio",

    # Optional HTTP transport support
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "httpx>=0.25.0",
    "sse-starlette>=2.0.0",
]

# Development requirements (unchanged)
dev_requires = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.10.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "coverage>=7.0.0",
]

setup(
    name="sailor-mcp",
    version="2.0.0",  # Bump major version for FastMCP migration
    author="Sailor Site Team",
    author_email="team@sailor-site.com",
    description="FastMCP-based server for generating and rendering Mermaid diagrams with AI assistance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sailor-site",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/sailor-site/issues",
        "Documentation": "https://github.com/yourusername/sailor-site/wiki",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",  # Updated from Beta
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "pytest-cov>=4.0.0",
        ],
        "http": [
            # Additional deps for HTTP transport
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
        ]
    },
    entry_points={
        "console_scripts": [
            # Simplified entry points with FastMCP
            "sailor-mcp=sailor_mcp.__main__:main",
            "sailor-mcp-http=sailor_mcp.server_fastmcp:run_http",  # HTTP server variant
        ],
    },
    include_package_data=True,
    package_data={
        "sailor_mcp": ["*.json", "*.md"],
    },
)