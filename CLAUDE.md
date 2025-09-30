# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Python package for **Microsoft Dynamics 365 Finance & Operations (D365 F&O)** that provides:

- **OData Client Library**: Full CRUD operations on D365 F&O data entities with async/await patterns
- **CLI Application**: Command-line interface for D365 F&O operations with hierarchical commands
- **MCP Server**: Production-ready Model Context Protocol server for AI assistant integration (34 tools, 12 resources)
- **Metadata Management V2**: Advanced caching and discovery system with SQLite FTS5 search
- **Label Operations V2**: Multilingual label retrieval with intelligent caching
- **Multi-tier Integration Testing**: Mock, sandbox, and live environment testing framework

## Development Environment

- **Package Manager**: `uv` for fast Python package management
- **Python Version**: >=3.13
- **Build Backend**: `setuptools` configured in pyproject.toml
- **Distribution**: PyPI.org as `d365fo-client`
- **Architecture**: Async/await throughout with comprehensive type hints

## Essential Commands

### Development Setup
```bash
# Initial setup
uv sync
make dev-setup  # or .\make.ps1 dev-setup on Windows

# Quick development check (format + lint + test)
make dev        # or .\make.ps1 dev on Windows
```

### Testing
```bash
# Unit tests
uv run pytest

# Integration tests (recommended - tests against real D365 environments)
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput

# Mock server tests (fast, no external dependencies)
.\tests\integration\integration-test-simple.ps1 test-mock

# Tests with coverage
uv run pytest --cov=d365fo_client --cov-report=html
```

### Code Quality
```bash
# Format code
uv run black .
uv run isort .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/

# All quality checks
make quality-check  # or .\make.ps1 quality-check
```

### Build and Publish
```bash
# Build package
uv build

# Publish to PyPI
uv publish
```

## Architecture Overview

### Core Package Structure
```
src/d365fo_client/
├── __init__.py              # Package exports and public API
├── main.py                  # CLI entry point (d365fo-client command)
├── cli.py                   # CLI command handlers with argparse
├── client.py                # Main FOClient class - primary API entry point
├── config.py                # Configuration management with FOClientConfig
├── auth.py                  # Azure AD authentication with default credentials
├── session.py               # HTTP session management with connection pooling
├── crud.py                  # CRUD operations with OData query support
├── query.py                 # OData query building with QueryOptions
├── metadata_api.py          # Metadata API client for D365 F&O metadata
├── metadata_v2/             # Enhanced metadata system V2
│   ├── cache_v2.py          # SQLite-based metadata cache with FTS5
│   ├── database_v2.py       # Database operations and schema management
│   ├── search_engine_v2.py  # Full-text search with advanced filtering
│   ├── sync_manager_v2.py   # Smart synchronization with session tracking
│   ├── sync_session_manager.py # Session-based sync progress tracking
│   └── version_detector.py  # Module-based version detection
├── labels.py                # Label operations with multilingual support
├── models.py                # Data models and type definitions
├── exceptions.py            # Custom exception classes
└── mcp/                     # Model Context Protocol server
    ├── main.py              # MCP server entry point (d365fo-mcp-server)
    ├── fastmcp_main.py      # FastMCP server entry point (d365fo-fastmcp-server)
    ├── server.py            # Core MCP server implementation
    ├── fastmcp_server.py    # FastMCP server implementation (recommended)
    ├── client_manager.py    # Connection pooling for D365 F&O clients
    ├── tools/               # 34 MCP tools across 7 functional categories
    ├── resources/           # 12 MCP resource types for discovery
    └── prompts/             # MCP prompt templates
```

### Key Classes and Components

#### Main Client (`client.py`)
- **FOClient**: Primary API entry point with async context manager support
- **create_client()**: Convenience function for quick client creation
- Integrates all subsystems: auth, metadata, CRUD, labels

#### Configuration (`config.py`)
- **FOClientConfig**: Comprehensive configuration management
- Supports Azure AD default credentials, service principals, and Key Vault
- Environment variable substitution and profile-based configuration

#### Metadata System V2 (`metadata_v2/`)
- **MetadataCacheV2**: SQLite-based cache with FTS5 full-text search
- **SmartSyncManagerV2**: Intelligent synchronization with session tracking
- **SyncSessionManager**: Progress tracking for long-running sync operations
- Cross-environment cache sharing with module-based version detection

#### MCP Server (`mcp/`)
- **Two implementations**: Traditional MCP SDK and modern FastMCP framework
- **34 comprehensive tools** covering connection, CRUD, metadata, labels, profiles, database analysis, and synchronization
- **12 resource types** for entity, metadata, environment, and query discovery
- Multi-transport support (stdio, HTTP, SSE) for web integration

## Integration Testing Framework

The project includes a sophisticated **three-tier integration testing system**:

### Test Levels
1. **Mock Server Tests** (`mock`) - Fast, isolated tests with simulated D365 API
2. **Sandbox Tests** (`sandbox`) - Default level, tests against real D365 test environments
3. **Live Tests** (`live`) - Production validation against live environments

### Running Integration Tests
```bash
# Primary method (PowerShell automation)
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput
.\tests\integration\integration-test-simple.ps1 test-mock
.\tests\integration\integration-test-simple.ps1 coverage

# Alternative (Direct Python execution)
python tests/integration/test_runner.py sandbox --verbose
```

### Test Configuration
Create `tests/integration/.env` from `.env.template`:
```bash
INTEGRATION_TEST_LEVEL=sandbox
D365FO_SANDBOX_BASE_URL=https://your-test-environment.dynamics.com
D365FO_CLIENT_ID=your-client-id
D365FO_CLIENT_SECRET=your-client-secret
D365FO_TENANT_ID=your-tenant-id
```

## Development Patterns

### Adding New Features
1. Create feature branch from `main`
2. Add tests first (TDD approach) in `tests/unit/`
3. Implement feature with proper type hints and async/await patterns
4. Add integration tests if feature interacts with D365 F&O APIs
5. Update documentation and ensure all quality checks pass
6. Run integration tests: `.\tests\integration\integration-test-simple.ps1 test-sandbox`

### CLI Development Guidelines
- Use `argparse` with subparsers for hierarchical commands
- Follow pattern: `d365fo-client [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]`
- Implement async command handlers in `CLIManager` class
- Support multiple output formats: JSON, table, CSV, YAML
- Use profile-based configuration in `~/.d365fo-client/config.yaml`

### MCP Server Development
- Add new tools in `src/d365fo_client/mcp/tools/`
- Add new resources in `src/d365fo_client/mcp/resources/`
- Register tools and resources in server configuration
- Follow MCP protocol specifications for tool and resource interfaces
- Test with both traditional MCP SDK and FastMCP implementations

## D365 F&O Specific Patterns

### Entity Operations
- Check `data_service_enabled` before OData operations
- Use `public_collection_name` for collection queries: `/data/{collection_name}`
- Use `public_entity_name` for single record access: `/data/{entity_name}(key)`
- Handle composite keys properly in URL construction

### Metadata Management
- Use V2 metadata system for enhanced performance and search capabilities
- Leverage SQLite FTS5 for full-text search across entities, actions, and enumerations
- Implement smart synchronization strategies based on environment changes

### Authentication
- Prefer Azure Default Credentials (`use_default_credentials=True`)
- Support service principal authentication for CI/CD scenarios
- Integrate with Azure Key Vault for secure credential storage

## Code Quality Standards

- **Formatting**: Black with 88-character line length
- **Import Sorting**: isort with Black compatibility
- **Linting**: Ruff for fast, comprehensive linting
- **Type Checking**: mypy with strict configuration
- **Test Coverage**: Maintain >90% coverage for core functionality
- **Documentation**: Google-style docstrings for all public APIs

## Common Development Workflows

### Before Committing
```bash
make dev  # Format, lint, type-check, and test
.\tests\integration\integration-test-simple.ps1 test-sandbox  # Integration tests
```

### Publishing Workflow
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
uv build
uv publish  # Requires PyPI API token
```

### Debugging Integration Tests
```bash
# Enable verbose logging
export D365FO_LOG_LEVEL="DEBUG"

# Run specific test categories
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput
```

## Entry Points and CLI Commands

### Python API Entry Points
```python
from d365fo_client import FOClient, FOClientConfig, create_client

# Main client
config = FOClientConfig(base_url="...", use_default_credentials=True)
async with FOClient(config) as client:
    # Your code here

# Convenience function
async with create_client("https://your-environment.dynamics.com") as client:
    # Your code here
```

### CLI Commands
```bash
# Main CLI (installed as d365fo-client)
d365fo-client entities list --pattern "customer"
d365fo-client metadata sync --force-refresh
d365fo-client version app

# MCP Servers (installed as separate commands)
d365fo-mcp-server           # Traditional MCP SDK
d365fo-fastmcp-server       # FastMCP implementation (recommended)
```

## Package Distribution

- **PyPI Package**: `d365fo-client`
- **Install Command**: `pip install d365fo-client` or `uv add d365fo-client`
- **Dependencies**: Includes MCP dependencies by default for AI assistant integration
- **Python Requirement**: >=3.13 for modern async/await and type hint support