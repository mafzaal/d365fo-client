"""Integration test for API Key authentication server startup."""

import os

import pytest


@pytest.mark.integration
def test_api_key_settings_configured():
    """Test that API key settings can be configured from environment."""
    # Set environment variables
    os.environ["D365FO_MCP_API_KEY_VALUE"] = "test-integration-key"

    from d365fo_client.settings import get_settings, reset_settings

    # Reset settings to reload from environment
    reset_settings()
    settings = get_settings(reload=True)

    assert settings.has_mcp_api_key_auth() is True
    assert settings.mcp_api_key_value is not None
    assert settings.mcp_api_key_value.get_secret_value() == "test-integration-key"

    # Clean up
    del os.environ["D365FO_MCP_API_KEY_VALUE"]
    reset_settings()


@pytest.mark.integration
def test_api_key_provider_initialization():
    """Test that API Key provider can be initialized."""
    from pydantic import SecretStr

    from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier

    provider = APIKeyVerifier(
        api_key=SecretStr("test-key"), base_url="http://localhost:8000"
    )

    assert provider.api_key.get_secret_value() == "test-key"
    assert (
        str(provider.base_url) == "http://localhost:8000/"
    )  # AnyHttpUrl adds trailing slash


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_key_token_verification():
    """Test that API Key provider can verify tokens."""
    from pydantic import SecretStr

    from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier

    provider = APIKeyVerifier(api_key=SecretStr("my-secret-key"))

    # Valid token
    token = await provider.verify_token("my-secret-key")
    assert token is not None
    assert token.token == "my-secret-key"
    assert token.client_id == "api_key_client"

    # Invalid token
    invalid_token = await provider.verify_token("wrong-key")
    assert invalid_token is None


@pytest.mark.integration
def test_fastmcp_with_api_key_config():
    """Test that FastMCP can be configured with API Key authentication."""
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.fastmcp import FastMCP
    from pydantic import AnyHttpUrl, SecretStr

    from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier

    # Create API Key provider
    api_key_provider = APIKeyVerifier(
        api_key=SecretStr("test-fastmcp-key"), base_url="http://localhost:8000"
    )

    # Create minimal auth settings WITHOUT resource_server_url
    # This prevents OAuth-specific metadata endpoints from being created
    auth_settings = AuthSettings(
        issuer_url=AnyHttpUrl("http://localhost:8000"),
        resource_server_url=None,  # Don't create OAuth metadata endpoints
        required_scopes=[],
    )

    # This should not raise an error
    mcp = FastMCP(
        name="test-server",
        token_verifier=api_key_provider,
        auth=auth_settings,
        host="127.0.0.1",
        port=8001,  # Use different port to avoid conflicts
    )

    assert mcp.name == "test-server"
    assert mcp._token_verifier is not None
    assert mcp.settings.auth is not None
    assert mcp.settings.auth.resource_server_url is None  # Verify no OAuth metadata
    assert mcp._auth_server_provider is None  # Verify no OAuth provider
