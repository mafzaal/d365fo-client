# Tests

This directory contains the test suite for the d365fo-client package, organized into unit tests and integration tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated, no external dependencies)
│   ├── test_cli.py         # CLI functionality tests
│   ├── test_enhanced_client.py # Enhanced client features tests
│   ├── test_get_application_version.py # Application version tests
│   ├── test_main.py        # Main module tests
│   ├── test_mcp_server.py  # MCP server tests
│   ├── test_metadata.py    # Metadata operations tests
│   ├── test_metadata_api.py # Metadata API tests
│   ├── test_metadata_api_simplified.py # Simplified metadata API tests
│   ├── test_metadata_cache.py # Metadata caching tests
│   ├── test_metadata_statistics.py # Metadata statistics tests
│   ├── test_utils.py       # Utility functions tests
│   ├── test_version_methods.py # Version methods tests
│   └── __init__.py
├── integration/             # Integration tests (slower, external dependencies)
│   ├── test_mock_server.py # Mock server integration tests
│   ├── test_sandbox.py     # Sandbox environment tests
│   ├── conftest.py         # Integration test fixtures
│   ├── pytest.ini         # Integration test configuration
│   ├── mock_server/        # Mock D365 F&O server implementation
│   └── README.md           # Integration test documentation
├── __init__.py
└── README.md               # This file
```

## Test Types

### Unit Tests (`tests/unit/`)

Unit tests are fast, isolated tests that don't require external dependencies. They use mocks and fixtures to test individual components in isolation.

**Characteristics:**
- ✅ Fast execution (typically < 1 second per test)
- ✅ No external dependencies
- ✅ Use mocking extensively
- ✅ Test individual functions/classes
- ✅ Run in any environment

**Purpose:**
- Validate individual component behavior
- Test error handling and edge cases
- Ensure code quality and coverage
- Quick feedback during development

### Integration Tests (`tests/integration/`)

Integration tests validate the interaction between components and with external systems. They test against real or simulated D365 Finance & Operations environments.

**Characteristics:**
- ⏱️ Slower execution (typically 1-30 seconds per test)
- 🌐 May require external dependencies
- 🔧 Test component interactions
- 📡 Validate API integrations
- 🔐 May require authentication

**Test Tiers:**
1. **Mock Server Tests** - Fast, reliable, local mock D365 F&O API
2. **Sandbox Tests** - Against real D365 test environments
3. **Live Tests** - Against production environments (optional)

## Running Tests

### Using Make Commands (Recommended)

The project provides cross-platform make commands for running tests:

```powershell
# Windows PowerShell
.\make.ps1 test-unit          # Run unit tests only
.\make.ps1 test-integration   # Run integration tests only
.\make.ps1 test              # Run all tests
.\make.ps1 test-coverage     # Run tests with coverage report

# Windows Command Prompt
make.bat test-unit
make.bat test-integration
make.bat test
make.bat test-coverage

# Unix/Linux/macOS
make test-unit
make test-integration
make test
make test-coverage
```

### Using pytest Directly

```bash
# Run unit tests
uv run pytest tests/unit

# Run integration tests
uv run pytest tests/integration

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=d365fo_client --cov-report=html --cov-report=term

# Run specific test file
uv run pytest tests/unit/test_cli.py

# Run specific test
uv run pytest tests/unit/test_cli.py::TestCLIManager::test_config_list_empty

# Run tests with verbose output
uv run pytest -v

# Run tests and stop on first failure
uv run pytest -x
```

## Test Configuration

### Main Configuration (pyproject.toml)

The main test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

### Integration Test Configuration

Integration tests have their own `pytest.ini` configuration in `tests/integration/pytest.ini` with specific markers and asyncio settings.

## Test Markers

### Unit Test Markers

Unit tests use standard pytest markers:

```python
@pytest.mark.asyncio      # For async tests
@pytest.mark.parametrize  # For parameterized tests
@pytest.mark.skip         # Skip tests
@pytest.mark.skipif       # Conditional skip
```

### Integration Test Markers

Integration tests use custom markers defined in `tests/integration/pytest.ini`:

```python
@pytest.mark.integration     # Mark as integration test
@pytest.mark.mock_server    # Mock server tests
@pytest.mark.sandbox       # Sandbox environment tests
@pytest.mark.live          # Live environment tests
@pytest.mark.slow          # Slow running tests
@pytest.mark.performance   # Performance tests
@pytest.mark.crud          # CRUD operation tests
@pytest.mark.metadata      # Metadata API tests
@pytest.mark.auth          # Authentication tests
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from d365fo_client import FOClient

class TestFOClient:
    @pytest.mark.asyncio
    async def test_get_application_version_success(self):
        """Test successful application version retrieval."""
        # Arrange
        mock_config = Mock()
        mock_response = "10.0.1985.137"
        
        with patch('d365fo_client.FOClient.get_application_version') as mock_method:
            mock_method.return_value = mock_response
            client = FOClient(mock_config)
            
            # Act
            result = await client.get_application_version()
            
            # Assert
            assert result == mock_response
            mock_method.assert_called_once()
```

### Integration Test Example

```python
import pytest
from d365fo_client import FOClient

class TestConnectionIntegration:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connection_success(self, mock_client: FOClient):
        """Test successful connection to D365 F&O."""
        result = await mock_client.test_connection()
        assert result is True
```

## Test Data and Fixtures

### Unit Test Fixtures

Unit tests use local fixtures defined in individual test files or shared fixtures in `conftest.py` files within the unit test directories.

### Integration Test Fixtures

Integration tests use fixtures defined in `tests/integration/conftest.py`:

- `mock_server` - Local mock D365 F&O server
- `mock_client` - FOClient configured for mock server
- `sandbox_client` - FOClient configured for sandbox environment
- `live_client` - FOClient configured for live environment
- `adaptive_client` - Parameterized fixture providing appropriate client
- `performance_metrics` - Performance measurement utilities
- `entity_validator` - Data validation utilities

## Environment Variables

### Unit Tests

Unit tests should not require environment variables as they use mocks.

### Integration Tests

Integration tests may require environment variables for authentication and endpoints:

```bash
# Required for sandbox tests
D365FO_SANDBOX_BASE_URL=https://your-test-environment.dynamics.com

# Optional: Explicit authentication (if not using default credentials)
D365FO_CLIENT_ID=your-client-id
D365FO_CLIENT_SECRET=your-client-secret
D365FO_TENANT_ID=your-tenant-id

# Test level control
INTEGRATION_TEST_LEVEL=sandbox  # mock, sandbox, live, or all
```

## Troubleshooting

### Common Issues

#### Unit Tests Failing Due to Import Errors
- Ensure all dependencies are installed: `uv sync`
- Check that the package is properly installed in development mode

#### Integration Tests Hanging
- This was a known issue that has been fixed by correcting asyncio fixture scopes
- If tests still hang, check that the mock server can start on the specified port

#### Permission Errors with Cache Tests
- Some cache tests may fail on Windows due to file locking
- This is typically a test cleanup issue and doesn't affect functionality

#### Authentication Errors in Integration Tests
- Ensure you have proper Azure AD credentials configured
- Use `az login` for Azure CLI authentication
- Set `use_default_credentials=True` in test configurations

### Getting Help

1. Check the integration test documentation: `tests/integration/README.md`
2. Review the main project documentation in the `docs/` folder
3. Check the GitHub issues for known problems
4. Run tests with verbose output: `pytest -v --tb=long`

## Coverage

To generate test coverage reports:

```bash
# Generate HTML coverage report
uv run pytest --cov=d365fo_client --cov-report=html

# Generate terminal coverage report
uv run pytest --cov=d365fo_client --cov-report=term

# Generate both
uv run pytest --cov=d365fo_client --cov-report=html --cov-report=term
```

Coverage reports are generated in the `htmlcov/` directory.

### Integration Test Coverage Report

A comprehensive integration test coverage report is available at:
- **Latest Report**: `integration_test_coverage_report.md`

This report includes:
- Detailed coverage statistics by module
- Test execution results and analysis
- Identified areas for improvement
- Recommendations for better coverage

## Continuous Integration

Tests are designed to run in CI/CD environments:

- Unit tests should always pass and run quickly
- Integration tests may be skipped in CI if external dependencies aren't available
- Use environment variables to control test execution in different environments
- Consider running only mock server integration tests in CI for speed

## Best Practices

### For Unit Tests
- Keep tests fast (< 1 second each)
- Use mocks for external dependencies
- Test one thing at a time
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### For Integration Tests
- Test realistic scenarios
- Use appropriate test markers
- Clean up resources in teardown
- Handle network timeouts gracefully
- Use fixtures for common setup

### General
- Maintain high test coverage (>90%)
- Write tests before fixing bugs
- Keep tests independent
- Use meaningful assertions
- Document complex test scenarios