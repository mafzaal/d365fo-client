"""Test for DataEntityInfo to_dict method with both string and enum entity_category."""

import pytest
from d365fo_client.models import DataEntityInfo, EntityCategory


class TestDataEntityInfoToDict:
    """Test DataEntityInfo.to_dict() method handling of entity_category."""

    def test_to_dict_with_enum_entity_category(self):
        """Test to_dict when entity_category is an enum."""
        entity = DataEntityInfo(
            name="TestEntity",
            public_entity_name="TestEntityName",
            public_collection_name="TestEntities",
            label_id="@TEST123",
            label_text="Test Entity",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category=EntityCategory.MASTER,  # Enum value
            is_read_only=False
        )
        
        result = entity.to_dict()
        
        assert result["entity_category"] == "Master"
        assert result["name"] == "TestEntity"
        assert result["data_service_enabled"] is True

    def test_to_dict_with_string_entity_category(self):
        """Test to_dict when entity_category is a string (edge case)."""
        entity = DataEntityInfo(
            name="TestEntity",
            public_entity_name="TestEntityName", 
            public_collection_name="TestEntities",
            label_id="@TEST123",
            label_text="Test Entity",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category="Transaction",  # String value
            is_read_only=False
        )
        
        result = entity.to_dict()
        
        assert result["entity_category"] == "Transaction"
        assert result["name"] == "TestEntity"
        assert result["data_service_enabled"] is True

    def test_to_dict_with_none_entity_category(self):
        """Test to_dict when entity_category is None."""
        entity = DataEntityInfo(
            name="TestEntity",
            public_entity_name="TestEntityName",
            public_collection_name="TestEntities",
            label_id="@TEST123",
            label_text="Test Entity",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category=None,  # None value
            is_read_only=False
        )
        
        result = entity.to_dict()
        
        assert result["entity_category"] is None
        assert result["name"] == "TestEntity"
        assert result["data_service_enabled"] is True