# Sailor Documentation

This directory contains comprehensive documentation for the Sailor Mermaid diagram generator.

## Architecture Overview

![Sailor Architecture](images/sailor-architecture.png)

Sailor provides **11 tools**, **11 prompts**, and a comprehensive resource library for Mermaid diagram generation.

## Documentation Structure

### Main Documentation
- **[DOCKER.md](DOCKER.md)** - Docker deployment guide, container configuration, and best practices
- **[PRODUCTION.md](PRODUCTION.md)** - Production deployment checklist, security hardening, and monitoring setup
- **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** - Deploy Sailor as a remote MCP server on Railway

### Archive
Documentation from previous development phases is archived for reference:

- **[archive/QA_ASSESSMENT_REPORT.md](archive/QA_ASSESSMENT_REPORT.md)** - Comprehensive security and quality assessment
- **[archive/migration/](archive/migration/)** - FastMCP migration documentation
  - `FASTMCP_MIGRATION.md` - Migration guide
  - `FASTMCP_MIGRATION_PLAN.md` - Detailed migration plan
  - `FASTMCP_MIGRATION_REPORT.md` - Migration completion report
  - `MIGRATION.md` - General migration overview
  - `MIGRATION_SUMMARY.md` - Summary of changes

## Quick Links

### Getting Started
See the main [README.md](../README.md) in the project root for:
- Installation instructions
- Quick start guide
- Usage examples

### Development
See [CLAUDE.md](../CLAUDE.md) in the project root for:
- Development commands
- Testing instructions
- Architecture overview
- Code patterns

### Deployment
- **Docker**: See [DOCKER.md](DOCKER.md)
- **Production**: See [PRODUCTION.md](PRODUCTION.md)

## Contributing

When adding new documentation:
1. Place active documentation in this `docs/` directory
2. Archive outdated or historical documentation in `docs/archive/`
3. Update this README with links to new documentation
4. Keep the main README.md focused on user-facing information
