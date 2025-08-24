"""Integration tests package for d365fo-client.

This package contains integration tests that test the client against real or mock D365 F&O environments.
Integration tests are organized into different tiers:

1. Mock Server Tests (tests/integration/mock_server/) - Fast, reliable, no external dependencies
2. Sandbox Tests (tests/integration/sandbox/) - Against test D365 environments
3. Live Tests (tests/integration/live/) - Against real D365 environments (optional)

Configuration:
- Set INTEGRATION_TEST_LEVEL environment variable to control which tests run
- Values: 'mock', 'sandbox', 'live', 'all'
- Default: 'sandbox' (sandbox environment tests)

Environment Variables:
- D365FO_TEST_BASE_URL: Base URL for test environment
- D365FO_SANDBOX_BASE_URL: Base URL for sandbox environment
- D365FO_LIVE_BASE_URL: Base URL for live environment (if available)
- AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID: Auth credentials
"""

import os

import pytest

# Integration test configuration
INTEGRATION_TEST_LEVEL = os.getenv("INTEGRATION_TEST_LEVEL", "sandbox").lower()


def skip_if_not_level(required_level: str):
    """Decorator to skip tests based on integration test level."""
    levels = ["mock", "sandbox", "live", "all"]

    if INTEGRATION_TEST_LEVEL == "all":
        return pytest.mark.integration

    if required_level not in levels:
        raise ValueError(f"Invalid level: {required_level}. Must be one of {levels}")

    if INTEGRATION_TEST_LEVEL != required_level:
        return pytest.mark.skip(
            f"Skipping {required_level} integration test. Set INTEGRATION_TEST_LEVEL={required_level} to run."
        )

    return pytest.mark.integration


# Test environment configurations
TEST_ENVIRONMENTS = {
    "mock": {
        "base_url": "http://localhost:8000",
        "requires_auth": False,
        "description": "Local mock server",
    },
    "sandbox": {
        "base_url": os.getenv("D365FO_SANDBOX_BASE_URL", "https://test.dynamics.com"),
        "requires_auth": True,
        "description": "D365 F&O test/sandbox environment",
    },
    "live": {
        "base_url": os.getenv("D365FO_LIVE_BASE_URL", "https://prod.dynamics.com"),
        "requires_auth": True,
        "description": "D365 F&O production environment",
    },
}
