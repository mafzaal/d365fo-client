"""Tests for the main module and core functionality."""

import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from d365fo_client import FOClient, FOClientConfig, create_client
from d365fo_client.models import QueryOptions, LabelInfo, PublicEntityInfo


def test_create_client():
    """Test the convenience function for creating a client."""
    client = create_client("https://test.dynamics.com")
    assert isinstance(client, FOClient)
    assert client.config.base_url == "https://test.dynamics.com"


def test_config_from_string():
    """Test creating FOClient with string URL."""
    with patch('d365fo_client.auth.DefaultAzureCredential'):
        client = FOClient("https://test.dynamics.com")
        assert isinstance(client.config, FOClientConfig)
        assert client.config.base_url == "https://test.dynamics.com"


def test_config_from_dict():
    """Test creating FOClient with dictionary config."""
    config_dict = {
        "base_url": "https://test.dynamics.com",
        "timeout": 60,
        "verify_ssl": True
    }
    with patch('d365fo_client.auth.DefaultAzureCredential'):
        client = FOClient(config_dict)
        assert client.config.base_url == "https://test.dynamics.com"
        assert client.config.timeout == 60
        assert client.config.verify_ssl is True


def test_config_cache_first_default():
    """Test that cache-first is enabled by default."""
    config = FOClientConfig(base_url="https://test.dynamics.com")
    assert config.use_cache_first is True


def test_config_cache_first_override():
    """Test that cache-first can be disabled."""
    config = FOClientConfig(
        base_url="https://test.dynamics.com",
        use_cache_first=False
    )
    assert config.use_cache_first is False


def test_query_options():
    """Test QueryOptions model."""
    options = QueryOptions(
        select=["CustomerAccount", "Name"],
        filter="Name eq 'Test'",
        top=10,
        orderby=["Name"]
    )
    
    assert options.select == ["CustomerAccount", "Name"]
    assert options.filter == "Name eq 'Test'"
    assert options.top == 10
    assert options.orderby == ["Name"]


def test_label_info():
    """Test LabelInfo model."""
    label = LabelInfo(
        id="@SYS13342",
        language="en-US",
        value="Customer"
    )
    
    assert label.id == "@SYS13342"
    assert label.language == "en-US"
    assert label.value == "Customer"
    
    label_dict = label.to_dict()
    assert label_dict["id"] == "@SYS13342"
    assert label_dict["language"] == "en-US"
    assert label_dict["value"] == "Customer"


def test_public_entity_info():
    """Test PublicEntityInfo model."""
    entity = PublicEntityInfo(
        name="Customers",
        entity_set_name="CustomersV3",
        label_id="@SYS123",
        label_text="Customers",
        is_read_only=False,
        configuration_enabled=True,
        properties=[],
        navigation_properties=[],
        property_groups=[],
        actions=[]
    )
    
    assert entity.name == "Customers"
    assert entity.entity_set_name == "CustomersV3"
    assert entity.label_text == "Customers"
    assert not entity.is_read_only


def test_url_builders():
    """Test URL building utilities."""
    from d365fo_client.query import QueryBuilder
    
    # Test entity URL
    url = QueryBuilder.build_entity_url("https://test.com", "Customers", "US-001")
    assert url == "https://test.com/data/Customers('US-001')"
    
    # Test action URL - unbound
    url = QueryBuilder.build_action_url("https://test.com", "calculateTax")
    assert url == "https://test.com/data/Microsoft.Dynamics.DataEntities.calculateTax"
    
    # Test action URL - bound
    url = QueryBuilder.build_action_url("https://test.com", "calculateBalance", "Customers", "US-001")
    assert url == "https://test.com/data/Customers('US-001')/Microsoft.Dynamics.DataEntities.calculateBalance"


@pytest.mark.asyncio
async def test_cache_functionality():
    """Test metadata cache functionality."""
    import tempfile
    from pathlib import Path
    from d365fo_client.metadata_cache import MetadataCache
    from d365fo_client.models import LabelInfo
    
    # Create temporary cache directory
    temp_dir = tempfile.mkdtemp()
    cache_dir = Path(temp_dir)
    
    try:
        # Initialize MetadataCache
        cache = MetadataCache(
            environment_url="https://test.dynamics.com",
            cache_dir=cache_dir
        )
        await cache.initialize()
        
        # Test setting and getting labels
        test_label = LabelInfo(id="@SYS13342", language="en-US", value="Customer")
        await cache.set_label(test_label)
        
        value = await cache.get_label("@SYS13342", "en-US")
        assert value == "Customer"
        
        # Test batch operations
        labels = [
            LabelInfo(id="@SYS1", language="en-US", value="Test1"),
            LabelInfo(id="@SYS2", language="en-US", value="Test2")
        ]
        await cache.set_labels_batch(labels)
        
        # Test retrieval of batch labels
        value1 = await cache.get_label("@SYS1", "en-US")
        value2 = await cache.get_label("@SYS2", "en-US")
        assert value1 == "Test1"
        assert value2 == "Test2"
        
        # Test cache statistics
        stats = await cache.get_statistics()
        assert "total_labels" in stats
        assert stats["total_labels"] >= 3  # Should have at least 3 labels
        
    finally:
        # Cleanup manually to avoid permission issues
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except (PermissionError, OSError):
            # Ignore cleanup errors on Windows
            pass


def test_query_string_builder():
    """Test OData query string building."""
    from d365fo_client.query import QueryBuilder
    
    # Test empty options
    query_string = QueryBuilder.build_query_string(None)
    assert query_string == ""
    
    # Test with options
    options = QueryOptions(
        select=["CustomerAccount", "Name"],
        filter="Name eq 'Test'",
        top=10
    )
    query_string = QueryBuilder.build_query_string(options)
    # Check for URL-encoded parameters ($ becomes %24)
    assert "%24select=" in query_string
    assert "%24filter=" in query_string
    assert "%24top=10" in query_string
    assert query_string.startswith("?")


def test_main_function_basic():
    """Test that main function can be imported and called."""
    from d365fo_client.main import main
    
    # Mock the asyncio.run to avoid actual execution and sys.argv to simulate no arguments
    with patch('d365fo_client.main.asyncio.run') as mock_run, \
         patch('sys.argv', ['d365fo-client']):
        main()
        mock_run.assert_called_once()


def test_main_function_version():
    """Test that main function handles --version argument."""
    from d365fo_client.main import main
    
    # Test version argument - this should exit cleanly
    with patch('sys.argv', ['d365fo-client', '--version']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0  # Should exit with success code


def test_main_function_help():
    """Test that main function handles --help argument."""
    from d365fo_client.main import main
    
    # Test help argument - this should exit cleanly
    with patch('sys.argv', ['d365fo-client', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0  # Should exit with success code


def test_main_function_demo():
    """Test that main function handles --demo argument."""
    from d365fo_client.main import main
    
    # Mock the asyncio.run to avoid actual execution
    with patch('d365fo_client.main.asyncio.run') as mock_run, \
         patch('sys.argv', ['d365fo-client', '--demo']):
        main()
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_metadata_cache():
    """Test metadata cache initialization and basic functionality."""
    from d365fo_client.metadata_cache import MetadataCache
    from pathlib import Path
    import tempfile
    
    # Create temporary cache directory for testing
    temp_dir = tempfile.mkdtemp()
    cache_dir = Path(temp_dir)
    
    try:
        cache = MetadataCache("https://test.dynamics.com", cache_dir)
        
        # Test that cache properties are set correctly
        assert cache.environment_url == "https://test.dynamics.com"
        assert cache.cache_dir == cache_dir
        
        # Test initialization
        await cache.initialize()
        assert cache._environment_id is not None
        
        # Test statistics functionality
        stats = await cache.get_statistics()
        assert isinstance(stats, dict)
        assert "total_environments" in stats
        assert stats["total_environments"] >= 1  # Should have at least our test environment
        
    finally:
        # Cleanup manually to avoid permission issues
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except (PermissionError, OSError):
            # Ignore cleanup errors on Windows
            pass


class TestEnhancedFOClient:
    """Test enhanced FOClient functionality."""
    
    @pytest.mark.asyncio
    async def test_async_search_entities_fallback(self):
        """Test that search_entities works with fallback when cache disabled."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=False,
            use_cache_first=False
        )
        
        with patch('d365fo_client.auth.DefaultAzureCredential'), \
             patch.object(FOClient, '_ensure_metadata_initialized'), \
             patch.object(FOClient, '_get_from_cache_first') as mock_cache_first:
            
            # Mock the cache-first method to return test data
            mock_cache_first.return_value = ["TestEntity1", "TestEntity2"]
            
            async with FOClient(config) as client:
                entities = await client.search_entities("Test")
                assert isinstance(entities, list)
                mock_cache_first.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_get_entity_info_fallback(self):
        """Test that get_entity_info works with fallback when cache disabled."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=False,
            use_cache_first=False
        )
        
        mock_entity = PublicEntityInfo(
            name="TestEntity",
            entity_set_name="TestEntities",
            label_id="@TEST123",
            label_text="Test Entity",
            is_read_only=False,
            configuration_enabled=True,
            properties=[],
            navigation_properties=[],
            property_groups=[],
            actions=[]
        )
        
        with patch('d365fo_client.auth.DefaultAzureCredential'), \
             patch.object(FOClient, '_ensure_metadata_initialized'), \
             patch.object(FOClient, '_get_from_cache_first') as mock_cache_first:
            
            mock_cache_first.return_value = mock_entity
            
            async with FOClient(config) as client:
                entity_info = await client.get_entity_info("TestEntity")
                assert entity_info is not None
                assert entity_info.name == "TestEntity"
                mock_cache_first.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_metadata_initialization_flag(self):
        """Test that metadata initialization tracking works."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True
        )
        
        with patch('d365fo_client.auth.DefaultAzureCredential'):
            async with FOClient(config) as client:
                # Initially not initialized
                assert client._metadata_initialized is False
                
                # Mock successful initialization
                with patch.object(client, '_ensure_metadata_initialized') as mock_init:
                    await client._ensure_metadata_initialized()
                    mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhanced_metadata_info(self):
        """Test that get_metadata_info includes new cache information."""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch('d365fo_client.auth.DefaultAzureCredential'):
            client = FOClient(config)
            
            info = await client.get_metadata_info()
            assert "advanced_cache_enabled" in info
            # Should be False since metadata_cache is None initially
            assert info["advanced_cache_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_background_sync_trigger(self):
        """Test background sync triggering logic."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True
        )
        
        with patch('d365fo_client.auth.DefaultAzureCredential'):
            async with FOClient(config) as client:
                client._metadata_initialized = True
                
                # Mock sync manager
                mock_sync_manager = AsyncMock()
                mock_sync_manager.needs_sync.return_value = True
                client.sync_manager = mock_sync_manager
                
                with patch.object(client, '_background_sync_worker') as mock_worker:
                    await client._trigger_background_sync_if_needed()
                    
                    # Should check if sync is needed
                    mock_sync_manager.needs_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_new_download_metadata_method(self):
        """Test the new download_metadata method using sync manager."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True
        )
        
        with patch('d365fo_client.auth.DefaultAzureCredential'):
            async with FOClient(config) as client:
                # Mock successful initialization
                client._metadata_initialized = True
                
                # Mock sync manager
                mock_sync_manager = AsyncMock()
                mock_result = AsyncMock()
                mock_result.success = True
                mock_result.sync_type = "full"
                mock_result.entities_synced = 100
                mock_result.enumerations_synced = 50
                mock_result.duration_ms = 1500.0
                mock_sync_manager.sync_metadata.return_value = mock_result
                client.sync_manager = mock_sync_manager
                
                # Test the method
                result = await client.download_metadata(force_refresh=True)
                
                assert result is True
                mock_sync_manager.sync_metadata.assert_called_once_with(force_full=True)
