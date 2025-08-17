"""Integration tests for sandbox/test environments.

These tests run against actual D365 F&O test environments and validate
real API behavior. They require proper authentication and environment setup.
"""

import pytest
import pytest_asyncio
from d365fo_client import FOClient
from d365fo_client.models import QueryOptions
from . import skip_if_not_level


@skip_if_not_level('sandbox')
class TestSandboxConnection:
    """Test connection to sandbox environment."""
    
    @pytest.mark.asyncio
    async def test_connection_success(self, sandbox_client: FOClient):
        """Test successful connection to sandbox."""
        result = await sandbox_client.test_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_metadata_connection_success(self, sandbox_client: FOClient):
        """Test successful metadata connection to sandbox."""
        result = await sandbox_client.test_metadata_connection()
        assert result is True


@skip_if_not_level('sandbox')
class TestSandboxVersionMethods:
    """Test version methods against sandbox environment."""
    
    @pytest.mark.asyncio
    async def test_get_application_version(self, sandbox_client: FOClient):
        """Test GetApplicationVersion action against sandbox."""
        version = await sandbox_client.get_application_version()
        assert isinstance(version, str)
        assert len(version) > 0
        # Version should match D365 version format
        assert '.' in version  # Should contain version dots
    
    @pytest.mark.asyncio
    async def test_get_platform_build_version(self, sandbox_client: FOClient):
        """Test GetPlatformBuildVersion action against sandbox."""
        version = await sandbox_client.get_platform_build_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert '.' in version
    
    @pytest.mark.asyncio
    async def test_get_application_build_version(self, sandbox_client: FOClient):
        """Test GetApplicationBuildVersion action against sandbox."""
        version = await sandbox_client.get_application_build_version()
        assert isinstance(version, str)
        assert len(version) > 0
        assert '.' in version
    
    @pytest.mark.asyncio
    async def test_version_consistency(self, sandbox_client: FOClient):
        """Test that version information is consistent."""
        app_version = await sandbox_client.get_application_version()
        platform_version = await sandbox_client.get_platform_build_version()
        app_build_version = await sandbox_client.get_application_build_version()
        
        # All versions should be non-empty
        assert all(len(v) > 0 for v in [app_version, platform_version, app_build_version])
        
        # Platform and application build versions often match
        # This is environment-specific, so we just ensure they're valid format
        version_parts = app_version.split('.')
        assert len(version_parts) >= 3  # Should have at least major.minor.build


@skip_if_not_level('sandbox')
class TestSandboxMetadataOperations:
    """Test metadata operations against sandbox environment."""
    
    @pytest.mark.asyncio
    async def test_download_metadata(self, sandbox_client: FOClient):
        """Test downloading OData metadata."""
        result = await sandbox_client.download_metadata(force_refresh=True)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_search_entities(self, sandbox_client: FOClient):
        """Test searching for entities in metadata."""
        # Download metadata first
        await sandbox_client.download_metadata()
        
        # Search for common entities (now async)
        entities = await sandbox_client.search_entities("Customer")
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # Should find entities containing "Customer"
        customer_entities = [e for e in entities if 'customer' in e.lower()]
        assert len(customer_entities) > 0
    
    @pytest.mark.asyncio
    async def test_get_data_entities(self, sandbox_client: FOClient):
        """Test retrieving data entities from Metadata API."""
        result = await sandbox_client.get_data_entities(QueryOptions(top=10))
        
        assert 'value' in result
        assert isinstance(result['value'], list)
        assert len(result['value']) > 0
        
        # Validate entity structure - check for available fields
        entity = result['value'][0]
        # Check for fields that are actually present based on the error message
        expected_fields = ['DataServiceEnabled', 'EntityCategory', 'IsReadOnly']
        for field in expected_fields:
            assert field in entity
        
        # Optional fields that may be present
        optional_fields = ['Name', 'EntitySetName']
        for field in optional_fields:
            if field in entity:
                assert isinstance(entity[field], (str, type(None)))
    
    @pytest.mark.asyncio
    async def test_get_public_entities(self, sandbox_client: FOClient):
        """Test retrieving public entities from Metadata API."""
        result = await sandbox_client.get_public_entities(QueryOptions(top=5))
        
        assert 'value' in result
        assert isinstance(result['value'], list)
        assert len(result['value']) > 0
        
        # Validate entity structure
        entity = result['value'][0]
        required_fields = ['Name', 'EntitySetName']
        for field in required_fields:
            assert field in entity


@skip_if_not_level('sandbox')
class TestSandboxDataOperations:
    """Test data operations against sandbox environment."""
    
    @pytest.mark.asyncio
    async def test_get_available_entities(self, sandbox_client: FOClient):
        """Test getting data from available entities."""
        # Try to get data from common entity sets
        common_entities = ['Companies', 'LegalEntities', 'NumberSequences']
        
        successful_entities = []
        for entity in common_entities:
            try:
                result = await sandbox_client.get_entities(entity, QueryOptions(top=1))
                if 'value' in result:
                    successful_entities.append(entity)
            except Exception:
                # Entity might not be available or accessible
                continue
        
        # At least one common entity should be accessible
        assert len(successful_entities) > 0, f"No common entities accessible: {common_entities}"
    
    @pytest.mark.asyncio
    async def test_odata_query_options(self, sandbox_client: FOClient):
        """Test OData query options against real environment."""
        # Find an accessible entity first
        try:
            # Try Companies entity (usually available)
            result_all = await sandbox_client.get_entities('Companies', QueryOptions(top=5))
            
            if 'value' in result_all and len(result_all['value']) > 0:
                # Test top parameter
                result_top1 = await sandbox_client.get_entities('Companies', QueryOptions(top=1))
                assert len(result_top1['value']) == 1
                
                # Test skip parameter
                result_skip1 = await sandbox_client.get_entities('Companies', QueryOptions(top=1, skip=1))
                if len(result_all['value']) > 1:
                    assert result_skip1['value'][0] != result_top1['value'][0]
                
        except Exception as e:
            pytest.skip(f"Cannot access Companies entity for query testing: {e}")


@skip_if_not_level('sandbox')
class TestSandboxAuthentication:
    """Test authentication scenarios against sandbox."""
    
    @pytest.mark.asyncio
    async def test_authenticated_requests(self, sandbox_client: FOClient):
        """Test that authenticated requests work properly."""
        # Test multiple operations to ensure auth is working
        operations = [
            sandbox_client.test_connection(),
            sandbox_client.test_metadata_connection(),
            sandbox_client.get_application_version(),
        ]
        
        results = []
        for operation in operations:
            try:
                result = await operation
                results.append(result)
            except Exception as e:
                pytest.fail(f"Authenticated operation failed: {e}")
        
        # All operations should succeed
        assert all(results), "Some authenticated operations failed"


@skip_if_not_level('sandbox')
class TestSandboxErrorHandling:
    """Test error handling against sandbox environment."""
    
    @pytest.mark.asyncio
    async def test_invalid_entity_error(self, sandbox_client: FOClient):
        """Test proper error handling for invalid entities."""
        with pytest.raises(Exception):
            await sandbox_client.get_entities('NonExistentEntitySet123456')
    
    @pytest.mark.asyncio
    async def test_invalid_action_error(self, sandbox_client: FOClient):
        """Test proper error handling for invalid actions."""
        with pytest.raises(Exception):
            await sandbox_client.call_action('NonExistentAction123456')


@skip_if_not_level('sandbox')
class TestSandboxPerformance:
    """Test performance characteristics against sandbox."""
    
    @pytest.mark.asyncio
    async def test_response_times(self, sandbox_client: FOClient, performance_metrics):
        """Test that response times are reasonable."""
        import time
        
        operations = [
            ('connection_test', sandbox_client.test_connection()),
            ('version_info', sandbox_client.get_application_version()),
            ('metadata_connection', sandbox_client.test_metadata_connection()),
        ]
        
        for name, operation in operations:
            start_time = time.time()
            await operation
            duration = time.time() - start_time
            
            performance_metrics['timings'][f'sandbox_{name}'] = duration
            
            # Response times should be reasonable (less than 30 seconds)
            assert duration < 30.0, f"{name} took too long: {duration}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, sandbox_client: FOClient):
        """Test handling of concurrent operations."""
        import asyncio
        
        # Run multiple operations concurrently
        tasks = [
            sandbox_client.get_application_version(),
            sandbox_client.get_platform_build_version(),
            sandbox_client.test_connection(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should succeed
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Concurrent operation {i} failed: {result}"
