#!/usr/bin/env python3
"""
D365 F&O Settings Example

This example demonstrates how to use the new Pydantic settings model
for managing D365FO environment variables with type safety and validation.

Usage:
    python settings_example.py

Environment Variables:
    D365FO_BASE_URL - D365 F&O environment URL
    D365FO_CLIENT_ID, D365FO_CLIENT_SECRET, D365FO_TENANT_ID - Azure AD credentials
    D365FO_LOG_LEVEL - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    D365FO_HTTP_HOST, D365FO_HTTP_PORT - HTTP server configuration
    D365FO_MAX_CONCURRENT_REQUESTS - Performance tuning
    And many more...
"""

import asyncio
import os
import sys

# Add the src directory to Python path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from d365fo_client import FOClient, FOClientConfig, D365FOSettings, get_settings


def demonstrate_settings_usage():
    """Demonstrate various ways to use the D365FOSettings."""
    
    print("🔧 D365FO Pydantic Settings Example")
    print("=" * 45)
    
    # Method 1: Get global settings instance
    print("\\n📋 Method 1: Global Settings Instance")
    settings = get_settings()
    
    print(f"Base URL: {settings.base_url}")
    print(f"HTTP Host: {settings.http_host}")
    print(f"HTTP Port: {settings.http_port}")
    print(f"Log Level: {settings.log_level}")
    print(f"Max Concurrent Requests: {settings.max_concurrent_requests}")
    print(f"Request Timeout: {settings.request_timeout}")
    print(f"Use Label Cache: {settings.use_label_cache}")
    print(f"Cache Directory: {settings.cache_dir}")
    print(f"Metadata Cache Directory: {settings.meta_cache_dir}")
    
    # Method 2: Create settings instance directly
    print("\\n📋 Method 2: Direct Settings Instance")
    custom_settings = D365FOSettings()
    print(f"Transport Protocol: {custom_settings.mcp_transport}")
    print(f"Verify SSL: {custom_settings.verify_ssl}")
    print(f"Debug Mode: {custom_settings.debug}")
    
    # Method 3: Access credential information
    print("\\n🔐 Method 3: Credential Information")
    print(f"Has Client Credentials: {settings.has_client_credentials()}")
    print(f"Startup Mode: {settings.get_startup_mode()}")
    
    if settings.has_client_credentials():
        print("✅ Client credentials are configured")
        print(f"Client ID: {settings.client_id}")
        print(f"Tenant ID: {settings.tenant_id}")
        # Don't print the secret for security
        print(f"Client Secret: {'*' * len(settings.client_secret) if settings.client_secret else 'Not set'}")
    else:
        print("ℹ️  Using default authentication (Azure CLI, Managed Identity, etc.)")
    
    # Method 4: Convert to dictionary format
    print("\\n📝 Method 4: Export Settings")
    settings_dict = settings.to_dict()
    print(f"Settings as dict (first 5 items):")
    for i, (key, value) in enumerate(settings_dict.items()):
        if i >= 5:
            print("  ... (and more)")
            break
        print(f"  {key}: {value}")
    
    # Method 5: Environment variable format
    print("\\n🌍 Method 5: Environment Variables Format")
    env_dict = settings.to_env_dict()
    print("Settings as environment variables (first 5 items):")
    for i, (key, value) in enumerate(env_dict.items()):
        if i >= 5:
            print("  ... (and more)")
            break
        print(f"  {key}={value}")


async def demonstrate_client_with_settings():
    """Demonstrate using settings with FOClient."""
    
    print("\\n\\n🔌 Using Settings with FOClient")
    print("=" * 35)
    
    # Get settings
    settings = get_settings()
    
    # Create FOClient configuration using settings
    from d365fo_client.credential_sources import EnvironmentCredentialSource
    
    # Determine credential source based on settings
    credential_source = None
    if settings.has_client_credentials():
        credential_source = EnvironmentCredentialSource(
            client_id_var="D365FO_CLIENT_ID",
            client_secret_var="D365FO_CLIENT_SECRET", 
            tenant_id_var="D365FO_TENANT_ID"
        )
    
    config = FOClientConfig(
        base_url=settings.base_url,
        credential_source=credential_source,
        verify_ssl=settings.verify_ssl,
        timeout=settings.timeout,
        use_label_cache=settings.use_label_cache,
        metadata_cache_dir=settings.cache_dir,
    )
    
    print(f"📍 Connecting to: {config.base_url}")
    print(f"🔐 Auth mode: {'Client Credentials' if settings.has_client_credentials() else 'Default Credentials'}")
    print(f"⚙️  Timeout: {config.timeout}s")
    print(f"🏷️  Label cache: {'Enabled' if config.use_label_cache else 'Disabled'}")
    print(f"💾 Metadata cache: {config.metadata_cache_dir}")
    
    try:
        async with FOClient(config=config) as client:
            print("✅ Connection successful!")
            
            # Test a simple operation
            try:
                version = await client.get_application_version()
                print(f"📦 Application version: {version}")
            except Exception as e:
                print(f"⚠️  Could not get version: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")


def print_environment_info():
    """Print current environment variable configuration."""
    
    print("\\n\\n🌍 Current Environment Configuration")
    print("=" * 40)
    
    env_vars = [
        "D365FO_BASE_URL",
        "D365FO_CLIENT_ID", 
        "D365FO_CLIENT_SECRET",
        "D365FO_TENANT_ID",
        "D365FO_LOG_LEVEL",
        "D365FO_HTTP_HOST",
        "D365FO_HTTP_PORT",
        "D365FO_MAX_CONCURRENT_REQUESTS",
        "D365FO_REQUEST_TIMEOUT",
        "D365FO_USE_LABEL_CACHE",
        "D365FO_VERIFY_SSL",
        "D365FO_DEBUG",
    ]
    
    print("Environment Variables:")
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if "SECRET" in var and value != "Not set":
            value = "*" * 20  # Hide secrets
        print(f"  {var}: {value}")


async def main():
    """Main function."""
    
    # Demonstrate settings usage
    demonstrate_settings_usage()
    
    # Show environment info
    print_environment_info()
    
    # Demonstrate with client
    await demonstrate_client_with_settings()
    
    print("\\n✨ Settings demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())