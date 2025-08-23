"""Integration tests using mock server.

These tests run against a local mock server that simulates D365 F&O API responses.
They are fast, reliable, and don't require external dependencies.
"""

import pytest
import pytest_asyncio

from d365fo_client import FOClient
from d365fo_client.models import QueryOptions


class TestConnectionMockServer:
    """Test basic connection functionality against mock server."""

    @pytest.mark.asyncio
    async def test_connection_success(self, mock_client: FOClient):
        """Test successful connection to mock server."""
        result = await mock_client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_metadata_connection_success(self, mock_client: FOClient):
        """Test successful metadata connection to mock server."""
        result = await mock_client.test_metadata_connection()
        assert result is True


class TestVersionMethodsMockServer:
    """Test version methods against mock server."""

    @pytest.mark.asyncio
    async def test_get_application_version(self, mock_client: FOClient):
        """Test GetApplicationVersion action."""
        version = await mock_client.get_application_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert version == "10.0.1985.137"

    @pytest.mark.asyncio
    async def test_get_platform_build_version(self, mock_client: FOClient):
        """Test GetPlatformBuildVersion action."""
        version = await mock_client.get_platform_build_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert version == "10.0.1985.137"

    @pytest.mark.asyncio
    async def test_get_application_build_version(self, mock_client: FOClient):
        """Test GetApplicationBuildVersion action."""
        version = await mock_client.get_application_build_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert version == "10.0.1985.137"

    @pytest.mark.asyncio
    async def test_all_version_methods_parallel(
        self, mock_client: FOClient, performance_metrics
    ):
        """Test calling all version methods in parallel."""
        import asyncio
        import time

        start_time = time.time()

        # Call all methods in parallel
        versions = await asyncio.gather(
            mock_client.get_application_version(),
            mock_client.get_platform_build_version(),
            mock_client.get_application_build_version(),
        )

        duration = time.time() - start_time
        performance_metrics["timings"]["parallel_version_calls"] = duration

        # Verify all responses
        assert len(versions) == 3
        for version in versions:
            assert isinstance(version, str)
            assert len(version) > 0

        # Performance assertion - parallel should be faster than sequential
        assert duration < 5.0  # Should complete within 5 seconds


class TestCrudOperationsMockServer:
    """Test CRUD operations against mock server."""

    @pytest.mark.asyncio
    async def test_get_customers(self, mock_client: FOClient, entity_validator):
        """Test retrieving customers."""
        result = await mock_client.get_entities("Customers")

        assert entity_validator["odata_response"](result)
        assert "value" in result
        assert isinstance(result["value"], list)

        # Validate customer data
        for customer in result["value"]:
            assert entity_validator["customer"](customer)

    @pytest.mark.asyncio
    async def test_get_customers_with_query_options(self, mock_client: FOClient):
        """Test retrieving customers with OData query options."""
        options = QueryOptions(top=1, skip=0)
        result = await mock_client.get_entities("Customers", options)

        assert "value" in result
        assert len(result["value"]) == 1

    @pytest.mark.asyncio
    async def test_get_customer_by_key(self, mock_client: FOClient, entity_validator):
        """Test retrieving single customer by key."""
        customer = await mock_client.get_entity("Customers", "US-001")

        assert entity_validator["customer"](customer)
        assert customer["CustomerAccount"] == "US-001"
        assert customer["CustomerName"] == "Contoso Corporation"

    @pytest.mark.asyncio
    async def test_create_customer(self, mock_client: FOClient, entity_validator):
        """Test creating a new customer."""
        new_customer = {
            "CustomerAccount": "TEST-001",
            "CustomerName": "Test Customer Inc",
            "CustomerGroupId": "CORPORATE",
            "CurrencyCode": "USD",
            "PaymentTerms": "Net30",
        }

        result = await mock_client.create_entity("Customers", new_customer)

        assert entity_validator["customer"](result)
        assert result["CustomerAccount"] == "TEST-001"
        assert result["CustomerName"] == "Test Customer Inc"
        assert "CreatedDateTime" in result

    @pytest.mark.asyncio
    async def test_update_customer(self, mock_client: FOClient, entity_validator):
        """Test updating an existing customer."""
        update_data = {
            "CustomerName": "Updated Contoso Corporation",
            "PaymentTerms": "Net15",
        }

        result = await mock_client.update_entity("Customers", "US-001", update_data)

        assert entity_validator["customer"](result)
        assert result["CustomerName"] == "Updated Contoso Corporation"
        assert result["PaymentTerms"] == "Net15"
        assert result["CustomerAccount"] == "US-001"  # Key should remain unchanged

    @pytest.mark.asyncio
    async def test_delete_customer(self, mock_client: FOClient):
        """Test deleting a customer."""
        result = await mock_client.delete_entity("Customers", "US-002")
        assert result is True


class TestMetadataApiMockServer:
    """Test Metadata API operations against mock server."""

    @pytest.mark.asyncio
    async def test_get_data_entities(self, mock_client: FOClient):
        """Test retrieving data entities metadata."""
        result = await mock_client.get_data_entities()

        assert "value" in result
        assert isinstance(result["value"], list)
        assert len(result["value"]) > 0

        # Check entity structure
        entity = result["value"][0]
        assert "Name" in entity
        assert "EntitySetName" in entity
        assert "IsReadOnly" in entity

    @pytest.mark.asyncio
    async def test_get_data_entities_with_options(self, mock_client: FOClient):
        """Test retrieving data entities with query options."""
        options = QueryOptions(top=1)
        result = await mock_client.get_data_entities(options)

        assert "value" in result
        assert len(result["value"]) == 1

    @pytest.mark.asyncio
    async def test_search_data_entities(self, mock_client: FOClient):
        """Test searching data entities."""
        entities = await mock_client.search_data_entities(pattern="Customers")

        assert isinstance(entities, list)
        assert len(entities) > 0

        # Check entity structure
        entity = entities[0]
        assert hasattr(entity, "name")
        assert hasattr(entity, "public_collection_name")
        assert entity.name == "Customers"

    @pytest.mark.asyncio
    async def test_get_public_entities(self, mock_client: FOClient):
        """Test retrieving public entities metadata."""
        result = await mock_client.get_public_entities()

        assert "value" in result
        assert isinstance(result["value"], list)
        assert len(result["value"]) > 0

        # Check entity structure
        entity = result["value"][0]
        assert "Name" in entity
        assert "EntitySetName" in entity
        assert "Properties" in entity

    @pytest.mark.asyncio
    async def test_get_public_entity_info(self, mock_client: FOClient):
        """Test retrieving detailed public entity information."""
        entity_info = await mock_client.get_public_entity_info("Customers")

        assert entity_info is not None
        assert entity_info.name == "Customers"
        assert entity_info.entity_set_name == "Customers"
        assert len(entity_info.properties) > 0

        # Check property structure
        prop = entity_info.properties[0]
        assert hasattr(prop, "name")
        assert hasattr(prop, "type_name")
        assert hasattr(prop, "is_key")

    @pytest.mark.asyncio
    async def test_get_public_enumerations(self, mock_client: FOClient):
        """Test retrieving public enumerations."""
        result = await mock_client.get_public_enumerations()

        assert "value" in result
        assert isinstance(result["value"], list)
        assert len(result["value"]) > 0

        # Check enumeration structure
        enum = result["value"][0]
        assert "Name" in enum
        assert "LabelId" in enum


class TestLabelOperationsMockServer:
    """Test label operations against mock server."""

    @pytest.mark.asyncio
    async def test_get_label_text(self, mock_client: FOClient):
        """Test retrieving label text."""
        label_text = await mock_client.get_label_text("@SYS1234")

        assert label_text is not None
        assert isinstance(label_text, str)
        assert label_text == "Customers"

    @pytest.mark.asyncio
    async def test_get_labels_batch(self, mock_client: FOClient):
        """Test retrieving multiple labels in batch."""
        label_ids = ["@SYS1234", "@SYS5678", "@SYS9999"]  # Last one doesn't exist
        labels = await mock_client.get_labels_batch(label_ids)

        assert isinstance(labels, dict)
        assert "@SYS1234" in labels
        assert "@SYS5678" in labels
        assert labels["@SYS1234"] == "Customers"
        assert labels["@SYS5678"] == "Vendors"


class TestErrorHandlingMockServer:
    """Test error handling against mock server."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity(self, mock_client: FOClient):
        """Test error handling for non-existent entity."""
        with pytest.raises(Exception):  # Should raise an appropriate exception
            await mock_client.get_entities("NonExistentEntity")

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity_by_key(self, mock_client: FOClient):
        """Test error handling for non-existent entity key."""
        with pytest.raises(Exception):
            await mock_client.get_entity("Customers", "NON-EXISTENT")

    @pytest.mark.asyncio
    async def test_get_nonexistent_label(self, mock_client: FOClient):
        """Test error handling for non-existent label."""
        label_text = await mock_client.get_label_text("@NONEXISTENT")
        assert label_text is None  # Should return None for missing labels


class TestPerformanceMockServer:
    """Test performance characteristics against mock server."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self, mock_client: FOClient, performance_metrics
    ):
        """Test handling multiple concurrent requests."""
        import asyncio
        import time

        start_time = time.time()

        # Create multiple concurrent requests
        tasks = [
            mock_client.get_entities("Customers"),
            mock_client.get_entities("Vendors"),
            mock_client.get_application_version(),
            mock_client.get_platform_build_version(),
            mock_client.test_connection(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time
        performance_metrics["timings"]["concurrent_requests"] = duration

        # Verify all requests succeeded
        for result in results:
            assert not isinstance(result, Exception), f"Request failed: {result}"

        # Performance assertion
        assert duration < 3.0  # Should complete within 3 seconds

    @pytest.mark.asyncio
    async def test_large_dataset_handling(
        self, mock_client: FOClient, performance_metrics
    ):
        """Test handling of large dataset requests."""
        import time

        start_time = time.time()

        # Request a larger dataset (though still limited by mock server)
        options = QueryOptions(top=1000)  # Request more than available
        result = await mock_client.get_entities("Customers", options)

        duration = time.time() - start_time
        performance_metrics["timings"]["large_dataset"] = duration

        assert "value" in result
        assert isinstance(result["value"], list)
        # Should return all available data even if less than requested
        assert len(result["value"]) >= 0

        # Performance assertion
        assert duration < 2.0  # Should complete within 2 seconds
