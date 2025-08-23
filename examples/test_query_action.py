#!/usr/bin/env python3
"""
Test script for the new query_data_management_entities method.

This script demonstrates how to use the new OData query action
implementation in the FOClient.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, "src")

from d365fo_client import FOClient, FOClientConfig


async def test_query_action():
    """Test the query_data_management_entities method"""

    # Configure client
    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        ),
        use_default_credentials=True,
        use_label_cache=True,
    )

    async with FOClient(config) as client:
        print("Testing query_data_management_entities method...")
        print("=" * 60)

        try:
            # Test 1: Query all entities (no filters)
            print("\n1. Query all data management entities:")
            all_entities = await client.query_data_management_entities()
            print(f"   Found {len(all_entities)} total entities")

            if all_entities:
                first_entity = all_entities[0]
                print(f"   First entity: {first_entity.get('EntityName', 'N/A')}")
                print(f"   Available keys: {list(first_entity.keys())}")

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 2: Query with category filter
            print("\n2. Query entities with category filter (Master):")
            master_entities = await client.query_data_management_entities(
                category_filters=["Master"]
            )
            print(f"   Found {len(master_entities)} Master entities")

            if master_entities:
                # Show first few entities
                for i, entity in enumerate(master_entities[:3]):
                    print(
                        f"   - {entity.get('EntityName', 'N/A')} (Category: {entity.get('Category', 'N/A')})"
                    )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 3: Query with multiple category filters
            print("\n3. Query entities with multiple category filters:")
            multi_category_entities = await client.query_data_management_entities(
                category_filters=["Master", "Transaction"]
            )
            print(
                f"   Found {len(multi_category_entities)} Master/Transaction entities"
            )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 4: Query with module filter
            print("\n4. Query entities with module filter:")
            module_entities = await client.query_data_management_entities(
                module_filters=["General ledger"]
            )
            print(f"   Found {len(module_entities)} General ledger entities")

            if module_entities:
                for i, entity in enumerate(module_entities[:3]):
                    print(
                        f"   - {entity.get('EntityName', 'N/A')} (Module: {entity.get('Module', 'N/A')})"
                    )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 5: Complex query with multiple filters
            print("\n5. Complex query with multiple filters:")
            complex_entities = await client.query_data_management_entities(
                category_filters=["Master"],
                is_shared_filters=[True],  # Only shared entities
            )
            print(f"   Found {len(complex_entities)} shared Master entities")

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 6: Compare with direct OData call
            print("\n6. Compare with direct call_action:")
            direct_result = await client.call_action(
                "query",
                parameters={"categoryFilters": "Master"},
                entity_name="DataManagementEntities",
            )

            if isinstance(direct_result, dict) and "value" in direct_result:
                direct_count = len(direct_result["value"])
            elif isinstance(direct_result, list):
                direct_count = len(direct_result)
            else:
                direct_count = 1 if direct_result else 0

            print(f"   Direct call returned {direct_count} entities")

        except Exception as e:
            print(f"   Error: {e}")

        print("\n" + "=" * 60)
        print("Query action testing completed!")


if __name__ == "__main__":
    asyncio.run(test_query_action())
