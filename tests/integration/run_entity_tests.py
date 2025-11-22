#!/usr/bin/env python3
"""
Integration test runner for entity validation and OData serialization.

This script demonstrates how to find and test entities with composite keys
and different data types in a real D365 F&O environment.

Usage:
    python run_entity_tests.py [--sandbox | --live] [--discovery-only]

Environment Variables:
    D365FO_SANDBOX_BASE_URL: Sandbox environment URL
    D365FO_LIVE_BASE_URL: Live environment URL (optional)
    INTEGRATION_TEST_LEVEL: Test level (sandbox, live, all)
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.mcp.mixins.base_tools_mixin import BaseToolsMixin
from d365fo_client.models import QueryOptions

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EntityTestRunner:
    """Test runner for entity validation and OData serialization."""

    def __init__(self, client: FOClient):
        self.client = client
        self.mixin = self._create_test_mixin()

    def _create_test_mixin(self):
        """Create a testable mixin instance."""

        class TestMixin(BaseToolsMixin):
            def __init__(self, client):
                self.test_client = client

            async def _get_client(self, profile: str = "default"):
                return self.test_client

        return TestMixin(self.client)

    async def run_discovery_tests(self) -> Dict[str, Any]:
        """Run entity discovery tests to find composite key entities."""
        print("🔍 Starting Entity Discovery Tests")
        print("=" * 50)

        results = {
            "total_entities_checked": 0,
            "composite_key_entities": [],
            "data_types_found": set(),
            "mixed_type_entities": [],
            "validation_results": {"passed": 0, "failed": 0},
        }

        try:
            # Get public entities for detailed schema analysis
            print("📋 Retrieving public entities...")
            public_entities_result = await self.client.get_public_entities(
                QueryOptions(top=50)
            )
            public_entities = public_entities_result.get("value", [])

            if not public_entities:
                print("❌ No public entities found")
                return results

            print(f"✅ Found {len(public_entities)} public entities to analyze")

            # Analyze each entity for composite keys
            for i, entity_info in enumerate(
                public_entities[:25], 1
            ):  # Limit to 25 for demo
                entity_name = entity_info.get("Name", "")
                if not entity_name:
                    continue

                print(f"  🔍 [{i:2d}/25] Analyzing {entity_name}...")
                results["total_entities_checked"] += 1

                try:
                    # Get detailed entity schema
                    entity_schema = await self.client.get_public_entity_info(
                        entity_name, resolve_labels=False
                    )
                    if not entity_schema:
                        continue

                    # Find key properties
                    key_properties = [
                        prop for prop in entity_schema.properties if prop.is_key
                    ]

                    if len(key_properties) > 1:  # Composite key found!
                        key_info = []
                        key_data_types = set()

                        for prop in key_properties:
                            key_info.append(
                                {
                                    "name": prop.name,
                                    "data_type": prop.data_type,
                                    "type_name": prop.type_name,
                                    "is_mandatory": prop.is_mandatory,
                                }
                            )
                            key_data_types.add(prop.data_type)
                            results["data_types_found"].add(prop.data_type)

                        entity_data = {
                            "entity_name": entity_name,
                            "entity_set_name": entity_schema.entity_set_name,
                            "key_count": len(key_properties),
                            "key_fields": key_info,
                            "data_types": list(key_data_types),
                            "is_read_only": entity_schema.is_read_only,
                            "has_mixed_types": len(key_data_types) > 1,
                        }

                        results["composite_key_entities"].append(entity_data)

                        if len(key_data_types) > 1:
                            results["mixed_type_entities"].append(entity_data)

                        print(
                            f"    ✅ Composite key found! {len(key_properties)} keys with types: {list(key_data_types)}"
                        )

                        # Stop after finding several examples
                        if len(results["composite_key_entities"]) >= 10:
                            print(
                                f"    🎯 Found {len(results['composite_key_entities'])} composite key entities, stopping discovery"
                            )
                            break

                    results["validation_results"]["passed"] += 1

                except Exception as e:
                    print(f"    ❌ Error analyzing {entity_name}: {e}")
                    results["validation_results"]["failed"] += 1
                    continue

            # Convert sets to lists for JSON serialization
            results["data_types_found"] = list(results["data_types_found"])

            return results

        except Exception as e:
            print(f"❌ Discovery test failed: {e}")
            return results

    async def run_validation_tests(
        self, composite_entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run validation tests on discovered composite key entities."""
        print("\n🧪 Starting Validation Tests")
        print("=" * 50)

        if not composite_entities:
            print("⚠️  No composite key entities to test")
            return {"validation_tests": [], "summary": {"passed": 0, "failed": 0}}

        validation_results = []

        for i, entity in enumerate(composite_entities[:5], 1):  # Test first 5
            entity_name = entity["entity_name"]
            key_fields = entity["key_fields"]

            print(f"  🔍 [{i}/5] Testing validation for {entity_name}...")

            test_result = {
                "entity_name": entity_name,
                "tests": {},
                "overall_success": True,
            }

            try:
                # Test 1: Entity existence validation
                exists = await self.mixin._validate_entity_exists(entity_name)
                test_result["tests"]["entity_exists"] = exists
                print(f"    📋 Entity exists: {exists}")

                # Test 2: Entity name resolution
                resolved = await self.mixin._resolve_entity_name(entity_name)
                test_result["tests"]["name_resolution"] = resolved is not None
                print(f"    🔗 Name resolution: {resolved}")

                # Test 3: Query validation
                query_valid = await self.mixin._validate_entity_for_query(entity_name)
                test_result["tests"]["query_validation"] = query_valid
                print(f"    🔍 Query validation: {query_valid}")

                # Test 4: Schema and key validation
                key_field_names = [field["name"] for field in key_fields]
                dummy_values = ["test"] * len(key_field_names)

                is_valid, schema, error = (
                    await self.mixin._validate_entity_schema_and_keys(
                        entity_name, key_field_names, dummy_values
                    )
                )
                test_result["tests"]["schema_validation"] = is_valid
                test_result["tests"]["schema_error"] = (
                    error.get("error", "") if error else ""
                )
                print(f"    📝 Schema validation: {is_valid}")
                if error:
                    print(f"        ℹ️  Error details: {error.get('error', 'Unknown')}")

                # Test 5: OData serialization for each key field
                serialization_tests = {}
                if schema:
                    for key_field in key_fields:
                        field_name = key_field["name"]
                        data_type = key_field["data_type"]
                        type_name = key_field["type_name"]

                        try:
                            # Test with appropriate sample value
                            test_value = self._get_sample_value(data_type)
                            serialized = self.mixin._serialize_odata_value(
                                test_value, data_type, type_name
                            )
                            serialization_tests[field_name] = {
                                "success": True,
                                "data_type": data_type,
                                "test_value": test_value,
                                "serialized": serialized,
                            }
                        except Exception as se:
                            serialization_tests[field_name] = {
                                "success": False,
                                "data_type": data_type,
                                "error": str(se),
                            }

                test_result["tests"]["serialization"] = serialization_tests

                # Overall success check
                test_result["overall_success"] = all(
                    [exists, resolved is not None, query_valid]
                )

                validation_results.append(test_result)

                if test_result["overall_success"]:
                    print(f"    ✅ All validation tests passed for {entity_name}")
                else:
                    print(f"    ⚠️  Some validation tests failed for {entity_name}")

            except Exception as e:
                test_result["overall_success"] = False
                test_result["error"] = str(e)
                validation_results.append(test_result)
                print(f"    ❌ Validation test failed for {entity_name}: {e}")

        # Summary
        passed = sum(1 for r in validation_results if r["overall_success"])
        failed = len(validation_results) - passed

        return {
            "validation_tests": validation_results,
            "summary": {
                "passed": passed,
                "failed": failed,
                "total": len(validation_results),
            },
        }

    def _get_sample_value(self, data_type: str) -> Any:
        """Get appropriate sample value for data type."""
        sample_values = {
            "String": "TEST001",
            "Int32": 42,
            "Int64": 123456789,
            "Real": 3.14159,
            "Decimal": 999.99,
            "Money": 1234.56,
            "Boolean": True,
            "Date": "2023-12-25",
            "Time": "14:30:00",
            "DateTime": "2023-12-25T14:30:00",
            "UtcDateTime": "2023-12-25T14:30:00Z",
            "Guid": "12345678-1234-1234-1234-123456789abc",
            "Enum": "Yes",
        }
        return sample_values.get(data_type, "default_value")

    def print_summary(
        self, discovery_results: Dict[str, Any], validation_results: Dict[str, Any]
    ):
        """Print comprehensive test summary."""
        print("\n📊 Test Summary Report")
        print("=" * 50)

        # Discovery summary
        print(f"🔍 Discovery Results:")
        print(
            f"  📋 Total entities checked: {discovery_results['total_entities_checked']}"
        )
        print(
            f"  🔑 Composite key entities found: {len(discovery_results['composite_key_entities'])}"
        )
        print(
            f"  🎭 Mixed data type entities: {len(discovery_results['mixed_type_entities'])}"
        )
        print(
            f"  📊 Data types discovered: {len(discovery_results['data_types_found'])}"
        )
        print(f"     Types: {', '.join(sorted(discovery_results['data_types_found']))}")

        # Validation summary
        if validation_results.get("summary"):
            summary = validation_results["summary"]
            print(f"\n🧪 Validation Results:")
            print(f"  ✅ Passed: {summary['passed']}")
            print(f"  ❌ Failed: {summary['failed']}")
            print(f"  📊 Total: {summary['total']}")

            if summary["total"] > 0:
                success_rate = (summary["passed"] / summary["total"]) * 100
                print(f"  🎯 Success Rate: {success_rate:.1f}%")

        # Detailed composite key entities
        if discovery_results["composite_key_entities"]:
            print(f"\n🔑 Found Composite Key Entities:")
            for entity in discovery_results["composite_key_entities"][
                :5
            ]:  # Show first 5
                print(f"  📋 {entity['entity_name']} ({entity['key_count']} keys)")
                print(f"     Entity Set: {entity['entity_set_name']}")
                print(f"     Read-only: {entity['is_read_only']}")
                print(f"     Data Types: {', '.join(entity['data_types'])}")
                if entity["has_mixed_types"]:
                    print(f"     🎭 Has mixed data types in composite key")
                print()


async def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run entity validation and OData serialization tests"
    )
    parser.add_argument(
        "--sandbox", action="store_true", help="Run against sandbox environment"
    )
    parser.add_argument(
        "--live", action="store_true", help="Run against live environment"
    )
    parser.add_argument(
        "--discovery-only", action="store_true", help="Run discovery tests only"
    )
    args = parser.parse_args()

    # Determine environment
    if args.live:
        base_url = os.getenv("D365FO_LIVE_BASE_URL")
        env_name = "Live"
    else:
        base_url = os.getenv(
            "D365FO_SANDBOX_BASE_URL",
            "https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        )
        env_name = "Sandbox"

    if not base_url:
        print(f"❌ No base URL configured for {env_name} environment")
        print(
            "Set D365FO_SANDBOX_BASE_URL or D365FO_LIVE_BASE_URL environment variable"
        )
        sys.exit(1)

    print(f"🚀 Starting Entity Tests - {env_name} Environment")
    print(f"🌐 Base URL: {base_url}")
    print("=" * 70)

    # Create client configuration
    config = FOClientConfig(
        base_url=base_url,
        verify_ssl=not args.sandbox,  # Disable SSL verification for test environments
        timeout=60,
    )

    try:
        async with FOClient(config) as client:
            # Test connection
            print("🔗 Testing connection...")
            if not await client.test_connection():
                print("❌ Connection test failed")
                sys.exit(1)
            print("✅ Connection successful")

            # Run tests
            runner = EntityTestRunner(client)

            # Discovery tests
            discovery_results = await runner.run_discovery_tests()

            # Validation tests (unless discovery-only)
            validation_results = {}
            if not args.discovery_only and discovery_results["composite_key_entities"]:
                validation_results = await runner.run_validation_tests(
                    discovery_results["composite_key_entities"]
                )

            # Print summary
            runner.print_summary(discovery_results, validation_results)

            print("\n🎉 Entity validation and OData serialization tests completed!")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
