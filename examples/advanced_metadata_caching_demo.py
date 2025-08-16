"""
Advanced Metadata Caching Example

This example demonstrates the new SQLite-based metadata caching system
with full-text search capabilities.
"""

import asyncio
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the new caching system
from d365fo_client import FOClient, FOClientConfig
from d365fo_client.metadata_cache import MetadataCache, MetadataSearchEngine
from d365fo_client.metadata_sync import MetadataSyncManager
from d365fo_client.models import SearchQuery


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
        
        # Initialize metadata cache
        cache_dir = Path(config.metadata_cache_dir)
        metadata_cache = MetadataCache(config.base_url, cache_dir)
        await metadata_cache.initialize()
        
        print("✅ Metadata cache initialized")
        
        # Initialize sync manager
        sync_manager = MetadataSyncManager(metadata_cache, client.metadata_api_ops)
        
        # Perform initial sync
        print("\n📥 Syncing metadata...")
        try:
            sync_result = await sync_manager.sync_metadata()
            
            if sync_result.success:
                print(f"✅ Sync completed: {sync_result.sync_type}")
                print(f"   - Entities synced: {sync_result.entities_synced}")
                print(f"   - Enumerations synced: {sync_result.enumerations_synced}")
                print(f"   - Duration: {sync_result.duration_ms:.2f}ms")
            else:
                print(f"❌ Sync failed: {sync_result.errors}")
                print("📥 Continuing with partial sync for demo purposes...")
                # Let's still try to demonstrate the other features
        except Exception as e:
            print(f"❌ Sync failed with exception: {e}")
            print("📥 Continuing with partial sync for demo purposes...")
            # Let's still try to demonstrate the other features
        
        # Initialize search engine
        search_engine = MetadataSearchEngine(metadata_cache)
        
        
        # Example 1: Fast entity lookup
        print("\n🔍 Example 1: Fast Entity Lookup")
        print("-" * 30)
        
        customer_entity = await metadata_cache.get_entity("Customer", "public")
        if customer_entity:
            print(f"Found entity: {customer_entity.name}")
            print(f"Entity set: {customer_entity.entity_set_name}")
            print(f"Properties: {len(customer_entity.properties)}")
            print(f"Actions: {len(customer_entity.actions)}")
        
        # Example 2: Full-text search
        print("\n🔍 Example 2: Full-Text Search")
        print("-" * 30)
        
        search_queries = [
            "customer",
            "inventory",
            "sales order",
            "vendor"
        ]
        
        for query_text in search_queries:
            query = SearchQuery(
                text=query_text,
                limit=5,
                use_fulltext=True
            )
            
            results = await search_engine.search(query)
            
            print(f"\nQuery: '{query_text}'")
            print(f"Results: {len(results.results)} ({results.query_time_ms:.2f}ms)")
            
            for result in results.results[:3]:  # Show top 3
                print(f"  - {result.name} ({result.entity_type})")
                if result.snippet:
                    print(f"    {result.snippet}")
        
        # Example 3: Filtered search
        print("\n🔍 Example 3: Filtered Search")
        print("-" * 30)
        
        filtered_query = SearchQuery(
            text="master",
            entity_types=["data_entity"],
            limit=10
        )
        
        filtered_results = await search_engine.search(filtered_query)
        print(f"Data entities with 'master': {len(filtered_results.results)}")
        
        for result in filtered_results.results[:5]:
            print(f"  - {result.name}")
        
        # Example 4: Entity details with relationships
        print("\n🔍 Example 4: Entity Details")
        print("-" * 30)
        
        if customer_entity and customer_entity.navigation_properties:
            print(f"Navigation properties for {customer_entity.name}:")
            for nav_prop in customer_entity.navigation_properties[:3]:
                print(f"  - {nav_prop.name} -> {nav_prop.related_entity}")
                print(f"    Cardinality: {nav_prop.cardinality}")
                if nav_prop.constraints:
                    print(f"    Constraints: {len(nav_prop.constraints)}")
        
        # Example 5: Property groups
        if customer_entity and customer_entity.property_groups:
            print(f"\nProperty groups for {customer_entity.name}:")
            for group in customer_entity.property_groups[:2]:
                print(f"  - {group.name}: {len(group.properties)} properties")
        
        # Example 6: Actions and parameters
        if customer_entity and customer_entity.actions:
            print(f"\nActions for {customer_entity.name}:")
            for action in customer_entity.actions[:2]:
                print(f"  - {action.name} ({action.binding_kind})")
                if action.parameters:
                    print(f"    Parameters: {len(action.parameters)}")
                if action.return_type:
                    print(f"    Returns: {action.return_type.type_name}")
        
        # Example 7: Performance comparison
        print("\n⚡ Example 7: Performance Test")
        print("-" * 30)
        
        import time
        
        # Test multiple lookups
        entity_names = ["Customers", "Vendors", "Items", "SalesOrders", "PurchaseOrders"]
        
        start_time = time.time()
        for name in entity_names:
            entity = await metadata_cache.get_entity(name, "public")
        
        lookup_time = (time.time() - start_time) * 1000
        print(f"5 entity lookups: {lookup_time:.2f}ms ({lookup_time/5:.2f}ms avg)")
        
        # Test search performance
        start_time = time.time()
        for _ in range(10):
            results = await search_engine.search(SearchQuery(text="customer", limit=10))
        
        search_time = (time.time() - start_time) * 1000
        print(f"10 searches: {search_time:.2f}ms ({search_time/10:.2f}ms avg)")
        
        print("\n🎉 Demo completed successfully!")
        print("\nKey benefits:")
        print("✅ Fast SQLite-based metadata storage")
        print("✅ Full-text search with FTS5")
        print("✅ Complete entity relationships")
        print("✅ Multi-tier caching (memory + disk + database)")
        print("✅ Zero external dependencies")
        print("✅ Automatic synchronization")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise