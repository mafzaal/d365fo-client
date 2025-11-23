"""Unit tests for credential sources functionality."""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client.credential_sources import (
    CachedCredentials,
    CredentialManager,
    CredentialSource,
    EnvironmentCredentialProvider,
    EnvironmentCredentialSource,
    KeyVaultCredentialProvider,
    KeyVaultCredentialSource,
    create_credential_source,
)


class TestCredentialSourceModels:
    """Test credential source model classes."""

    def test_credential_source_base(self):
        """Test base CredentialSource class."""
        source = CredentialSource(source_type="test")
        assert source.source_type == "test"
        assert source.to_dict() == {"source_type": "test"}

    def test_environment_credential_source_defaults(self):
        """Test EnvironmentCredentialSource with default values."""
        source = EnvironmentCredentialSource()

        assert source.source_type == "environment"
        assert source.client_id_var == "D365FO_CLIENT_ID"
        assert source.client_secret_var == "D365FO_CLIENT_SECRET"
        assert source.tenant_id_var == "D365FO_TENANT_ID"

        expected_dict = {
            "source_type": "environment",
            "client_id_var": "D365FO_CLIENT_ID",
            "client_secret_var": "D365FO_CLIENT_SECRET",
            "tenant_id_var": "D365FO_TENANT_ID",
        }
        assert source.to_dict() == expected_dict

    def test_environment_credential_source_custom(self):
        """Test EnvironmentCredentialSource with custom values."""
        source = EnvironmentCredentialSource(
            client_id_var="CUSTOM_CLIENT_ID",
            client_secret_var="CUSTOM_CLIENT_SECRET",
            tenant_id_var="CUSTOM_TENANT_ID",
        )

        assert source.source_type == "environment"
        assert source.client_id_var == "CUSTOM_CLIENT_ID"
        assert source.client_secret_var == "CUSTOM_CLIENT_SECRET"
        assert source.tenant_id_var == "CUSTOM_TENANT_ID"

    def test_keyvault_credential_source_default_auth(self):
        """Test KeyVaultCredentialSource with default authentication."""
        source = KeyVaultCredentialSource(
            vault_url="https://myvault.vault.azure.net/",
            client_id_secret_name="client-id",
            client_secret_secret_name="client-secret",
            tenant_id_secret_name="tenant-id",
        )

        assert source.source_type == "keyvault"
        assert source.vault_url == "https://myvault.vault.azure.net/"
        assert source.keyvault_auth_mode == "default"
        assert source.keyvault_client_id is None

        expected_dict = {
            "source_type": "keyvault",
            "vault_url": "https://myvault.vault.azure.net/",
            "client_id_secret_name": "client-id",
            "client_secret_secret_name": "client-secret",
            "tenant_id_secret_name": "tenant-id",
            "keyvault_auth_mode": "default",
        }
        assert source.to_dict() == expected_dict

    def test_keyvault_credential_source_client_secret_auth(self):
        """Test KeyVaultCredentialSource with client secret authentication."""
        source = KeyVaultCredentialSource(
            vault_url="https://myvault.vault.azure.net/",
            client_id_secret_name="client-id",
            client_secret_secret_name="client-secret",
            tenant_id_secret_name="tenant-id",
            keyvault_auth_mode="client_secret",
            keyvault_client_id="kv-client-id",
            keyvault_client_secret="kv-client-secret",
            keyvault_tenant_id="kv-tenant-id",
        )

        assert source.keyvault_auth_mode == "client_secret"
        assert source.keyvault_client_id == "kv-client-id"

        result_dict = source.to_dict()
        assert result_dict["keyvault_client_id"] == "kv-client-id"
        assert result_dict["keyvault_client_secret"] == "kv-client-secret"
        assert result_dict["keyvault_tenant_id"] == "kv-tenant-id"


class TestCachedCredentials:
    """Test CachedCredentials functionality."""

    def test_cached_credentials_not_expired(self):
        """Test cached credentials that are not expired."""
        future_time = datetime.now() + timedelta(minutes=30)
        cached = CachedCredentials(
            client_id="test-id",
            client_secret="test-secret",
            tenant_id="test-tenant",
            expires_at=future_time,
            source_hash="abc123",
        )

        assert not cached.is_expired()
        assert cached.is_valid_for_source("abc123")
        assert not cached.is_valid_for_source("def456")  # Different hash

    def test_cached_credentials_expired(self):
        """Test cached credentials that are expired."""
        past_time = datetime.now() - timedelta(minutes=30)
        cached = CachedCredentials(
            client_id="test-id",
            client_secret="test-secret",
            tenant_id="test-tenant",
            expires_at=past_time,
            source_hash="abc123",
        )

        assert cached.is_expired()
        assert not cached.is_valid_for_source("abc123")


class TestEnvironmentCredentialProvider:
    """Test EnvironmentCredentialProvider functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.provider = EnvironmentCredentialProvider()

    @pytest.mark.asyncio
    async def test_get_credentials_success(self):
        """Test successful credential retrieval from environment."""
        source = EnvironmentCredentialSource()

        with patch.dict(
            os.environ,
            {
                "D365FO_CLIENT_ID": "test-client-id",
                "D365FO_CLIENT_SECRET": "test-client-secret",
                "D365FO_TENANT_ID": "test-tenant-id",
            },
        ):
            client_id, client_secret, tenant_id = await self.provider.get_credentials(
                source
            )

            assert client_id == "test-client-id"
            assert client_secret == "test-client-secret"
            assert tenant_id == "test-tenant-id"

    @pytest.mark.asyncio
    async def test_get_credentials_custom_vars(self):
        """Test credential retrieval with custom environment variables."""
        source = EnvironmentCredentialSource(
            client_id_var="CUSTOM_CLIENT_ID",
            client_secret_var="CUSTOM_CLIENT_SECRET",
            tenant_id_var="CUSTOM_TENANT_ID",
        )

        with patch.dict(
            os.environ,
            {
                "CUSTOM_CLIENT_ID": "custom-client-id",
                "CUSTOM_CLIENT_SECRET": "custom-client-secret",
                "CUSTOM_TENANT_ID": "custom-tenant-id",
            },
        ):
            client_id, client_secret, tenant_id = await self.provider.get_credentials(
                source
            )

            assert client_id == "custom-client-id"
            assert client_secret == "custom-client-secret"
            assert tenant_id == "custom-tenant-id"

    @pytest.mark.asyncio
    async def test_get_credentials_missing_vars(self):
        """Test error when environment variables are missing."""
        source = EnvironmentCredentialSource()

        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                await self.provider.get_credentials(source)

            assert "Missing required environment variables" in str(exc_info.value)
            assert "D365FO_CLIENT_ID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_credentials_wrong_source_type(self):
        """Test error with wrong source type."""
        source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="test",
            client_secret_secret_name="test",
            tenant_id_secret_name="test",
        )

        with pytest.raises(ValueError) as exc_info:
            await self.provider.get_credentials(source)

        assert "Expected EnvironmentCredentialSource" in str(exc_info.value)


class TestKeyVaultCredentialProvider:
    """Test KeyVaultCredentialProvider functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.provider = KeyVaultCredentialProvider()

    @pytest.mark.asyncio
    async def test_get_credentials_success(self):
        """Test successful credential retrieval from Key Vault."""
        source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id-secret",
            client_secret_secret_name="client-secret-secret",
            tenant_id_secret_name="tenant-id-secret",
        )

        # Mock SecretClient and secrets
        mock_secret_client = MagicMock()
        mock_client_id_secret = MagicMock()
        mock_client_id_secret.value = "kv-client-id"
        mock_client_secret_secret = MagicMock()
        mock_client_secret_secret.value = "kv-client-secret"
        mock_tenant_id_secret = MagicMock()
        mock_tenant_id_secret.value = "kv-tenant-id"

        mock_secret_client.get_secret.side_effect = [
            mock_client_id_secret,
            mock_client_secret_secret,
            mock_tenant_id_secret,
        ]

        with patch(
            "d365fo_client.credential_sources.SecretClient"
        ) as mock_secret_client_class:
            mock_secret_client_class.return_value = mock_secret_client

            client_id, client_secret, tenant_id = await self.provider.get_credentials(
                source
            )

            assert client_id == "kv-client-id"
            assert client_secret == "kv-client-secret"
            assert tenant_id == "kv-tenant-id"

            # Verify SecretClient was called correctly
            mock_secret_client_class.assert_called_once()
            assert mock_secret_client.get_secret.call_count == 3

    @pytest.mark.asyncio
    async def test_get_credentials_with_client_secret_auth(self):
        """Test Key Vault access with client secret authentication."""
        source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id-secret",
            client_secret_secret_name="client-secret-secret",
            tenant_id_secret_name="tenant-id-secret",
            keyvault_auth_mode="client_secret",
            keyvault_client_id="kv-auth-client-id",
            keyvault_client_secret="kv-auth-client-secret",
            keyvault_tenant_id="kv-auth-tenant-id",
        )

        mock_secret_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = "test-value"
        mock_secret_client.get_secret.return_value = mock_secret

        with (
            patch(
                "d365fo_client.credential_sources.SecretClient"
            ) as mock_secret_client_class,
            patch(
                "d365fo_client.credential_sources.ClientSecretCredential"
            ) as mock_cred_class,
        ):

            mock_secret_client_class.return_value = mock_secret_client

            await self.provider.get_credentials(source)

            # Verify ClientSecretCredential was created with correct parameters
            mock_cred_class.assert_called_once_with(
                tenant_id="kv-auth-tenant-id",
                client_id="kv-auth-client-id",
                client_secret="kv-auth-client-secret",
            )

    @pytest.mark.asyncio
    async def test_get_credentials_missing_kv_auth_params(self):
        """Test error when Key Vault client secret auth parameters are missing."""
        source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id-secret",
            client_secret_secret_name="client-secret-secret",
            tenant_id_secret_name="tenant-id-secret",
            keyvault_auth_mode="client_secret",
            # Missing keyvault_client_id, keyvault_client_secret, keyvault_tenant_id
        )

        with pytest.raises(ValueError) as exc_info:
            await self.provider.get_credentials(source)

        assert "Key Vault client_secret authentication requires" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_credentials_invalid_auth_mode(self):
        """Test error with invalid Key Vault authentication mode."""
        source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id-secret",
            client_secret_secret_name="client-secret-secret",
            tenant_id_secret_name="tenant-id-secret",
            keyvault_auth_mode="invalid_mode",
        )

        with pytest.raises(ValueError) as exc_info:
            await self.provider.get_credentials(source)

        assert "Invalid keyvault_auth_mode" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_credentials_secret_client_caching(self):
        """Test that SecretClient instances are cached."""
        source = KeyVaultCredentialSource(
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id-secret",
            client_secret_secret_name="client-secret-secret",
            tenant_id_secret_name="tenant-id-secret",
        )

        mock_secret_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = "test-value"
        mock_secret_client.get_secret.return_value = mock_secret

        with patch(
            "d365fo_client.credential_sources.SecretClient"
        ) as mock_secret_client_class:
            mock_secret_client_class.return_value = mock_secret_client

            # First call
            await self.provider.get_credentials(source)
            # Second call with same vault URL
            await self.provider.get_credentials(source)

            # SecretClient should only be created once due to caching
            assert mock_secret_client_class.call_count == 1


class TestCredentialManager:
    """Test CredentialManager functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.manager = CredentialManager(cache_ttl_minutes=30)

    @pytest.mark.asyncio
    async def test_get_credentials_environment_success(self):
        """Test successful credential retrieval from environment via manager."""
        source = EnvironmentCredentialSource()

        with patch.dict(
            os.environ,
            {
                "D365FO_CLIENT_ID": "test-client-id",
                "D365FO_CLIENT_SECRET": "test-client-secret",
                "D365FO_TENANT_ID": "test-tenant-id",
            },
        ):
            client_id, client_secret, tenant_id = await self.manager.get_credentials(
                source
            )

            assert client_id == "test-client-id"
            assert client_secret == "test-client-secret"
            assert tenant_id == "test-tenant-id"

    @pytest.mark.asyncio
    async def test_get_credentials_caching(self):
        """Test credential caching functionality."""
        source = EnvironmentCredentialSource()

        with patch.dict(
            os.environ,
            {
                "D365FO_CLIENT_ID": "test-client-id",
                "D365FO_CLIENT_SECRET": "test-client-secret",
                "D365FO_TENANT_ID": "test-tenant-id",
            },
        ):
            # First call
            result1 = await self.manager.get_credentials(source)
            # Second call should use cache
            result2 = await self.manager.get_credentials(source)

            assert result1 == result2

            # Check cache stats
            stats = self.manager.get_cache_stats()
            assert stats["total_cached"] == 1
            assert stats["active"] == 1

    @pytest.mark.asyncio
    async def test_get_credentials_unsupported_source(self):
        """Test error with unsupported credential source type."""
        # Create a custom source with unsupported type
        source = CredentialSource(source_type="unsupported")

        with pytest.raises(ValueError) as exc_info:
            await self.manager.get_credentials(source)

        assert "Unsupported credential source type: unsupported" in str(exc_info.value)

    def test_clear_cache_all(self):
        """Test clearing all cached credentials."""
        # Manually add some cache entries for testing
        self.manager._credential_cache["env:hash1"] = MagicMock()
        self.manager._credential_cache["kv:hash2"] = MagicMock()

        self.manager.clear_cache()

        assert len(self.manager._credential_cache) == 0

    def test_clear_cache_by_type(self):
        """Test clearing cached credentials by source type."""
        # Manually add some cache entries for testing
        self.manager._credential_cache["environment:hash1"] = MagicMock()
        self.manager._credential_cache["keyvault:hash2"] = MagicMock()

        self.manager.clear_cache(source_type="environment")

        assert len(self.manager._credential_cache) == 1
        assert "keyvault:hash2" in self.manager._credential_cache

    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        # Start with empty cache
        stats = self.manager.get_cache_stats()
        assert stats["total_cached"] == 0
        assert stats["active"] == 0
        assert stats["expired"] == 0

        # Add expired and active entries
        past_time = datetime.now() - timedelta(minutes=30)
        future_time = datetime.now() + timedelta(minutes=30)

        self.manager._credential_cache["expired"] = CachedCredentials(
            client_id="test",
            client_secret="test",
            tenant_id="test",
            expires_at=past_time,
            source_hash="hash1",
        )
        self.manager._credential_cache["active"] = CachedCredentials(
            client_id="test",
            client_secret="test",
            tenant_id="test",
            expires_at=future_time,
            source_hash="hash2",
        )

        stats = self.manager.get_cache_stats()
        assert stats["total_cached"] == 2
        assert stats["active"] == 1
        assert stats["expired"] == 1


class TestCreateCredentialSource:
    """Test credential source factory function."""

    def test_create_environment_source(self):
        """Test creating environment credential source."""
        source = create_credential_source("environment")

        assert isinstance(source, EnvironmentCredentialSource)
        assert source.source_type == "environment"

    def test_create_environment_source_with_params(self):
        """Test creating environment credential source with custom parameters."""
        source = create_credential_source(
            "environment",
            client_id_var="CUSTOM_CLIENT_ID",
            client_secret_var="CUSTOM_CLIENT_SECRET",
            tenant_id_var="CUSTOM_TENANT_ID",
        )

        assert isinstance(source, EnvironmentCredentialSource)
        assert source.client_id_var == "CUSTOM_CLIENT_ID"

    def test_create_keyvault_source(self):
        """Test creating Key Vault credential source."""
        source = create_credential_source(
            "keyvault",
            vault_url="https://test.vault.azure.net/",
            client_id_secret_name="client-id",
            client_secret_secret_name="client-secret",
            tenant_id_secret_name="tenant-id",
        )

        assert isinstance(source, KeyVaultCredentialSource)
        assert source.source_type == "keyvault"
        assert source.vault_url == "https://test.vault.azure.net/"

    def test_create_unsupported_source(self):
        """Test error when creating unsupported credential source type."""
        with pytest.raises(ValueError) as exc_info:
            create_credential_source("unsupported")

        assert "Unsupported credential source type: unsupported" in str(exc_info.value)
