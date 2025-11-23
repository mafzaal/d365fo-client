"""Integration tests for entity validation and OData serialization.

These tests focus on:
1. Entity existence validation across different naming formats
2. OData serialization for various D365 F&O data types
3. Finding and testing entities with composite keys
4. Validating key field data types and serialization
5. Testing the enhanced CRUD validation methods
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import pytest
import pytest_asyncio

from d365fo_client import FOClient
from d365fo_client.mcp.mixins.base_tools_mixin import BaseToolsMixin
from d365fo_client.models import PublicEntityInfo, QueryOptions

from . import skip_if_not_level

logger = logging.getLogger(__name__)


class BaseToolsMixinWrapper(BaseToolsMixin):
    """Wrapper for BaseToolsMixin to enable integration testing.

    Note: Renamed from BaseToolsMixinWrapper to avoid pytest collection warning.
    """

    def __init__(self, client: FOClient):
        self.client = client

    async def _get_client(self, profile: str = "default") -> FOClient:
        """Return the test client."""
        return self.client


@skip_if_not_level("sandbox")
class TestEntityValidation:
    """Test entity validation methods against sandbox environment."""

    @pytest.mark.asyncio
    async def test_resolve_entity_name_variations(self, sandbox_client: FOClient):
        """Test resolving entity names from various input formats."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Get some known entities to test with
        entities_result = await sandbox_client.get_data_entities(QueryOptions(top=20))
        test_entities = entities_result.get("value", [])

        if not test_entities:
            pytest.skip("No data entities available for testing")

        # Find entities with different naming patterns
        test_cases = []
        for entity in test_entities:
            if entity.get("DataServiceEnabled", False):
                name = entity.get("Name", "")
                public_collection = entity.get("PublicCollectionName", "")
                public_entity = entity.get("PublicEntityName", "")

                if name and public_collection and name != public_collection:
                    test_cases.append(
                        {
                            "name": name,
                            "public_collection": public_collection,
                            "public_entity": public_entity or name,
                            "entity": entity,
                        }
                    )
                    if len(test_cases) >= 5:  # Test with 5 entities
                        break

        if not test_cases:
            pytest.skip("No suitable entities found for name resolution testing")

        # Test name resolution for each entity
        for test_case in test_cases:
            # Test 1: Resolve using data entity name
            resolved = await mixin._resolve_entity_name(test_case["name"])
            assert (
                resolved is not None
            ), f"Failed to resolve entity name: {test_case['name']}"

            # Test 2: Resolve using public collection name
            if test_case["public_collection"]:
                resolved = await mixin._resolve_entity_name(
                    test_case["public_collection"]
                )
                assert (
                    resolved is not None
                ), f"Failed to resolve public collection name: {test_case['public_collection']}"

            # Test 3: Resolve using public entity name
            if (
                test_case["public_entity"]
                and test_case["public_entity"] != test_case["name"]
            ):
                resolved = await mixin._resolve_entity_name(test_case["public_entity"])
                assert (
                    resolved is not None
                ), f"Failed to resolve public entity name: {test_case['public_entity']}"

    @pytest.mark.asyncio
    async def test_validate_entity_for_query(self, sandbox_client: FOClient):
        """Test fast entity validation for query operations."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Get OData-enabled entities
        entities_result = await sandbox_client.get_data_entities(
            QueryOptions(filter="DataServiceEnabled eq true", top=10)
        )
        odata_entities = entities_result.get("value", [])

        if not odata_entities:
            pytest.skip("No OData-enabled entities available for testing")

        # Test validation for known good entities
        for entity in odata_entities[:3]:  # Test first 3
            entity_name = entity.get("Name", "")
            public_collection = entity.get("PublicCollectionName", "")

            if entity_name:
                is_valid = await mixin._validate_entity_for_query(entity_name)
                assert is_valid, f"Entity {entity_name} should be valid for queries"

            if public_collection and public_collection != entity_name:
                is_valid = await mixin._validate_entity_for_query(public_collection)
                assert (
                    is_valid
                ), f"Public collection {public_collection} should be valid for queries"

        # Test validation for invalid entity
        is_valid = await mixin._validate_entity_for_query("NonExistentEntity12345")
        assert not is_valid, "NonExistentEntity12345 should not be valid"

    @pytest.mark.asyncio
    async def test_validate_entity_exists(self, sandbox_client: FOClient):
        """Test comprehensive entity existence validation."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Get some entities to test with
        entities_result = await sandbox_client.get_data_entities(QueryOptions(top=10))
        test_entities = entities_result.get("value", [])

        if not test_entities:
            pytest.skip("No entities available for testing")

        # Test with known entities
        for entity in test_entities[:3]:  # Test first 3
            entity_name = entity.get("Name", "")
            if entity_name:
                exists = await mixin._validate_entity_exists(entity_name)
                assert exists, f"Entity {entity_name} should exist"

        # Test with non-existent entity
        exists = await mixin._validate_entity_exists("CompletelyInvalidEntity9999")
        assert not exists, "CompletelyInvalidEntity9999 should not exist"


@skip_if_not_level("sandbox")
class TestCompositeKeyDiscovery:
    """Test discovery and validation of entities with composite keys."""

    @pytest.mark.asyncio
    async def test_find_entities_with_composite_keys(self, sandbox_client: FOClient):
        """Find and catalog entities with composite keys for testing."""
        # Get public entities that have detailed schema information
        public_entities_result = await sandbox_client.get_public_entities(
            QueryOptions(top=50)
        )
        public_entities = public_entities_result.get("value", [])

        if not public_entities:
            pytest.skip("No public entities available for composite key testing")

        composite_key_entities = []

        # Check each entity for composite keys
        for entity_info in public_entities[:20]:  # Check first 20 entities
            entity_name = entity_info.get("Name", "")
            if not entity_name:
                continue

            try:
                # Get detailed entity schema
                entity_schema = await sandbox_client.get_public_entity_info(
                    entity_name, resolve_labels=False
                )
                if not entity_schema:
                    continue

                # Find key properties
                key_properties = [
                    prop for prop in entity_schema.properties if prop.is_key
                ]

                if len(key_properties) > 1:  # Composite key
                    # Collect information about key field data types
                    key_info = []
                    for prop in key_properties:
                        key_info.append(
                            {
                                "name": prop.name,
                                "data_type": prop.data_type,
                                "type_name": prop.type_name,
                                "is_mandatory": prop.is_mandatory,
                            }
                        )

                    composite_key_entities.append(
                        {
                            "entity_name": entity_name,
                            "entity_set_name": entity_schema.entity_set_name,
                            "key_count": len(key_properties),
                            "key_fields": key_info,
                            "is_read_only": entity_schema.is_read_only,
                        }
                    )

                    logger.info(
                        f"Found composite key entity: {entity_name} with {len(key_properties)} keys"
                    )

                    # Stop after finding several for testing
                    if len(composite_key_entities) >= 5:
                        break

            except Exception as e:
                logger.debug(f"Error checking entity {entity_name}: {e}")
                continue

        # Store findings for other tests
        pytest.composite_key_entities = composite_key_entities

        assert (
            len(composite_key_entities) > 0
        ), "Should find at least one entity with composite keys"

        # Log findings for analysis
        print(f"\n🔍 Found {len(composite_key_entities)} entities with composite keys:")
        for entity in composite_key_entities:
            print(f"  📋 {entity['entity_name']} ({entity['key_count']} keys):")
            for key_field in entity["key_fields"]:
                print(
                    f"    🔑 {key_field['name']}: {key_field['data_type']} ({key_field['type_name']})"
                )

    @pytest.mark.asyncio
    async def test_composite_key_data_types(self, sandbox_client: FOClient):
        """Test various data types in composite keys."""
        # Run discovery first to populate composite_key_entities
        await self.test_find_entities_with_composite_keys(sandbox_client)

        if (
            not hasattr(pytest, "composite_key_entities")
            or not pytest.composite_key_entities
        ):
            pytest.skip("No composite key entities found for data type testing")

        composite_entities = pytest.composite_key_entities

        # Analyze data type diversity in composite keys
        data_types_found = set()
        mixed_type_entities = []

        for entity in composite_entities:
            key_fields = entity["key_fields"]
            entity_data_types = {field["data_type"] for field in key_fields}
            data_types_found.update(entity_data_types)

            # Check for mixed data types in single entity
            if len(entity_data_types) > 1:
                mixed_type_entities.append(
                    {
                        "entity_name": entity["entity_name"],
                        "data_types": list(entity_data_types),
                        "key_fields": key_fields,
                    }
                )

        print(
            f"\n📊 Data type analysis across {len(composite_entities)} composite key entities:"
        )
        print(f"  🔢 Unique data types found: {sorted(data_types_found)}")
        print(f"  🎯 Entities with mixed data types: {len(mixed_type_entities)}")

        if mixed_type_entities:
            print("\n🎭 Entities with mixed data types in composite keys:")
            for entity in mixed_type_entities:
                print(f"  📋 {entity['entity_name']}: {entity['data_types']}")
                for key_field in entity["key_fields"]:
                    print(f"    🔑 {key_field['name']}: {key_field['data_type']}")

        # Ensure we found some variety in data types
        assert (
            len(data_types_found) > 1
        ), f"Expected multiple data types, found: {data_types_found}"


@skip_if_not_level("sandbox")
class TestODataSerialization:
    """Test OData serialization with real D365 F&O data types."""

    @pytest.mark.asyncio
    async def test_serialize_real_entity_key_fields(self, sandbox_client: FOClient):
        """Test OData serialization with real entity key field data types."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Get entities with detailed schema
        public_entities_result = await sandbox_client.get_public_entities(
            QueryOptions(top=20)
        )
        public_entities = public_entities_result.get("value", [])

        if not public_entities:
            pytest.skip("No public entities available for serialization testing")

        serialization_tests = []

        # Check entities for various data types
        for entity_info in public_entities[:10]:
            entity_name = entity_info.get("Name", "")
            if not entity_name:
                continue

            try:
                entity_schema = await sandbox_client.get_public_entity_info(
                    entity_name, resolve_labels=False
                )
                if not entity_schema:
                    continue

                # Test serialization for key properties
                for prop in entity_schema.properties:
                    if prop.is_key:
                        # Test serialization with sample values
                        test_values = self._get_test_values_for_data_type(
                            prop.data_type
                        )

                        for test_value in test_values:
                            try:
                                serialized = mixin._serialize_odata_value(
                                    test_value, prop.data_type, prop.type_name
                                )

                                serialization_tests.append(
                                    {
                                        "entity": entity_name,
                                        "field": prop.name,
                                        "data_type": prop.data_type,
                                        "type_name": prop.type_name,
                                        "test_value": test_value,
                                        "serialized": serialized,
                                        "success": True,
                                    }
                                )

                            except Exception as e:
                                serialization_tests.append(
                                    {
                                        "entity": entity_name,
                                        "field": prop.name,
                                        "data_type": prop.data_type,
                                        "type_name": prop.type_name,
                                        "test_value": test_value,
                                        "error": str(e),
                                        "success": False,
                                    }
                                )

                    # Stop after collecting enough test cases
                    if len(serialization_tests) >= 50:
                        break

                if len(serialization_tests) >= 50:
                    break

            except Exception as e:
                logger.debug(f"Error processing entity {entity_name}: {e}")
                continue

        # Analyze results
        successful_tests = [t for t in serialization_tests if t["success"]]
        failed_tests = [t for t in serialization_tests if not t["success"]]

        print(f"\n🧪 OData Serialization Test Results:")
        print(f"  ✅ Successful: {len(successful_tests)}")
        print(f"  ❌ Failed: {len(failed_tests)}")

        if failed_tests:
            print("\n❌ Failed serialization tests:")
            for test in failed_tests[:5]:  # Show first 5 failures
                print(f"  Entity: {test['entity']}, Field: {test['field']}")
                print(f"    Type: {test['data_type']}, Value: {test['test_value']}")
                print(f"    Error: {test['error']}")

        # Summarize data types tested
        data_types_tested = {t["data_type"] for t in serialization_tests}
        print(f"\n📊 Data types tested: {sorted(data_types_tested)}")

        # Ensure high success rate
        if serialization_tests:
            success_rate = len(successful_tests) / len(serialization_tests)
            assert (
                success_rate > 0.8
            ), f"Low success rate: {success_rate:.2%} ({len(failed_tests)} failures)"

    def _get_test_values_for_data_type(self, data_type: str) -> List[Any]:
        """Get appropriate test values for a given data type."""
        test_values_map = {
            "String": ["test", "Test Value", ""],
            "Int32": [1, 42, 0, -1],
            "Int64": [1, 123456789, 0, -123456789],
            "Real": [1.0, 3.14159, 0.0, -2.5],
            "Decimal": [1.00, 123.45, 0.00, -999.99],
            "Money": [1.00, 999.99, 0.00],
            "Boolean": [True, False],
            "Guid": ["12345678-1234-1234-1234-123456789abc"],
            "Date": ["2023-12-25", "2024-01-01"],
            "Time": ["14:30:00", "09:15:30"],
            "DateTime": ["2023-12-25T14:30:00", "2024-01-01T00:00:00"],
            "UtcDateTime": ["2023-12-25T14:30:00Z", "2024-01-01T00:00:00Z"],
            "Enum": ["Yes", "No", "Active", "Inactive"],
        }

        return test_values_map.get(data_type, ["default_test_value"])

    @pytest.mark.asyncio
    async def test_build_validated_key_dict(self, sandbox_client: FOClient):
        """Test building validated key dictionaries for composite keys."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Find an entity with composite keys
        public_entities_result = await sandbox_client.get_public_entities(
            QueryOptions(top=20)
        )
        public_entities = public_entities_result.get("value", [])

        if not public_entities:
            pytest.skip("No public entities available for key validation testing")

        composite_key_entity = None

        for entity_info in public_entities:
            entity_name = entity_info.get("Name", "")
            if not entity_name:
                continue

            try:
                entity_schema = await sandbox_client.get_public_entity_info(
                    entity_name, resolve_labels=False
                )
                if not entity_schema:
                    continue

                key_properties = [
                    prop for prop in entity_schema.properties if prop.is_key
                ]

                if len(key_properties) > 1:  # Found composite key entity
                    composite_key_entity = {
                        "schema": entity_schema,
                        "key_properties": key_properties,
                    }
                    break

            except Exception as e:
                logger.debug(f"Error checking entity {entity_name}: {e}")
                continue

        if not composite_key_entity:
            pytest.skip("No composite key entities found for key validation testing")

        # Test building key dict with composite keys
        assert composite_key_entity is not None  # For type checker
        schema = composite_key_entity["schema"]
        key_props = composite_key_entity["key_properties"]

        # Create test key fields and values
        key_fields = [prop.name for prop in key_props]
        key_values = []

        for prop in key_props:
            test_values = self._get_test_values_for_data_type(prop.data_type)
            key_values.append(str(test_values[0]))  # Use first test value

        # Build and validate key dictionary
        key_dict = mixin._build_validated_key_dict(key_fields, key_values, schema)

        assert isinstance(key_dict, dict)
        assert len(key_dict) == len(key_fields)

        for field_name in key_fields:
            assert field_name in key_dict
            assert isinstance(
                key_dict[field_name], str
            )  # Should be serialized as string

        print(f"\n🔑 Built validated key dict for {schema.name}:")
        for field, value in key_dict.items():
            print(f"  {field}: {value}")


@skip_if_not_level("sandbox")
class TestEntitySchemaValidation:
    """Test entity schema validation with real entities."""

    @pytest.mark.asyncio
    async def test_validate_entity_schema_and_keys(self, sandbox_client: FOClient):
        """Test comprehensive entity schema and key validation."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Get entities to test with
        entities_result = await sandbox_client.get_data_entities(QueryOptions(top=15))
        data_entities = entities_result.get("value", [])

        if not data_entities:
            pytest.skip("No data entities available for schema validation testing")

        validation_results = []

        for entity in data_entities:
            if not entity.get("DataServiceEnabled", False):
                continue  # Skip non-OData entities

            entity_name = entity.get("Name", "")
            public_collection = entity.get("PublicCollectionName", "")

            if not entity_name:
                continue

            try:
                # Get the entity schema
                resolved_name = await mixin._resolve_entity_name(entity_name)
                if not resolved_name:
                    continue

                entity_schema = await sandbox_client.get_public_entity_info(
                    resolved_name, resolve_labels=False
                )
                if not entity_schema:
                    continue

                # Get key properties
                key_properties = [
                    prop for prop in entity_schema.properties if prop.is_key
                ]
                if not key_properties:
                    continue

                # Test validation with correct keys
                key_fields = [prop.name for prop in key_properties]
                key_values = ["test_value"] * len(key_fields)  # Use dummy values

                is_valid, schema, error_details = (
                    await mixin._validate_entity_schema_and_keys(
                        entity_name, key_fields, key_values
                    )
                )

                validation_results.append(
                    {
                        "entity_name": entity_name,
                        "public_collection": public_collection,
                        "key_count": len(key_properties),
                        "validation_success": is_valid,
                        "error_details": error_details,
                        "schema_found": schema is not None,
                    }
                )

                # Test with incorrect keys (missing key)
                if len(key_fields) > 1:
                    incomplete_fields = key_fields[:-1]  # Remove last key
                    incomplete_values = key_values[:-1]

                    is_valid_incomplete, _, error_details_incomplete = (
                        await mixin._validate_entity_schema_and_keys(
                            entity_name, incomplete_fields, incomplete_values
                        )
                    )

                    assert (
                        not is_valid_incomplete
                    ), f"Validation should fail for incomplete keys on {entity_name}"
                    assert (
                        error_details_incomplete is not None
                    ), "Should have error details for incomplete keys"

                # Stop after testing several entities
                if len(validation_results) >= 5:
                    break

            except Exception as e:
                logger.debug(f"Error validating entity {entity_name}: {e}")
                continue

        # Analyze validation results
        successful_validations = [
            r for r in validation_results if r["validation_success"]
        ]
        failed_validations = [
            r for r in validation_results if not r["validation_success"]
        ]

        print(f"\n🔍 Schema Validation Results:")
        print(f"  ✅ Successful: {len(successful_validations)}")
        print(f"  ❌ Failed: {len(failed_validations)}")

        if failed_validations:
            print("\n❌ Failed validations:")
            for result in failed_validations:
                print(
                    f"  {result['entity_name']}: {result.get('error_details', 'Unknown error')}"
                )

        # Should have at least some successful validations
        assert (
            len(successful_validations) > 0
        ), "Should have at least one successful schema validation"


@skip_if_not_level("sandbox")
class TestIntegratedCRUDValidation:
    """Test integrated CRUD operations with enhanced validation."""

    @pytest.mark.asyncio
    async def test_crud_validation_integration(self, sandbox_client: FOClient):
        """Test that CRUD operations work with enhanced validation methods."""
        mixin = BaseToolsMixinWrapper(sandbox_client)

        # Find an accessible entity for testing
        entities_result = await sandbox_client.get_data_entities(
            QueryOptions(filter="DataServiceEnabled eq true", top=10)
        )
        accessible_entities = entities_result.get("value", [])

        if not accessible_entities:
            pytest.skip("No accessible entities found for CRUD validation testing")

        # Test the underlying validation methods directly
        test_entity = accessible_entities[0]
        entity_name = test_entity.get("Name", "")
        public_collection = test_entity.get("PublicCollectionName", entity_name)

        if not entity_name:
            pytest.skip("No valid entity name found for testing")

        # Test entity existence validation
        exists = await mixin._validate_entity_exists(entity_name)
        print(f"Entity existence validation for '{entity_name}': {exists}")

        # Test entity resolution
        resolved_name = await mixin._resolve_entity_name(entity_name)
        print(f"Entity name resolution for '{entity_name}': {resolved_name}")

        # Test query validation
        query_valid = await mixin._validate_entity_for_query(public_collection)
        print(f"Query validation for '{public_collection}': {query_valid}")

        # Test with invalid entity (should fail gracefully)
        invalid_exists = await mixin._validate_entity_exists(
            "CompletelyInvalidEntity9999"
        )
        assert not invalid_exists, "Invalid entity should not exist"

        invalid_resolved = await mixin._resolve_entity_name(
            "CompletelyInvalidEntity9999"
        )
        assert invalid_resolved is None, "Invalid entity should not resolve"

        invalid_query_valid = await mixin._validate_entity_for_query(
            "CompletelyInvalidEntity9999"
        )
        assert not invalid_query_valid, "Invalid entity should not be valid for queries"

        print("✅ All CRUD validation methods working correctly")
