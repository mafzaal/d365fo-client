"""Unit tests for enhanced authentication manager functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client.auth import AuthenticationManager
from d365fo_client.credential_sources import (
    EnvironmentCredentialSource,
    KeyVaultCredentialSource,
)
from d365fo_client.models import FOClientConfig


class TestEnhancedAuthenticationManager:
    """Test enhanced AuthenticationManager with credential source support."""

    @pytest.mark.asyncio
    async def test_setup_credentials_default_credentials(self):
        """Test credential setup with default credentials."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            credential_source=None,  # None means use default credentials
        )

        auth_manager = AuthenticationManager(config)
        await auth_manager._setup_credentials()

        # Should use DefaultAzureCredential
        from azure.identity import DefaultAzureCredential

        assert isinstance(auth_manager.credential, DefaultAzureCredential)

    @pytest.mark.asyncio
    async def test_setup_credentials_client_secret(self):
        """Test credential setup with client secret credentials."""
        credential_source = EnvironmentCredentialSource()
        config = FOClientConfig(
            base_url="https://test.dynamics.com", credential_source=credential_source
        )

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager to return test credentials
        mock_credentials = ("test-client-id", "test-client-secret", "test-tenant-id")
        auth_manager._credential_manager.get_credentials = AsyncMock(
            return_value=mock_credentials
        )

        await auth_manager._setup_credentials()

        # Should use ClientSecretCredential
        from azure.identity import ClientSecretCredential

        assert isinstance(auth_manager.credential, ClientSecretCredential)

    @pytest.mark.asyncio
    async def test_setup_credentials_environment_source(self):
        """Test credential setup with environment credential source."""
        credential_source = EnvironmentCredentialSource()

        # Create config with credential_source attribute
        config = FOClientConfig(base_url="https://test.dynamics.com")
        config.credential_source = credential_source

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager to return test credentials
        mock_credentials = ("test-client-id", "test-client-secret", "test-tenant-id")
        auth_manager._credential_manager.get_credentials = AsyncMock(
            return_value=mock_credentials
        )

        await auth_manager._setup_credentials()

        # Should use ClientSecretCredential with credentials from source
        from azure.identity import ClientSecretCredential

        assert isinstance(auth_manager.credential, ClientSecretCredential)

        # Verify credential manager was called
        auth_manager._credential_manager.get_credentials.assert_called_once_with(
            credential_source
        )

    @pytest.mark.asyncio
    async def test_setup_credentials_keyvault_source(self):
        """Test credential setup with Key Vault credential source."""
        credential_source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id",
            client_secret_secret_name="client-secret",
            tenant_id_secret_name="tenant-id",
        )

        # Create config with credential_source attribute
        config = FOClientConfig(base_url="https://test.dynamics.com")
        config.credential_source = credential_source

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager to return test credentials
        mock_credentials = ("kv-client-id", "kv-client-secret", "kv-tenant-id")
        auth_manager._credential_manager.get_credentials = AsyncMock(
            return_value=mock_credentials
        )

        await auth_manager._setup_credentials()

        # Should use ClientSecretCredential with credentials from Key Vault
        from azure.identity import ClientSecretCredential

        assert isinstance(auth_manager.credential, ClientSecretCredential)

    @pytest.mark.asyncio
    async def test_setup_credentials_source_failure(self):
        """Test credential setup failure with credential source."""
        credential_source = EnvironmentCredentialSource()

        # Create config with credential_source attribute
        config = FOClientConfig(base_url="https://test.dynamics.com")
        config.credential_source = credential_source

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager to raise an exception
        auth_manager._credential_manager.get_credentials = AsyncMock(
            side_effect=ValueError("Environment variables not found")
        )

        with pytest.raises(ValueError) as exc_info:
            await auth_manager._setup_credentials()

        assert "Failed to setup credentials from source" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_token_with_credential_source(self):
        """Test token retrieval with credential source configuration."""
        credential_source = EnvironmentCredentialSource()

        # Create config with credential_source attribute
        config = FOClientConfig(base_url="https://test.dynamics.com")
        config.credential_source = credential_source

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager and token retrieval
        mock_credentials = ("test-client-id", "test-client-secret", "test-tenant-id")
        auth_manager._credential_manager.get_credentials = AsyncMock(
            return_value=mock_credentials
        )

        # Mock the token response
        mock_token = MagicMock()
        mock_token.token = "test-access-token"
        mock_token.expires_on = 9999999999  # Far future

        # Mock the credential and its get_token method
        mock_credential_instance = MagicMock()
        mock_credential_instance.get_token.return_value = mock_token

        with patch(
            "d365fo_client.auth.ClientSecretCredential",
            return_value=mock_credential_instance,
        ):
            token = await auth_manager.get_token()

            assert token == "test-access-token"
            assert auth_manager._token == "test-access-token"

    @pytest.mark.asyncio
    async def test_get_token_localhost(self):
        """Test token retrieval for localhost (mock server)."""
        config = FOClientConfig(
            base_url="http://localhost:8080",
            credential_source=None,  # Use default credentials
        )

        auth_manager = AuthenticationManager(config)
        token = await auth_manager.get_token()

        assert token == "mock-token-for-localhost"

    @pytest.mark.asyncio
    async def test_get_token_cached(self):
        """Test token retrieval with cached token."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            credential_source=None,  # Use default credentials
        )

        auth_manager = AuthenticationManager(config)

        # Set up cached token (valid and not expired)
        auth_manager._token = "cached-token"
        auth_manager._token_expires = 9999999999  # Far future

        # Pre-set a credential to avoid setup
        auth_manager.credential = MagicMock()

        token = await auth_manager.get_token()

        assert token == "cached-token"
        # Credential should not be called for cached token
        auth_manager.credential.get_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_credentials(self):
        """Test credential invalidation functionality."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            credential_source=None,  # Use default credentials
        )

        auth_manager = AuthenticationManager(config)

        # Set up some state
        auth_manager._token = "test-token"
        auth_manager._token_expires = 9999999999
        auth_manager.credential = MagicMock()

        await auth_manager.invalidate_credentials()

        # All state should be cleared
        assert auth_manager._token is None
        assert auth_manager._token_expires is None
        assert auth_manager.credential is None

    def test_get_credential_cache_stats(self):
        """Test credential cache statistics retrieval."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            credential_source=None,  # Use default credentials
        )

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager stats
        auth_manager._credential_manager.get_cache_stats = MagicMock(
            return_value={"total_cached": 2, "expired": 1, "active": 1}
        )

        stats = auth_manager.get_credential_cache_stats()

        assert stats["total_cached"] == 2
        assert stats["expired"] == 1
        assert stats["active"] == 1

    def test_get_credential_cache_stats_no_manager(self):
        """Test credential cache statistics when no manager exists."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            credential_source=None,  # Use default credentials
        )

        auth_manager = AuthenticationManager(config)

        # Remove credential manager to simulate old behavior
        delattr(auth_manager, "_credential_manager")

        stats = auth_manager.get_credential_cache_stats()

        assert stats == {"total_cached": 0, "expired": 0, "active": 0}

    @pytest.mark.asyncio
    async def test_backward_compatibility_existing_config(self):
        """Test that existing configurations continue to work without changes."""
        # The old parameters are now migrated to credential_source automatically
        # So we directly use credential_source for backward compatibility
        from d365fo_client.credential_sources import EnvironmentCredentialSource

        credential_source = EnvironmentCredentialSource()
        config = FOClientConfig(
            base_url="https://test.dynamics.com", credential_source=credential_source
        )

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager
        mock_credentials = (
            "existing-client-id",
            "existing-client-secret",
            "existing-tenant-id",
        )
        auth_manager._credential_manager.get_credentials = AsyncMock(
            return_value=mock_credentials
        )

        await auth_manager._setup_credentials()

        # Should use ClientSecretCredential with credentials from source
        from azure.identity import ClientSecretCredential

        assert isinstance(auth_manager.credential, ClientSecretCredential)

    @pytest.mark.asyncio
    async def test_credential_source_takes_precedence(self):
        """Test that credential_source takes precedence."""
        credential_source = EnvironmentCredentialSource()

        # Create config with credential_source
        config = FOClientConfig(
            base_url="https://test.dynamics.com", credential_source=credential_source
        )

        auth_manager = AuthenticationManager(config)

        # Mock the credential manager to return different credentials
        mock_credentials = ("new-client-id", "new-client-secret", "new-tenant-id")
        auth_manager._credential_manager.get_credentials = AsyncMock(
            return_value=mock_credentials
        )

        await auth_manager._setup_credentials()

        # Should use credentials from source
        auth_manager._credential_manager.get_credentials.assert_called_once_with(
            credential_source
        )
