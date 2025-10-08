"""Unit tests for enhanced QueryBuilder OData encoding with schema awareness."""

import pytest
from unittest.mock import Mock

from d365fo_client.query import QueryBuilder
from d365fo_client.models import PublicEntityInfo, PublicEntityPropertyInfo


class TestQueryBuilderEnhancedEncoding:
    """Test the enhanced QueryBuilder encoding with schema-aware serialization."""

    @pytest.fixture
    def mock_entity_schema(self):
        """Create a mock entity schema with various data types."""
        # Create mock properties with different data types
        # Note: Mock(name='X') sets internal mock name, not the name attribute
        string_prop = Mock()
        string_prop.name = "StringKey"
        string_prop.data_type = "String"
        string_prop.type_name = "Edm.String"
        string_prop.is_key = True

        record_id_prop = Mock()
        record_id_prop.name = "RecordId"
        record_id_prop.data_type = "Int64"
        record_id_prop.type_name = "Edm.Int64"
        record_id_prop.is_key = True

        company_id_prop = Mock()
        company_id_prop.name = "CompanyId"
        company_id_prop.data_type = "Int32"
        company_id_prop.type_name = "Edm.Int32"
        company_id_prop.is_key = True

        date_prop = Mock()
        date_prop.name = "DateKey"
        date_prop.data_type = "Date"
        date_prop.type_name = "Edm.Date"
        date_prop.is_key = True

        enum_prop = Mock()
        enum_prop.name = "StatusKey"
        enum_prop.data_type = "Enum"
        enum_prop.type_name = "Microsoft.Dynamics.DataEntities.EntityStatus"
        enum_prop.is_key = True

        bool_prop = Mock()
        bool_prop.name = "IsActive"
        bool_prop.data_type = "Boolean"
        bool_prop.type_name = "Edm.Boolean"
        bool_prop.is_key = True

        properties = [string_prop, record_id_prop, company_id_prop, date_prop, enum_prop, bool_prop]

        # Create mock entity schema
        schema = Mock()
        schema.properties = properties
        return schema

    def test_simple_string_key_encoding(self):
        """Test encoding of simple string keys."""
        # Without schema (backward compatibility)
        result = QueryBuilder.encode_key("test-value")
        assert result == "test-value"  # ODataSerializer handles URL encoding

        # With schema (should work the same for simple keys)
        result_with_schema = QueryBuilder.encode_key("test-value", None)
        assert result_with_schema == "test-value"

    def test_composite_key_without_schema(self):
        """Test composite key encoding without schema (backward compatibility)."""
        key_dict = {
            "StringKey": "test-value",
            "RecordId": "123",
            "CompanyId": "456",
        }

        result = QueryBuilder.encode_key(key_dict)
        
        # Without schema, all values are treated as strings with quotes
        expected_parts = [
            "StringKey='test-value'",
            "RecordId='123'",
            "CompanyId='456'",
        ]
        
        # Check that all expected parts are in the result
        for part in expected_parts:
            assert part in result
        
        # Check proper comma separation
        assert result.count(",") == 2

    def test_composite_key_with_schema_mixed_types(self, mock_entity_schema):
        """Test composite key encoding with schema for mixed data types."""
        key_dict = {
            "StringKey": "test-value",
            "RecordId": "123",
            "CompanyId": "456",
            "DateKey": "2024-01-15",
            "StatusKey": "Microsoft.Dynamics.DataEntities.EntityStatus'Active'",
            "IsActive": "true",
        }

        result = QueryBuilder.encode_key(key_dict, mock_entity_schema)
        
        # With schema, different data types should be formatted correctly
        # String and date types should have quotes
        assert "StringKey='test-value'" in result
        assert "DateKey='2024-01-15'" in result
        assert "StatusKey='Microsoft.Dynamics.DataEntities.EntityStatus%27Active%27'" in result
        
        # Numeric types should not have quotes
        assert "RecordId=123" in result
        assert "CompanyId=456" in result
        
        # Boolean should not have quotes and be lowercase
        assert "IsActive=true" in result
        
        # Check proper comma separation
        assert result.count(",") == 5

    def test_composite_key_numeric_only(self, mock_entity_schema):
        """Test composite key with only numeric types."""
        key_dict = {
            "RecordId": "123",
            "CompanyId": "456",
        }

        result = QueryBuilder.encode_key(key_dict, mock_entity_schema)
        
        # Both should be numeric without quotes
        assert "RecordId=123" in result
        assert "CompanyId=456" in result
        assert result.count("'") == 0  # No quotes for numeric types

    def test_composite_key_string_only(self, mock_entity_schema):
        """Test composite key with only string types."""
        key_dict = {
            "StringKey": "test-value",
        }

        result = QueryBuilder.encode_key(key_dict, mock_entity_schema)
        
        # String should have quotes
        assert result == "StringKey='test-value'"

    def test_build_entity_url_with_schema(self, mock_entity_schema):
        """Test building entity URL with schema-aware key encoding."""
        base_url = "https://test.dynamics.com"
        entity_name = "TestEntities"
        
        # Simple string key
        url = QueryBuilder.build_entity_url(
            base_url, entity_name, "simple-key", mock_entity_schema
        )
        assert url == "https://test.dynamics.com/data/TestEntities('simple-key')"
        
        # Composite key with mixed types
        composite_key = {
            "StringKey": "test",
            "RecordId": "123",
        }
        
        url = QueryBuilder.build_entity_url(
            base_url, entity_name, composite_key, mock_entity_schema
        )
        
        # Should contain properly formatted composite key
        assert "https://test.dynamics.com/data/TestEntities(" in url
        assert "StringKey='test'" in url
        assert "RecordId=123" in url
        assert url.endswith(")")

    def test_build_action_url_with_schema(self, mock_entity_schema):
        """Test building action URL with schema-aware key encoding."""
        base_url = "https://test.dynamics.com"
        action_name = "TestAction"
        entity_name = "TestEntities"
        
        # Composite key for bound action
        composite_key = {
            "StringKey": "test",
            "RecordId": "123",
        }
        
        url = QueryBuilder.build_action_url(
            base_url, action_name, entity_name, composite_key, mock_entity_schema
        )
        
        # Should contain properly formatted composite key and action path
        assert "https://test.dynamics.com/data/TestEntities(" in url
        assert "StringKey='test'" in url
        assert "RecordId=123" in url
        assert "/Microsoft.Dynamics.DataEntities.TestAction" in url

    def test_backward_compatibility_no_schema(self):
        """Test that existing code without schema parameter still works."""
        # All existing QueryBuilder calls should work unchanged
        
        # Simple key
        result = QueryBuilder.encode_key("test")
        assert result == "test"
        
        # Composite key (legacy behavior - all strings with quotes)
        composite = {"key1": "value1", "key2": "value2"}
        result = QueryBuilder.encode_key(composite)
        assert "key1='value1'" in result
        assert "key2='value2'" in result
        
        # URL building without schema
        url = QueryBuilder.build_entity_url(
            "https://test.com", "Entity", composite
        )
        assert "Entity(" in url
        assert "key1='value1'" in url
        assert "key2='value2'" in url

    def test_special_characters_handling(self, mock_entity_schema):
        """Test handling of special characters in key values."""
        key_dict = {
            "StringKey": "test/value with spaces & symbols",
            "RecordId": "123",
        }

        result = QueryBuilder.encode_key(key_dict, mock_entity_schema)
        
        # String value should be URL encoded
        assert "StringKey=" in result
        assert "RecordId=123" in result
        # The exact URL encoding will depend on the ODataSerializer implementation

    def test_null_and_empty_values(self, mock_entity_schema):
        """Test handling of null and empty values."""
        key_dict = {
            "StringKey": "",
            "RecordId": "0",
        }

        result = QueryBuilder.encode_key(key_dict, mock_entity_schema)
        
        # Empty string should still be quoted
        assert "StringKey=''" in result
        # Zero should not be quoted
        assert "RecordId=0" in result

    def test_schema_property_lookup_missing_property(self):
        """Test behavior when schema doesn't contain all key properties."""
        # Create schema with only one property
        known_prop = Mock()
        known_prop.name = "KnownKey"
        known_prop.data_type = "String"
        known_prop.type_name = "Edm.String"
        known_prop.is_key = True

        limited_schema = Mock()
        limited_schema.properties = [known_prop]

        key_dict = {
            "KnownKey": "known-value",
            "UnknownKey": "unknown-value",
        }

        result = QueryBuilder.encode_key(key_dict, limited_schema)
        
        # Known key should use schema info (string with quotes)
        assert "KnownKey='known-value'" in result
        # Unknown key should fall back to string treatment
        assert "UnknownKey='unknown-value'" in result