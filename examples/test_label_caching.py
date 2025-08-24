#!/usr/bin/env python3
"""Test script for v2 label caching implementation."""

import asyncio
import os

# Add the src directory to Python path
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.models import LabelInfo


async def test_label_caching():
    """Test the label caching functionality"""
    print("Testing D365 F&O Label Caching V2 Implementation")
    print("=" * 50)

    # Create a temporary directory for cache
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "metadata_cache_v2"

        # Configure client with v2 cache enabled
        config = FOClientConfig(
            base_url=os.getenv(
                "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
            ),
            use_default_credentials=True,
            enable_metadata_cache=True,
            metadata_cache_dir=str(cache_dir),
        )

        print(f"Cache directory: {cache_dir}")
        print(f"Base URL: {config.base_url}")

        async with FOClient(config) as client:
            print("\n1. Testing connection...")
            if not await client.test_connection():
                print("❌ Connection failed")
                return
            print("✅ Connection successful")

            print("\n2. Initializing metadata cache...")
            await client._ensure_metadata_initialized()

            if not client._metadata_initialized:
                print("❌ Metadata cache initialization failed")
                return
            print("✅ Metadata cache v2 initialized")

            print("\n3. Testing label cache info...")
            label_cache_info = await client.get_label_cache_info_async()
            print(f"Label cache info: {label_cache_info}")

            print("\n4. Testing direct label operations...")
            if hasattr(client.metadata_cache, "get_label"):
                # Test storing and retrieving a label
                test_label_id = "@TEST123"
                test_label_text = "Test Label Text"

                print(f"Storing test label: {test_label_id} -> {test_label_text}")
                await client.metadata_cache.set_label(test_label_id, test_label_text)

                print(f"Retrieving test label...")
                retrieved = await client.metadata_cache.get_label(test_label_id)

                if retrieved == test_label_text:
                    print("✅ Direct label caching works")
                else:
                    print(
                        f"❌ Label retrieval failed: expected '{test_label_text}', got '{retrieved}'"
                    )

            print("\n5. Testing label operations through client...")
            try:
                # Try to get a common system label
                common_label = await client.get_label_text(
                    "@SYS1"
                )  # Usually "OK" or similar
                if common_label:
                    print(f"✅ Retrieved label @SYS1: '{common_label}'")
                else:
                    print("⚠️ No text found for @SYS1 (might not exist)")

                # Test batch label operations
                test_labels = ["@SYS1", "@SYS2", "@SYS3"]
                batch_result = await client.get_labels_batch(test_labels)
                print(f"✅ Batch label retrieval: {len(batch_result)} labels retrieved")
                for label_id, text in batch_result.items():
                    print(f"   {label_id} -> '{text}'")

            except Exception as e:
                print(f"⚠️ Label API operations encountered issue: {e}")

            print("\n6. Testing metadata sync with label pre-caching...")
            try:
                # Trigger metadata sync which should pre-cache labels
                result = await client.download_metadata(force_refresh=True)
                if result:
                    print("✅ Metadata sync completed successfully")

                    # Check label cache statistics
                    stats = await client.get_label_cache_info_async()
                    if "statistics" in stats:
                        label_stats = stats["statistics"]
                        print(f"   Labels cached: {label_stats.get('total_labels', 0)}")
                        print(
                            f"   Active labels: {label_stats.get('active_labels', 0)}"
                        )
                        print(f"   Languages: {label_stats.get('languages', {})}")
                    else:
                        print("   Label statistics not available")
                else:
                    print("❌ Metadata sync failed")
            except Exception as e:
                print(f"⚠️ Metadata sync encountered issue: {e}")

            print("\n7. Testing cache statistics...")
            try:
                cache_stats = await client.metadata_cache.get_cache_statistics()
                if "label_cache" in cache_stats:
                    label_cache = cache_stats["label_cache"]
                    print(
                        f"   Total labels in cache: {label_cache.get('total_labels', 0)}"
                    )
                    print(f"   Active labels: {label_cache.get('active_labels', 0)}")
                    if "hit_statistics" in label_cache:
                        hit_stats = label_cache["hit_statistics"]
                        print(f"   Total hits: {hit_stats.get('total_hits', 0)}")
                        print(
                            f"   Average hits per label: {hit_stats.get('average_hits_per_label', 0)}"
                        )
                else:
                    print("   No label cache statistics available")
            except Exception as e:
                print(f"⚠️ Error getting cache statistics: {e}")

    print("\n" + "=" * 50)
    print("Label caching test completed!")


if __name__ == "__main__":
    asyncio.run(test_label_caching())
