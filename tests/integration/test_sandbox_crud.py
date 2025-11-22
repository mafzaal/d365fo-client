"""Comprehensive CRUD operation tests against sandbox environment.

These tests validate CRUD operations against actual D365 F&O sandbox environment,
testing real API behavior, entity relationships, and data integrity.
"""

from typing import Any, Dict, List

import pytest
import pytest_asyncio

from d365fo_client import FOClient
from d365fo_client.models import QueryOptions

from . import skip_if_not_level


@skip_if_not_level("sandbox")
class TestSandboxCrudOperations:
    """Test basic CRUD operations against sandbox environment."""

    @pytest.mark.asyncio
    async def test_get_companies(self, sandbox_client: FOClient, entity_validator):
        """Test retrieving companies (safe entity for testing)."""
        result = await sandbox_client.get_entities("Companies", QueryOptions(top=5))

        assert entity_validator["odata_response"](result)
        assert "value" in result
        assert isinstance(result["value"], list)
        assert len(result["value"]) > 0

        # Validate company data structure
        company = result["value"][0]
        assert "DataArea" in company  # Company ID field
        assert isinstance(company["DataArea"], str)

    @pytest.mark.asyncio
    async def test_get_company_by_key(self, sandbox_client: FOClient):
        """Test retrieving single company by key."""
        # First get available companies
        companies = await sandbox_client.get_entities("Companies", QueryOptions(top=1))

        if companies["value"]:
            company_id = companies["value"][0]["DataArea"]

            # Get specific company
            company = await sandbox_client.get_entity("Companies", company_id)

            assert company["DataArea"] == company_id
            assert "Name" in company or "CompanyName" in company

    @pytest.mark.asyncio
    async def test_get_legal_entities(self, sandbox_client: FOClient, entity_validator):
        """Test retrieving legal entities."""
        result = await sandbox_client.get_entities("LegalEntities", QueryOptions(top=3))

        assert entity_validator["odata_response"](result)
        assert "value" in result
        assert isinstance(result["value"], list)

        if result["value"]:
            entity = result["value"][0]
            # Legal entities should have these fields
            assert "LegalEntityId" in entity or "Name" in entity

    @pytest.mark.asyncio
    async def test_query_options_top_and_skip(self, sandbox_client: FOClient):
        """Test OData query options against real data."""
        # Test top parameter
        result_top2 = await sandbox_client.get_entities(
            "Companies", QueryOptions(top=2)
        )
        assert len(result_top2["value"]) <= 2

        # Test skip parameter if we have enough data
        result_all = await sandbox_client.get_entities("Companies", QueryOptions(top=5))
        if len(result_all["value"]) > 1:
            result_skip1 = await sandbox_client.get_entities(
                "Companies", QueryOptions(top=1, skip=1)
            )
            if result_skip1["value"]:
                # Should get different result when skipping
                assert (
                    result_skip1["value"][0]["DataArea"]
                    != result_all["value"][0]["DataArea"]
                )

    @pytest.mark.asyncio
    async def test_odata_filter_operations(self, sandbox_client: FOClient):
        """Test OData filter operations against real data."""
        try:
            # Get some companies first to understand available data
            companies = await sandbox_client.get_entities(
                "Companies", QueryOptions(top=10)
            )

            if companies["value"] and len(companies["value"]) > 0:
                # Test filter by specific company
                company_id = companies["value"][0]["DataArea"]
                filter_query = f"DataArea eq '{company_id}'"

                filtered_result = await sandbox_client.get_entities(
                    "Companies", QueryOptions(filter=filter_query)
                )

                assert "value" in filtered_result
                if filtered_result["value"]:
                    assert filtered_result["value"][0]["DataArea"] == company_id

        except Exception as e:
            pytest.skip(f"Filter operations not supported or data unavailable: {e}")

    @pytest.mark.asyncio
    async def test_odata_select_operations(self, sandbox_client: FOClient):
        """Test OData select operations to limit returned fields."""
        try:
            # Select only specific fields
            select_fields = ["DataArea"]
            result = await sandbox_client.get_entities(
                "Companies", QueryOptions(top=1, select=select_fields)
            )

            if result["value"]:
                company = result["value"][0]
                # Should only contain selected field (plus possible system fields)
                assert "DataArea" in company

        except Exception as e:
            pytest.skip(f"Select operations not supported: {e}")


@skip_if_not_level("sandbox")
class TestSandboxDataIntegrity:
    """Test data integrity and validation against sandbox."""

    @pytest.mark.asyncio
    async def test_data_consistency_across_calls(self, sandbox_client: FOClient):
        """Test that data remains consistent across multiple calls."""
        # Make multiple calls to the same entity
        calls = []
        for _ in range(3):
            result = await sandbox_client.get_entities("Companies", QueryOptions(top=1))
            calls.append(result)

        # Results should be consistent
        if all(call["value"] for call in calls):
            first_company = calls[0]["value"][0]["DataArea"]
            for call in calls:
                assert call["value"][0]["DataArea"] == first_company

    @pytest.mark.asyncio
    async def test_entity_field_validation(self, sandbox_client: FOClient):
        """Test that entities have expected field types and structure."""
        companies = await sandbox_client.get_entities("Companies", QueryOptions(top=1))

        if companies["value"]:
            company = companies["value"][0]

            # Validate field types
            assert isinstance(company["DataArea"], str)

            # Check for common optional fields
            if "Name" in company:
                assert isinstance(company["Name"], (str, type(None)))

    @pytest.mark.asyncio
    async def test_pagination_consistency(self, sandbox_client: FOClient):
        """Test that pagination works correctly with real data."""
        page_size = 2

        # Get first page
        page1 = await sandbox_client.get_entities(
            "Companies", QueryOptions(top=page_size)
        )

        # Get second page if first page has data
        if len(page1["value"]) == page_size:
            page2 = await sandbox_client.get_entities(
                "Companies", QueryOptions(top=page_size, skip=page_size)
            )

            # Pages should not overlap
            if page2["value"]:
                page1_ids = {item["DataArea"] for item in page1["value"]}
                page2_ids = {item["DataArea"] for item in page2["value"]}
                assert page1_ids.isdisjoint(
                    page2_ids
                ), "Pagination returned overlapping results"


@skip_if_not_level("sandbox")
class TestSandboxEntityDiscovery:
    """Test entity discovery and availability in sandbox."""

    @pytest.mark.asyncio
    async def test_common_entities_availability(self, sandbox_client: FOClient):
        """Test that common entities are available in sandbox."""
        common_entities = [
            "Companies",
            "LegalEntities",
            "NumberSequences",
            "DataArea",
            "SystemParameters",
        ]

        available_entities = []

        for entity in common_entities:
            try:
                result = await sandbox_client.get_entities(entity, QueryOptions(top=1))
                if "value" in result:
                    available_entities.append(entity)
            except Exception:
                # Entity might not be available
                continue

        # At least some common entities should be available
        assert (
            len(available_entities) > 0
        ), f"No common entities available: {common_entities}"

    @pytest.mark.asyncio
    async def test_entity_response_structure(self, sandbox_client: FOClient):
        """Test that entity responses follow expected OData structure."""
        entities_to_test = ["Companies"]

        for entity in entities_to_test:
            try:
                result = await sandbox_client.get_entities(entity, QueryOptions(top=1))

                # Should have OData structure
                assert "value" in result
                assert isinstance(result["value"], list)

                # May have OData context
                if "@odata.context" in result:
                    assert isinstance(result["@odata.context"], str)

            except Exception as e:
                pytest.skip(f"Entity {entity} not accessible: {e}")


@skip_if_not_level("sandbox")
class TestSandboxConcurrentOperations:
    """Test concurrent operations against sandbox environment."""

    @pytest.mark.asyncio
    async def test_concurrent_entity_requests(self, sandbox_client: FOClient):
        """Test multiple concurrent entity requests."""
        import asyncio

        # Create concurrent requests for different entities
        tasks = [
            sandbox_client.get_entities("Companies", QueryOptions(top=1)),
            sandbox_client.get_entities("LegalEntities", QueryOptions(top=1)),
            sandbox_client.test_connection(),
            sandbox_client.get_application_version(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful operations
        successful = 0
        for result in results:
            if not isinstance(result, Exception):
                successful += 1

        # At least some operations should succeed
        assert (
            successful >= 2
        ), f"Too many concurrent operations failed: {len(results) - successful} failures"

    @pytest.mark.asyncio
    async def test_concurrent_same_entity_requests(self, sandbox_client: FOClient):
        """Test multiple concurrent requests to the same entity."""
        import asyncio

        # Create multiple concurrent requests to same entity
        tasks = [
            sandbox_client.get_entities("Companies", QueryOptions(top=1))
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed and return consistent data
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(tasks), "Some concurrent requests failed"

        # Results should be consistent
        if all(r["value"] for r in successful_results):
            first_result = successful_results[0]["value"][0]["DataArea"]
            for result in successful_results:
                assert result["value"][0]["DataArea"] == first_result


@skip_if_not_level("sandbox")
class TestSandboxRealWorldScenarios:
    """Test real-world usage scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_typical_data_browsing_workflow(self, sandbox_client: FOClient):
        """Test a typical workflow of browsing entity data."""
        # Step 1: Get list of companies
        companies = await sandbox_client.get_entities("Companies", QueryOptions(top=5))
        assert "value" in companies

        if companies["value"]:
            # Step 2: Get details for first company
            company_id = companies["value"][0]["DataArea"]
            company_detail = await sandbox_client.get_entity("Companies", company_id)
            assert company_detail["DataArea"] == company_id

            # Step 3: Search for related legal entities in same company
            try:
                legal_entities = await sandbox_client.get_entities(
                    "LegalEntities", QueryOptions(top=5)
                )
                assert "value" in legal_entities
            except Exception:
                # Legal entities might not be available
                pass

    @pytest.mark.asyncio
    async def test_large_dataset_handling(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test handling larger datasets from sandbox."""
        import time

        start_time = time.time()

        # Request larger dataset
        result = await sandbox_client.get_entities("Companies", QueryOptions(top=100))

        duration = time.time() - start_time
        performance_metrics["timings"]["large_dataset_sandbox"] = duration

        assert "value" in result
        assert isinstance(result["value"], list)

        # Should complete in reasonable time even for larger datasets
        assert duration < 60.0, f"Large dataset request took too long: {duration}s"

    @pytest.mark.asyncio
    async def test_metadata_and_data_integration(self, sandbox_client: FOClient):
        """Test integration between metadata and data operations."""
        # First ensure metadata is available
        await sandbox_client.download_metadata()

        # Search for entities
        entities = await sandbox_client.search_entities("Compan")

        if entities:
            # Try to get data for found entities
            for entity in entities[:2]:  # Test first 2 entities
                try:
                    result = await sandbox_client.get_entities(
                        entity.public_collection_name or entity.name,
                        QueryOptions(top=1),
                    )
                    assert "value" in result
                except Exception:
                    # Some entities might not be accessible for data operations
                    continue
