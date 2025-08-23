#!/usr/bin/env python3
"""
Test script for the new query_data_management_entities method.

This script demonstrates how to use the new OData query action
implementation in the FOClient with corrected parameter types.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, "src")

from d365fo_client import FOClient, FOClientConfig


async def test_query_action():
    """Test the query_data_management_entities method with correct parameter types"""

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
            # Test 1: Query all entities (empty arrays for required parameters)
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
            # Test 2: Query with category filter (integer values)
            print("\n2. Query entities with category filter (integers):")
            # Category filters expect integer values, not strings
            # Common category IDs: 0=Master, 1=Transaction, etc.
            category_entities = await client.query_data_management_entities(
                category_filters=[0]  # Using integer 0 instead of 'Master'
            )
            print(
                f"   Found {len(category_entities)} entities with category filter [0]"
            )

            if category_entities:
                # Show first few entities
                for i, entity in enumerate(category_entities[:3]):
                    print(
                        f"   - {entity.get('EntityName', 'N/A')} (Category: {entity.get('Category', 'N/A')})"
                    )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 3: Query with multiple category filters
            print("\n3. Query entities with multiple category filters:")
            multi_category_entities = await client.query_data_management_entities(
                category_filters=[0, 1, 2]  # Multiple integer category IDs
            )
            print(
                f"   Found {len(multi_category_entities)} entities with category filters [0, 1, 2]"
            )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 4: Query with module filter (if any exist)
            print("\n4. Query entities with module filter:")
            module_entities = await client.query_data_management_entities(
                module_filters=["GeneralLedger"]  # Try common module name
            )
            print(f"   Found {len(module_entities)} GeneralLedger entities")

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
                category_filters=[0],  # Master entities
                is_shared_filters=[1],  # Shared entities (1=True)
            )
            print(f"   Found {len(complex_entities)} shared Master entities")

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 6: Compare with direct OData call
            print("\n6. Compare with direct call_action:")
            direct_result = await client.call_action(
                "query",
                parameters={
                    "categoryFilters": [0],
                    "isSharedFilters": [],
                    "configKeyFilters": [],
                    "countryRegionCodeFilters": [],
                    "moduleFilters": [],
                    "tagFilters": [],
                },
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

        try:
            # Test 7: Test different shared filter values
            print("\n7. Test shared filter values:")
            shared_entities = await client.query_data_management_entities(
                is_shared_filters=[1]  # Only shared entities
            )
            print(f"   Found {len(shared_entities)} shared entities")

            non_shared_entities = await client.query_data_management_entities(
                is_shared_filters=[0]  # Only non-shared entities
            )
            print(f"   Found {len(non_shared_entities)} non-shared entities")

        except Exception as e:
            print(f"   Error: {e}")

        print("\n" + "=" * 60)
        print("Query action testing completed!")


if __name__ == "__main__":
    asyncio.run(test_query_action())
