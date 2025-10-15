"""OData serialization utilities for D365 F&O client.

This module provides shared OData value serialization functionality
that can be used by both QueryBuilder and other components requiring
type-aware OData serialization.
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from .models import PublicEntityInfo, PublicEntityPropertyInfo

logger = logging.getLogger(__name__)


class ODataSerializer:
    """Shared OData value serialization utilities.
    
    This class provides comprehensive OData serialization support for all
    D365 Finance & Operations data types, ensuring proper URL encoding
    and OData protocol compliance.
    """

    @staticmethod
    def serialize_value(value: Any, data_type: str, type_name: str) -> str:
        """Serialize a value according to OData protocol standards based on data type.

        Handles all OData EDM types and D365 F&O specific ODataXppType values.

        Args:
            value: The value to serialize
            data_type: The simplified data type (e.g., "String", "Int32", "DateTime")
            type_name: The full OData type name (e.g., "Edm.String", "Edm.Int32")

        Returns:
            Properly serialized value for OData URL
        """
        if value is None:
            return "null"

        # Convert to string first
        str_value = str(value)

        # Handle different data types according to OData standards and D365 F&O ODataXppType
        if data_type in [
            "String", 
            "Guid", 
            "Binary", 
            "Memo", 
            "Container", 
            "VarString",
            "Record",  # D365 F&O ODataXppType.RECORD
        ]:
            # String-like types need URL encoding
            # D365 F&O specific types:
            # - VarString: variable-length string type
            # - Memo: long text fields
            # - Container: binary/container data (ODataXppType.CONTAINER)
            # - Record: complex record type (ODataXppType.RECORD)
            return quote(str_value, safe="")

        elif data_type in [
            "Int32",
            "Int64", 
            "Decimal",
            "Double",
            "Single",
            "Real",  # D365 F&O ODataXppType.REAL - floating-point numbers
            "Float",
            "Money",  # D365 F&O currency type
            "Byte",
            "SByte",
            "Int16",
            "UInt16",
            "UInt32",
            "UInt64",
            "Number",  # Generic numeric type
        ]:
            # Numeric types don't need quotes or special encoding
            # Real is D365 F&O's primary floating-point type (ODataXppType.REAL)
            # Money handles currency values with proper decimal precision
            return str_value

        elif data_type == "Boolean":
            # Boolean values should be lowercase
            return (
                str_value.lower()
                if str_value.lower() in ["true", "false"]
                else str_value
            )

        elif data_type in [
            "DateTime", 
            "DateTimeOffset", 
            "Date",  # D365 F&O ODataXppType.DATE - date only
            "Time",  # D365 F&O ODataXppType.TIME - time only
            "UtcDateTime",  # D365 F&O ODataXppType.UTC_DATETIME - UTC timezone
        ]:
            # DateTime values need special formatting
            # OData expects ISO 8601 format: YYYY-MM-DDTHH:MM:SS.fffZ
            # D365 F&O specific types:
            # - Date: date only (YYYY-MM-DD)
            # - Time: time only (HH:MM:SS)  
            # - UtcDateTime: full datetime with UTC timezone
            if "T" in str_value and (
                "Z" in str_value or "+" in str_value or str_value.count("-") > 2
            ):
                # Already in ISO format
                return quote(str_value, safe="")
            else:
                # Try to handle common formats - for now, pass through with encoding
                return quote(str_value, safe="")

        elif data_type == "Enum":
            # Enum values need the full qualified name from type_name
            # e.g., Microsoft.Dynamics.DataEntities.NoYes'Yes'
            # Corresponds to D365 F&O ODataXppType.ENUM
            if "Microsoft.Dynamics.DataEntities." in type_name:
                # Value should already be in the correct enum format
                return quote(str_value, safe="")
            else:
                # Default enum handling
                return quote(str_value, safe="")

        elif data_type == "Void":
            # D365 F&O ODataXppType.VOID - represents void/empty values
            return "null"

        else:
            # Default: treat as string and URL encode
            # Log warning only for truly unknown types (not common variations)
            if data_type not in [
                "Text", "Char", "Character", "Varchar", "NVarchar", "LongText",
                "ShortText", "Description", "Name", "Code", "Id", "Key"
            ]:
                logger.warning(
                    f"Unknown data type '{data_type}' for OData serialization, treating as string"
                )
            return quote(str_value, safe="")

    @staticmethod
    def serialize_key_dict(
        key_dict: Dict[str, Any], 
        entity_schema: Optional["PublicEntityInfo"] = None
    ) -> Dict[str, str]:
        """Serialize key dictionary with proper data type handling.

        Args:
            key_dict: Dictionary of key field names to values
            entity_schema: Optional entity schema for type-aware serialization

        Returns:
            Dictionary with properly serialized key values (URL-encoded but not OData-quoted)
        """
        serialized_dict = {}

        if entity_schema:
            # Create property lookup for efficient access
            property_lookup = {prop.name: prop for prop in entity_schema.properties}

            for field_name, field_value in key_dict.items():
                prop = property_lookup.get(field_name)
                if prop:
                    # Serialize value according to property data type
                    # For key formatting, we need URL encoding but not OData quoting yet
                    serialized_value = ODataSerializer._serialize_for_key(
                        field_value,
                        prop.data_type or "String",
                        prop.type_name or "Edm.String",
                    )
                    serialized_dict[field_name] = serialized_value
                else:
                    # Fallback: treat as string (URL encode but don't quote)
                    serialized_dict[field_name] = quote(str(field_value), safe="")
        else:
            # No schema available - fallback to string serialization
            for field_name, field_value in key_dict.items():
                serialized_dict[field_name] = quote(str(field_value), safe="")

        return serialized_dict

    @staticmethod
    def _serialize_for_key(value: Any, data_type: str, type_name: str) -> str:
        """Serialize a value for use in OData keys (URL-encoded, no OData quotes).

        Args:
            value: The value to serialize
            data_type: The simplified data type
            type_name: The full OData type name

        Returns:
            URL-encoded value ready for key formatting
        """
        if value is None:
            return "null"

        # Convert to string first
        str_value = str(value)

        # Handle different data types - URL encode when needed but don't add OData quotes
        if data_type in [
            "String", "Guid", "Binary", "Memo", "Container", "VarString",
            "Record", "Text", "Char", "Character", "Varchar", "NVarchar",
            "LongText", "ShortText", "Description", "Name", "Code", "Id", "Key"
        ]:
            # String-like types need URL encoding
            return quote(str_value, safe="")

        elif data_type in [
            "DateTime", "DateTimeOffset", "Date", "Time", "UtcDateTime"
        ]:
            # DateTime values need URL encoding
            return quote(str_value, safe="")

        elif data_type == "Enum":
            # Enum values need URL encoding
            return quote(str_value, safe="")

        elif data_type == "Boolean":
            # Boolean values should be lowercase, no encoding needed
            return str_value.lower() if str_value.lower() in ["true", "false"] else str_value

        elif data_type in [
            "Int32", "Int64", "Decimal", "Double", "Single", "Real", "Float",
            "Money", "Byte", "SByte", "Int16", "UInt16", "UInt32", "UInt64", "Number"
        ]:
            # Numeric types don't need URL encoding
            return str_value

        elif data_type == "Void":
            return "null"

        else:
            # Default: treat as string and URL encode
            return quote(str_value, safe="")

    @staticmethod
    def format_composite_key(
        key_dict: Dict[str, str], 
        entity_schema: Optional["PublicEntityInfo"] = None
    ) -> str:
        """Format a composite key dictionary into OData key string.

        Args:
            key_dict: Dictionary of serialized key field names to values
            entity_schema: Optional entity schema for determining quote requirements

        Returns:
            Formatted composite key string (e.g., "key1='value1',key2=123")
        """
        key_parts = []

        if entity_schema:
            # Use schema information to determine if quotes are needed
            property_lookup = {prop.name: prop for prop in entity_schema.properties}

            for key_name, key_value in key_dict.items():
                prop = property_lookup.get(key_name)
                if prop and ODataSerializer._needs_quotes(prop.data_type):
                    # String-like types need quotes
                    key_parts.append(f"{key_name}='{key_value}'")
                elif prop and not ODataSerializer._needs_quotes(prop.data_type):
                    # Numeric, boolean types don't need quotes
                    key_parts.append(f"{key_name}={key_value}")
                else:
                    # Unknown property - default to string behavior (needs quotes)
                    key_parts.append(f"{key_name}='{key_value}'")
        else:
            # No schema - default to quoting all values (backward compatibility)
            for key_name, key_value in key_dict.items():
                key_parts.append(f"{key_name}='{key_value}'")

        return ",".join(key_parts)

    @staticmethod
    def _needs_quotes(data_type: str) -> bool:
        """Determine if a data type needs quotes in OData key formatting.

        Args:
            data_type: The data type to check

        Returns:
            True if the data type needs quotes, False otherwise
        """
        # Types that need quotes in OData keys (D365 F&O specific)
        # Note: Date/Time types do NOT need quotes in D365 F&O OData
        quoted_types = {
            # String-like types
            "String", "Guid", "Binary", "Memo", "Container", "VarString",
            "Record", "Enum", "Text", "Char", "Character", "Varchar",
            "NVarchar", "LongText", "ShortText", "Description", "Name",
            "Code", "Id", "Key"
        }

        return data_type in quoted_types 