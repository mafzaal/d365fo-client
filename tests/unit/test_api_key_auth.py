"""Unit tests for API Key authentication."""

import pytest
from pydantic import SecretStr

from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier
from d365fo_client.mcp.auth_server.auth.auth import AccessToken


class TestAPIKeyVerifier:
    """Tests for APIKeyVerifier."""

    def test_init(self):
        """Test initialization."""
        provider = APIKeyVerifier(api_key=SecretStr("test-key"))

        assert provider.api_key.get_secret_value() == "test-key"

    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful token verification."""
        provider = APIKeyVerifier(api_key=SecretStr("test-secret-key"))

        token = await provider.verify_token("test-secret-key")

        assert token is not None
        assert isinstance(token, AccessToken)
        assert token.token == "test-secret-key"
        assert token.client_id == "api_key_client"

    @pytest.mark.asyncio
    async def test_verify_token_failure(self):
        """Test token verification fails with wrong key."""
        provider = APIKeyVerifier(api_key=SecretStr("test-secret-key"))

        token = await provider.verify_token("wrong-key")

        assert token is None

    @pytest.mark.asyncio
    async def test_verify_token_with_scopes(self):
        """Test token verification includes required scopes."""
        provider = APIKeyVerifier(
            api_key=SecretStr("test-key"),
            required_scopes=["read", "write"]
        )

        token = await provider.verify_token("test-key")

        assert token is not None
        assert token.scopes == ["read", "write"]

    @pytest.mark.asyncio
    async def test_verify_token_no_expiration(self):
        """Test that API key tokens don't expire."""
        provider = APIKeyVerifier(api_key=SecretStr("test-key"))

        token = await provider.verify_token("test-key")

        assert token is not None
        assert token.expires_at is None  # API keys don't expire

    @pytest.mark.asyncio
    async def test_verify_token_constant_time_comparison(self):
        """Test that token verification uses constant-time comparison."""
        import time

        provider = APIKeyVerifier(api_key=SecretStr("a" * 64))

        # Test with completely wrong key
        start = time.perf_counter()
        await provider.verify_token("b" * 64)
        time_wrong = time.perf_counter() - start

        # Test with almost correct key (differs only in last character)
        start = time.perf_counter()
        await provider.verify_token("a" * 63 + "b")
        time_almost = time.perf_counter() - start

        # Timing should be similar (within reasonable tolerance)
        assert abs(time_wrong - time_almost) < 0.001  # 1ms tolerance


class TestAPIKeyVerifierSecurity:
    """Security-focused tests for API key authentication."""

    def test_secret_str_prevents_logging(self):
        """Test that SecretStr prevents accidental key exposure."""
        api_key = SecretStr("super-secret-key")
        provider = APIKeyVerifier(api_key=api_key)

        # repr should not expose the key
        provider_repr = repr(provider.api_key)
        assert "super-secret-key" not in provider_repr
        assert "SecretStr" in provider_repr

    @pytest.mark.asyncio
    async def test_empty_key_not_accepted(self):
        """Test that empty API key is not accepted."""
        provider = APIKeyVerifier(api_key=SecretStr("real-key"))

        token = await provider.verify_token("")

        assert token is None

    @pytest.mark.asyncio
    async def test_none_key_not_accepted(self):
        """Test that None is not accepted as API key."""
        provider = APIKeyVerifier(api_key=SecretStr("real-key"))

        # This should not raise an error, just return None
        try:
            token = await provider.verify_token(None)  # type: ignore
            # If it doesn't raise, it should return None
            assert token is None
        except (TypeError, AttributeError):
            # If it raises, that's also acceptable
            pass


class TestAPIKeyVerifierIntegrationWithBearerAuthBackend:
    """Tests for integration with FastMCP's BearerAuthBackend."""

    @pytest.mark.asyncio
    async def test_works_with_bearer_auth_backend(self):
        """Test that APIKeyVerifier works with FastMCP's BearerAuthBackend."""
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend

        provider = APIKeyVerifier(api_key=SecretStr("my-api-key-123"))
        backend = BearerAuthBackend(token_verifier=provider)

        # Mock HTTP connection with Authorization: Bearer header
        class MockConnection:
            headers = {"authorization": "Bearer my-api-key-123"}

        conn = MockConnection()
        result = await backend.authenticate(conn)

        assert result is not None
        credentials, user = result
        assert user.username == "api_key_client"

    @pytest.mark.asyncio
    async def test_bearer_backend_rejects_invalid_key(self):
        """Test that BearerAuthBackend rejects invalid API keys."""
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend

        provider = APIKeyVerifier(api_key=SecretStr("correct-key"))
        backend = BearerAuthBackend(token_verifier=provider)

        class MockConnection:
            headers = {"authorization": "Bearer wrong-key"}

        conn = MockConnection()
        result = await backend.authenticate(conn)

        assert result is None

    @pytest.mark.asyncio
    async def test_bearer_backend_requires_bearer_prefix(self):
        """Test that BearerAuthBackend requires 'Bearer ' prefix."""
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend

        provider = APIKeyVerifier(api_key=SecretStr("my-key"))
        backend = BearerAuthBackend(token_verifier=provider)

        # Without Bearer prefix
        class MockConnection:
            headers = {"authorization": "my-key"}

        conn = MockConnection()
        result = await backend.authenticate(conn)

        assert result is None  # Should fail without Bearer prefix
