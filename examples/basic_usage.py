"""
Example usage of the d365fo-client library.

This example demonstrates how to use the D365 F&O client to:
- Connect to a D365 F&O environment
- Download and search metadata
- Perform CRUD operations
- Work with labels
- Handle errors properly

To run this example:
1. Install the library: pip install d365fo-client
2. Update the configuration below with your environment details
3. Run: python examples/basic_usage.py
"""

import asyncio
import logging
import os

from d365fo_client import (
    FOClient,
    FOClientConfig,
    FOClientError,
    QueryOptions,
    get_default_cache_directory,
    get_user_cache_dir,
)

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cache_directory_example():
    """Demonstrate cache directory configuration options."""
    print("\n" + "=" * 50)
    print("CACHE DIRECTORY CONFIGURATION EXAMPLE")
    print("=" * 50)

    # Show default cache directory behavior
    print("📁 Cache Directory Options:")

    # Get platform-appropriate cache directory
    default_cache = get_default_cache_directory()
    print(f"   Default cache directory: {default_cache}")

    # Get custom cache directory
    custom_cache = get_user_cache_dir("my-custom-app")
    print(f"   Custom app cache directory: {custom_cache}")

    # Example 1: Use default cache directory (recommended)
    print("\n📋 Example 1: Default cache directory")
    config_default = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        # metadata_cache_dir is automatically set to platform-appropriate directory
    )
    print(f"   Cache directory: {config_default.metadata_cache_dir}")

    # Example 2: Custom cache directory
    print("\n📋 Example 2: Custom cache directory")
    config_custom = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        metadata_cache_dir="./my_custom_cache",  # Explicit custom directory
    )
    print(f"   Cache directory: {config_custom.metadata_cache_dir}")

    # Example 3: App-specific cache directory
    print("\n📋 Example 3: App-specific cache directory")
    app_cache_dir = str(get_user_cache_dir("my-erp-integration"))
    config_app = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        metadata_cache_dir=app_cache_dir,
    )
    print(f"   Cache directory: {config_app.metadata_cache_dir}")

    print("\n✅ Cache directory configuration examples complete!")


async def basic_crud_example():
    """Demonstrate basic CRUD operations."""
    print("\n" + "=" * 50)
    print("BASIC CRUD OPERATIONS EXAMPLE")
    print("=" * 50)

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    # Configure the client
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,  # Use Azure Default Credential
        verify_ssl=False,  # Set to True for production
        timeout=30,
        use_label_cache=True,
        label_cache_expiry_minutes=60,
    )

    try:
        async with FOClient(config) as client:
            # Test connection
            print("🔗 Testing connection...")
            if await client.test_connection():
                print("✅ Connected to F&O successfully!")
            else:
                print("❌ Failed to connect to F&O")
                return

            # Download metadata (optional but recommended)
            print("\n📥 Downloading metadata...")
            await client.download_metadata()

            # Search for entities
            print("\n🔍 Searching for customer entities...")
            customer_entities = client.search_entities("customer")
            print(f"Found {len(customer_entities)} customer-related entities:")
            for entity in customer_entities[:5]:  # Show first 5
                print(f"  - {entity}")

            # Get entities with query options
            print(f"\n📊 Getting customers with query options...")
            query_options = QueryOptions(
                select=["CustomerAccount", "Name", "SalesCurrencyCode"],
                top=5,
                orderby=["Name"],
            )

            customers = await client.get_entities("Customers", query_options)
            customer_list = customers.get("value", [])
            print(f"Retrieved {len(customer_list)} customers:")

            for customer in customer_list:
                account = customer.get("CustomerAccount", "N/A")
                name = customer.get("Name", "N/A")
                currency = customer.get("SalesCurrencyCode", "N/A")
                print(f"  - {account}: {name} ({currency})")

            # Get a specific customer (if any exist)
            if customer_list:
                first_customer_account = customer_list[0].get("CustomerAccount")
                if first_customer_account:
                    print(
                        f"\n📋 Getting details for customer: {first_customer_account}"
                    )
                    customer_detail = await client.get_entity(
                        "Customers", first_customer_account
                    )
                    print(f"Customer details: {customer_detail.get('Name', 'N/A')}")

    except FOClientError as e:
        print(f"❌ F&O Client Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def metadata_example():
    """Demonstrate metadata operations."""
    print("\n" + "=" * 50)
    print("METADATA OPERATIONS EXAMPLE")
    print("=" * 50)

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    config = FOClientConfig(base_url=base_url, use_default_credentials=True)

    try:
        async with FOClient(config) as client:
            # Download metadata
            print("📥 Downloading metadata...")
            await client.download_metadata()

            # Search entities by pattern
            print("\n🔍 Searching entities...")
            sales_entities = client.search_entities("sales")
            print(f"Sales entities: {sales_entities[:5]}")

            # Get entity information
            if sales_entities:
                entity_name = sales_entities[0]
                print(f"\n📊 Getting info for entity: {entity_name}")
                entity_info = client.get_entity_info(entity_name)
                if entity_info:
                    print(f"Entity: {entity_info.name}")
                    print(f"Keys: {entity_info.keys}")
                    print(f"Properties: {len(entity_info.properties)}")

            # Search actions
            print(f"\n⚡ Searching for calculation actions...")
            calc_actions = client.search_actions("calculate")
            print(f"Found {len(calc_actions)} calculation actions:")
            for action in calc_actions[:5]:
                print(f"  - {action}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def labels_example():
    """Demonstrate label operations."""
    print("\n" + "=" * 50)
    print("LABEL OPERATIONS EXAMPLE")
    print("=" * 50)
    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    config = FOClientConfig(
        base_url=base_url, use_default_credentials=True, use_label_cache=True
    )

    try:
        async with FOClient(config) as client:
            # Test metadata connection
            if not await client.test_metadata_connection():
                print("❌ Cannot connect to Metadata API")
                return

            print("✅ Connected to Metadata API")

            # Get specific labels
            print("\n🏷️ Getting specific labels...")
            test_labels = ["@SYS13342", "@SYS9490", "@GLS63332"]

            for label_id in test_labels:
                try:
                    text = await client.get_label_text(label_id)
                    print(f"  {label_id}: '{text or 'Not found'}'")
                except Exception as e:
                    print(f"  {label_id}: Error - {e}")

            # Show cache info
            cache_info = client.get_label_cache_info()
            print(f"Cache info: {cache_info}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def enhanced_entity_example():
    """Demonstrate enhanced entity operations with labels."""
    print("\n" + "=" * 50)
    print("ENHANCED ENTITY WITH LABELS EXAMPLE")
    print("=" * 50)

    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    config = FOClientConfig(
        base_url=base_url, use_default_credentials=True, use_label_cache=True
    )

    try:
        async with FOClient(config) as client:
            # Get entity info with resolved labels
            print("📊 Getting enhanced entity information...")
            entity_info = await client.get_entity_info_with_labels("Customers")

            if entity_info:
                print(f"Entity: {entity_info.name}")
                if entity_info.label_text:
                    print(f"Display Name: '{entity_info.label_text}'")

                print(f"Entity Set: {entity_info.entity_set_name}")
                print(f"Read Only: {entity_info.is_read_only}")
                print(f"Properties: {len(entity_info.enhanced_properties)}")

                # Show properties with labels
                labeled_props = [
                    p for p in entity_info.enhanced_properties if p.label_text
                ]
                if labeled_props:
                    print(f"\nProperties with labels ({len(labeled_props)}):")
                    for prop in labeled_props[:10]:  # Show first 10
                        key_indicator = " (Key)" if prop.is_key else ""
                        mandatory_indicator = " (Required)" if prop.is_mandatory else ""
                        print(
                            f"  {prop.name}: '{prop.label_text}'{key_indicator}{mandatory_indicator}"
                        )
            else:
                print("❌ Could not retrieve entity information")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    print("Microsoft Dynamics 365 Finance & Operations Client Examples")
    print("=" * 60)
    print(
        "IMPORTANT: Update the base_url in each example with your F&O environment URL"
    )
    print("=" * 60)

    # Run examples
    await cache_directory_example()
    await basic_crud_example()
    await metadata_example()
    await labels_example()
    await enhanced_entity_example()

    print(f"\n✅ All examples completed!")
    print(f"\nNext steps:")
    print(f"1. Update the base_url with your actual F&O environment")
    print(f"2. Configure authentication (Azure AD app registration if needed)")
    print(f"3. Explore the full API documentation")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n❌ Examples cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
