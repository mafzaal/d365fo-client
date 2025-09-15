"""Fixtures for integration testing."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from d365fo_client import FOClient, FOClientConfig

from . import INTEGRATION_TEST_LEVEL, TEST_ENVIRONMENTS


@pytest_asyncio.fixture
async def sandbox_client() -> AsyncGenerator[FOClient, None]:
    """Create FOClient configured for sandbox environment."""
    if INTEGRATION_TEST_LEVEL not in ["sandbox", "all"]:
        pytest.skip("Sandbox integration tests not enabled")

    import os

    # Check required environment variables
    required_vars = ["D365FO_SANDBOX_BASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")

    config = FOClientConfig(
        base_url=os.getenv("D365FO_SANDBOX_BASE_URL"),
        use_default_credentials=True,
        verify_ssl=False,  # Often needed for test environments
        timeout=60,
    )

    async with FOClient(config) as client:
        # Test connection before yielding
        if not await client.test_connection():
            pytest.skip("Cannot connect to sandbox environment")
        yield client


@pytest_asyncio.fixture
async def live_client() -> AsyncGenerator[FOClient, None]:
    """Create FOClient configured for live environment."""
    if INTEGRATION_TEST_LEVEL not in ["live", "all"]:
        pytest.skip("Live integration tests not enabled")

    import os

    # Check required environment variables
    required_vars = ["D365FO_LIVE_BASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")

    config = FOClientConfig(
        base_url=os.getenv("D365FO_LIVE_BASE_URL"),
        use_default_credentials=True,
        verify_ssl=True,
        timeout=60,
    )

    async with FOClient(config) as client:
        # Test connection before yielding
        if not await client.test_connection():
            pytest.skip("Cannot connect to live environment")
        yield client


@pytest.fixture(params=["sandbox", "live"])
def adaptive_client(request, sandbox_client, live_client):
    """Fixture that provides appropriate client based on test level."""
    client_type = request.param

    if INTEGRATION_TEST_LEVEL == "sandbox" and client_type not in ["sandbox"]:
        pytest.skip(
            f"Skipping {client_type} test, only sandbox level enabled"
        )
    elif INTEGRATION_TEST_LEVEL == "live" and client_type not in ["live"]:
        pytest.skip(f"Skipping {client_type} test, only live level enabled")

    if client_type == "sandbox":
        return sandbox_client
    elif client_type == "live":
        return live_client
    else:
        pytest.skip(f"Unknown client type: {client_type}")


# Performance testing fixtures


@pytest.fixture
def performance_metrics():
    """Fixture to collect performance metrics during tests."""
    import time
    from typing import Dict, List

    metrics = {"timings": {}, "call_counts": {}, "errors": []}

    def start_timer(operation: str):
        metrics["timings"][operation] = time.time()

    def end_timer(operation: str) -> float:
        if operation in metrics["timings"]:
            duration = time.time() - metrics["timings"][operation]
            metrics["timings"][operation] = duration
            return duration
        return 0.0

    def increment_counter(operation: str):
        metrics["call_counts"][operation] = metrics["call_counts"].get(operation, 0) + 1

    def add_error(operation: str, error: str):
        metrics["errors"].append({"operation": operation, "error": error})

    # Attach helper methods
    metrics["start_timer"] = start_timer
    metrics["end_timer"] = end_timer
    metrics["increment_counter"] = increment_counter
    metrics["add_error"] = add_error

    return metrics


# Sandbox-specific fixtures


@pytest_asyncio.fixture
async def sandbox_test_entities(sandbox_client: FOClient):
    """Fixture to provide test entities for sandbox testing."""
    test_entities = {
        "companies": [],
        "legal_entities": [],
    }

    # Get available companies for testing
    try:
        companies_result = await sandbox_client.get_entities("Companies", QueryOptions(top=5))
        if companies_result.get("value"):
            test_entities["companies"] = companies_result["value"]
    except Exception:
        pass  # Companies might not be available

    # Get available legal entities for testing
    try:
        legal_entities_result = await sandbox_client.get_entities("LegalEntities", QueryOptions(top=3))
        if legal_entities_result.get("value"):
            test_entities["legal_entities"] = legal_entities_result["value"]
    except Exception:
        pass  # Legal entities might not be available

    return test_entities


@pytest_asyncio.fixture
async def sandbox_metadata_cache(sandbox_client: FOClient):
    """Fixture to ensure metadata is downloaded and cached for tests."""
    try:
        await sandbox_client.download_metadata(force_refresh=False)
        return True
    except Exception:
        return False


@pytest.fixture
def sandbox_environment_info():
    """Fixture to provide sandbox environment information."""
    import os

    return {
        "base_url": os.getenv("D365FO_SANDBOX_BASE_URL"),
        "has_auth": bool(os.getenv("D365FO_CLIENT_ID") or os.getenv("D365FO_TENANT_ID")),
        "test_level": os.getenv("INTEGRATION_TEST_LEVEL", "sandbox"),
    }


@pytest_asyncio.fixture
async def sandbox_connectivity_check(sandbox_client: FOClient):
    """Fixture to verify sandbox connectivity before running tests."""
    try:
        connection_ok = await sandbox_client.test_connection()
        metadata_ok = await sandbox_client.test_metadata_connection()

        return {
            "connection": connection_ok,
            "metadata": metadata_ok,
            "overall": connection_ok and metadata_ok,
        }
    except Exception as e:
        return {
            "connection": False,
            "metadata": False,
            "overall": False,
            "error": str(e),
        }


# Test data cleanup fixtures


@pytest_asyncio.fixture
async def sandbox_cleanup():
    """Fixture to handle cleanup of test data in sandbox."""
    created_entities = []

    def register_for_cleanup(entity_set: str, entity_key: str):
        """Register an entity for cleanup after test."""
        created_entities.append((entity_set, entity_key))

    yield register_for_cleanup

    # Cleanup logic would go here, but for sandbox testing
    # we typically don't create/modify data, so this is placeholder


# Data validation fixtures


@pytest.fixture
def entity_validator():
    """Fixture to validate entity data structures."""

    def validate_customer(customer_data: dict) -> bool:
        """Validate customer entity data."""
        required_fields = ["CustomerAccount", "CustomerName"]
        return all(field in customer_data for field in required_fields)

    def validate_vendor(vendor_data: dict) -> bool:
        """Validate vendor entity data."""
        required_fields = ["VendorAccount", "VendorName"]
        return all(field in vendor_data for field in required_fields)

    def validate_odata_response(response: dict) -> bool:
        """Validate OData response structure."""
        if "value" in response:
            return isinstance(response["value"], list)
        return "@odata.context" in response

    def validate_company(company_data: dict) -> bool:
        """Validate company entity data."""
        required_fields = ["DataAreaId"]
        return all(field in company_data for field in required_fields)

    def validate_legal_entity(legal_entity_data: dict) -> bool:
        """Validate legal entity data."""
        # Legal entities might have different field names in different environments
        possible_id_fields = ["DataAreaId", "CompanyCode", "LegalEntityId"]
        return any(field in legal_entity_data for field in possible_id_fields)

    return {
        "customer": validate_customer,
        "vendor": validate_vendor,
        "company": validate_company,
        "legal_entity": validate_legal_entity,
        "odata_response": validate_odata_response,
    }
