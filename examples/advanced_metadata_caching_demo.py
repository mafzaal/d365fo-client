"""
Advanced Metadata Caching Example

This example demonstrates the new SQLite-based metadata caching system
with full-text search capabilities.
"""

import asyncio
import logging
import os
from pathlib import Path

from d365fo_client.metadata_v2.cache_v2 import MetadataCacheV2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the new caching system
from d365fo_client import FOClient, FOClientConfig
from d365fo_client.metadata_v2.sync_manager_v2 import SmartSyncManagerV2


async def main():
    """Demonstrate advanced metadata caching"""
    
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    
    # Configuration
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        enable_metadata_cache=True,
        enable_fts_search=True
    )
    
    print("🚀 Advanced Metadata Caching Demo")
    print("=" * 50)
    
    # Initialize client
    async with FOClient(config) as client:
        
        print(config.metadata_cache_dir)

        # Initialize metadata cache
        cache_dir = Path(config.metadata_cache_dir)
        
        metadata_cache = MetadataCacheV2(cache_dir,config.base_url, client.metadata_api_ops)
        await metadata_cache.initialize()
        
        print("✅ Metadata cache initialized")
        
        # Initialize sync manager
        sync_manager = SmartSyncManagerV2(metadata_cache, client.metadata_api_ops)
        
        # Check version and determine if sync is needed
        print("\n🔍 Checking environment version...")
        sync_needed, global_version_id = await metadata_cache.check_version_and_sync(client.metadata_api_ops)
        
        if global_version_id:
            print(f"✅ Environment version detected: {global_version_id}")
        else:
            print("⚠️ Could not determine environment version")
        
        # Perform initial sync
        print("\n📥 Syncing metadata...")
        try:
            if sync_needed:
                sync_result = await sync_manager.sync_metadata(global_version_id)
            else:
                print("⚠️ Skipping sync due to no changes detected")
                sync_result = None
            
            if sync_result and sync_result.success:
                print(f"✅ Sync completed successfully")
                print(f"   - Duration: {sync_result.duration_ms:.2f}ms")
                if hasattr(sync_result, 'entity_count'):
                    print(f"   - Entities synced: {sync_result.entity_count}")
                if hasattr(sync_result, 'enumeration_count'):
                    print(f"   - Enumerations synced: {sync_result.enumeration_count}")
            elif sync_result:
                print(f"❌ Sync failed: {sync_result.error}")
                print("📥 Continuing with partial sync for demo purposes...")
                # Let's still try to demonstrate the other features
            else:
                print("⚠️ Sync skipped - using existing cache")
        except Exception as e:
            print(f"❌ Sync failed with exception: {e}")
            print("📥 Continuing with partial sync for demo purposes...")
            # Let's still try to demonstrate the other features
        
        
        # Examples start here
        # Example 1: Data Entities Lookup
        print("\n🔍 Example 1: Data Entities Lookup")
        print("-" * 30)
        
        # Get data entities with pattern matching
        customer_entities = await metadata_cache.get_data_entities(name_pattern="%Customer%")
        if customer_entities:
            print(f"Found {len(customer_entities)} customer-related entities:")
            for entity in customer_entities[:5]:  # Show first 5
                print(f"  - {entity.name} ({entity.entity_category})")
                if entity.label_text:
                    print(f"    {entity.label_text}")
        
        # Example 2: Public Entity Schema
        print("\n🔍 Example 2: Public Entity Schema")
        print("-" * 30)
        
        # Try common entity names
        entity_names_to_try = ["Customer", "Customers", "CustomersV3", "CustTable"]
        customer_entity = None
        
        for entity_name in entity_names_to_try:
            customer_entity = await metadata_cache.get_public_entity_schema(entity_name)
            if customer_entity:
                print(f"Found public entity: {customer_entity.name}")
                print(f"Entity set: {customer_entity.entity_set_name}")
                print(f"Properties: {len(customer_entity.properties)}")
                break
        
        if not customer_entity:
            print("No customer entity found in public entities")
        
        # Example 3: Enumeration Information
        print("\n🔍 Example 3: Enumeration Information")
        print("-" * 30)
        
        # Common D365 enumerations
        enum_names = ["NoYes", "LedgerTransType", "CustVendOpenTrans"]
        
        for enum_name in enum_names:
            enum_info = await metadata_cache.get_enumeration_info(enum_name)
            if enum_info:
                print(f"Enumeration: {enum_name}")
                print(f"  Members: {len(enum_info.members)}")
                if enum_info.members:
                    for member in enum_info.members[:3]:  # Show first 3
                        print(f"    {member.name} = {member.value}")
                break
        
        # Example 4: Data Entities by Category
        print("\n🔍 Example 4: Data Entities by Category")
        print("-" * 30)
        
        master_entities = await metadata_cache.get_data_entities(entity_category="Master")
        if master_entities:
            print(f"Found {len(master_entities)} Master entities")
            for entity in master_entities[:5]:
                print(f"  - {entity.name}")
        
        # Example 5: Data Service Enabled Entities
        print("\n🔍 Example 5: Data Service Enabled Entities")
        print("-" * 30)
        
        api_entities = await metadata_cache.get_data_entities(data_service_enabled=True)
        if api_entities:
            print(f"Found {len(api_entities)} API-enabled entities")
            for entity in api_entities[:5]:
                print(f"  - {entity.name} ({entity.entity_category})")
        
        # Example 6: Label Caching
        print("\n🔍 Example 6: Label Caching")
        print("-" * 30)
        
        # Test label operations
        test_labels = ["@SYS13342", "@SYS1", "@SYS2"]
        for label_id in test_labels:
            label_text = await metadata_cache.get_label(label_id)
            if label_text:
                print(f"Label {label_id}: {label_text}")
        
        # Example 7: Performance Test
        print("\n⚡ Example 7: Performance Test")
        print("-" * 30)
        
        import time
        
        # Test data entity lookups
        start_time = time.time()
        for _ in range(5):
            entities = await metadata_cache.get_data_entities(name_pattern="%Customer%")
        
        lookup_time = (time.time() - start_time) * 1000
        print(f"5 data entity searches: {lookup_time:.2f}ms ({lookup_time/5:.2f}ms avg)")
        
        # Test enumeration lookups
        start_time = time.time()
        for _ in range(10):
            enum_info = await metadata_cache.get_enumeration_info("NoYes")
        
        enum_time = (time.time() - start_time) * 1000
        print(f"10 enumeration lookups: {enum_time:.2f}ms ({enum_time/10:.2f}ms avg)")
        
        print("\n🎉 Demo completed successfully!")
        print("\nKey benefits:")
        print("✅ Version-aware SQLite-based metadata storage")
        print("✅ Complete entity and enumeration metadata")
        print("✅ Intelligent sync with change detection")
        print("✅ Multi-tier caching (memory + disk + database)")
        print("✅ Label caching with TTL support")
        print("✅ Automatic version management")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise