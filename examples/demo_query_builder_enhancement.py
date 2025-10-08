#!/usr/bin/env python3
"""
Demonstration of enhanced QueryBuilder OData key encoding with schema awareness.

This script demonstrates the fix for the critical issue where QueryBuilder.encode_key()
was treating all key values as strings, which caused incorrect OData URL formatting
for numeric, boolean, and date key fields.
"""

from unittest.mock import Mock
from d365fo_client.query import QueryBuilder
from d365fo_client.odata_serializer import ODataSerializer


def create_mock_schema():
    """Create a mock entity schema with various data types."""
    # Create properties with different data types
    string_prop = Mock()
    string_prop.name = "CustomerId"
    string_prop.data_type = "String"
    string_prop.type_name = "Edm.String"
    string_prop.is_key = True

    record_prop = Mock()
    record_prop.name = "RecordId"
    record_prop.data_type = "Int64"
    record_prop.type_name = "Edm.Int64"
    record_prop.is_key = True

    company_prop = Mock()
    company_prop.name = "CompanyId"
    company_prop.data_type = "Int32"
    company_prop.type_name = "Edm.Int32"
    company_prop.is_key = True

    date_prop = Mock()
    date_prop.name = "EffectiveDate"
    date_prop.data_type = "Date"
    date_prop.type_name = "Edm.Date"
    date_prop.is_key = True

    bool_prop = Mock()
    bool_prop.name = "IsActive"
    bool_prop.data_type = "Boolean"
    bool_prop.type_name = "Edm.Boolean"
    bool_prop.is_key = True

    enum_prop = Mock()
    enum_prop.name = "Status"
    enum_prop.data_type = "Enum"
    enum_prop.type_name = "Microsoft.Dynamics.DataEntities.EntityStatus"
    enum_prop.is_key = True

    schema = Mock()
    schema.properties = [string_prop, record_prop, company_prop, date_prop, bool_prop, enum_prop]
    return schema


def demo_backward_compatibility():
    """Demonstrate backward compatibility without schema."""
    print("=" * 60)
    print("BACKWARD COMPATIBILITY DEMO (No Schema)")
    print("=" * 60)
    
    # Simple string key
    simple_key = "CUST001"
    encoded = QueryBuilder.encode_key(simple_key)
    print(f"Simple key '{simple_key}' -> '{encoded}'")
    
    # Composite key (legacy behavior - all strings with quotes)
    composite_key = {
        "CustomerId": "CUST001",
        "RecordId": "123456",
        "CompanyId": "100"
    }
    
    encoded = QueryBuilder.encode_key(composite_key)
    print(f"Composite key (no schema): {encoded}")
    print("Note: All values are quoted as strings (legacy behavior)")
    
    # Build URL
    url = QueryBuilder.build_entity_url(
        "https://example.com", "Customers", composite_key
    )
    print(f"Entity URL: {url}")
    print()


def demo_schema_aware_encoding():
    """Demonstrate schema-aware encoding with proper data types."""
    print("=" * 60)
    print("SCHEMA-AWARE ENCODING DEMO")
    print("=" * 60)
    
    schema = create_mock_schema()
    
    # Mixed data type composite key
    composite_key = {
        "CustomerId": "CUST001",      # String -> should be quoted
        "RecordId": "123456",         # Int64 -> should NOT be quoted
        "CompanyId": "100",           # Int32 -> should NOT be quoted
        "EffectiveDate": "2024-01-15", # Date -> should be quoted
        "IsActive": "true",           # Boolean -> should NOT be quoted
        "Status": "Microsoft.Dynamics.DataEntities.EntityStatus'Active'" # Enum -> should be quoted
    }
    
    # Encode with schema awareness
    encoded = QueryBuilder.encode_key(composite_key, schema)
    print(f"Schema-aware encoding: {encoded}")
    print()
    
    print("Data type handling:")
    print("- CustomerId (String): 'CUST001' (quoted)")
    print("- RecordId (Int64): 123456 (no quotes)")
    print("- CompanyId (Int32): 100 (no quotes)")
    print("- EffectiveDate (Date): '2024-01-15' (quoted)")
    print("- IsActive (Boolean): true (no quotes)")
    print("- Status (Enum): 'Microsoft...Active%27' (quoted and URL-encoded)")
    print()
    
    # Build URL with schema
    url = QueryBuilder.build_entity_url(
        "https://example.com", "Customers", composite_key, schema
    )
    print(f"Entity URL with schema: {url}")
    print()


def demo_individual_serialization():
    """Demonstrate individual value serialization."""
    print("=" * 60)
    print("INDIVIDUAL VALUE SERIALIZATION DEMO")
    print("=" * 60)
    
    test_values = [
        ("Hello World", "String", "Edm.String"),
        ("123456", "Int64", "Edm.Int64"),
        ("100", "Int32", "Edm.Int32"),
        ("2024-01-15T10:30:00Z", "DateTime", "Edm.DateTime"),
        ("true", "Boolean", "Edm.Boolean"),
        ("Microsoft.Dynamics.DataEntities.NoYes'Yes'", "Enum", "Microsoft.Dynamics.DataEntities.NoYes"),
        ("99.99", "Decimal", "Edm.Decimal"),
        ("test/value with spaces", "String", "Edm.String"),
    ]
    
    for value, data_type, type_name in test_values:
        serialized = ODataSerializer.serialize_value(value, data_type, type_name)
        print(f"{data_type:12} '{value}' -> '{serialized}'")
    print()


def demo_performance_comparison():
    """Demonstrate the difference between old and new approaches."""
    print("=" * 60)
    print("BEFORE vs AFTER COMPARISON")
    print("=" * 60)
    
    composite_key = {
        "CustomerId": "CUST001",
        "RecordId": "123456",
        "CompanyId": "100"
    }
    
    print("BEFORE (Old QueryBuilder behavior):")
    # Simulate old behavior - all values quoted as strings
    old_style = "CustomerId='CUST001',RecordId='123456',CompanyId='100'"
    print(f"  Result: {old_style}")
    print("  Problem: Numeric IDs incorrectly quoted as strings")
    print("  Issue: RecordId='123456' should be RecordId=123456")
    print()
    
    schema = create_mock_schema()
    print("AFTER (Enhanced QueryBuilder with schema):")
    new_style = QueryBuilder.encode_key(composite_key, schema)
    print(f"  Result: {new_style}")
    print("  Fixed: String values quoted, numeric values unquoted")
    print("  Correct: RecordId=123456 (no quotes for Int64)")
    print()


def main():
    """Run all demonstrations."""
    print("Enhanced QueryBuilder OData Key Encoding Demonstration")
    print("=" * 60)
    print("This demonstrates the fix for the critical QueryBuilder limitation")
    print("where encode_key() treated all values as strings.")
    print()
    
    demo_backward_compatibility()
    demo_schema_aware_encoding()
    demo_individual_serialization()
    demo_performance_comparison()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Backward compatibility maintained (no schema parameter)")
    print("✅ Schema-aware encoding added (optional entity_schema parameter)")
    print("✅ Proper OData compliance for all D365 F&O data types")
    print("✅ String values: quoted and URL-encoded")
    print("✅ Numeric values: unquoted")
    print("✅ Boolean values: unquoted, lowercase")
    print("✅ Date values: quoted and URL-encoded")
    print("✅ Enum values: quoted and URL-encoded")
    print("✅ Unknown properties: default to string behavior")
    print()
    print("This fix resolves the critical issue where composite keys with")
    print("numeric fields were incorrectly formatted as RecordId='123'")
    print("instead of the correct OData format RecordId=123")


if __name__ == "__main__":
    main()