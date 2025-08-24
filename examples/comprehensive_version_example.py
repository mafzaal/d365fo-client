"""Comprehensive example using all version methods."""

import asyncio
import os

from d365fo_client import FOClient, FOClientConfig


async def comprehensive_version_example():
    """Comprehensive example showing all version methods"""

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    # Configure the client
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        try:
            # Test connection first
            if not await client.test_connection():
                print("❌ Failed to connect to D365 F&O")
                return

            print("✅ Connected to D365 F&O")

            # Get all version information using dedicated methods
            print("\n🔍 Getting all version information using dedicated methods...")

            # Method 1: Sequential calls
            print("\n📋 Sequential calls:")
            app_version = await client.get_application_version()
            print(f"  🎯 Application Version: {app_version}")

            platform_version = await client.get_platform_build_version()
            print(f"  🔧 Platform Build Version: {platform_version}")

            app_build_version = await client.get_application_build_version()
            print(f"  🏗️ Application Build Version: {app_build_version}")

            # Method 2: Parallel calls (faster)
            print("\n🚀 Parallel calls:")
            versions = await asyncio.gather(
                client.get_application_version(),
                client.get_platform_build_version(),
                client.get_application_build_version(),
                return_exceptions=True,
            )

            version_labels = [
                "Application Version",
                "Platform Build Version",
                "Application Build Version",
            ]

            for label, version in zip(version_labels, versions):
                if isinstance(version, Exception):
                    print(f"  ❌ {label}: Error - {version}")
                else:
                    print(f"  ✅ {label}: {version}")

            # Method 3: With error handling per method
            print("\n🛡️ Individual error handling:")

            version_methods = [
                (client.get_application_version, "Application Version", "🎯"),
                (client.get_platform_build_version, "Platform Build Version", "🔧"),
                (
                    client.get_application_build_version,
                    "Application Build Version",
                    "🏗️",
                ),
            ]

            for method, label, icon in version_methods:
                try:
                    version = await method()
                    print(f"  {icon} {label}: {version}")
                except Exception as e:
                    print(f"  ❌ {label}: Error - {e}")

            # Compare with generic call_action approach
            print("\n🔄 Comparison with generic call_action:")

            action_configs = [
                ("GetApplicationVersion", "Application Version"),
                ("GetPlatformBuildVersion", "Platform Build Version"),
                ("GetApplicationBuildVersion", "Application Build Version"),
            ]

            for action_name, label in action_configs:
                try:
                    version = await client.call_action(
                        action_name, entity_name="DataManagementEntities"
                    )
                    print(f"  📞 {label} (via call_action): {version}")
                except Exception as e:
                    print(f"  ❌ {label} (via call_action): Error - {e}")

        except Exception as e:
            print(f"❌ Overall error: {e}")


async def performance_comparison():
    """Compare performance between sequential, parallel, and mixed approaches"""

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    config = FOClientConfig(
        base_url=base_url, use_default_credentials=True, verify_ssl=False
    )

    async with FOClient(config) as client:
        try:
            if not await client.test_connection():
                print("❌ Failed to connect to D365 F&O")
                return

            print("⏱️ Performance Comparison")
            print("=" * 30)

            # Sequential approach
            import time

            start_time = time.time()

            await client.get_application_version()
            await client.get_platform_build_version()
            await client.get_application_build_version()

            sequential_time = time.time() - start_time
            print(f"Sequential calls: {sequential_time:.2f} seconds")

            # Parallel approach
            start_time = time.time()

            await asyncio.gather(
                client.get_application_version(),
                client.get_platform_build_version(),
                client.get_application_build_version(),
            )

            parallel_time = time.time() - start_time
            print(f"Parallel calls: {parallel_time:.2f} seconds")

            # Performance improvement
            if sequential_time > 0:
                improvement = (
                    (sequential_time - parallel_time) / sequential_time
                ) * 100
                print(f"Performance improvement: {improvement:.1f}%")

        except Exception as e:
            print(f"❌ Performance test error: {e}")


if __name__ == "__main__":
    print("D365 F&O Comprehensive Version Methods Example")
    print("=" * 50)

    # Run the comprehensive example
    asyncio.run(comprehensive_version_example())

    print("\n" + "=" * 50)

    # Run the performance comparison
    asyncio.run(performance_comparison())
