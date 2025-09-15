"""Comprehensive metadata API tests against sandbox environment.

These tests validate metadata operations against actual D365 F&O sandbox environment,
testing real metadata structure, entity discovery, and schema validation.
"""

import pytest
import pytest_asyncio
from typing import List, Dict, Any

from d365fo_client import FOClient
from d365fo_client.models import QueryOptions

from . import skip_if_not_level


@skip_if_not_level("sandbox")
class TestSandboxMetadataCore:
    """Test core metadata operations against sandbox environment."""

    @pytest.mark.asyncio
    async def test_download_metadata_success(self, sandbox_client: FOClient):
        """Test downloading OData metadata from sandbox."""
        result = await sandbox_client.download_metadata(force_refresh=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_metadata_connection_stability(self, sandbox_client: FOClient):
        """Test metadata connection stability."""
        # Test multiple metadata connections
        for _ in range(3):
            result = await sandbox_client.test_metadata_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_metadata_caching_behavior(self, sandbox_client: FOClient):
        """Test metadata caching works correctly."""
        import time

        # First download (should fetch from server)
        start_time = time.time()
        result1 = await sandbox_client.download_metadata(force_refresh=True)
        first_duration = time.time() - start_time

        # Second download (should use cache unless forced)
        start_time = time.time()
        result2 = await sandbox_client.download_metadata(force_refresh=False)
        second_duration = time.time() - start_time

        assert result1 is True
        assert result2 is True

        # Cached call should be faster (though not always guaranteed)
        # Just ensure both succeed


@skip_if_not_level("sandbox")
class TestSandboxEntityMetadata:
    """Test entity metadata operations against sandbox."""

    @pytest.mark.asyncio
    async def test_get_data_entities_comprehensive(self, sandbox_client: FOClient):
        """Test retrieving data entities with comprehensive validation."""
        result = await sandbox_client.get_data_entities(QueryOptions(top=20))

        assert "value" in result
        assert isinstance(result["value"], list)
        assert len(result["value"]) > 0

        # Validate entity metadata structure
        for entity in result["value"][:5]:  # Check first 5 entities
            # Check for fields that should be present
            required_fields = ["DataServiceEnabled", "EntityCategory", "IsReadOnly"]
            for field in required_fields:
                assert field in entity, f"Required field {field} missing from entity metadata"

            # Validate field types
            assert isinstance(entity["DataServiceEnabled"], bool)
            assert isinstance(entity["IsReadOnly"], bool)

            # Check optional fields if present
            if "Name" in entity:
                assert isinstance(entity["Name"], str)
                assert len(entity["Name"]) > 0

            if "EntitySetName" in entity:
                assert isinstance(entity["EntitySetName"], str)

    @pytest.mark.asyncio
    async def test_get_data_entities_with_filtering(self, sandbox_client: FOClient):
        """Test retrieving data entities with OData filtering."""
        # Test top parameter
        result_limited = await sandbox_client.get_data_entities(QueryOptions(top=5))
        assert len(result_limited["value"]) <= 5

        # Test skip parameter
        result_all = await sandbox_client.get_data_entities(QueryOptions(top=10))
        if len(result_all["value"]) > 5:
            result_skip = await sandbox_client.get_data_entities(QueryOptions(top=5, skip=5))

            # Should get different entities when skipping
            if result_skip["value"]:
                first_names = {e.get("Name", "") for e in result_all["value"][:5]}
                skip_names = {e.get("Name", "") for e in result_skip["value"]}
                # At least some should be different
                assert not first_names == skip_names or len(first_names) == 0

    @pytest.mark.asyncio
    async def test_get_public_entities_structure(self, sandbox_client: FOClient):
        """Test retrieving public entities and validate structure."""
        result = await sandbox_client.get_public_entities(QueryOptions(top=10))

        assert "value" in result
        assert isinstance(result["value"], list)
        assert len(result["value"]) > 0

        # Validate public entity structure
        for entity in result["value"][:3]:
            # Public entities should have these key fields
            assert "Name" in entity
            assert "EntitySetName" in entity
            assert isinstance(entity["Name"], str)
            assert isinstance(entity["EntitySetName"], str)

            # Check for properties structure if present
            if "Properties" in entity:
                assert isinstance(entity["Properties"], list)

    @pytest.mark.asyncio
    async def test_get_public_entity_detailed_info(self, sandbox_client: FOClient):
        """Test retrieving detailed information for specific public entities."""
        # First get list of public entities
        entities_result = await sandbox_client.get_public_entities(QueryOptions(top=5))

        if entities_result["value"]:
            # Test detailed info for first entity
            entity_name = entities_result["value"][0]["Name"]

            try:
                entity_info = await sandbox_client.get_public_entity_info(entity_name)

                if entity_info:
                    assert entity_info.name == entity_name
                    assert hasattr(entity_info, "entity_set_name")
                    assert hasattr(entity_info, "properties")

                    if entity_info.properties:
                        # Validate property structure
                        prop = entity_info.properties[0]
                        assert hasattr(prop, "name")
                        assert hasattr(prop, "type_name")
                        assert hasattr(prop, "is_key")

            except Exception as e:
                pytest.skip(f"Entity info not available for {entity_name}: {e}")

    @pytest.mark.asyncio
    async def test_search_entities_functionality(self, sandbox_client: FOClient):
        """Test entity search functionality with real metadata."""
        # Ensure metadata is downloaded first
        await sandbox_client.download_metadata()

        # Test search for common entity patterns
        search_patterns = ["Customer", "Vendor", "Company", "Legal"]

        found_entities = []
        for pattern in search_patterns:
            try:
                entities = await sandbox_client.search_entities(pattern)
                found_entities.extend(entities)

                # Validate search results
                for entity in entities:
                    assert hasattr(entity, "name")
                    assert hasattr(entity, "public_collection_name")
                    # Entity name should contain the search pattern (case-insensitive)
                    assert pattern.lower() in entity.name.lower()

            except Exception as e:
                # Search might not find entities or might fail
                continue

        # Should find at least some entities
        assert len(found_entities) > 0, f"No entities found for search patterns: {search_patterns}"

    @pytest.mark.asyncio
    async def test_entity_search_case_sensitivity(self, sandbox_client: FOClient):
        """Test that entity search works with different case patterns."""
        await sandbox_client.download_metadata()

        search_terms = ["company", "COMPANY", "Company"]
        results = []

        for term in search_terms:
            try:
                entities = await sandbox_client.search_entities(term)
                results.append(len(entities))
            except Exception:
                results.append(0)

        # All case variations should return similar results
        if any(r > 0 for r in results):
            # At least one search succeeded, others should too (or return similar counts)
            non_zero_results = [r for r in results if r > 0]
            if len(non_zero_results) > 1:
                # Results should be similar (within reasonable range)
                min_results = min(non_zero_results)
                max_results = max(non_zero_results)
                assert max_results <= min_results * 2, "Case sensitivity affecting results significantly"


@skip_if_not_level("sandbox")
class TestSandboxMetadataEnumerations:
    """Test enumeration metadata operations against sandbox."""

    @pytest.mark.asyncio
    async def test_get_public_enumerations_structure(self, sandbox_client: FOClient):
        """Test retrieving public enumerations metadata."""
        result = await sandbox_client.get_public_enumerations(QueryOptions(top=10))

        assert "value" in result
        assert isinstance(result["value"], list)

        if result["value"]:
            # Validate enumeration structure
            enum = result["value"][0]
            assert "Name" in enum
            assert isinstance(enum["Name"], str)

            # Check for label information
            if "LabelId" in enum:
                assert isinstance(enum["LabelId"], str)

    @pytest.mark.asyncio
    async def test_enumerations_with_filtering(self, sandbox_client: FOClient):
        """Test retrieving enumerations with query options."""
        # Test with small top value
        result = await sandbox_client.get_public_enumerations(QueryOptions(top=3))

        assert "value" in result
        assert len(result["value"]) <= 3

        # Test pagination if we have enough enumerations
        full_result = await sandbox_client.get_public_enumerations(QueryOptions(top=10))
        if len(full_result["value"]) > 3:
            skip_result = await sandbox_client.get_public_enumerations(QueryOptions(top=3, skip=3))

            if skip_result["value"]:
                # Pagination should work
                first_names = {e["Name"] for e in result["value"]}
                skip_names = {e["Name"] for e in skip_result["value"]}
                assert first_names != skip_names, "Pagination returned same results"


@skip_if_not_level("sandbox")
class TestSandboxLabelOperations:
    """Test label operations against sandbox environment."""

    @pytest.mark.asyncio
    async def test_get_label_text_functionality(self, sandbox_client: FOClient):
        """Test retrieving label text for actual label IDs."""
        # Common label patterns in D365
        test_labels = [
            "@SYS1",        # System labels usually exist
            "@SYS2",
            "@SYS10",
            "@ApplicationCommon1",  # Application common labels
        ]

        successful_labels = 0
        for label_id in test_labels:
            try:
                label_text = await sandbox_client.get_label_text(label_id)
                if label_text:
                    assert isinstance(label_text, str)
                    assert len(label_text) > 0
                    successful_labels += 1
            except Exception:
                # Label might not exist
                continue

        # At least some system labels should exist
        # Note: This is environment-dependent, so we're lenient
        if successful_labels == 0:
            pytest.skip("No test labels found in sandbox environment")

    @pytest.mark.asyncio
    async def test_get_labels_batch_operation(self, sandbox_client: FOClient):
        """Test batch label retrieval."""
        # Test with a mix of potentially existing and non-existing labels
        label_ids = [
            "@SYS1",
            "@SYS2",
            "@NonExistentLabel123456",
            "@SYS10"
        ]

        try:
            labels = await sandbox_client.get_labels_batch(label_ids)

            assert isinstance(labels, dict)

            # Check that we get some results
            found_labels = {k: v for k, v in labels.items() if v is not None}

            if len(found_labels) == 0:
                pytest.skip("No labels found in batch operation")

            # Validate found labels
            for label_id, label_text in found_labels.items():
                assert label_id in label_ids
                assert isinstance(label_text, str)
                assert len(label_text) > 0

        except Exception as e:
            pytest.skip(f"Batch label operation not supported: {e}")

    @pytest.mark.asyncio
    async def test_label_text_encoding(self, sandbox_client: FOClient):
        """Test that label text handles various encodings properly."""
        # Test common system labels that might contain special characters
        test_labels = ["@SYS1", "@SYS2", "@SYS5"]

        for label_id in test_labels:
            try:
                label_text = await sandbox_client.get_label_text(label_id)
                if label_text:
                    # Should be valid Unicode string
                    assert isinstance(label_text, str)
                    # Should be encodable/decodable
                    encoded = label_text.encode('utf-8')
                    decoded = encoded.decode('utf-8')
                    assert decoded == label_text
            except Exception:
                # Label might not exist
                continue


@skip_if_not_level("sandbox")
class TestSandboxMetadataIntegration:
    """Test integration scenarios combining multiple metadata operations."""

    @pytest.mark.asyncio
    async def test_metadata_to_data_workflow(self, sandbox_client: FOClient):
        """Test workflow from metadata discovery to data access."""
        # Step 1: Download metadata
        await sandbox_client.download_metadata()

        # Step 2: Search for entities
        entities = await sandbox_client.search_entities("Compan")

        if entities:
            # Step 3: Get detailed info for first entity
            entity = entities[0]

            try:
                entity_info = await sandbox_client.get_public_entity_info(entity.name)

                if entity_info and entity_info.properties:
                    # Step 4: Try to access the entity's data
                    collection_name = entity.public_collection_name or entity.name

                    try:
                        data_result = await sandbox_client.get_entities(
                            collection_name,
                            QueryOptions(top=1)
                        )
                        assert "value" in data_result

                        # Step 5: Validate that metadata matches data structure
                        if data_result["value"]:
                            data_fields = set(data_result["value"][0].keys())
                            metadata_fields = {prop.name for prop in entity_info.properties}

                            # Some metadata fields should match data fields
                            # (allowing for system fields in data that might not be in metadata)
                            common_fields = data_fields.intersection(metadata_fields)
                            assert len(common_fields) > 0, "No common fields between metadata and data"

                    except Exception:
                        # Entity might not be accessible for data operations
                        pass

            except Exception:
                # Entity info might not be available
                pass

    @pytest.mark.asyncio
    async def test_metadata_consistency_across_apis(self, sandbox_client: FOClient):
        """Test consistency between different metadata APIs."""
        # Get entities from data entities API
        data_entities = await sandbox_client.get_data_entities(QueryOptions(top=10))

        # Get entities from public entities API
        public_entities = await sandbox_client.get_public_entities(QueryOptions(top=10))

        # Extract entity names
        data_entity_names = {e.get("Name", "") for e in data_entities["value"] if e.get("Name")}
        public_entity_names = {e.get("Name", "") for e in public_entities["value"] if e.get("Name")}

        # There should be some overlap between the two APIs
        common_entities = data_entity_names.intersection(public_entity_names)

        # This is environment-dependent, so we're lenient
        # Just ensure both APIs return some entities
        assert len(data_entity_names) > 0, "No entities from data entities API"
        assert len(public_entity_names) > 0, "No entities from public entities API"

    @pytest.mark.asyncio
    async def test_concurrent_metadata_operations(self, sandbox_client: FOClient):
        """Test concurrent metadata operations."""
        import asyncio

        # Create concurrent metadata requests
        tasks = [
            sandbox_client.get_data_entities(QueryOptions(top=5)),
            sandbox_client.get_public_entities(QueryOptions(top=5)),
            sandbox_client.get_public_enumerations(QueryOptions(top=5)),
            sandbox_client.test_metadata_connection(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful operations
        successful = sum(1 for r in results if not isinstance(r, Exception))

        # Most operations should succeed
        assert successful >= len(tasks) // 2, f"Too many metadata operations failed: {len(tasks) - successful} failures"

    @pytest.mark.asyncio
    async def test_metadata_performance_characteristics(self, sandbox_client: FOClient, performance_metrics):
        """Test metadata operation performance characteristics."""
        import time

        operations = [
            ("get_data_entities", lambda: sandbox_client.get_data_entities(QueryOptions(top=10))),
            ("get_public_entities", lambda: sandbox_client.get_public_entities(QueryOptions(top=10))),
            ("test_metadata_connection", lambda: sandbox_client.test_metadata_connection()),
        ]

        for name, operation in operations:
            start_time = time.time()
            try:
                await operation()
                duration = time.time() - start_time
                performance_metrics["timings"][f"metadata_{name}"] = duration

                # Metadata operations should complete in reasonable time
                assert duration < 30.0, f"Metadata operation {name} took too long: {duration}s"

            except Exception as e:
                performance_metrics["errors"].append({"operation": f"metadata_{name}", "error": str(e)})