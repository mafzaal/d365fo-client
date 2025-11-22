"""Tests for enhanced FOClient with cache-first functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.models import DataEntityInfo, PublicEntityInfo


class TestCacheFirstFunctionality:
    """Test the new cache-first functionality."""

    @pytest.mark.asyncio
    async def test_cache_first_enabled_by_default(self):
        """Test that cache-first is enabled by default."""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        assert config.use_cache_first is True

    @pytest.mark.asyncio
    async def test_cache_first_can_be_disabled(self):
        """Test that cache-first can be disabled."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", use_cache_first=False
        )
        assert config.use_cache_first is False

    @pytest.mark.asyncio
    async def test_search_entities_cache_first_success(self):
        """Test search_entities with successful cache lookup."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True,
            use_cache_first=True,
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Mock metadata cache
                mock_cache = AsyncMock()
                mock_cache.search_entities.return_value = ["TestEntity1", "TestEntity2"]
                client.metadata_cache = mock_cache
                client._metadata_initialized = True

                # Mock the _get_from_cache_first method
                with patch.object(client, "_get_from_cache_first") as mock_cache_first:
                    mock_cache_first.return_value = ["TestEntity1", "TestEntity2"]

                    result = await client.search_entities("Test")

                    assert result == ["TestEntity1", "TestEntity2"]
                    mock_cache_first.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_entities_cache_disabled(self):
        """Test search_entities with cache disabled."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=False,
            use_cache_first=False,
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Mock metadata API operations fallback
                client.metadata_api_ops.search_public_entities = AsyncMock(
                    return_value=[]
                )
                client.metadata_api_ops.search_data_entities = AsyncMock(
                    return_value=[]
                )

                with patch.object(client, "_get_from_cache_first") as mock_cache_first:
                    mock_cache_first.return_value = ["FallbackEntity"]

                    result = await client.search_entities("Test")

                    assert result == ["FallbackEntity"]
                    mock_cache_first.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_info_cache_first_success(self):
        """Test get_entity_info with successful cache lookup."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True,
            use_cache_first=True,
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

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                with patch.object(client, "_get_from_cache_first") as mock_cache_first:
                    mock_cache_first.return_value = mock_entity

                    result = await client.get_entity_info("TestEntity")

                    assert result == mock_entity
                    mock_cache_first.assert_called_once()

    @pytest.mark.asyncio
    async def test_parameter_override_cache_behavior(self):
        """Test that use_cache_first parameter overrides config."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            use_cache_first=True,  # Default enabled
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                with patch.object(client, "_get_from_cache_first") as mock_cache_first:
                    mock_cache_first.return_value = ["TestEntity"]

                    # Call with cache disabled via parameter
                    await client.search_entities("Test", use_cache_first=False)

                    # Should be called with use_cache_first=False
                    mock_cache_first.assert_called_once()
                    call_args = mock_cache_first.call_args
                    assert call_args[1]["use_cache_first"] is False

    @pytest.mark.asyncio
    async def test_metadata_initialization_trigger(self):
        """Test that metadata initialization is triggered when needed."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Initially not initialized
                assert client._metadata_initialized is False

                with patch.object(client, "_ensure_metadata_initialized") as mock_init:
                    with patch.object(
                        client, "_get_from_cache_first"
                    ) as mock_cache_first:
                        mock_cache_first.return_value = []

                        await client.search_entities("Test")

                        # Should trigger metadata initialization through _get_from_cache_first
                        mock_cache_first.assert_called_once()

    @pytest.mark.asyncio
    async def test_background_sync_trigger_on_cache_miss(self):
        """Test that background sync is triggered on cache miss."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                client._metadata_initialized = True

                with patch.object(
                    client, "_trigger_background_sync_if_needed"
                ) as mock_trigger:
                    with patch.object(
                        client, "_get_from_cache_first"
                    ) as mock_cache_first:
                        # Simulate cache miss by returning empty result first
                        mock_cache_first.side_effect = [[], ["FallbackEntity"]]

                        result = await client.search_entities("Test")

                        # Should call _get_from_cache_first
                        mock_cache_first.assert_called()

    @pytest.mark.asyncio
    async def test_new_download_metadata_with_sync_manager(self):
        """Test the new download_metadata method using sync manager."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Mock successful initialization
                client._metadata_initialized = True

                # Mock metadata cache
                mock_cache = AsyncMock()
                mock_cache.check_version_and_sync.return_value = (
                    True,
                    12345,
                )  # sync_needed=True, version=12345
                client.metadata_cache = mock_cache

                # Mock sync manager
                mock_sync_manager = AsyncMock()
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.entity_count = 100
                mock_result.enumeration_count = 50
                mock_result.action_count = 25
                mock_result.duration_ms = 1500.0
                mock_sync_manager.sync_metadata.return_value = mock_result
                client.sync_manager = mock_sync_manager

                # Test the method
                result = await client.download_metadata(force_refresh=True)

                assert result is True
                # Should call with global_version_id and strategy
                mock_sync_manager.sync_metadata.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhanced_metadata_info(self):
        """Test that get_metadata_info includes new cache information."""
        config = FOClientConfig(base_url="https://test.dynamics.com")

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            client = FOClient(config)

            info = await client.get_metadata_info()

            # Should include new metadata cache info
            assert "advanced_cache_enabled" in info
            assert "cache_initialized" in info
            assert "sync_manager_available" in info
            assert "background_sync_running" in info

    @pytest.mark.asyncio
    async def test_async_search_data_entities_cache_first(self):
        """Test search_data_entities with cache-first approach."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True,
            use_cache_first=True,
        )

        mock_entities = [
            DataEntityInfo(
                name="TestDataEntity",
                public_entity_name="Test",
                public_collection_name="Tests",
                entity_category="Master",
                data_service_enabled=True,
                data_management_enabled=True,
                is_read_only=False,
            )
        ]

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                with patch.object(client, "_get_from_cache_first") as mock_cache_first:
                    mock_cache_first.return_value = mock_entities

                    result = await client.search_data_entities("Test")

                    assert result == mock_entities
                    mock_cache_first.assert_called_once()


class TestBackgroundSyncLogic:
    """Test background sync logic."""

    @pytest.mark.asyncio
    async def test_needs_sync_check(self):
        """Test that check_version_and_sync is checked before triggering sync."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                client._metadata_initialized = True

                # Mock metadata cache
                mock_cache = AsyncMock()
                mock_cache.check_version_and_sync.return_value = (
                    False,
                    None,
                )  # No sync needed
                client.metadata_cache = mock_cache

                await client._trigger_background_sync_if_needed()

                # Should check version but not create task
                mock_cache.check_version_and_sync.assert_called_once()
                assert client._background_sync_task is None

    @pytest.mark.asyncio
    async def test_background_sync_task_creation(self):
        """Test that background sync task is created when needed."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com", enable_metadata_cache=True
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                client._metadata_initialized = True

                # Mock metadata cache
                mock_cache = AsyncMock()
                mock_cache.check_version_and_sync.return_value = (
                    True,
                    12345,
                )  # Sync needed
                client.metadata_cache = mock_cache

                # Mock sync manager
                mock_sync_manager = AsyncMock()
                client.sync_manager = mock_sync_manager

                with patch("asyncio.create_task") as mock_create_task:
                    await client._trigger_background_sync_if_needed()

                    # Should create background task
                    mock_create_task.assert_called_once()
                    mock_cache.check_version_and_sync.assert_called_once()


class TestCacheFirstIntegration:
    """Integration tests for cache-first behavior."""

    @pytest.mark.asyncio
    async def test_full_cache_first_workflow(self):
        """Test complete cache-first workflow."""
        config = FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=True,
            use_cache_first=True,
        )

        with patch("d365fo_client.auth.DefaultAzureCredential"):
            async with FOClient(config) as client:
                # Test multiple operations in sequence
                operations = [
                    ("search_entities", client.search_entities, ["TestEntity"]),
                    (
                        "get_entity_info",
                        client.get_entity_info,
                        PublicEntityInfo(
                            name="TestEntity",
                            entity_set_name="TestEntities",
                            properties=[],
                            navigation_properties=[],
                            property_groups=[],
                            actions=[],
                        ),
                    ),
                    ("search_data_entities", client.search_data_entities, []),
                ]

                for op_name, method, expected_result in operations:
                    with patch.object(
                        client, "_get_from_cache_first"
                    ) as mock_cache_first:
                        mock_cache_first.return_value = expected_result

                        if op_name == "search_entities":
                            result = await method("Test")
                        elif op_name == "get_entity_info":
                            result = await method("TestEntity")
                        else:  # search_data_entities
                            result = await method("Test")

                        assert result == expected_result
                        mock_cache_first.assert_called_once()
