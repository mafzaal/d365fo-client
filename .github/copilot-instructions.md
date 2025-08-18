# Copilot Instructions for d365fo-client Python Package

## Project Overview
This is a comprehensive Python package for **Microsoft Dynamics 365 Finance & Operations (D365 F&O)** that provides:

- **OData Client Library**: Full CRUD operations on D365 F&O data entities
- **CLI Application**: Command-line interface for D365 F&O operations  
- **MCP Server**: Model Context Protocol server for AI assistant integration
- **Metadata Management**: Advanced caching and discovery of D365 F&O entities/actions
- **Label Operations**: Multilingual label retrieval and management

## Development Environment
- **Package Manager**: `uv` (for fast Python package management)
- **Python Version**: >=3.13  
- **Build Backend**: `setuptools` (configured in pyproject.toml)
- **Distribution**: PyPI.org
- **Architecture**: Async/await throughout, type-safe with comprehensive hints



## Project Structure Guidelines

### Current Architecture
```
d365fo-client/
├── src/d365fo_client/           # Main package source
│   ├── __init__.py              # Package exports and public API
│   ├── main.py                  # CLI entry point
│   ├── cli.py                   # CLI command handlers
│   ├── client.py                # Core D365FO client
│   ├── config.py                # Configuration management
│   ├── auth.py                  # Azure AD authentication
│   ├── session.py               # HTTP session management
│   ├── crud.py                  # CRUD operations
│   ├── query.py                 # OData query building
│   ├── metadata.py              # Metadata operations
│   ├── metadata_api.py          # Metadata API client
│   ├── metadata_cache.py        # Metadata caching layer
│   ├── metadata_sync.py         # Metadata synchronization
│   ├── labels.py                # Label operations
│   ├── profiles.py              # Profile data models
│   ├── profile_manager.py       # Profile management
│   ├── models.py                # Data models and types
│   ├── output.py                # Output formatting
│   ├── utils.py                 # Utility functions
│   ├── exceptions.py            # Custom exceptions
│   └── mcp/                     # Model Context Protocol server
│       ├── __init__.py          # MCP package exports
│       ├── main.py              # MCP server entry point
│       ├── server.py            # Core MCP server implementation
│       ├── client_manager.py    # D365FO client connection pooling
│       ├── models.py            # MCP-specific data models
│       ├── tools/               # MCP tool handlers (12 tools)
│       │   ├── connection_tools.py # Connection testing tools
│       │   ├── crud_tools.py    # CRUD operation tools
│       │   ├── metadata_tools.py# Metadata discovery tools
│       │   └── label_tools.py   # Label retrieval tools
│       ├── resources/           # MCP resource handlers (4 types)
│       │   ├── entity_handler.py    # Entity resource handler
│       │   ├── metadata_handler.py  # Metadata resource handler
│       │   ├── environment_handler.py # Environment resource handler
│       │   └── query_handler.py     # Query resource handler
│       └── prompts/             # MCP prompt templates
├── tests/                       # Comprehensive test suite
│   ├── unit/                    # Unit tests (pytest-based)
│   ├── integration/             # Multi-tier integration testing
│   │   ├── mock_server/         # Mock D365 F&O API server
│   │   ├── test_mock_server.py  # Mock server tests
│   │   ├── test_sandbox.py      # Sandbox environment tests ✅
│   │   ├── test_live.py         # Live environment tests
│   │   ├── conftest.py          # Shared pytest fixtures
│   │   ├── test_runner.py       # Python test execution engine
│   │   └── integration-test-simple.ps1 # PowerShell automation
│   └── test_mcp_server.py       # MCP server unit tests
├── docs/                        # Comprehensive documentation
├── examples/                    # Usage examples and demos
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lock file
├── Makefile                     # Unix make commands
├── make.bat                     # Windows batch commands
├── make.ps1                     # PowerShell make commands
├── README.md                    # Project documentation
├── CHANGELOG.md                 # Release notes
└── LICENSE                      # MIT license
```

### Package Entry Points
- **CLI**: `d365fo-client` command (via `d365fo_client.main:main`)
- **MCP Server**: `d365fo-mcp-server` command (via `d365fo_client.mcp.main:main`)
- **Python API**: `from d365fo_client import D365FOClient, FOClientConfig`

## Key Development Practices

### 1. Package Management with uv
- Use `uv add <package>` to add dependencies  
- Use `uv add --group dev <package>` for development dependencies (new syntax)
- Use `uv sync` to install dependencies from lockfile
- Use `uv run <command>` to run commands in the project environment
- Use `uv build` to build distribution packages
- Use `uv publish` to publish to PyPI

### 2. Build System and Make Commands
The project includes three make implementations for cross-platform development:

#### Quick Commands (choose your platform):
```bash
# Unix/Linux/macOS
make dev-setup         # Initial setup
make dev               # Quick dev check (format + lint + test)
make quality-check     # Comprehensive quality checks

# Windows Command Prompt  
make.bat dev-setup
make.bat dev
make.bat quality-check

# Windows PowerShell (recommended)
.\make.ps1 dev-setup
.\make.ps1 dev
.\make.ps1 quality-check
```

#### Available Make Targets:
- `dev-setup` - Set up development environment
- `dev` - Quick development check (format + lint + test)  
- `quality-check` - Run all code quality checks
- `test` - Run unit tests
- `test-coverage` - Run tests with coverage report
- `format` - Format code with black and isort
- `lint` - Run linting with ruff
- `type-check` - Run type checking with mypy
- `build` - Build distribution packages
- `publish-test` - Publish to Test PyPI
- `publish` - Publish to PyPI
- `clean` - Clean build artifacts
- `security-check` - Run security checks
- `info` - Show environment information

### 3. Code Organization
- Place all source code in `src/d365fo_client/` directory
- Use proper `__init__.py` files for package initialization
- Export main functionality through `__init__.py`
- Follow PEP 8 style guidelines
- Use type hints for all functions and methods

### 4. Dependencies and Requirements
- Add all runtime dependencies to `pyproject.toml` under `[project]` dependencies
- Add development dependencies using `uv add --group dev`
- Pin exact versions for reproducible builds
- Keep dependencies minimal and well-justified

### 5. Testing Framework

#### Unit Testing
- Use `pytest` as the testing framework
- Place unit tests in `tests/` directory
- Name test files with `test_` prefix
- Aim for high test coverage (>90%)
- Run tests with `uv run pytest`

#### Integration Testing
This project includes a comprehensive **multi-tier integration testing framework** that validates the d365fo-client against real and simulated D365 Finance & Operations environments.

**Integration Test Architecture:**
```
tests/integration/
├── __init__.py                      # Test level configuration (default: sandbox)
├── conftest.py                      # Shared pytest fixtures
├── test_runner.py                   # Python test execution engine
├── integration-test-simple.ps1     # PowerShell automation wrapper
├── .env / .env.template            # Environment configuration
├── README.md                       # Comprehensive testing documentation
│
├── mock_server/                    # Mock D365 F&O API server
│   ├── __init__.py
│   └── server.py                   # Complete API simulation (400+ lines)
│
├── test_mock_server.py            # Mock server tests
├── test_sandbox.py                # Sandbox environment tests ✅ (17/17 passing)
└── test_live.py                   # Live environment tests (future)
```

**Three-Tier Testing Strategy:**

1. **Mock Server Tests** (`mock`) - Fast, isolated testing
   - Local aiohttp server simulating D365 F&O API
   - No external dependencies
   - Complete OData endpoint simulation
   - Ideal for CI/CD pipelines

2. **Sandbox Tests** (`sandbox`) ⭐ **DEFAULT** - Realistic validation  
   - Tests against real D365 F&O test environments
   - Azure AD authentication integration
   - Real API behavior validation
   - **Status: 17/17 tests passing** ✅

3. **Live Tests** (`live`) - Production validation
   - Optional tests against production environments
   - Performance benchmarking
   - Final deployment validation

**Running Integration Tests:**

```powershell
# Primary method - PowerShell automation (Windows)
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput
.\tests\integration\integration-test-simple.ps1 test-mock
.\tests\integration\integration-test-simple.ps1 coverage

# Alternative - Direct Python execution
python tests/integration/test_runner.py sandbox --verbose
python tests/integration/test_runner.py mock --coverage
```

**Environment Configuration:**

Integration tests use environment variables configured in `.env` file:
```bash
# Default configuration (copy from .env.template)
INTEGRATION_TEST_LEVEL=sandbox
D365FO_SANDBOX_BASE_URL=https://your-test-environment.dynamics.com
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

**Test Coverage Areas:**
- ✅ Connection & Authentication (Azure AD integration)
- ✅ Version Methods (application, platform, build versions)
- ✅ Metadata Operations (entity discovery, metadata APIs)
- ✅ Data Operations (CRUD, OData query validation)
- ✅ Error Handling (network failures, auth errors)
- ✅ Performance Testing (response times, concurrent operations)

**Integration Test Commands:**
- `setup` - Environment setup and dependency checking
- `deps-check` - Validate required dependencies
- `test-mock` - Fast mock server tests
- `test-sandbox` - Sandbox environment tests (default)
- `test-live` - Live environment tests
- `test-all` - All test levels
- `coverage` - Coverage reporting
- `clean` - Clean up test artifacts

**Key Testing Practices:**
- Integration tests complement unit tests
- Default to sandbox testing (most realistic)
- Use mock tests for fast feedback in CI/CD
- Environment-based test filtering
- Comprehensive fixture system for resource management
- Performance metrics collection and validation

### 6. CLI Development Practices

#### 6.1 Command Structure Guidelines
- Use `argparse` with subparsers for hierarchical commands
- Follow pattern: `d365fo-client [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]`
- Implement global options before subcommands (--base-url, --output, --verbose, etc.)
- Use consistent naming: dash-separated for CLI args, underscore for internal code

#### 6.2 Command Implementation Pattern
```python
# CLI Manager with async command handlers
class CLIManager:
    async def execute_command(self, args: argparse.Namespace) -> int:
        # Setup -> Create client -> Route command -> Handle errors
        
    async def _handle_command(self, args: argparse.Namespace) -> int:
        # Execute client operations and format output
        # Return 0 for success, 1 for errors
```

#### 6.3 Configuration Management
- Support profile-based configuration in YAML format
- Location: `~/.d365fo-client/config.yaml`
- Environment variable substitution: `${VAR_NAME}`
- Precedence: CLI args > Environment variables > Profile config > Defaults

#### 6.4 Output Formatting Requirements
- Support multiple formats: JSON, table, CSV, YAML
- Use `tabulate` library for table formatting
- Consistent data structures for formatting
- Handle error output separately from data output

#### 6.5 CLI Testing Practices
- Mock `FOClient` for CLI tests
- Test argument parsing separately from command execution
- Use `argparse.Namespace` objects for test scenarios
- Test both success and error cases for each command

#### 6.6 Backward Compatibility
- Maintain existing `--demo` option functionality
- Keep `example_usage()` function for demo mode
- Preserve existing API without breaking changes
- Support both new CLI and legacy demo modes

### 7. Documentation
- Store all documentation files in the `docs/` folder
- Maintain comprehensive README.md with usage examples
- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring format
- Place API documentation, guides, and tutorials in `docs/`
- Consider using Sphinx for API documentation with output to `docs/`

### 8. Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml` before releases
- Maintain CHANGELOG.md with release notes
- Tag releases in git with version numbers

## Development Workflow

### Setting up development environment:
1. `uv sync` - Install dependencies
2. `uv add --group dev pytest black isort mypy` - Add development tools
3. `uv run pytest` - Run tests

### Before committing:
1. `uv run black .` - Format code
2. `uv run isort .` - Sort imports
3. `uv run mypy src/` - Type checking
4. `uv run pytest` - Run unit tests
5. `.\tests\integration\integration-test-simple.ps1 test-sandbox` - Run integration tests

### Publishing workflow:
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. `uv build` - Build distribution packages
4. `uv publish` - Publish to PyPI (requires API token)

## Code Quality Standards
- Use Black for code formatting
- Use isort for import sorting
- Use mypy for static type checking
- Use ruff for fast linting
- Maintain test coverage above 90%
- All public APIs must have type hints and docstrings

## Example Code Guidelines
When writing example code or documentation that demonstrates D365 Finance & Operations client usage:

### Base URL Configuration
Always use the following pattern for setting the base URL in example code:

```python
import os

# Use the One Box development environment as default
base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
```

This pattern:
- Allows users to override the URL via environment variable
- Provides a sensible default (One Box development environment)
- Demonstrates proper environment variable usage
- Works for both development and production scenarios

### Authentication Configuration
For example code, use the `FOClientConfig` with `use_default_credentials=True` to simplify examples:

```python
import os
from d365fo_client import FOClientConfig

# Use default credentials for authentication
config = FOClientConfig(
    base_url=base_url,
    use_default_credentials=True,
    use_label_cache=True
)

# Alternative: explicit credentials if needed
# config = FOClientConfig(
#     base_url=base_url,
#     client_id=os.getenv('AZURE_CLIENT_ID'),
#     client_secret=os.getenv('AZURE_CLIENT_SECRET'),
#     tenant_id=os.getenv('AZURE_TENANT_ID'),
#     use_label_cache=True
# )
```

Benefits of using `use_default_credentials=True`:
- Simplifies example code by reducing authentication boilerplate
- Works seamlessly in Azure environments (Managed Identity, Azure CLI, etc.)
- Provides automatic credential discovery and selection
- Falls back gracefully to environment variables when needed
- Follows Azure SDK best practices for authentication

### Example Code Structure
```python
import os
from d365fo_client import D365FOClient, FOClientConfig

# Base URL configuration
base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')

# Configuration with default credentials (preferred approach)
config = FOClientConfig(
    base_url=base_url,
    use_default_credentials=True,
    use_label_cache=True
)

# Client initialization with default credentials
client = D365FOClient(config=config)

# Alternative: explicit credentials configuration (commented out)
# config = FOClientConfig(
#     base_url=base_url,
#     client_id=os.getenv('AZURE_CLIENT_ID'),
#     client_secret=os.getenv('AZURE_CLIENT_SECRET'),
#     tenant_id=os.getenv('AZURE_TENANT_ID'),
#     use_label_cache=True
# )
# client = D365FOClient(config=config)

# Your example code here...
```

## Metadata Scripts

The project includes a comprehensive set of metadata scripts in the `scripts/` folder for working with D365 F&O metadata. These scripts provide convenient command-line access to metadata operations.

### Available Scripts

#### Data Entity Scripts
- **`search_data_entities.ps1`** - Search for data entities by pattern using CLI
- **`get_data_entity_schema.ps1`** - Get detailed schema information for a specific entity using CLI

#### Enumeration Scripts  
- **`search_enums.py`** - Search for enumerations by pattern using Python API
- **`get_enumeration_info.py`** - Get detailed information for a specific enumeration using Python API

#### Action Scripts
- **`search_actions.ps1`** - Search for actions by pattern using CLI
- **`get_action_info.py`** - Get detailed information for a specific action using Python API

### Usage Examples

#### Search Data Entities
```powershell
# Basic search
.\scripts\search_data_entities.ps1 -Pattern "customer"

# Advanced search with options
.\scripts\search_data_entities.ps1 -Pattern ".*sales.*" -Output json -Limit 10
```

#### Get Entity Schema
```powershell
# Get detailed schema with all information
.\scripts\get_data_entity_schema.ps1 -EntityName "CustomersV3" -Properties -Keys -Labels -Output json
```

#### Search Enumerations
```bash
# Search enumerations using Python API
uv run python scripts\search_enums.py "status" --output json --limit 5
```

#### Get Enumeration Details
```bash
# Get enumeration details with labels
uv run python scripts\get_enumeration_info.py "CustVendorBlocked" --output table
```

#### Search Actions
```powershell
# Search actions by pattern
.\scripts\search_actions.ps1 -Pattern "post" -Output json
```

#### Get Action Information
```bash
# Get detailed action information
uv run python scripts\get_action_info.py "Microsoft.Dynamics.DataEntities.GetKeys" --output json
```

### Script Configuration

All scripts support:
- **Multiple output formats**: table, json, csv, yaml/list
- **Environment configuration**: via `--base-url` parameter or environment variables
- **Profile support**: via `--profile` parameter (where implemented)
- **Verbose output**: via `--verbose` or `-VerboseOutput` parameters

### Prerequisites for Scripts
- d365fo-client package installed (`uv sync`)
- PowerShell (for .ps1 scripts)
- Python 3.13+ with uv (for .py scripts)
- D365 F&O environment access with proper authentication
- Environment variables set: `D365FO_BASE_URL`, optional Azure AD credentials

See `scripts/README.md` for comprehensive documentation and additional examples.

## Security Considerations
- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow security best practices for package distribution

## Publishing Checklist
Before publishing to PyPI:
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] All unit tests passing (`uv run pytest`)
- [ ] All integration tests passing (`.\tests\integration\integration-test-simple.ps1 test-sandbox`)
- [ ] Documentation updated
- [ ] License file included
- [ ] README.md comprehensive
- [ ] Clean git working directory
- [ ] Tagged release in git

## Common Commands
- `uv add package-name` - Add dependency
- `uv add --group dev package-name` - Add dev dependency
- `uv sync` - Install/sync dependencies
- `uv run command` - Run command in project environment
- `uv build` - Build distribution packages
- `uv publish` - Publish to PyPI
- `uv run pytest` - Run unit tests
- `uv run black .` - Format code

### Make Commands (Cross-Platform)
- `make dev-setup` / `make.bat dev-setup` / `.\make.ps1 dev-setup` - Development environment setup
- `make dev` / `make.bat dev` / `.\make.ps1 dev` - Quick development check (format + lint + test)
- `make quality-check` / `make.bat quality-check` / `.\make.ps1 quality-check` - Comprehensive quality checks
- `make test-coverage` / `make.bat test-coverage` / `.\make.ps1 test-coverage` - Run tests with coverage
- `make build` / `make.bat build` / `.\make.ps1 build` - Build distribution packages

### Integration Testing Commands
- `.\tests\integration\integration-test-simple.ps1 test-sandbox` - Run sandbox integration tests (default)
- `.\tests\integration\integration-test-simple.ps1 test-mock` - Run mock server tests
- `.\tests\integration\integration-test-simple.ps1 coverage` - Run tests with coverage
- `.\tests\integration\integration-test-simple.ps1 setup` - Setup integration test environment
- `python tests/integration/test_runner.py sandbox --verbose` - Alternative test execution

### Metadata Scripts Commands
- `.\scripts\search_data_entities.ps1 -Pattern "customer"` - Search data entities  
- `.\scripts\get_data_entity_schema.ps1 -EntityName "CustomersV3" -Properties -Keys` - Get entity schema
- `uv run python scripts\search_enums.py "status" --output json` - Search enumerations
- `uv run python scripts\get_enumeration_info.py "CustVendorBlocked"` - Get enumeration details
- `.\scripts\search_actions.ps1 -Pattern "post"` - Search actions
- `uv run python scripts\get_action_info.py "ActionName" --output json` - Get action details

## When creating new features:
1. Create feature branch
2. Add tests first (TDD approach)
3. Implement feature with proper type hints
4. Update documentation
5. Ensure all quality checks pass
6. Run integration tests to validate against D365 F&O environments
7. Create pull request

## Integration Testing Best Practices
- Always run sandbox tests before submitting PRs
- Use mock tests for fast feedback during development
- Update integration tests when adding new D365 F&O functionality
- Ensure tests are environment-agnostic (don't rely on specific test data)
- Add performance assertions for new operations
- Document any new environment configuration requirements

## Error Handling
- Use specific exception types
- Provide clear error messages
- Log errors appropriately
- Handle edge cases gracefully
- Document expected exceptions in docstrings