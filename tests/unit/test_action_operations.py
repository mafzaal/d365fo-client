"""Unit tests for action search and lookup functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from d365fo_client.client import FOClient
from d365fo_client.config import FOClientConfig
from d365fo_client.models import (
    ActionInfo,
    ActionParameterInfo,
    ActionParameterTypeInfo,
    ActionReturnTypeInfo,
    ODataBindingKind,
    PublicEntityActionInfo,
    PublicEntityInfo,
)


class TestActionSearchAndLookup:
    """Test action search and lookup functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        return FOClientConfig(
            base_url="https://test.dynamics.com",
            enable_metadata_cache=False,
            use_cache_first=False,
        )

    @pytest.fixture
    def mock_client(self, mock_config):
        """Create a mock client"""
        client = FOClient(mock_config)
        client.metadata_api_ops = AsyncMock()
        client.label_ops = AsyncMock()
        return client

    @pytest.fixture
    def sample_action_info(self):
        """Create a sample ActionInfo object"""
        return ActionInfo(
            name="TestAction",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_SET,
            entity_name="TestEntity",
            entity_set_name="TestEntities",
            parameters=[
                ActionParameterInfo(
                    name="param1",
                    type=ActionParameterTypeInfo(
                        type_name="Edm.String",
                        is_collection=False,
                    ),
                )
            ],
            return_type=ActionReturnTypeInfo(
                type_name="Edm.String",
                is_collection=False,
            ),
        )

    @pytest.fixture
    def sample_public_entity_info(self):
        """Create a sample PublicEntityInfo with actions"""
        action = PublicEntityActionInfo(
            name="TestAction",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_SET,
            parameters=[
                ActionParameterInfo(
                    name="param1",
                    type=ActionParameterTypeInfo(
                        type_name="Edm.String",
                        is_collection=False,
                    ),
                )
            ],
            return_type=ActionReturnTypeInfo(
                type_name="Edm.String",
                is_collection=False,
            ),
        )

        return PublicEntityInfo(
            name="TestEntity",
            entity_set_name="TestEntities",
            label_id="@TestLabel",
            label_text="Test Entity",
            is_read_only=False,
            configuration_enabled=True,
            properties=[],
            navigation_properties=[],
            property_groups=[],
            actions=[action],
        )

    @pytest.mark.asyncio
    async def test_search_actions_success(self, mock_client, sample_action_info):
        """Test successful action search"""
        # Mock the metadata API operations
        mock_client.metadata_api_ops.search_actions.return_value = [sample_action_info]

        # Mock label resolution
        async def mock_resolve_labels(obj, label_ops):
            return obj

        with patch(
            "d365fo_client.client.resolve_labels_generic", side_effect=mock_resolve_labels
        ):
            result = await mock_client.search_actions(pattern="Test")

        # Verify results
        assert len(result) == 1
        assert result[0].name == "TestAction"
        assert result[0].binding_kind == ODataBindingKind.BOUND_TO_ENTITY_SET
        assert result[0].entity_name == "TestEntity"

        # Verify metadata API was called correctly
        mock_client.metadata_api_ops.search_actions.assert_called_once_with(
            "Test", None, None
        )

    @pytest.mark.asyncio
    async def test_search_actions_with_entity_filter(
        self, mock_client, sample_action_info
    ):
        """Test action search with entity filter"""
        mock_client.metadata_api_ops.search_actions.return_value = [sample_action_info]

        with patch("d365fo_client.client.resolve_labels_generic", return_value=[]):
            result = await mock_client.search_actions(
                pattern="Test", entity_name="TestEntity"
            )

        mock_client.metadata_api_ops.search_actions.assert_called_once_with(
            "Test", "TestEntity", None
        )

    @pytest.mark.asyncio
    async def test_search_actions_with_binding_kind_filter(
        self, mock_client, sample_action_info
    ):
        """Test action search with binding kind filter"""
        mock_client.metadata_api_ops.search_actions.return_value = [sample_action_info]

        with patch("d365fo_client.client.resolve_labels_generic", return_value=[]):
            result = await mock_client.search_actions(
                pattern="Test", binding_kind="BoundToEntitySet"
            )

        mock_client.metadata_api_ops.search_actions.assert_called_once_with(
            "Test", None, "BoundToEntitySet"
        )

    @pytest.mark.asyncio
    async def test_search_actions_empty_result(self, mock_client):
        """Test action search with no results"""
        mock_client.metadata_api_ops.search_actions.return_value = []

        with patch("d365fo_client.client.resolve_labels_generic", return_value=[]):
            result = await mock_client.search_actions(pattern="NonExistent")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_action_info_success(self, mock_client, sample_action_info):
        """Test successful action info retrieval"""
        mock_client.metadata_api_ops.get_action_info.return_value = sample_action_info

        # Mock label resolution
        async def mock_resolve_labels(obj, label_ops):
            return obj

        with patch(
            "d365fo_client.client.resolve_labels_generic", side_effect=mock_resolve_labels
        ):
            result = await mock_client.get_action_info("TestAction")

        # Verify result
        assert result.name == "TestAction"
        assert result.binding_kind == ODataBindingKind.BOUND_TO_ENTITY_SET
        assert result.entity_name == "TestEntity"

        # Verify metadata API was called correctly
        mock_client.metadata_api_ops.get_action_info.assert_called_once_with(
            "TestAction", None
        )

    @pytest.mark.asyncio
    async def test_get_action_info_with_entity(self, mock_client, sample_action_info):
        """Test action info retrieval with entity name"""
        mock_client.metadata_api_ops.get_action_info.return_value = sample_action_info

        with patch("d365fo_client.client.resolve_labels_generic", return_value=None):
            result = await mock_client.get_action_info("TestAction", "TestEntity")

        mock_client.metadata_api_ops.get_action_info.assert_called_once_with(
            "TestAction", "TestEntity"
        )

    @pytest.mark.asyncio
    async def test_get_action_info_not_found(self, mock_client):
        """Test action info retrieval when action not found"""
        mock_client.metadata_api_ops.get_action_info.return_value = None

        result = await mock_client.get_action_info("NonExistentAction")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_actions_cache_first_disabled(self, mock_client):
        """Test that cache-first is properly disabled for action search"""
        mock_client.config.use_cache_first = False
        mock_client.metadata_api_ops.search_actions.return_value = []

        with patch("d365fo_client.client.resolve_labels_generic", return_value=[]):
            await mock_client.search_actions()

        # Should call metadata API directly when cache-first is disabled
        mock_client.metadata_api_ops.search_actions.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_action_info_cache_first_disabled(self, mock_client):
        """Test that cache-first is properly disabled for action lookup"""
        mock_client.config.use_cache_first = False
        mock_client.metadata_api_ops.get_action_info.return_value = None

        await mock_client.get_action_info("TestAction")

        # Should call metadata API directly when cache-first is disabled
        mock_client.metadata_api_ops.get_action_info.assert_called_once()