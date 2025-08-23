#!/usr/bin/env python3
"""
Test script to verify label cache hit statistics functionality
"""

import asyncio
import tempfile
import os
from pathlib import Path

from d365fo_client import FOClient, FOClientConfig


async def test_label_hit_statistics():
    """Test label cache hit statistics by accessing labels multiple times"""
    print("Testing Label Cache Hit Statistics")
    print("==================================")
    
    # Create a temporary cache directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "metadata_cache_v2"
        print(f"Cache directory: {cache_dir}")
        
        # Configuration with v2 cache enabled
        base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
        print(f"Base URL: {base_url}\n")
        
        config = FOClientConfig(
            base_url=base_url,
            use_default_credentials=True,
            metadata_cache_dir=str(cache_dir),
            use_label_cache=True
        )
        
        # Initialize client
        client = FOClient(config=config)
        
        print("1. Initializing cache...")
        await client._ensure_metadata_initialized()
        print("✅ Cache initialized\n")
        
        # Test specific label multiple times
        test_label = "@SYS1"
        print(f"2. Testing label '{test_label}' multiple times...")
        
        # First access - should be cache miss, then cached
        result1 = await client.get_label_text(test_label)
        print(f"First access: {result1}")
        
        # Subsequent accesses - should be cache hits
        for i in range(2, 6):
            result = await client.get_label_text(test_label)
            print(f"Access {i}: {result}")
        
        print()
        
        # Test batch operations
        test_labels = ["@SYS1", "@SYS2", "@SYS3", "@SYS4", "@SYS5"]
        print(f"3. Testing batch operations with labels: {test_labels}")
        
        # First batch access
        batch_result1 = await client.get_labels_batch(test_labels)
        print(f"First batch: {len(batch_result1)} labels retrieved")
        
        # Second batch access - should increase hit counts
        batch_result2 = await client.get_labels_batch(test_labels)
        print(f"Second batch: {len(batch_result2)} labels retrieved")
        
        print()
        
        # Check hit statistics
        print("4. Checking hit statistics...")
        cache_info = await client.get_label_cache_info_async()
        if cache_info and 'statistics' in cache_info:
            stats = cache_info['statistics']
            hit_stats = stats.get('hit_statistics', {})
            
            print(f"   Total labels: {stats.get('total_labels', 0)}")
            print(f"   Active labels: {stats.get('active_labels', 0)}")
            print(f"   Accessed labels: {hit_stats.get('accessed_labels', 0)}")
            print(f"   Total hits: {hit_stats.get('total_hits', 0)}")
            print(f"   Average hits per label: {hit_stats.get('average_hits_per_label', 0)}")
            print(f"   Max hits: {hit_stats.get('max_hits', 0)}")
            
            # Verify that we have hits recorded
            if hit_stats.get('total_hits', 0) > 0:
                print("✅ Hit statistics are working correctly!")
            else:
                print("⚠️ No hits recorded - this might indicate an issue")
        else:
            print(f"❌ Could not retrieve cache statistics: {cache_info}")
        
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_label_hit_statistics())