#!/usr/bin/env python3
"""
Comprehensive test script for the query_data_management_entities methods.

This script tests both the direct integer-based method and the convenience
string-based method for querying data management entities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, "src")

from d365fo_client import FOClient, FOClientConfig


async def test_query_methods():
    """Test both query methods comprehensively"""

    # Configure client
    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        ),
        use_default_credentials=True,
        use_label_cache=True,
    )

    async with FOClient(config) as client:
        print("Testing Data Management Entity Query Methods")
        print("=" * 70)

        try:
            # Test 1: Query all entities (baseline)
            print("\n1. Query all data management entities (baseline):")
            all_entities = await client.query_data_management_entities()
            print(f"   Found {len(all_entities)} total entities")

        except Exception as e:
            print(f"   Error: {e}")
            return  # Exit if basic query fails

        try:
            # Test 2: Query with integer category filter (Master = 0)
            print("\n2. Query Master entities using integer filter:")
            master_entities_int = await client.query_data_management_entities(
                category_filters=[0]  # Master = 0
            )
            print(
                f"   Found {len(master_entities_int)} Master entities (integer method)"
            )

            if master_entities_int:
                # Show sample
                for i, entity in enumerate(master_entities_int[:3]):
                    print(
                        f"   - {entity.get('EntityName', 'N/A')} (Category: {entity.get('Category', 'N/A')})"
                    )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 3: Query with convenience method using strings
            print("\n3. Query Master entities using convenience method:")
            master_entities_str = (
                await client.query_data_management_entities_by_category(
                    categories=["Master"]
                )
            )
            print(
                f"   Found {len(master_entities_str)} Master entities (string method)"
            )

            # Verify both methods return the same count
            if "master_entities_int" in locals():
                if len(master_entities_int) == len(master_entities_str):
                    print("   ✓ Both methods returned the same count")
                else:
                    print(
                        f"   ⚠ Count mismatch: int={len(master_entities_int)} vs str={len(master_entities_str)}"
                    )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 4: Query multiple categories
            print("\n4. Query multiple categories (Master + Transaction):")
            multi_entities = await client.query_data_management_entities_by_category(
                categories=["Master", "Transaction"]
            )
            print(f"   Found {len(multi_entities)} Master+Transaction entities")

            # Show distribution
            master_count = sum(
                1 for e in multi_entities if e.get("Category") == "Master"
            )
            transaction_count = sum(
                1 for e in multi_entities if e.get("Category") == "Transaction"
            )
            print(
                f"   Distribution: {master_count} Master, {transaction_count} Transaction"
            )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 5: Query with shared filter
            print("\n5. Query shared entities:")
            shared_entities = await client.query_data_management_entities_by_category(
                categories=["Master"], is_shared=True
            )
            print(f"   Found {len(shared_entities)} shared Master entities")

            non_shared_entities = (
                await client.query_data_management_entities_by_category(
                    categories=["Master"], is_shared=False
                )
            )
            print(f"   Found {len(non_shared_entities)} non-shared Master entities")
            print(
                f"   Total Master entities check: {len(shared_entities) + len(non_shared_entities)}"
            )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 6: Query with module filter
            print("\n6. Query entities by module:")
            gl_entities = await client.query_data_management_entities_by_category(
                categories=["Master", "Configuration"], modules=["GeneralLedger"]
            )
            print(
                f"   Found {len(gl_entities)} General Ledger Master/Configuration entities"
            )

            if gl_entities:
                for i, entity in enumerate(gl_entities[:3]):
                    print(
                        f"   - {entity.get('EntityName', 'N/A')} (Category: {entity.get('Category', 'N/A')}, Module: {entity.get('Modules', 'N/A')})"
                    )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 7: Test all categories
            print("\n7. Test all category types:")
            all_categories = [
                "Master",
                "Configuration",
                "Transaction",
                "Reference",
                "Document",
                "Parameters",
            ]
            category_counts = {}

            for category in all_categories:
                try:
                    entities = await client.query_data_management_entities_by_category(
                        categories=[category]
                    )
                    category_counts[category] = len(entities)
                    print(f"   {category}: {len(entities)} entities")
                except Exception as e:
                    print(f"   {category}: Error - {e}")

            total_by_category = sum(category_counts.values())
            print(f"   Total entities by category: {total_by_category}")
            print(f"   Total entities (direct query): {len(all_entities)}")

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 8: Test integer method with multiple values
            print("\n8. Test direct integer method with multiple filters:")
            complex_entities = await client.query_data_management_entities(
                category_filters=[0, 1],  # Master + Configuration
                is_shared_filters=[1],  # Only shared
                module_filters=["GeneralLedger"],
            )
            print(
                f"   Found {len(complex_entities)} shared Master/Configuration GeneralLedger entities"
            )

        except Exception as e:
            print(f"   Error: {e}")

        try:
            # Test 9: Error handling
            print("\n9. Test error handling:")
            try:
                await client.query_data_management_entities_by_category(
                    categories=["InvalidCategory"]
                )
                print("   ⚠ Should have thrown an error for invalid category")
            except ValueError as ve:
                print(f"   ✓ Correctly caught ValueError: {ve}")
            except Exception as e:
                print(f"   ⚠ Unexpected error type: {e}")

        except Exception as e:
            print(f"   Outer error: {e}")

        print("\n" + "=" * 70)
        print("Query methods testing completed!")


if __name__ == "__main__":
    asyncio.run(test_query_methods())
