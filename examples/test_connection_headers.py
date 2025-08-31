#!/usr/bin/env python3
"""
Simple test program to verify D365 F&O connection and display response headers.
This script tests the connection to D365 Finance & Operations and shows the HTTP headers
returned by the server.
"""

import asyncio
import os
import sys
from typing import Any, Dict

# Add the src directory to Python path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from d365fo_client import FOClient, FOClientConfig


async def test_connection_with_headers():
    """Test D365 F&O connection and display response headers."""

    print("D365 F&O Connection Test with Headers")
    print("=" * 50)

    # Configuration
    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    # Use default credentials for simplicity
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        use_label_cache=False,  # Disable cache for simple test
    )

    print(f"Base URL: {base_url}")
    print(f"Using default credentials: {config.use_default_credentials}")
    print()

    try:
        # Create client
        print("Creating D365 F&O client...")
        client = FOClient(config=config)

        # Test basic connection with application version (simple endpoint)
        print("Testing connection with GetApplicationVersion...")

        # Get application version using existing method
        app_version = await client.get_application_version()
        print("✅ Connection successful!")
        print(f"Application Version: {app_version}")
        print()

        # Now manually test endpoints to get headers
        session = await client.session_manager.get_session()

        # Test 1: GetApplicationVersion endpoint
        print("Testing GetApplicationVersion endpoint for headers...")
        url = f"{client.config.base_url}/api/services/MetadataService/GetApplicationVersion"

        async with session.get(url) as response:
            print("✅ GetApplicationVersion successful!")
            print("Response Headers:")
            print("-" * 30)

            # Display all headers
            for header_name, header_value in response.headers.items():
                print(f"{header_name}: {header_value}")

            # Get the response content
            response_text = await response.text()
            print(f"\nResponse Data: {response_text}")

        print()

        # Test 2: OData service document
        print("Testing OData service document for headers...")
        odata_url = f"{client.config.base_url}/data"

        try:
            async with session.get(odata_url) as response:
                print("✅ OData endpoint successful!")
                print("Key OData Headers:")
                print("-" * 20)

                # Display key headers
                key_headers = [
                    "content-type",
                    "odata-version",
                    "server",
                    "cache-control",
                    "x-ms-environment-id",
                    "x-ms-tenant-id",
                    "x-powered-by",
                ]

                for header in key_headers:
                    value = response.headers.get(header)
                    if value:
                        print(f"{header}: {value}")

                print(f"\nStatus Code: {response.status}")
                print(f"Reason: {response.reason}")

            print()

        except Exception as e:
            print(f"⚠️  OData endpoint failed: {e}")
            print()

        # Test 3: Metadata endpoint
        print("Testing metadata endpoint for headers...")
        metadata_url = f"{client.config.base_url}/api/metadata/DataEntities"

        try:
            async with session.get(metadata_url, params={"$top": 1}) as response:
                print("✅ Metadata endpoint successful!")
                print("Key Metadata Headers:")
                print("-" * 22)

                # Display key headers
                key_headers = [
                    "content-type",
                    "content-length",
                    "server",
                    "cache-control",
                    "x-ms-environment-id",
                    "x-ms-request-id",
                    "date",
                ]

                for header in key_headers:
                    value = response.headers.get(header)
                    if value:
                        print(f"{header}: {value}")

                print(f"\nStatus Code: {response.status}")
                print(f"Reason: {response.reason}")

            print()

        except Exception as e:
            print(f"⚠️  Metadata endpoint failed: {e}")
            print()

        # Test 4: Show all unique headers across endpoints
        print("Summary: All unique headers found:")
        print("-" * 40)

        all_headers = set()

        # Collect headers from a simple request
        try:
            async with session.get(odata_url) as response:
                all_headers.update(response.headers.keys())
        except:
            pass

        try:
            async with session.get(metadata_url, params={"$top": 1}) as response:
                all_headers.update(response.headers.keys())
        except:
            pass

        # Display all unique headers found
        for header in sorted(all_headers):
            print(f"• {header}")

        print()

        print("🎉 Connection test completed successfully!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("Troubleshooting tips:")
        print("1. Check your base URL is correct")
        print("2. Ensure you have proper authentication configured")
        print("3. Verify network connectivity to the D365 F&O environment")
        print("4. Check if you need to set environment variables:")
        print("   - D365FO_BASE_URL")
        print(
            "   - D365FO_CLIENT_ID, D365FO_CLIENT_SECRET, D365FO_TENANT_ID (if not using default credentials)"
        )

        return False

    finally:
        # Clean up the client session
        try:
            if "client" in locals():
                await client.session_manager.close()
        except Exception as e:
            print(f"Warning: Error closing client session: {e}")

    return True


def display_environment_info():
    """Display current environment configuration."""
    print("Environment Configuration:")
    print("-" * 30)

    env_vars = [
        "D365FO_BASE_URL",
        "D365FO_CLIENT_ID",
        "D365FO_CLIENT_SECRET",
        "D365FO_TENANT_ID",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "PASSWORD" in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"{var}: {display_value}")
        else:
            print(f"{var}: Not set")

    print()


async def main():
    """Main function."""
    print("D365 Finance & Operations Connection Test")
    print("========================================")
    print()

    # Display environment info
    display_environment_info()

    # Run connection test
    success = await test_connection_with_headers()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
