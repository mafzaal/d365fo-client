"""Tests for the main module and core functionality."""

import warnings
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from d365fo_client import FOClient, FOClientConfig, create_client
from d365fo_client.models import LabelInfo, PublicEntityInfo, QueryOptions

# Filter out known coroutine warnings from background tasks and module imports
warnings.filterwarnings(
    "ignore", message="coroutine.*was never awaited", category=RuntimeWarning
)


def test_create_client():
    """Test the convenience function for creating a client."""
    client = create_client("https://test.dynamics.com")
    assert isinstance(client, FOClient)
    assert client.config.base_url == "https://test.dynamics.com"


def test_config_from_string():
    """Test creating FOClient with string URL."""
    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch.object(
            FOClient, "_trigger_background_sync_if_needed", new_callable=AsyncMock
        ),
    ):
        client = FOClient("https://test.dynamics.com")
        assert isinstance(client.config, FOClientConfig)
        assert client.config.base_url == "https://test.dynamics.com"


def test_config_from_dict():
    """Test creating FOClient with dictionary config."""
    config_dict = {
        "base_url": "https://test.dynamics.com",
        "timeout": 60,
        "verify_ssl": True,
    }
    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch("d365fo_client.session.SessionManager"),
        patch.object(
            FOClient, "_trigger_background_sync_if_needed", new_callable=AsyncMock
        ),
    ):
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
    config = FOClientConfig(base_url="https://test.dynamics.com", use_cache_first=False)
    assert config.use_cache_first is False


def test_query_options():
    """Test QueryOptions model."""
    options = QueryOptions(
        select=["CustomerAccount", "Name"],
        filter="Name eq 'Test'",
        top=10,
        orderby=["Name"],
    )

    assert options.select == ["CustomerAccount", "Name"]
    assert options.filter == "Name eq 'Test'"
    assert options.top == 10
    assert options.orderby == ["Name"]


def test_label_info():
    """Test LabelInfo model."""
    label = LabelInfo(id="@SYS13342", language="en-US", value="Customer")

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
        actions=[],
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
    url = QueryBuilder.build_action_url(
        "https://test.com", "calculateBalance", "Customers", "US-001"
    )
    assert (
        url
        == "https://test.com/data/Customers('US-001')/Microsoft.Dynamics.DataEntities.calculateBalance"
    )


# test_cache_functionality removed - functionality is now tested in test_metadata_cache.py


def test_query_string_builder():
    """Test OData query string building."""
    from d365fo_client.query import QueryBuilder

    # Test empty options
    query_string = QueryBuilder.build_query_string(None)
    assert query_string == ""

    # Test with options
    options = QueryOptions(
        select=["CustomerAccount", "Name"], filter="Name eq 'Test'", top=10
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
    with (
        patch("d365fo_client.main.asyncio.run") as mock_run,
        patch("sys.argv", ["d365fo-client"]),
    ):
        main()
        mock_run.assert_called_once()


def test_main_function_version():
    """Test that main function handles --version argument."""
    from d365fo_client.main import main

    # Test version argument - this should exit cleanly
    with (
        patch("sys.argv", ["d365fo-client", "--version"]),
        patch("d365fo_client.main.example_usage"),  # Mock to prevent coroutine creation
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0  # Should exit with success code


def test_main_function_help():
    """Test that main function handles --help argument."""
    from d365fo_client.main import main

    # Test help argument - this should exit cleanly
    with (
        patch("sys.argv", ["d365fo-client", "--help"]),
        patch("d365fo_client.main.example_usage"),  # Mock to prevent coroutine creation
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0  # Should exit with success code


def test_main_function_demo():
    """Test that main function handles --demo argument."""
    from d365fo_client.main import main

    # Mock the asyncio.run to avoid actual execution
    with (
        patch("d365fo_client.main.asyncio.run") as mock_run,
        patch("sys.argv", ["d365fo-client", "--demo"]),
    ):
        main()
        mock_run.assert_called_once()


# test_metadata_cache removed - functionality is now tested in test_metadata_cache.py


class TestEnhancedFOClient:
    """Test enhanced FOClient functionality."""

    @pytest.mark.asyncio
    async def test_async_search_entities_fallback(self):
        """Test that search_entities works with fallback when cache disabled."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=False,
            use_cache_first=False,
        )

        with (
            patch("d365fo_client.auth.DefaultAzureCredential"),
            patch("d365fo_client.session.SessionManager"),
            patch.object(FOClient, "_ensure_metadata_initialized"),
            patch.object(FOClient, "_get_from_cache_first") as mock_cache_first,
        ):

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
            use_cache_first=False,
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
            actions=[],
        )

        with (
            patch("d365fo_client.auth.DefaultAzureCredential"),
            patch("d365fo_client.session.SessionManager"),
            patch.object(FOClient, "_ensure_metadata_initialized"),
            patch.object(FOClient, "_get_from_cache_first") as mock_cache_first,
        ):

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
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Initially not initialized
                assert client._metadata_initialized is False

                # Mock successful initialization
                with patch.object(client, "_ensure_metadata_initialized") as mock_init:
                    await client._ensure_metadata_initialized()
                    mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhanced_metadata_info(self):
        """Test that get_metadata_info includes new cache information."""
        config = FOClientConfig(base_url="https://test.dynamics.com")

        with (
            patch("d365fo_client.auth.DefaultAzureCredential"),
            patch.object(
                FOClient, "_trigger_background_sync_if_needed", new_callable=AsyncMock
            ),
        ):
            client = FOClient(config)

            info = await client.get_metadata_info()
            assert "advanced_cache_enabled" in info
            # Should be False since metadata_cache is None initially
            assert info["advanced_cache_enabled"] is True

    @pytest.mark.asyncio
    async def test_background_sync_trigger(self):
        """Test background sync triggering logic."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                client._metadata_initialized = True

                # Mock metadata cache
                mock_metadata_cache = AsyncMock()
                mock_metadata_cache.check_version_and_sync.return_value = (True, 123)
                client.metadata_cache = mock_metadata_cache

                with patch.object(client, "_background_sync_worker") as mock_worker:
                    await client._trigger_background_sync_if_needed()

                    # Should check if sync is needed
                    mock_metadata_cache.check_version_and_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_download_metadata_method(self):
        """Test the new download_metadata method using sync manager."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Mock successful initialization
                client._metadata_initialized = True

                # Mock metadata cache
                mock_metadata_cache = AsyncMock()
                mock_metadata_cache.check_version_and_sync.return_value = (True, 123)
                client.metadata_cache = mock_metadata_cache

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
                # Check that sync_metadata was called with the correct parameters
                mock_sync_manager.sync_metadata.assert_called_once()
                call_args = mock_sync_manager.sync_metadata.call_args
                assert call_args[0][0] == 123  # global_version_id
                # Check that strategy is FULL when force_refresh=True
                from d365fo_client.sync_models import SyncStrategy

                assert call_args[0][1] == SyncStrategy.FULL
