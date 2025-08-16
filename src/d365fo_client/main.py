"""Main module for d365fo-client package with example usage."""

import asyncio
from .client import FOClient, create_client
from .models import FOClientConfig, QueryOptions


async def example_usage():
    """Example usage of the F&O client with label functionality"""
    config = FOClientConfig(
        base_url="https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        use_default_credentials=True,
        verify_ssl=False,
        use_label_cache=True,
        label_cache_expiry_minutes=60
    )
    
    async with FOClient(config) as client:
        # Test connections
        print("🔗 Testing connections...")
        if await client.test_connection():
            print("✅ Connected to F&O OData successfully")
        
        if await client.test_metadata_connection():
            print("✅ Connected to F&O Metadata API successfully")
        
        # Download metadata
        print("\n📥 Downloading metadata...")
        await client.download_metadata()
        
        # Search entities
        print("\n🔍 Searching entities...")
        customer_entities = client.search_entities("customer")
        print(f"Found {len(customer_entities)} customer-related entities")
        for entity in customer_entities[:5]:  # Show first 5
            print(f"  - {entity}")
        
        # Get entity info with labels
        print("\n📊 Getting entity information...")
        customers_info = await client.get_entity_info_with_labels("Customer")
        if customers_info:
            print(f"Customers entity: {customers_info.name}")
            if customers_info.label_text:
                print(f"Entity label: '{customers_info.label_text}'")
            print(f"Has {len(customers_info.enhanced_properties)} properties")
            
            # Show properties with labels
            labeled_props = [p for p in customers_info.enhanced_properties if p.label_text][:5]
            if labeled_props:
                print("Properties with labels:")
                for prop in labeled_props:
                    print(f"  {prop.name}: '{prop.label_text}'")
        
        # Test label operations
        print("\n🏷️ Label Operations:")
        
        # Get specific labels
        test_labels = ["@SYS78125", "@SYS9490", "@GLS63332"]
        print("Fetching specific labels:")
        for label_id in test_labels:
            text = await client.get_label_text(label_id)
            print(f"  {label_id}: '{text}'")
        
        # Search labels
        # customer_labels = await client.search_labels("customer", limit=3)
        # print(f"\nFound {len(customer_labels)} labels containing 'customer':")
        # for label in customer_labels:
        #     print(f"  {label.id}: '{label.value}'")
        
        # Build label cache
        # print("\nBuilding label cache...")
        # cached_count = await client.build_label_cache(["@SYS"], "en-US")
        
        # Show cache info
        cache_info = client.get_label_cache_info()
        print(f"Label cache: {cache_info}")
        
        # Get entities with query options
        print("\n📋 Querying entities...")
        query_options = QueryOptions(
            select=["CustomerAccount", "Name", "SalesCurrencyCode"],
            top=5,
            orderby=["Name"]
        )
        
        try:
            customers = await client.get_entities("Customers", query_options)
            print(f"Retrieved {len(customers.get('value', []))} customers")
            for customer in customers.get('value', [])[:3]:  # Show first 3
                print(f"  - {customer.get('CustomerAccount')}: {customer.get('Name')}")
        except Exception as e:
            print(f"Error querying customers: {e}")
        
        # Search and call actions
        print("\n⚡ Searching actions...")
        calc_actions = client.search_actions("calculate")
        print(f"Found {len(calc_actions)} calculation actions")
        for action in calc_actions[:5]:  # Show first 5
            print(f"  - {action}")

        print("\n🔧 Calling actions...")
        entity_actions = { "DataManagementEntities": [
                    "GetApplicationVersion",
                    "GetPlatformBuildVersion", 
                    "GetApplicationBuildVersion"
                    ],
                    "DocumentRoutingClientApps": ["GetPlatformVersion"],
                    
                }

        for entity in entity_actions:
            for action in entity_actions[entity]:
                print(f"Calling action '{action}' on entity '{entity}'...")
                result = await client.call_action(action, entity_name=entity)
                print(f"Action '{action}' result: {result}")


def main() -> None:
    """Main entry point for the d365fo-client application."""
    print("Microsoft Dynamics 365 Finance & Operations Client")
    print("=" * 50)
    
    try:
        asyncio.run(example_usage())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n\nError: {e}")


if __name__ == "__main__":
    main()
