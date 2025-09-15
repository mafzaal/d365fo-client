# Integration Tests - Sandbox Strategy

This directory contains integration tests that validate the D365 F&O client against real sandbox environments.

## Strategy Overview

The integration test strategy has been refactored to focus on **sandbox-only testing**, eliminating the need for mock servers while providing comprehensive real-world API validation.

## Test Structure

### Active Test Files

- **`test_sandbox.py`** - Core connection, version, and basic operations
- **`test_sandbox_crud.py`** - Comprehensive CRUD operations and data validation
- **`test_sandbox_metadata.py`** - Metadata API operations and entity discovery
- **`test_sandbox_performance.py`** - Performance benchmarking and load testing
- **`test_sandbox_error_handling.py`** - Error scenarios and resilience testing

### Deprecated Files

- `test_mock_server.py.deprecated` - Previously tested against mock server
- `test_crud_comprehensive.py.deprecated` - Mock-based CRUD tests
- `test_cli_integration.py.deprecated` - Mock-based CLI tests

## Configuration

### Environment Variables

Required for sandbox testing:
- `D365FO_SANDBOX_BASE_URL` - Sandbox environment URL
- `INTEGRATION_TEST_LEVEL=sandbox` - Enable sandbox tests

Optional authentication (if not using default credentials):
- `D365FO_CLIENT_ID` - OAuth client ID
- `D365FO_CLIENT_SECRET` - OAuth client secret
- `D365FO_TENANT_ID` - Azure tenant ID

### Running Tests

```bash
# Run all sandbox tests
INTEGRATION_TEST_LEVEL=sandbox pytest tests/integration/

# Run specific test categories
pytest tests/integration/test_sandbox_crud.py
pytest tests/integration/test_sandbox_metadata.py
pytest tests/integration/test_sandbox_performance.py
pytest tests/integration/test_sandbox_error_handling.py

# Skip slow performance tests
pytest tests/integration/ -m "not slow"
```

## Test Categories

### 1. CRUD Operations (`test_sandbox_crud.py`)
- Entity retrieval and validation
- Query options (top, skip, filter, select)
- Data integrity and consistency
- Pagination and large datasets
- Real entity relationships

**Benefits vs Mock:**
- Tests actual D365 entity schemas
- Validates real OData response formats
- Tests actual data relationships and constraints

### 2. Metadata Operations (`test_sandbox_metadata.py`)
- Metadata download and caching
- Entity discovery and search
- Data entities and public entities
- Label operations and enumerations
- Schema validation

**Benefits vs Mock:**
- Tests real metadata structure
- Validates actual entity properties and types
- Tests real label system integration

### 3. Performance Testing (`test_sandbox_performance.py`)
- Connection establishment timing
- Query performance benchmarks
- Concurrent operation handling
- Large dataset performance
- Metadata operation timing

**Benefits vs Mock:**
- Real network latency and throttling
- Actual D365 performance characteristics
- Real-world load behavior

### 4. Error Handling (`test_sandbox_error_handling.py`)
- Invalid entity/action errors
- Authentication failures
- Malformed request handling
- Error recovery scenarios
- Timeout and connectivity issues

**Benefits vs Mock:**
- Real D365 error messages and codes
- Actual authentication flow errors
- Real timeout and rate limiting behavior

## Test Organization

```
tests/integration/
├── __init__.py              # Test level configuration
├── conftest.py              # Shared fixtures
├── pytest.ini              # Pytest configuration
├── test_runner.py           # Test execution script
├── mock_server/             # Mock server implementation
│   ├── __init__.py
│   └── server.py           # D365 F&O API mock server
├── test_mock_server.py      # Mock server tests
├── test_sandbox.py          # Sandbox environment tests
└── test_live.py            # Live environment tests (future)
```

## Environment Configuration

### Setting Test Level

Control which tests run using the `INTEGRATION_TEST_LEVEL` environment variable:

```bash
# Only mock server tests
export INTEGRATION_TEST_LEVEL=mock

# Mock + sandbox tests  
export INTEGRATION_TEST_LEVEL=sandbox

# Mock + live tests
export INTEGRATION_TEST_LEVEL=live

# All tests
export INTEGRATION_TEST_LEVEL=all
```

### Authentication Setup

For sandbox and live tests, configure Azure AD authentication:

```bash
# Using Service Principal
export D365FO_CLIENT_ID="your-app-registration-id"
export D365FO_CLIENT_SECRET="your-app-secret"
export D365FO_TENANT_ID="your-tenant-id"

# Or use Default Azure Credential (Azure CLI, Managed Identity, etc.)
# No environment variables needed if using DefaultAzureCredential
```

### D365 F&O Environment URLs

```bash
# Test/Sandbox Environment
export D365FO_SANDBOX_BASE_URL="https://your-sandbox.sandbox.operations.dynamics.com"

# Production Environment (optional)
export D365FO_LIVE_BASE_URL="https://your-prod.operations.dynamics.com"
```

## Test Categories

### Connection Tests
- Basic connectivity validation
- Authentication verification
- SSL/TLS validation
- Timeout handling

### API Functionality Tests
- OData CRUD operations
- Action method calls
- Metadata API operations
- Label service operations
- Version information retrieval

### Data Validation Tests
- Response structure validation
- Data type verification
- OData compliance checking
- Error response validation

### Performance Tests
- Response time validation
- Concurrent request handling
- Large dataset processing
- Memory usage patterns

### Error Handling Tests
- Network failure scenarios
- Authentication errors
- Invalid request handling
- Timeout scenarios

## Fixtures and Utilities

### Key Fixtures

- `mock_server`: Starts local D365 F&O mock server
- `mock_client`: FOClient configured for mock server
- `sandbox_client`: FOClient configured for sandbox environment
- `live_client`: FOClient configured for live environment
- `adaptive_client`: Automatically selects appropriate client based on test level
- `performance_metrics`: Collects timing and performance data
- `entity_validator`: Validates entity data structures

### Mock Server Features

The mock server provides realistic D365 F&O API simulation:

```python
# Supports standard OData operations
GET /data/Customers                    # Get collection
GET /data/Customers('US-001')          # Get by key
POST /data/Customers                   # Create
PATCH /data/Customers('US-001')        # Update
DELETE /data/Customers('US-001')       # Delete

# Supports D365 F&O specific operations
POST /data/DataManagementEntities/Microsoft.Dynamics.DataEntities.GetApplicationVersion
GET /Metadata/DataEntities
GET /Metadata/PublicEntities
GET /Metadata/Labels?labelId=@SYS1234
```

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync --group integration
    
    - name: Run mock server tests
      run: |
        python tests/integration/test_runner.py mock --coverage
    
    - name: Run sandbox tests
      if: env.D365FO_SANDBOX_BASE_URL != ''
      env:
        D365FO_SANDBOX_BASE_URL: ${{ secrets.D365FO_SANDBOX_BASE_URL }}
        D365FO_CLIENT_ID: ${{ secrets.D365FO_CLIENT_ID }}
        D365FO_CLIENT_SECRET: ${{ secrets.D365FO_CLIENT_SECRET }}
        D365FO_TENANT_ID: ${{ secrets.D365FO_TENANT_ID }}
      run: |
        python tests/integration/test_runner.py sandbox
```

### Azure DevOps Example

```yaml
trigger:
- main
- develop

pool:
  vmImage: 'ubuntu-latest'

variables:
- group: D365FO-Test-Credentials

stages:
- stage: MockTests
  displayName: 'Mock Server Tests'
  jobs:
  - job: MockServerTests
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.13'
    
    - script: |
        pip install uv
        uv sync --group integration
      displayName: 'Install dependencies'
    
    - script: |
        python tests/integration/test_runner.py mock --coverage
      displayName: 'Run mock server tests'

- stage: SandboxTests
  displayName: 'Sandbox Tests'
  dependsOn: MockTests
  condition: and(succeeded(), ne(variables['D365FO_SANDBOX_BASE_URL'], ''))
  jobs:
  - job: SandboxTests
    steps:
    - script: |
        python tests/integration/test_runner.py sandbox
      env:
        D365FO_SANDBOX_BASE_URL: $(D365FO_SANDBOX_BASE_URL)
        D365FO_CLIENT_ID: $(D365FO_CLIENT_ID)
        D365FO_CLIENT_SECRET: $(D365FO_CLIENT_SECRET)
        D365FO_TENANT_ID: $(D365FO_TENANT_ID)
      displayName: 'Run sandbox tests'
```

## Best Practices

### Writing Integration Tests

1. **Use Appropriate Test Level**: Start with mock server tests, add sandbox tests for critical functionality
2. **Handle Environment Variability**: Use skips for unavailable environments
3. **Validate Real Data**: Don't assume specific data exists in test environments
4. **Test Error Scenarios**: Ensure proper error handling
5. **Monitor Performance**: Include performance assertions
6. **Clean Up Resources**: Ensure tests clean up any created data

### Mock Server Development

1. **Realistic Responses**: Match actual D365 F&O response structures
2. **Error Simulation**: Implement realistic error scenarios
3. **State Management**: Maintain consistent state across requests
4. **Performance**: Keep mock responses fast
5. **Extensibility**: Easy to add new endpoints and scenarios

### Environment Management

1. **Separation**: Use different environments for different test levels
2. **Data Management**: Don't rely on specific test data
3. **Credentials**: Use secure credential management
4. **Isolation**: Ensure tests don't interfere with each other
5. **Documentation**: Document environment setup requirements

## Troubleshooting

### Common Issues

1. **Mock Server Port Conflicts**
   ```bash
   # Check if port 8000 is in use
   netstat -an | grep 8000
   # Kill process using port
   lsof -ti:8000 | xargs kill -9
   ```

2. **Authentication Failures**
   ```bash
   # Verify Azure credentials
   az account show
   # Test authentication
   az rest --url "https://your-environment.dynamics.com/data"
   ```

3. **Environment Connectivity**
   ```bash
   # Test basic connectivity
   curl -I "https://your-environment.dynamics.com/data"
   # Test with authentication
   python -c "from d365fo_client import FOClient, FOClientConfig; import asyncio; asyncio.run(FOClient(FOClientConfig('https://your-env.dynamics.com')).test_connection())"
   ```

4. **SSL Certificate Issues**
   ```bash
   # For test environments, you may need to disable SSL verification
   export PYTHONHTTPSVERIFY=0
   # Or in test configuration
   verify_ssl=False
   ```

### Debugging Tests

```bash
# Run with maximum verbosity
python tests/integration/test_runner.py mock --verbose -vv

# Run specific test with debugging
pytest tests/integration/test_mock_server.py::TestConnectionMockServer::test_connection_success -vv -s

# Enable asyncio debugging
PYTHONASYNCIODEBUG=1 python tests/integration/test_runner.py mock
```

## Performance Benchmarks

### Mock Server Tests
- Full test suite: < 30 seconds
- Individual test: < 1 second
- Concurrent operations: < 3 seconds

### Sandbox Tests  
- Connection tests: < 10 seconds
- Metadata operations: < 30 seconds
- Data operations: < 60 seconds

### Performance Monitoring

Tests automatically collect performance metrics:

```python
# Access performance data in tests
def test_performance_example(performance_metrics):
    # Test operations...
    
    # Check recorded timings
    assert performance_metrics['timings']['operation_name'] < 5.0
    
    # Check call counts
    assert performance_metrics['call_counts']['api_call'] > 0
```

## Contributing

When adding new integration tests:

1. **Follow the tier structure**: Add to appropriate test level
2. **Update mock server**: Add new endpoints as needed
3. **Document requirements**: Update environment variable documentation
4. **Add performance checks**: Include timing assertions
5. **Test error scenarios**: Include negative test cases
6. **Update fixtures**: Add new fixtures for common functionality

## Support

For issues with integration tests:

1. Check this README for common solutions
2. Review test logs for specific error messages
3. Validate environment configuration
4. Test connectivity manually
5. Open an issue with detailed environment information