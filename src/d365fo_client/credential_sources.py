"""Credential source management for D365 F&O client authentication."""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)


@dataclass
class CredentialSource:
    """Base credential source configuration."""
    
    source_type: str  # "environment", "keyvault", "file", etc.
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return {"source_type": self.source_type}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CredentialSource":
        """Create CredentialSource from dictionary."""
        source_type = data.get("source_type")
        
        if source_type == "environment":
            return EnvironmentCredentialSource(
                client_id_var=data.get("client_id_var", "D365FO_CLIENT_ID"),
                client_secret_var=data.get("client_secret_var", "D365FO_CLIENT_SECRET"),
                tenant_id_var=data.get("tenant_id_var", "D365FO_TENANT_ID")
            )
        elif source_type == "keyvault":
            return KeyVaultCredentialSource(
                vault_url=data.get("vault_url", ""),
                client_id_secret_name=data.get("client_id_secret_name", "D365FO_CLIENT_ID"),
                client_secret_secret_name=data.get("client_secret_secret_name", "D365FO_CLIENT_SECRET"),
                tenant_id_secret_name=data.get("tenant_id_secret_name", "D365FO_TENANT_ID"),
                keyvault_auth_mode=data.get("keyvault_auth_mode", "default"),
                keyvault_client_id=data.get("keyvault_client_id"),
                keyvault_client_secret=data.get("keyvault_client_secret"),
                keyvault_tenant_id=data.get("keyvault_tenant_id")
            )
        else:
            raise ValueError(f"Unknown credential source type: {source_type}")


@dataclass 
class EnvironmentCredentialSource(CredentialSource):
    """Environment variable credential source."""
    
    client_id_var: str = "D365FO_CLIENT_ID"
    client_secret_var: str = "D365FO_CLIENT_SECRET"
    tenant_id_var: str = "D365FO_TENANT_ID"

    def __init__(self, client_id_var: str = "D365FO_CLIENT_ID",
                 client_secret_var: str = "D365FO_CLIENT_SECRET",
                 tenant_id_var: str = "D365FO_TENANT_ID"):
        """Initialize environment credential source."""
        super().__init__(source_type="environment")
        self.client_id_var = client_id_var
        self.client_secret_var = client_secret_var
        self.tenant_id_var = tenant_id_var
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "source_type": self.source_type,
            "client_id_var": self.client_id_var,
            "client_secret_var": self.client_secret_var,
            "tenant_id_var": self.tenant_id_var,
        }


@dataclass
class KeyVaultCredentialSource(CredentialSource):
    """Azure Key Vault credential source."""
    
    vault_url: str
    client_id_secret_name: str
    client_secret_secret_name: str
    tenant_id_secret_name: str
    # Authentication to Key Vault itself
    keyvault_auth_mode: str = "default"  # "default" or "client_secret"
    keyvault_client_id: Optional[str] = None
    keyvault_client_secret: Optional[str] = None
    keyvault_tenant_id: Optional[str] = None
    
    def __init__(self, vault_url: str, client_id_secret_name: str,
                 client_secret_secret_name: str, tenant_id_secret_name: str,
                 keyvault_auth_mode: str = "default",
                 keyvault_client_id: Optional[str] = None,
                 keyvault_client_secret: Optional[str] = None,
                 keyvault_tenant_id: Optional[str] = None):
        """Initialize Key Vault credential source."""
        super().__init__(source_type="keyvault")
        self.vault_url = vault_url
        self.client_id_secret_name = client_id_secret_name
        self.client_secret_secret_name = client_secret_secret_name
        self.tenant_id_secret_name = tenant_id_secret_name
        self.keyvault_auth_mode = keyvault_auth_mode
        self.keyvault_client_id = keyvault_client_id
        self.keyvault_client_secret = keyvault_client_secret
        self.keyvault_tenant_id = keyvault_tenant_id
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        result = {
            "source_type": self.source_type,
            "vault_url": self.vault_url,
            "client_id_secret_name": self.client_id_secret_name,
            "client_secret_secret_name": self.client_secret_secret_name,
            "tenant_id_secret_name": self.tenant_id_secret_name,
            "keyvault_auth_mode": self.keyvault_auth_mode,
        }
        
        # Only include Key Vault auth credentials if using client_secret mode
        if self.keyvault_auth_mode == "client_secret":
            result.update({
                "keyvault_client_id": self.keyvault_client_id or "",
                "keyvault_client_secret": self.keyvault_client_secret or "",
                "keyvault_tenant_id": self.keyvault_tenant_id or "",
            })
        
        return result


@dataclass
class CachedCredentials:
    """Cached credential information with expiry."""
    
    client_id: str
    client_secret: str
    tenant_id: str
    expires_at: datetime
    source_hash: str  # Hash of source configuration for invalidation
    
    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        return datetime.now() >= self.expires_at
    
    def is_valid_for_source(self, source_hash: str) -> bool:
        """Check if cached credentials are valid for the given source."""
        return not self.is_expired() and self.source_hash == source_hash


class CredentialProvider(ABC):
    """Base class for credential providers."""
    
    @abstractmethod
    async def get_credentials(self, source: CredentialSource) -> Tuple[str, str, str]:
        """
        Retrieve credentials from the source.
        
        Args:
            source: Credential source configuration
            
        Returns:
            Tuple of (client_id, client_secret, tenant_id)
            
        Raises:
            ValueError: If credentials cannot be retrieved or are invalid
            Exception: For other retrieval errors
        """
        pass
    
    def _get_source_hash(self, source: CredentialSource) -> str:
        """Generate a hash for the credential source configuration."""
        import hashlib
        source_data = str(source.to_dict())
        return hashlib.sha256(source_data.encode()).hexdigest()[:16]


class EnvironmentCredentialProvider(CredentialProvider):
    """Provides credentials from environment variables."""
    
    async def get_credentials(self, source: CredentialSource) -> Tuple[str, str, str]:
        """
        Retrieve credentials from environment variables.
        
        Args:
            source: EnvironmentCredentialSource configuration
            
        Returns:
            Tuple of (client_id, client_secret, tenant_id)
            
        Raises:
            ValueError: If required environment variables are missing
        """
        if not isinstance(source, EnvironmentCredentialSource):
            raise ValueError(f"Expected EnvironmentCredentialSource, got {type(source)}")
        
        client_id = os.getenv(source.client_id_var)
        client_secret = os.getenv(source.client_secret_var)
        tenant_id = os.getenv(source.tenant_id_var)
        
        missing_vars = []
        if not client_id:
            missing_vars.append(source.client_id_var)
        if not client_secret:
            missing_vars.append(source.client_secret_var)
        if not tenant_id:
            missing_vars.append(source.tenant_id_var)
            
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        logger.debug(f"Retrieved credentials from environment variables: {source.client_id_var}, {source.client_secret_var}, {source.tenant_id_var}")
        assert client_id and client_secret and tenant_id  # For type checker

        return client_id, client_secret, tenant_id


class KeyVaultCredentialProvider(CredentialProvider):
    """Provides credentials from Azure Key Vault."""
    
    def __init__(self):
        """Initialize Key Vault credential provider."""
        self._secret_clients: Dict[str, SecretClient] = {}
    
    async def get_credentials(self, source: CredentialSource) -> Tuple[str, str, str]:
        """
        Retrieve credentials from Azure Key Vault.
        
        Args:
            source: KeyVaultCredentialSource configuration
            
        Returns:
            Tuple of (client_id, client_secret, tenant_id)
            
        Raises:
            ValueError: If Key Vault access fails or secrets are missing
        """
        if not isinstance(source, KeyVaultCredentialSource):
            raise ValueError(f"Expected KeyVaultCredentialSource, got {type(source)}")
        
        try:
            secret_client = self._get_secret_client(source)
            
            # Retrieve secrets from Key Vault
            client_id_secret = secret_client.get_secret(source.client_id_secret_name)
            client_secret_secret = secret_client.get_secret(source.client_secret_secret_name)
            tenant_id_secret = secret_client.get_secret(source.tenant_id_secret_name)
            
            client_id = client_id_secret.value
            client_secret = client_secret_secret.value
            tenant_id = tenant_id_secret.value
            
            if not all([client_id, client_secret, tenant_id]):
                raise ValueError("One or more secrets retrieved from Key Vault are empty")
            
            logger.debug(f"Retrieved credentials from Key Vault: {source.vault_url}")
            assert client_id and client_secret and tenant_id  # For type checker
            return client_id, client_secret, tenant_id
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials from Key Vault {source.vault_url}: {e}")
            raise ValueError(f"Key Vault credential retrieval failed: {e}")
    
    def _get_secret_client(self, source: KeyVaultCredentialSource) -> SecretClient:
        """
        Get or create a SecretClient for the Key Vault.
        
        Args:
            source: KeyVaultCredentialSource configuration
            
        Returns:
            SecretClient instance
        """
        vault_url = source.vault_url
        
        # Return cached client if available
        if vault_url in self._secret_clients:
            return self._secret_clients[vault_url]
        
        # Create credential for Key Vault authentication
        if source.keyvault_auth_mode == "default":
            credential = DefaultAzureCredential()
            logger.debug(f"Using default credentials for Key Vault authentication: {vault_url}")
        elif source.keyvault_auth_mode == "client_secret":
            if not all([source.keyvault_client_id, source.keyvault_client_secret, source.keyvault_tenant_id]):
                raise ValueError("Key Vault client_secret authentication requires keyvault_client_id, keyvault_client_secret, and keyvault_tenant_id")
            
            assert source.keyvault_client_id and source.keyvault_client_secret and source.keyvault_tenant_id  # For type checker
            
            credential = ClientSecretCredential(
                tenant_id=source.keyvault_tenant_id,
                client_id=source.keyvault_client_id,
                client_secret=source.keyvault_client_secret,
            )
            logger.debug(f"Using client secret credentials for Key Vault authentication: {vault_url}")
        else:
            raise ValueError(f"Invalid keyvault_auth_mode: {source.keyvault_auth_mode}. Must be 'default' or 'client_secret'")
        
        # Create and cache the SecretClient
        secret_client = SecretClient(vault_url=vault_url, credential=credential)
        self._secret_clients[vault_url] = secret_client
        
        return secret_client


class CredentialManager:
    """
    Manages credential retrieval from multiple sources with caching.
    
    This class provides a unified interface for retrieving credentials from
    various sources (environment variables, Key Vault, etc.) with automatic
    caching and validation.
    """
    
    def __init__(self, cache_ttl_minutes: int = 30):
        """
        Initialize credential manager.
        
        Args:
            cache_ttl_minutes: Time-to-live for cached credentials in minutes
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self._credential_cache: Dict[str, CachedCredentials] = {}
        self._providers: Dict[str, CredentialProvider] = {
            "environment": EnvironmentCredentialProvider(),
            "keyvault": KeyVaultCredentialProvider(),
        }
    
    async def get_credentials(self, source: CredentialSource) -> Tuple[str, str, str]:
        """
        Retrieve credentials from the specified source with caching.
        
        Args:
            source: Credential source configuration
            
        Returns:
            Tuple of (client_id, client_secret, tenant_id)
            
        Raises:
            ValueError: If source type is unsupported or credentials cannot be retrieved
        """
        # Check cache first
        source_hash = self._get_source_hash(source)
        cache_key = f"{source.source_type}:{source_hash}"
        
        if cache_key in self._credential_cache:
            cached = self._credential_cache[cache_key]
            if cached.is_valid_for_source(source_hash):
                logger.debug(f"Using cached credentials for source type: {source.source_type}")
                return cached.client_id, cached.client_secret, cached.tenant_id
            else:
                # Remove expired cache entry
                del self._credential_cache[cache_key]
                logger.debug(f"Expired cached credentials removed for source type: {source.source_type}")
        
        # Retrieve from provider
        provider = self._providers.get(source.source_type)
        if not provider:
            raise ValueError(f"Unsupported credential source type: {source.source_type}")
        
        client_id, client_secret, tenant_id = await provider.get_credentials(source)
        
        # Cache the credentials
        expires_at = datetime.now() + timedelta(minutes=self.cache_ttl_minutes)
        cached_credentials = CachedCredentials(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            expires_at=expires_at,
            source_hash=source_hash,
        )
        self._credential_cache[cache_key] = cached_credentials
        
        logger.debug(f"Retrieved and cached credentials from source type: {source.source_type}")
        return client_id, client_secret, tenant_id
    
    def _get_source_hash(self, source: CredentialSource) -> str:
        """Generate a hash for the credential source configuration."""
        import hashlib
        source_data = str(source.to_dict())
        return hashlib.sha256(source_data.encode()).hexdigest()[:16]
    
    def clear_cache(self, source_type: Optional[str] = None) -> None:
        """
        Clear credential cache.
        
        Args:
            source_type: If specified, only clear cache for this source type.
                        If None, clear all cached credentials.
        """
        if source_type is None:
            self._credential_cache.clear()
            logger.debug("Cleared all cached credentials")
        else:
            keys_to_remove = [key for key in self._credential_cache.keys() if key.startswith(f"{source_type}:")]
            for key in keys_to_remove:
                del self._credential_cache[key]
            logger.debug(f"Cleared cached credentials for source type: {source_type}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_cached = len(self._credential_cache)
        expired_count = sum(1 for cached in self._credential_cache.values() if cached.is_expired())
        
        return {
            "total_cached": total_cached,
            "expired": expired_count,
            "active": total_cached - expired_count,
        }


def create_credential_source(source_type: str, **kwargs) -> CredentialSource:
    """
    Factory function to create credential source instances.
    
    Args:
        source_type: Type of credential source ("environment", "keyvault")
        **kwargs: Source-specific configuration parameters
        
    Returns:
        CredentialSource instance
        
    Raises:
        ValueError: If source_type is unsupported
    """
    if source_type == "environment":
        return EnvironmentCredentialSource(**kwargs)
    elif source_type == "keyvault":
        return KeyVaultCredentialSource(**kwargs)
    else:
        raise ValueError(f"Unsupported credential source type: {source_type}")