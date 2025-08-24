#!/usr/bin/env python3
"""Test script to demonstrate the optimized public entities parsing."""

import asyncio
import logging
import time

from d365fo_client import FOClient, FOClientConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_optimized_public_entities():
    """Test the optimized public entities parsing approach."""

    # Initialize client
    config = FOClientConfig(
        base_url="https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        use_default_credentials=True,
        enable_metadata_cache=True,
        enable_fts_search=True,
    )

    async with FOClient(config) as client:
        print("\n🚀 Testing Optimized Public Entities Parsing")
        print("=" * 50)

        # Test the new optimized method
        start_time = time.time()
        entities = await client.get_all_public_entities_with_details(
            resolve_labels=False
        )
        duration = (time.time() - start_time) * 1000

        print(f"✅ Retrieved {len(entities)} public entities in {duration:.2f}ms")
        print(f"📊 Average per entity: {duration/len(entities):.2f}ms")

        # Check first few entities for completeness
        print(f"\n🔍 Sample entities with full details:")
        for i, entity in enumerate(entities[:3]):
            print(f"   {i+1}. {entity.name}")
            print(f"      - Properties: {len(entity.properties)}")
            print(f"      - Navigation Properties: {len(entity.navigation_properties)}")
            print(f"      - Property Groups: {len(entity.property_groups)}")
            print(f"      - Actions: {len(entity.actions)}")

            # Show navigation property details for the first entity
            if i == 0 and entity.navigation_properties:
                print(f"      📋 Navigation Properties:")
                for nav_prop in entity.navigation_properties[:2]:  # Show first 2
                    print(
                        f"         - {nav_prop.name} -> {nav_prop.related_entity} ({nav_prop.cardinality})"
                    )
                    if nav_prop.constraints:
                        print(f"           Constraints: {len(nav_prop.constraints)}")

        # Performance comparison (if someone wants to test the old way)
        print(f"\n⚡ Performance Benefits:")
        print(f"   - Single API call instead of {len(entities)} individual calls")
        print(f"   - Reduced network overhead")
        print(f"   - Faster synchronization")
        print(f"   - Lower server load")


if __name__ == "__main__":
    asyncio.run(test_optimized_public_entities())
