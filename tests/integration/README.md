# Integration Testing for D365 F&O Client

This directory contains comprehensive integration tests for the D365 F&O Client package. Integration tests validate the client's behavior against real or simulated D365 F&O environments.

## Overview

The integration testing framework is designed with multiple tiers to provide flexibility in testing environments:

1. **Mock Server Tests** - Fast, reliable tests against a local mock server
2. **Sandbox Tests** - Tests against D365 F&O test/sandbox environments  
3. **Live Tests** - Optional tests against production D365 F&O environments

## Quick Start

### Prerequisites

```bash
# Install integration test dependencies
uv add --group integration

# Or manually install required packages
uv add --dev aiohttp pytest-asyncio pytest-cov httpx responses
```

### Running Tests

```bash
# Run only mock server tests (fastest, no external dependencies)
python tests/integration/test_runner.py mock

# Run mock + sandbox tests (requires test environment)
python tests/integration/test_runner.py sandbox

# Run with verbose output and coverage
python tests/integration/test_runner.py mock --verbose --coverage

# Run specific test file
python tests/integration/test_runner.py mock --test test_mock_server.py
```

## Test Levels

### 1. Mock Server Tests (`mock`)

- **Purpose**: Fast, reliable testing without external dependencies
- **Technology**: Local aiohttp server that simulates D365 F&O API
- **Speed**: Very fast (< 30 seconds for full suite)
- **Dependencies**: None (fully self-contained)
- **Use Cases**: 
  - CI/CD pipelines
  - Local development testing
  - API contract validation
  - Error handling verification

**Features of Mock Server:**
- Complete OData API simulation
- Realistic D365 F&O response structures
- CRUD operations support
- Metadata API endpoints
- Version method responses
- Label service simulation
- Error scenario testing

### 2. Sandbox Tests (`sandbox`)

- **Purpose**: Validate against real D365 F&O test environments
- **Requirements**: Access to D365 F&O sandbox/test environment
- **Speed**: Moderate (2-5 minutes depending on environment)
- **Use Cases**:
  - Pre-deployment validation
  - Authentication testing
  - Environment-specific testing
  - Performance baseline establishment

**Required Environment Variables:**
```bash
D365FO_SANDBOX_BASE_URL=https://your-test-environment.dynamics.com
D365FO_CLIENT_ID=your-client-id
D365FO_CLIENT_SECRET=your-client-secret  
D365FO_TENANT_ID=your-tenant-id
```

### 3. Live Tests (`live`)

- **Purpose**: Optional validation against production environments
- **Requirements**: Access to live D365 F&O environment
- **Speed**: Slower (may include rate limiting)
- **Use Cases**:
  - Production readiness verification
  - Real-world performance testing
  - Final validation before major releases

**Required Environment Variables:**
```bash
D365FO_LIVE_BASE_URL=https://your-prod-environment.dynamics.com
# Same Azure credentials as sandbox
```

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