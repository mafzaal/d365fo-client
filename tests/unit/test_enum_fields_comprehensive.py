"""Comprehensive tests for all enum fields in models.py to ensure proper to_dict() handling."""

import pytest
from d365fo_client.models import (
    ActionInfo,
    ActionParameterInfo,
    ActionParameterTypeInfo,
    ActionReturnTypeInfo,
    Cardinality,
    DataEntityInfo,
    EntityCategory,
    NavigationPropertyInfo,
    ODataBindingKind,
    PublicEntityActionInfo,
)


class TestEnumFieldsToDict:
    """Test all enum fields in models for proper to_dict() handling."""

    def test_data_entity_info_enum_fields(self):
        """Test DataEntityInfo with enum and string entity_category."""
        # Test with enum
        entity_enum = DataEntityInfo(
            name="TestEntity",
            public_entity_name="TestEntityName",
            public_collection_name="TestEntities",
            entity_category=EntityCategory.MASTER,  # Enum
            is_read_only=False
        )
        
        result_enum = entity_enum.to_dict()
        assert result_enum["entity_category"] == "Master"
        
        # Test with string (edge case)
        entity_string = DataEntityInfo(
            name="TestEntity",
            public_entity_name="TestEntityName", 
            public_collection_name="TestEntities",
            entity_category="Transaction",  # String
            is_read_only=False
        )
        
        result_string = entity_string.to_dict()
        assert result_string["entity_category"] == "Transaction"
        
        # Test with None
        entity_none = DataEntityInfo(
            name="TestEntity",
            public_entity_name="TestEntityName",
            public_collection_name="TestEntities",
            entity_category=None,  # None
            is_read_only=False
        )
        
        result_none = entity_none.to_dict()
        assert result_none["entity_category"] is None

    def test_public_entity_action_info_enum_fields(self):
        """Test PublicEntityActionInfo with enum and string binding_kind."""
        # Test with enum
        action_enum = PublicEntityActionInfo(
            name="TestAction",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_SET,  # Enum
        )
        
        result_enum = action_enum.to_dict()
        assert result_enum["binding_kind"] == "BoundToEntitySet"
        
        # Test with string (edge case)
        action_string = PublicEntityActionInfo(
            name="TestAction",
            binding_kind="Unbound",  # String
        )
        
        result_string = action_string.to_dict()
        assert result_string["binding_kind"] == "Unbound"

    def test_navigation_property_info_enum_fields(self):
        """Test NavigationPropertyInfo with enum and string cardinality."""
        # Test with enum
        nav_prop_enum = NavigationPropertyInfo(
            name="TestNavProp",
            related_entity="RelatedEntity",
            cardinality=Cardinality.MULTIPLE,  # Enum
        )
        
        result_enum = nav_prop_enum.to_dict()
        assert result_enum["cardinality"] == "Multiple"
        
        # Test with string (edge case)
        nav_prop_string = NavigationPropertyInfo(
            name="TestNavProp",
            related_entity="RelatedEntity",
            cardinality="Single",  # String
        )
        
        result_string = nav_prop_string.to_dict()
        assert result_string["cardinality"] == "Single"

    def test_action_info_enum_fields(self):
        """Test ActionInfo with enum and string binding_kind."""
        # Test with enum
        action_enum = ActionInfo(
            name="TestAction",
            binding_kind=ODataBindingKind.BOUND_TO_ENTITY_INSTANCE,  # Enum
        )
        
        result_enum = action_enum.to_dict()
        assert result_enum["binding_kind"] == "BoundToEntityInstance"
        
        # Test with string (edge case)
        action_string = ActionInfo(
            name="TestAction",
            binding_kind="BoundToEntitySet",  # String
        )
        
        result_string = action_string.to_dict()
        assert result_string["binding_kind"] == "BoundToEntitySet"

    def test_complex_objects_with_nested_enums(self):
        """Test complex objects that contain other objects with enum fields."""
        # Create nested objects
        param_type = ActionParameterTypeInfo(
            type_name="Edm.String",
            is_collection=False
        )
        
        param = ActionParameterInfo(
            name="testParam",
            type=param_type
        )
        
        return_type = ActionReturnTypeInfo(
            type_name="Edm.String",
            is_collection=False
        )
        
        # Create action with nested objects and enum
        action = ActionInfo(
            name="ComplexAction",
            binding_kind=ODataBindingKind.UNBOUND,  # Enum
            entity_name="TestEntity",
            parameters=[param],
            return_type=return_type
        )
        
        result = action.to_dict()
        
        # Verify enum was handled correctly
        assert result["binding_kind"] == "Unbound"
        
        # Verify nested objects still work
        assert len(result["parameters"]) == 1
        assert result["parameters"][0]["name"] == "testParam"
        assert result["return_type"]["type_name"] == "Edm.String"

    def test_strenum_behavior_directly(self):
        """Test StrEnum behavior directly."""
        
        # Test with StrEnum - should work seamlessly
        assert str(EntityCategory.MASTER) == "Master"
        assert str(ODataBindingKind.UNBOUND) == "Unbound"
        assert str(Cardinality.SINGLE) == "Single"
        
        # Test equality with strings
        assert EntityCategory.MASTER == "Master"
        assert ODataBindingKind.UNBOUND == "Unbound"
        assert Cardinality.SINGLE == "Single"
        
        # Test JSON serialization
        import json
        assert json.dumps(EntityCategory.MASTER) == '"Master"'
        assert json.dumps(ODataBindingKind.UNBOUND) == '"Unbound"'
        
        # Test None handling
        assert None is None  # Basic sanity check