"""
Example demonstrating the new credential source functionality in d365fo-client.

This example shows how to use the enhanced authentication system with different
credential sources including environment variables and Azure Key Vault.
"""

import asyncio
import os
from d365fo_client.credential_sources import (
    EnvironmentCredentialSource,
    KeyVaultCredentialSource,
    CredentialManager,
)
from d365fo_client.auth import AuthenticationManager
from d365fo_client.models import FOClientConfig


async def example_environment_credentials():
    """Example using environment variable credential source."""
    print("=== Environment Variable Credential Source ===")
    
    # Create environment credential source with default variable names
    env_source = EnvironmentCredentialSource()
    print(f"Environment source: {env_source.to_dict()}")
    
    # Create custom environment credential source
    custom_env_source = EnvironmentCredentialSource(
        client_id_var="CUSTOM_CLIENT_ID",
        client_secret_var="CUSTOM_CLIENT_SECRET",
        tenant_id_var="CUSTOM_TENANT_ID"
    )
    print(f"Custom environment source: {custom_env_source.to_dict()}")
    
    # Test credential retrieval (requires environment variables to be set)
    if all(os.getenv(var) for var in ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]):
        credential_manager = CredentialManager()
        try:
            client_id, client_secret, tenant_id = await credential_manager.get_credentials(env_source)
            print(f"Successfully retrieved credentials from environment")
            print(f"Client ID: {client_id[:8]}...")  # Show only first 8 chars for security
        except Exception as e:
            print(f"Failed to retrieve credentials: {e}")
    else:
        print("Environment variables not set - skipping credential retrieval")


async def example_keyvault_credentials():
    """Example using Azure Key Vault credential source."""
    print("\n=== Azure Key Vault Credential Source ===")
    
    # Create Key Vault credential source with default authentication
    kv_source = KeyVaultCredentialSource(
        vault_url="https://myvault.vault.azure.net/",
        client_id_secret_name="d365fo-client-id",
        client_secret_secret_name="d365fo-client-secret",
        tenant_id_secret_name="d365fo-tenant-id"
    )
    print(f"Key Vault source (default auth): {kv_source.to_dict()}")
    
    # Create Key Vault credential source with client secret authentication
    kv_client_auth_source = KeyVaultCredentialSource(
        vault_url="https://myvault.vault.azure.net/",
        client_id_secret_name="d365fo-client-id",
        client_secret_secret_name="d365fo-client-secret",
        tenant_id_secret_name="d365fo-tenant-id",
        keyvault_auth_mode="client_secret",
        keyvault_client_id="kv-auth-client-id",
        keyvault_client_secret="kv-auth-client-secret",
        keyvault_tenant_id="kv-auth-tenant-id"
    )
    print(f"Key Vault source (client secret auth): {kv_client_auth_source.to_dict()}")
    
    # Note: Actual Key Vault retrieval requires real vault and permissions
    print("Note: Key Vault credential retrieval requires real vault setup and permissions")


async def example_authentication_manager_integration():
    """Example showing integration with AuthenticationManager."""
    print("\n=== Authentication Manager Integration ===")
    
    # Create a config with credential source
    config = FOClientConfig(base_url="https://test.dynamics.com")
    
    # Add credential source to config (this would be part of Phase 2)
    credential_source = EnvironmentCredentialSource()
    config.credential_source = credential_source  # This adds the attribute dynamically
    
    # Create authentication manager
    auth_manager = AuthenticationManager(config)
    
    print(f"AuthenticationManager created with credential source: {type(credential_source).__name__}")
    print(f"Credential source config: {credential_source.to_dict()}")
    
    # Show cache statistics
    stats = auth_manager.get_credential_cache_stats()
    print(f"Initial cache stats: {stats}")
    
    # Note: Actual token retrieval requires valid credentials
    print("Note: Token retrieval requires valid credentials to be available")


async def example_credential_caching():
    """Example demonstrating credential caching functionality."""
    print("\n=== Credential Caching Example ===")
    
    # Create credential manager with custom cache TTL
    credential_manager = CredentialManager(cache_ttl_minutes=5)
    
    # Show initial cache stats
    stats = credential_manager.get_cache_stats()
    print(f"Initial cache stats: {stats}")
    
    # Create a credential source
    source = EnvironmentCredentialSource()
    
    if all(os.getenv(var) for var in ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]):
        try:
            # First retrieval - will fetch from source
            print("First credential retrieval (from source)...")
            credentials1 = await credential_manager.get_credentials(source)
            
            # Show cache stats after first retrieval
            stats = credential_manager.get_cache_stats()
            print(f"Cache stats after first retrieval: {stats}")
            
            # Second retrieval - should use cache
            print("Second credential retrieval (from cache)...")
            credentials2 = await credential_manager.get_credentials(source)
            
            print(f"Credentials match: {credentials1 == credentials2}")
            
            # Clear cache
            credential_manager.clear_cache()
            stats = credential_manager.get_cache_stats()
            print(f"Cache stats after clearing: {stats}")
            
        except Exception as e:
            print(f"Credential retrieval failed: {e}")
    else:
        print("Environment variables not set - skipping caching demonstration")


async def example_error_handling():
    """Example demonstrating error handling scenarios."""
    print("\n=== Error Handling Examples ===")
    
    credential_manager = CredentialManager()
    
    # Test with missing environment variables
    print("Testing missing environment variables...")
    missing_env_source = EnvironmentCredentialSource(
        client_id_var="MISSING_CLIENT_ID",
        client_secret_var="MISSING_CLIENT_SECRET",
        tenant_id_var="MISSING_TENANT_ID"
    )
    
    try:
        await credential_manager.get_credentials(missing_env_source)
    except ValueError as e:
        print(f"Expected error for missing env vars: {e}")
    
    # Test with invalid Key Vault authentication mode
    print("Testing invalid Key Vault auth mode...")
    invalid_kv_source = KeyVaultCredentialSource(
        vault_url="https://test.vault.azure.net/",
        client_id_secret_name="test",
        client_secret_secret_name="test",
        tenant_id_secret_name="test",
        keyvault_auth_mode="invalid_mode"
    )
    
    try:
        await credential_manager.get_credentials(invalid_kv_source)
    except ValueError as e:
        print(f"Expected error for invalid auth mode: {e}")


async def main():
    """Run all examples."""
    print("D365FO Client Credential Sources Example")
    print("=" * 50)
    
    await example_environment_credentials()
    await example_keyvault_credentials()
    await example_authentication_manager_integration()
    await example_credential_caching()
    await example_error_handling()
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nNext Steps:")
    print("1. Set environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)")
    print("2. Configure Azure Key Vault with appropriate secrets")
    print("3. Use credential sources in your D365FO client configuration")


if __name__ == "__main__":
    asyncio.run(main())