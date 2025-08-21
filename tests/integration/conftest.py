"""Fixtures for integration testing."""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from d365fo_client import FOClient, FOClientConfig
from .mock_server import D365MockServer
from . import TEST_ENVIRONMENTS, INTEGRATION_TEST_LEVEL


@pytest_asyncio.fixture(scope="function")
async def mock_server() -> AsyncGenerator[D365MockServer, None]:
    """Start mock D365 F&O server for testing."""
    server = D365MockServer(port=8000)
    await server.start()
    
    # Wait a bit for server to be ready
    await asyncio.sleep(0.1)
    
    try:
        yield server
    finally:
        await server.stop()


@pytest_asyncio.fixture
async def mock_client(mock_server: D365MockServer) -> AsyncGenerator[FOClient, None]:
    """Create FOClient configured for mock server."""
    config = FOClientConfig(
        base_url="http://localhost:8000",
        use_default_credentials=True,  # Use default credentials for mock server
        verify_ssl=False,
        timeout=30
    )
    
    async with FOClient(config) as client:
        yield client


@pytest_asyncio.fixture
async def sandbox_client() -> AsyncGenerator[FOClient, None]:
    """Create FOClient configured for sandbox environment."""
    if INTEGRATION_TEST_LEVEL not in ['sandbox', 'all']:
        pytest.skip("Sandbox integration tests not enabled")
    
    import os
    
    # Check required environment variables
    required_vars = ['D365FO_SANDBOX_BASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_SANDBOX_BASE_URL'),
        use_default_credentials=True,
        verify_ssl=False,  # Often needed for test environments
        timeout=60
    )
    
    async with FOClient(config) as client:
        # Test connection before yielding
        if not await client.test_connection():
            pytest.skip("Cannot connect to sandbox environment")
        yield client


@pytest_asyncio.fixture
async def live_client() -> AsyncGenerator[FOClient, None]:
    """Create FOClient configured for live environment."""
    if INTEGRATION_TEST_LEVEL not in ['live', 'all']:
        pytest.skip("Live integration tests not enabled")
    
    import os
    
    # Check required environment variables
    required_vars = ['D365FO_LIVE_BASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_LIVE_BASE_URL'),
        use_default_credentials=True,
        verify_ssl=True,
        timeout=60
    )
    
    async with FOClient(config) as client:
        # Test connection before yielding
        if not await client.test_connection():
            pytest.skip("Cannot connect to live environment")
        yield client


@pytest.fixture(params=['mock', 'sandbox', 'live'])
def adaptive_client(request, mock_client, sandbox_client, live_client):
    """Fixture that provides appropriate client based on test level."""
    client_type = request.param
    
    if INTEGRATION_TEST_LEVEL == 'mock' and client_type != 'mock':
        pytest.skip(f"Skipping {client_type} test, only mock level enabled")
    elif INTEGRATION_TEST_LEVEL == 'sandbox' and client_type not in ['mock', 'sandbox']:
        pytest.skip(f"Skipping {client_type} test, only mock and sandbox levels enabled")
    elif INTEGRATION_TEST_LEVEL == 'live' and client_type not in ['mock', 'live']:
        pytest.skip(f"Skipping {client_type} test, only mock and live levels enabled")
    
    if client_type == 'mock':
        return mock_client
    elif client_type == 'sandbox':
        return sandbox_client
    elif client_type == 'live':
        return live_client
    else:
        pytest.skip(f"Unknown client type: {client_type}")


# Performance testing fixtures

@pytest.fixture
def performance_metrics():
    """Fixture to collect performance metrics during tests."""
    import time
    from typing import Dict, List
    
    metrics = {
        'timings': {},
        'call_counts': {},
        'errors': []
    }
    
    def start_timer(operation: str):
        metrics['timings'][operation] = time.time()
    
    def end_timer(operation: str) -> float:
        if operation in metrics['timings']:
            duration = time.time() - metrics['timings'][operation]
            metrics['timings'][operation] = duration
            return duration
        return 0.0
    
    def increment_counter(operation: str):
        metrics['call_counts'][operation] = metrics['call_counts'].get(operation, 0) + 1
    
    def add_error(operation: str, error: str):
        metrics['errors'].append({'operation': operation, 'error': error})
    
    # Attach helper methods
    metrics['start_timer'] = start_timer
    metrics['end_timer'] = end_timer  
    metrics['increment_counter'] = increment_counter
    metrics['add_error'] = add_error
    
    return metrics


# Data validation fixtures

@pytest.fixture
def entity_validator():
    """Fixture to validate entity data structures."""
    
    def validate_customer(customer_data: dict) -> bool:
        """Validate customer entity data."""
        required_fields = ['CustomerAccount', 'CustomerName']
        return all(field in customer_data for field in required_fields)
    
    def validate_vendor(vendor_data: dict) -> bool:
        """Validate vendor entity data."""
        required_fields = ['VendorAccount', 'VendorName']
        return all(field in vendor_data for field in required_fields)
    
    def validate_odata_response(response: dict) -> bool:
        """Validate OData response structure."""
        if 'value' in response:
            return isinstance(response['value'], list)
        return '@odata.context' in response
    
    return {
        'customer': validate_customer,
        'vendor': validate_vendor,
        'odata_response': validate_odata_response
    }