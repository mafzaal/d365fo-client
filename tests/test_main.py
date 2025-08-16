"""Tests for the main module and core functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from d365fo_client import FOClient, FOClientConfig, create_client
from d365fo_client.models import QueryOptions, LabelInfo, EntityInfo


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


def test_entity_info():
    """Test EntityInfo model."""
    entity = EntityInfo(
        name="Customers",
        keys=["CustomerAccount"],
        properties=[{"name": "CustomerAccount", "type": "Edm.String"}],
        actions=[]
    )
    
    assert entity.name == "Customers"
    assert entity.keys == ["CustomerAccount"]
    assert len(entity.properties) == 1
    assert entity.enhanced_properties == []  # Should be initialized by __post_init__


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


def test_cache_functionality():
    """Test label cache functionality."""
    from d365fo_client.cache import LabelCache
    
    cache = LabelCache(expiry_minutes=60)
    
    # Test setting and getting
    cache.set("@SYS13342", "en-US", "Customer")
    value = cache.get("@SYS13342", "en-US")
    assert value == "Customer"
    
    # Test cache info
    info = cache.get_info()
    assert info["size"] == 1
    assert info["expiry_minutes"] == 60
    
    # Test batch operations
    labels = [
        LabelInfo("@SYS1", "en-US", "Test1"),
        LabelInfo("@SYS2", "en-US", "Test2")
    ]
    cache.set_batch(labels)
    assert cache.size() == 3


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
    
    # Mock the asyncio.run to avoid actual execution
    with patch('d365fo_client.main.asyncio.run') as mock_run:
        main()
        mock_run.assert_called_once()


def test_metadata_manager():
    """Test metadata manager functionality."""
    import tempfile
    import os
    from d365fo_client.metadata import MetadataManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MetadataManager(temp_dir)
        
        # Test cache info
        info = manager.get_cache_info()
        assert "metadata_file_exists" in info
        assert "cache_directory" in info
        assert info["cache_directory"] == temp_dir
        
        # Test that directory was created
        assert os.path.exists(temp_dir)
