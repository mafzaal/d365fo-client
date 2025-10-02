"""Test to verify API Key authentication header format."""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bearer_auth_backend_with_api_key():
    """Test that BearerAuthBackend can verify API keys sent as Bearer tokens."""
    from pydantic import SecretStr
    from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
    from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier

    # Create API Key provider
    provider = APIKeyVerifier(
        api_key=SecretStr("test-api-key-12345")
    )

    # Create BearerAuthBackend (this is what FastMCP uses)
    backend = BearerAuthBackend(token_verifier=provider)

    # Mock HTTP connection with Authorization: Bearer header
    class MockConnection:
        def __init__(self, auth_header):
            self.headers = {"authorization": auth_header}

    # Test 1: Correct format - Authorization: Bearer <api-key>
    conn_valid = MockConnection("Bearer test-api-key-12345")
    result = await backend.authenticate(conn_valid)

    assert result is not None, "Authentication should succeed with correct API key"
    credentials, user = result
    assert "authenticated" not in credentials.scopes  # API keys don't have scopes by default
    assert user.username == "api_key_client"

    # Test 2: Wrong API key
    conn_wrong_key = MockConnection("Bearer wrong-key")
    result = await backend.authenticate(conn_wrong_key)
    assert result is None, "Authentication should fail with wrong API key"

    # Test 3: Missing Bearer prefix
    conn_no_bearer = MockConnection("test-api-key-12345")
    result = await backend.authenticate(conn_no_bearer)
    assert result is None, "Authentication should fail without Bearer prefix"

    # Test 4: Custom header (X-API-Key) - This WON'T work with BearerAuthBackend
    class MockConnectionCustomHeader:
        headers = {"x-api-key": "test-api-key-12345"}

    conn_custom = MockConnectionCustomHeader()
    result = await backend.authenticate(conn_custom)
    assert result is None, "BearerAuthBackend doesn't support custom headers"


@pytest.mark.integration
def test_api_key_documentation():
    """Test that documentation is accurate about header format."""
    import d365fo_client.mcp.auth_server.auth.providers.apikey as apikey_module

    # Check that the module docstring mentions Authorization: Bearer
    assert "Authorization: Bearer" in apikey_module.__doc__
    assert "Authorization header" in apikey_module.__doc__
