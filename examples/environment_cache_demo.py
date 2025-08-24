#!/usr/bin/env python3
"""
Demonstration of environment-specific cache directories.

This example shows how the d365fo-client automatically creates separate
cache directories for different F&O environments, preventing conflicts
when working with multiple environments simultaneously.
"""

from d365fo_client.models import FOClientConfig
from d365fo_client.utils import extract_domain_from_url, get_environment_cache_directory


def demo_environment_cache_directories():
    """Demonstrate how different environments get separate cache directories."""

    # Different F&O environment URLs
    environments = [
        "https://prod.dynamics.com",
        "https://test.dynamics.com",
        "https://sandbox.dynamics.com",
        "https://mycompany.sandbox.operations.dynamics.com",
        "https://dev-environment.westus2.cloudax.dynamics.com",
        "http://localhost:8080",  # Local development
    ]

    print("Environment-Specific Cache Directory Demo")
    print("=" * 50)
    print()

    for url in environments:
        # Extract domain for demonstration
        domain = extract_domain_from_url(url)

        # Get the cache directory for this environment
        cache_dir = get_environment_cache_directory(url)

        print(f"Environment: {url}")
        print(f"Domain:      {domain}")
        print(f"Cache Dir:   {cache_dir}")
        print("-" * 50)


def demo_client_config():
    """Demonstrate automatic cache directory assignment in client configuration."""

    print("\nClient Configuration Demo")
    print("=" * 30)
    print()

    # Create configurations for different environments
    configs = [
        FOClientConfig(
            base_url="https://prod.dynamics.com",
            tenant_id="your-tenant-id",
            client_id="your-client-id",
            client_secret="your-client-secret",
        ),
        FOClientConfig(
            base_url="https://test.sandbox.operations.dynamics.com",
            tenant_id="your-tenant-id",
            client_id="your-client-id",
            client_secret="your-client-secret",
        ),
    ]

    for i, config in enumerate(configs, 1):
        print(f"Config {i}:")
        print(f"  Base URL:         {config.base_url}")
        print(f"  Cache Directory:  {config.metadata_cache_dir}")
        print()


if __name__ == "__main__":
    demo_environment_cache_directories()
    demo_client_config()

    print("\nKey Benefits:")
    print("- Each environment has isolated cache storage")
    print("- No conflicts when switching between environments")
    print("- Cache data is persisted across sessions")
    print("- Follows OS-specific cache directory conventions")
    print("- Automatic cleanup and organization")
