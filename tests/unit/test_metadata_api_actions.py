"""Unit tests for action-related metadata API operations."""

import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch

from d365fo_client.metadata_api import MetadataAPIOperations
from d365fo_client.models import (
    ActionInfo,
    ActionParameterInfo,
    ActionParameterTypeInfo,
    ActionReturnTypeInfo,
    ODataBindingKind,
    PublicEntityActionInfo,
    PublicEntityInfo,
)


class TestMetadataAPIActionOperations:
    """Test action-related metadata API operations"""

    @pytest.fixture
    def mock_session_manager(self):
        """Create a mock session manager"""
        return AsyncMock()

    @pytest.fixture
    def mock_label_ops(self):
        """Create a mock label operations"""
        return AsyncMock()

    @pytest.fixture
    def metadata_api_ops(self, mock_session_manager, mock_label_ops):
        """Create metadata API operations instance"""
        return MetadataAPIOperations(
            mock_session_manager, "https://test.dynamics.com/Metadata", mock_label_ops
        )

    @pytest.fixture
    def sample_public_entity_with_actions(self):
        """Create a sample PublicEntityInfo with actions"""
        action1 = PublicEntityActionInfo(
            name="GetCustomerDetails",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_SET,
            parameters=[
                ActionParameterInfo(
                    name="customerId",
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

        action2 = PublicEntityActionInfo(
            name="UpdateCustomerStatus",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_INSTANCE,
            parameters=[
                ActionParameterInfo(
                    name="status",
                    type=ActionParameterTypeInfo(
                        type_name="Edm.String",
                        is_collection=False,
                    ),
                )
            ],
            return_type=ActionReturnTypeInfo(
                type_name="Edm.Boolean",
                is_collection=False,
            ),
        )

        return PublicEntityInfo(
            name="Customer",
            entity_set_name="Customers",
            label_id="@CustomerLabel",
            label_text="Customer",
            is_read_only=False,
            configuration_enabled=True,
            properties=[],
            navigation_properties=[],
            property_groups=[],
            actions=[action1, action2],
        )

    @pytest.fixture
    def sample_entity_without_actions(self):
        """Create a sample PublicEntityInfo without actions"""
        return PublicEntityInfo(
            name="Product",
            entity_set_name="Products",
            label_id="@ProductLabel",
            label_text="Product",
            is_read_only=False,
            configuration_enabled=True,
            properties=[],
            navigation_properties=[],
            property_groups=[],
            actions=[],
        )

    @pytest.mark.asyncio
    async def test_search_actions_all_entities(
        self,
        metadata_api_ops,
        sample_public_entity_with_actions,
        sample_entity_without_actions,
    ):
        """Test searching actions across all entities"""
        # Mock get_all_public_entities_with_details
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            return_value=[sample_public_entity_with_actions, sample_entity_without_actions]
        )

        result = await metadata_api_ops.search_actions()

        # Should return all actions from all entities
        assert len(result) == 2
        assert result[0].name == "GetCustomerDetails"
        assert result[0].entity_name == "Customer"
        assert result[0].entity_set_name == "Customers"
        assert result[1].name == "UpdateCustomerStatus"
        assert result[1].entity_name == "Customer"

    @pytest.mark.asyncio
    async def test_search_actions_with_pattern(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test searching actions with pattern filter"""
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            return_value=[sample_public_entity_with_actions]
        )

        # Search for actions containing "Get"
        result = await metadata_api_ops.search_actions(pattern=".*Get.*")

        # Should only return actions matching the pattern
        assert len(result) == 1
        assert result[0].name == "GetCustomerDetails"

    @pytest.mark.asyncio
    async def test_search_actions_with_entity_filter(
        self,
        metadata_api_ops,
        sample_public_entity_with_actions,
        sample_entity_without_actions,
    ):
        """Test searching actions with entity filter"""
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            return_value=[sample_public_entity_with_actions, sample_entity_without_actions]
        )

        # Search for actions in Customer entity only
        result = await metadata_api_ops.search_actions(entity_name="Customer")

        # Should only return actions from Customer entity
        assert len(result) == 2
        assert all(action.entity_name == "Customer" for action in result)

    @pytest.mark.asyncio
    async def test_search_actions_with_binding_kind_filter(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test searching actions with binding kind filter"""
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            return_value=[sample_public_entity_with_actions]
        )

        # Search for actions bound to entity set
        result = await metadata_api_ops.search_actions(
            binding_kind="BoundToEntitySet"
        )

        # Should only return actions with matching binding kind
        assert len(result) == 1
        assert result[0].name == "GetCustomerDetails"
        assert result[0].binding_kind == ODataBindingKind.BOUND_TO_ENTITY_SET

    @pytest.mark.asyncio
    async def test_search_actions_invalid_regex(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test searching actions with invalid regex pattern"""
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            return_value=[sample_public_entity_with_actions]
        )

        # Use invalid regex pattern - should fall back to string search
        result = await metadata_api_ops.search_actions(pattern="[invalid")

        # Should handle invalid regex gracefully and return empty results
        # since the literal string "[invalid" won't match any action names
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_actions_case_insensitive(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test searching actions is case insensitive"""
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            return_value=[sample_public_entity_with_actions]
        )

        # Search with different case
        result = await metadata_api_ops.search_actions(pattern="getcustomer")

        # Should return matches regardless of case
        assert len(result) == 1
        assert result[0].name == "GetCustomerDetails"

    @pytest.mark.asyncio
    async def test_search_actions_error_handling(self, metadata_api_ops):
        """Test error handling in action search"""
        # Mock an error in get_all_public_entities_with_details
        metadata_api_ops.get_all_public_entities_with_details = AsyncMock(
            side_effect=Exception("API error")
        )

        # Should return empty list on error, not raise exception
        result = await metadata_api_ops.search_actions()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_action_info_with_entity_name(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test getting action info with entity name specified"""
        metadata_api_ops.get_public_entity_info = AsyncMock(
            return_value=sample_public_entity_with_actions
        )

        result = await metadata_api_ops.get_action_info(
            "GetCustomerDetails", "Customer"
        )

        # Should return the matching action
        assert result is not None
        assert result.name == "GetCustomerDetails"
        assert result.entity_name == "Customer"
        assert result.entity_set_name == "Customers"

        # Should have called get_public_entity_info with entity name
        metadata_api_ops.get_public_entity_info.assert_called_once_with(
            "Customer", resolve_labels=False
        )

    @pytest.mark.asyncio
    async def test_get_action_info_without_entity_name(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test getting action info without entity name specified"""
        # Mock search_actions to return a specific action
        expected_action = ActionInfo(
            name="GetCustomerDetails",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_SET,
            entity_name="Customer",
            entity_set_name="Customers",
            parameters=[],
            return_type=None,
        )

        with patch.object(
            metadata_api_ops, "search_actions", return_value=[expected_action]
        ):
            result = await metadata_api_ops.get_action_info("GetCustomerDetails")

        # Should return the action found by search
        assert result is not None
        assert result.name == "GetCustomerDetails"
        assert result.entity_name == "Customer"

    @pytest.mark.asyncio
    async def test_get_action_info_action_not_found(self, metadata_api_ops):
        """Test getting action info when action is not found"""
        metadata_api_ops.get_public_entity_info = AsyncMock(return_value=None)

        result = await metadata_api_ops.get_action_info(
            "NonExistentAction", "Customer"
        )

        # Should return None when entity is not found
        assert result is None

    @pytest.mark.asyncio
    async def test_get_action_info_action_not_in_entity(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test getting action info when action is not in the specified entity"""
        metadata_api_ops.get_public_entity_info = AsyncMock(
            return_value=sample_public_entity_with_actions
        )

        result = await metadata_api_ops.get_action_info(
            "NonExistentAction", "Customer"
        )

        # Should return None when action is not found in entity
        assert result is None

    @pytest.mark.asyncio
    async def test_get_action_info_error_handling(self, metadata_api_ops):
        """Test error handling in get action info"""
        metadata_api_ops.get_public_entity_info = AsyncMock(
            side_effect=Exception("API error")
        )

        # Should return None on error, not raise exception
        result = await metadata_api_ops.get_action_info("TestAction", "TestEntity")
        assert result is None

    @pytest.mark.asyncio
    async def test_action_info_conversion_from_public_entity_action(
        self, metadata_api_ops, sample_public_entity_with_actions
    ):
        """Test conversion from PublicEntityActionInfo to ActionInfo"""
        metadata_api_ops.get_public_entity_info = AsyncMock(
            return_value=sample_public_entity_with_actions
        )

        result = await metadata_api_ops.get_action_info(
            "GetCustomerDetails", "Customer"
        )

        # Verify all fields are properly converted
        assert result.name == "GetCustomerDetails"
        assert result.binding_kind == ODataBindingKind.BOUND_TO_ENTITY_SET
        assert result.entity_name == "Customer"
        assert result.entity_set_name == "Customers"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "customerId"
        assert result.return_type is not None
        assert result.return_type.type_name == "Edm.String"