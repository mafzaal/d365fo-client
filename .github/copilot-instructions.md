# Copilot Instructions for d365fo-client Python Package

## Project Overview
This is a Python package project named `d365fo-client` that uses `uv` for dependency management and will be published to PyPI.org. The project follows modern Python packaging standards with `pyproject.toml` configuration.

## Development Environment
- **Package Manager**: `uv` (for fast Python package management)
- **Python Version**: >=3.13
- **Build Backend**: `hatchling` (default for uv projects)
- **Distribution**: PyPI.org

## Project Structure Guidelines
```
d365fo-client/
├── src/
│   └── d365fo_client/
│       ├── __init__.py
│       ├── main.py
│       └── ...
├── tests/
│   ├── __init__.py
│   └── test_*.py
├── docs/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
└── CHANGELOG.md
```

## Key Development Practices

### 1. Package Management with uv
- Use `uv add <package>` to add dependencies
- Use `uv add --dev <package>` for development dependencies
- Use `uv sync` to install dependencies from lockfile
- Use `uv run <command>` to run commands in the project environment
- Use `uv build` to build distribution packages
- Use `uv publish` to publish to PyPI

### 2. Code Organization
- Place all source code in `src/d365fo_client/` directory
- Use proper `__init__.py` files for package initialization
- Export main functionality through `__init__.py`
- Follow PEP 8 style guidelines
- Use type hints for all functions and methods

### 3. Dependencies and Requirements
- Add all runtime dependencies to `pyproject.toml` under `[project]` dependencies
- Add development dependencies using `uv add --dev`
- Pin exact versions for reproducible builds
- Keep dependencies minimal and well-justified

### 4. Testing Framework

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

### 5. Documentation
- Store all documentation files in the `docs/` folder
- Maintain comprehensive README.md with usage examples
- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring format
- Place API documentation, guides, and tutorials in `docs/`
- Consider using Sphinx for API documentation with output to `docs/`

### 6. Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml` before releases
- Maintain CHANGELOG.md with release notes
- Tag releases in git with version numbers

## pyproject.toml Configuration Guidelines

### Essential sections to include:
```toml
[project]
name = "d365fo-client"
version = "x.y.z"
description = "Microsot Dynamics 365 Finance & Operations client"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "Muhammad Afzaal", email = "mo@thedataguy.pro" }]
requires-python = ">=3.13"
dependencies = []
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
]

[project.urls]
Homepage = "https://github.com/mafzaal/d365fo-client"
Repository = "https://github.com/mafzaal/d365fo-client"
Documentation = "https://d365fo-client.readthedocs.io"
Issues = "https://github.com/mafzaal/d365fo-client/issues"

[project.scripts]
d365fo-client = "d365fo_client.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build_meta"

[tool.hatch.build.targets.sdist]
include = ["src/d365fo_client"]

[tool.hatch.build.targets.wheel]
packages = ["src/d365fo_client"]
```

## Development Workflow

### Setting up development environment:
1. `uv sync` - Install dependencies
2. `uv add --dev pytest black isort mypy` - Add development tools
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
- `uv add --dev package-name` - Add dev dependency
- `uv sync` - Install/sync dependencies
- `uv run command` - Run command in project environment
- `uv build` - Build distribution packages
- `uv publish` - Publish to PyPI
- `uv run pytest` - Run unit tests
- `uv run black .` - Format code

### Integration Testing Commands
- `.\tests\integration\integration-test-simple.ps1 test-sandbox` - Run sandbox integration tests (default)
- `.\tests\integration\integration-test-simple.ps1 test-mock` - Run mock server tests
- `.\tests\integration\integration-test-simple.ps1 coverage` - Run tests with coverage
- `.\tests\integration\integration-test-simple.ps1 setup` - Setup integration test environment
- `python tests/integration/test_runner.py sandbox --verbose` - Alternative test execution

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