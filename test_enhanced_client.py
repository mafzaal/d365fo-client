#!/usr/bin/env python3
"""Test script for enhanced FOClient with cache-first metadata operations."""

import asyncio
import os
from d365fo_client import FOClient, FOClientConfig

async def test_enhanced_client():
    """Test the enhanced FOClient with cache-first metadata operations."""
    
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    
    # Test with cache-first enabled (default)
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        enable_metadata_cache=True,
        use_cache_first=True,  # This is the new setting
        verify_ssl=False
    )
    
    print("🚀 Testing Enhanced FOClient with Cache-First Metadata Operations")
    print("=" * 70)
    
    async with FOClient(config) as client:
        
        print(f"✅ Client initialized with cache-first: {config.use_cache_first}")
        
        # Test connection
        if not await client.test_connection():
            print("❌ Failed to connect to D365 F&O")
            return
        
        print("✅ Connected to D365 F&O")
        
        # Test metadata download/sync
        print("\n📥 Testing metadata sync...")
        sync_result = await client.download_metadata(force_refresh=False)
        print(f"Metadata sync result: {sync_result}")
        
        # Test cache-first search operations
        print("\n🔍 Testing cache-first search operations...")
        
        # Search entities with cache-first (default)
        entities = await client.search_entities("Customer", use_cache_first=True)
        print(f"Cache-first entity search results: {len(entities)} entities found")
        if entities:
            print(f"First few entities: {entities[:3]}")
        
        # Search entities bypassing cache
        entities_no_cache = await client.search_entities("Customer", use_cache_first=False)
        print(f"Fallback entity search results: {len(entities_no_cache)} entities found")
        
        # Test entity info retrieval
        if entities:
            entity_name = entities[0]
            print(f"\n📋 Testing entity info for: {entity_name}")
            
            entity_info = await client.get_entity_info(entity_name, use_cache_first=True)
            if entity_info:
                print(f"✅ Entity info retrieved: {entity_info.name}")
                print(f"   Keys: {entity_info.keys}")
                print(f"   Properties: {len(entity_info.properties)}")
            else:
                print("❌ Entity info not found")
        
        # Test public entities search
        print("\n🔍 Testing public entities search...")
        public_entities = await client.search_public_entities("Customer", use_cache_first=True)
        print(f"Public entities found: {len(public_entities)}")
        
        # Test data entities search
        print("\n🔍 Testing data entities search...")
        data_entities = await client.search_data_entities("Customer", use_cache_first=True)
        print(f"Data entities found: {len(data_entities)}")
        
        # Get metadata info
        print("\n📊 Metadata cache information:")
        info = client.get_metadata_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        print("\n🎉 Enhanced FOClient testing completed!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_client())