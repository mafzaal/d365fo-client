"""Example usage of the GetApplicationVersion action method."""

import asyncio
import os

from d365fo_client import FOClient, FOClientConfig


async def get_application_version_example():
    """Example of how to get the application version from D365 F&O"""

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    # Configure the client
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,  # or configure specific auth
        verify_ssl=False,  # Set to True in production
    )

    async with FOClient(config) as client:
        try:
            # Test connection first
            if not await client.test_connection():
                print("❌ Failed to connect to D365 F&O")
                return

            print("✅ Connected to D365 F&O")

            # Get the application version
            print("\n📋 Getting application version...")
            version = await client.get_application_version()

            print(f"🎯 Application Version: {version}")

            # You can also get other version information using dedicated methods
            print("\n📋 Getting other version information...")

            # Get platform build version using dedicated method
            platform_version = await client.get_platform_build_version()
            print(f"🔧 Platform Build Version: {platform_version}")

            # Get application build version using dedicated method
            app_build_version = await client.get_application_build_version()
            print(f"🏗️ Application Build Version: {app_build_version}")

        except Exception as e:
            print(f"❌ Error: {e}")


async def batch_version_info():
    """Get all version information in one go"""

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    config = FOClientConfig(
        base_url=base_url, use_default_credentials=True, verify_ssl=False
    )

    async with FOClient(config) as client:
        try:
            print("📊 Getting all version information...")

            # Get all version information using dedicated methods
            try:
                app_version = await client.get_application_version()
                print(f"  Application Version: {app_version}")
            except Exception as e:
                print(f"  Application Version: ❌ Error - {e}")

            try:
                platform_version = await client.get_platform_build_version()
                print(f"  Platform Build Version: {platform_version}")
            except Exception as e:
                print(f"  Platform Build Version: ❌ Error - {e}")

            try:
                app_build_version = await client.get_application_build_version()
                print(f"  Application Build Version: {app_build_version}")
            except Exception as e:
                print(f"  Application Build Version: ❌ Error - {e}")

        except Exception as e:
            print(f"❌ Overall error: {e}")


if __name__ == "__main__":
    print("D365 F&O GetApplicationVersion Example")
    print("=" * 40)

    # Run the basic example
    asyncio.run(get_application_version_example())

    print("\n" + "=" * 40)

    # Run the batch example
    asyncio.run(batch_version_info())
