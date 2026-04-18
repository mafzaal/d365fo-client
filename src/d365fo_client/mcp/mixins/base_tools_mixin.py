"""Base mixin class for FastMCP tool categories."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP

from d365fo_client.client import FOClient
from d365fo_client.odata_serializer import ODataSerializer
from d365fo_client.profile_manager import ProfileManager

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class BaseToolsMixin:
    """Base mixin for FastMCP tool categories.

    Provides common functionality and client access patterns
    for all tool category mixins.
    """

    # These will be injected by the main server class
    client_manager: D365FOClientManager
    mcp: FastMCP
    profile_manager: ProfileManager

    async def _get_client(self, profile: str = "default") -> FOClient:
        """Get D365FO client for specified profile.

        Args:
            profile: Profile name to use

        Returns:
            Configured D365FO client instance
        """
        if not hasattr(self, "client_manager") or not self.client_manager:
            raise RuntimeError("Client manager not initialized")
        return await self.client_manager.get_client(profile)

    def _create_error_response(
        self, error: Exception, tool_name: str, arguments: dict
    ) -> dict:
        """Create standardized error response.

        Args:
            error: Exception that occurred
            tool_name: Name of the tool that failed
            arguments: Arguments passed to the tool

        Returns:
            Dictionary with error details
        """
        return {
            "error": str(error),
            "tool": tool_name,
            "arguments": arguments,
            "error_type": type(error).__name__,
        }

    async def _resolve_entity_name(
        self, name: str, profile: str = "default"
    ) -> Optional[str]:
        """Resolve an entity name to its OData-accessible collection name.

        Handles entity name, public entity name, and public collection name inputs.

        Args:
            name: Entity name in any format
            profile: Profile name for connection

        Returns:
            The entity set name (public collection name) if found, otherwise None
        """
        try:
            client = await self._get_client(profile)
            schema = await client.get_public_entity_schema_by_entityset(name)
            if schema:
                return schema.entity_set_name or schema.name
            return None
        except Exception:
            return None

    async def _validate_entity_for_query(
        self, entity_name: str, profile: str = "default"
    ) -> bool:
        """Check if an entity is accessible for OData queries.

        Args:
            entity_name: Entity name to validate
            profile: Profile name for connection

        Returns:
            True if entity supports OData queries, False otherwise
        """
        try:
            resolved = await self._resolve_entity_name(entity_name, profile)
            return resolved is not None
        except Exception:
            return False

    async def _validate_entity_exists(
        self, entity_name: str, profile: str = "default"
    ) -> bool:
        """Check if an entity exists in D365 F&O metadata.

        Checks both OData-accessible and non-OData (DMF-only) entities.

        Args:
            entity_name: Entity name to check
            profile: Profile name for connection

        Returns:
            True if entity exists, False otherwise
        """
        try:
            client = await self._get_client(profile)
            # Try OData-accessible entity first (fastest path)
            schema = await client.get_public_entity_schema_by_entityset(entity_name)
            if schema:
                return True
            # Fall back to full data entity search (covers DMF-only entities)
            entities = await client.search_entities(entity_name)
            for entity in entities:
                if (
                    entity.name == entity_name
                    or entity.public_entity_name == entity_name
                    or entity.public_collection_name == entity_name
                ):
                    return True
            return False
        except Exception:
            return False

    def _serialize_odata_value(
        self, value: Any, data_type: str, type_name: str
    ) -> str:
        """Serialize a Python value to its OData string representation.

        Args:
            value: Python value to serialize
            data_type: D365 data type (e.g., 'String', 'Int32', 'Boolean', 'Enum')
            type_name: Full OData type name (e.g., 'Edm.String', 'Microsoft.Dynamics.DataEntities.NoYes')

        Returns:
            OData-formatted string representation of the value
        """
        return ODataSerializer.serialize_value(value, data_type, type_name)

    def _build_validated_key_dict(
        self,
        key_fields: List[str],
        key_values: List[str],
        schema: Any,
    ) -> Dict[str, str]:
        """Build a key dictionary with serialized values from field names and values.

        Args:
            key_fields: List of key field names
            key_values: List of key values corresponding to key_fields
            schema: PublicEntityInfo schema object with property metadata

        Returns:
            Dictionary mapping field names to serialized string values
        """
        prop_lookup = {prop.name: prop for prop in schema.properties}
        key_dict: Dict[str, str] = {}
        for field_name, field_value in zip(key_fields, key_values):
            prop = prop_lookup.get(field_name)
            if prop:
                serialized = self._serialize_odata_value(
                    field_value, prop.data_type, prop.type_name
                )
            else:
                serialized = str(field_value)
            key_dict[field_name] = serialized
        return key_dict

    async def _validate_entity_schema_and_keys(
        self,
        entity_name: str,
        key_fields: List[str],
        key_values: List[str],
        profile: str = "default",
    ) -> Tuple[bool, Optional[Any], Optional[str]]:
        """Validate entity schema and key field configuration.

        Args:
            entity_name: Entity name to validate
            key_fields: List of key field names to verify
            key_values: List of key values corresponding to key_fields
            profile: Profile name for connection

        Returns:
            Tuple of (is_valid, schema, error_details):
            - is_valid: True if validation passed
            - schema: PublicEntityInfo if found, None if not
            - error_details: Error description if validation failed, None if valid
        """
        if len(key_fields) != len(key_values):
            return (
                False,
                None,
                f"Key field count ({len(key_fields)}) doesn't match value count ({len(key_values)})",
            )

        resolved_name = await self._resolve_entity_name(entity_name, profile)
        if not resolved_name:
            return (
                False,
                None,
                f"Entity '{entity_name}' not found or not accessible for OData operations",
            )

        try:
            client = await self._get_client(profile)
            schema = await client.get_public_entity_info(
                resolved_name, resolve_labels=False
            )
            if not schema:
                return (
                    False,
                    None,
                    f"Could not retrieve schema for entity '{entity_name}'",
                )
        except Exception as e:
            return (False, None, f"Error retrieving schema for '{entity_name}': {e}")

        schema_key_fields = [prop.name for prop in schema.properties if prop.is_key]

        for field in key_fields:
            if field not in schema_key_fields:
                return (
                    False,
                    schema,
                    f"Field '{field}' is not a key field in '{entity_name}'. Valid key fields: {schema_key_fields}",
                )

        if len(key_fields) != len(schema_key_fields):
            missing = [f for f in schema_key_fields if f not in key_fields]
            return (
                False,
                schema,
                f"Missing key fields for '{entity_name}': {missing}",
            )

        return (True, schema, None)
