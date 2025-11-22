"""OData query utilities for D365 F&O client."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from urllib.parse import quote, urlencode

from .models import QueryOptions
from .odata_serializer import ODataSerializer

if TYPE_CHECKING:
    from .models import PublicEntityInfo


class QueryBuilder:
    """Utility class for building OData queries"""

    @staticmethod
    def merge_query_strings(base_query: str, additional_query: str) -> str:
        """Merge two query strings properly.

        Args:
            base_query: Base query string (may or may not start with ?)
            additional_query: Additional query string to merge (may or may not start with ?)

        Returns:
            Merged query string with proper separators
        """
        # Normalize by removing leading ? from both
        base = base_query.lstrip("?")
        additional = additional_query.lstrip("?")

        if not base and not additional:
            return ""
        elif not base:
            return f"?{additional}"
        elif not additional:
            return f"?{base}"
        else:
            return f"?{base}&{additional}"

    @staticmethod
    def build_query_string(options: Optional[QueryOptions] = None) -> str:
        """Build OData query string from options

        Args:
            options: Query options to convert

        Returns:
            URL query string (with leading ? if parameters exist)
        """
        if not options:
            return ""

        params = QueryBuilder.build_query_params(options)

        if params:
            return "?" + urlencode(params, quote_via=quote)
        return ""

    @staticmethod
    def build_query_params(options: Optional[QueryOptions] = None) -> dict:
        """Build OData query parameters dict from options

        Args:
            options: Query options to convert

        Returns:
            Dictionary of query parameters
        """
        if not options:
            return {}

        params = {}

        if options.select:
            params["$select"] = ",".join(options.select)

        if options.filter:
            params["$filter"] = options.filter
            # If filter contains dataAreaId, add cross-company=true for D365 F&O
            # This enables querying data across multiple legal entities
            if "dataareaid" in options.filter.lower():
                params["cross-company"] = "true"

        if options.expand:
            params["$expand"] = ",".join(options.expand)

        if options.orderby:
            params["$orderby"] = ",".join(options.orderby)

        if options.top is not None:
            params["$top"] = str(options.top)

        if options.skip is not None:
            params["$skip"] = str(options.skip)

        if options.count:
            params["$count"] = "true"

        if options.search:
            params["$search"] = options.search

        return params

    @staticmethod
    def has_data_area_id_in_key(key: Union[str, Dict[str, Any]]) -> bool:
        """Check if dataAreaId is present in the key.

        Args:
            key: Entity key value (string for simple keys, dict for composite keys)

        Returns:
            True if dataAreaId is present in the key, False otherwise
        """
        if isinstance(key, dict):
            # Check if any key name is dataAreaId (case-insensitive)
            return any(k.lower() == "dataareaid" for k in key.keys())
        return False

    @staticmethod
    def encode_key(
        key: Union[str, Dict[str, Any]],
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> str:
        """Encode entity key for URL with optional schema-aware serialization.

        Args:
            key: Entity key value (string for simple keys, dict for composite keys)
            entity_schema: Optional entity schema for type-aware serialization

        Returns:
            URL-encoded key with proper data type handling
        """
        if isinstance(key, dict):
            # Serialize values according to their data types
            serialized_dict = ODataSerializer.serialize_key_dict(key, entity_schema)
            # Format as composite key with proper quoting
            return ODataSerializer.format_composite_key(serialized_dict, entity_schema)
        else:
            # Simple key - serialize as string type
            return ODataSerializer.serialize_value(str(key), "String", "Edm.String")

    @staticmethod
    def build_entity_url(
        base_url: str,
        entity_name: str,
        key: Optional[Union[str, Dict[str, Any]]] = None,
        entity_schema: Optional["PublicEntityInfo"] = None,
        add_cross_company: bool = False,
    ) -> str:
        """Build entity URL with optional schema-aware key encoding.

        Args:
            base_url: Base F&O URL
            entity_name: Entity set name
            key: Optional entity key (string for simple keys, dict for composite keys)
            entity_schema: Optional entity schema for type-aware key encoding
            add_cross_company: If True, adds cross-company=true to query string (auto-detected if False)

        Returns:
            Complete entity URL with properly encoded keys and cross-company parameter if needed
        """
        base = f"{base_url.rstrip('/')}/data/{entity_name}"
        if key:
            encoded_key = QueryBuilder.encode_key(key, entity_schema)
            if isinstance(key, dict):
                # For composite keys, formatting is handled by ODataSerializer
                url = f"{base}({encoded_key})"
            else:
                # For simple string keys, wrap in quotes
                url = f"{base}('{encoded_key}')"

            # Add cross-company parameter if dataAreaId is in the key
            # (unless explicitly disabled via add_cross_company=False)
            if add_cross_company or QueryBuilder.has_data_area_id_in_key(key):
                url += "?cross-company=true"

            return url
        return base

    @staticmethod
    def build_action_url(
        base_url: str,
        action_name: str,
        entity_name: Optional[str] = None,
        entity_key: Optional[Union[str, Dict[str, Any]]] = None,
        entity_schema: Optional["PublicEntityInfo"] = None,
        add_cross_company: bool = False,
    ) -> str:
        """Build action URL with optional schema-aware key encoding.

        Args:
            base_url: Base F&O URL
            action_name: Action name
            entity_name: Optional entity name for bound actions
            entity_key: Optional entity key for bound actions (string for simple keys, dict for composite keys)
            entity_schema: Optional entity schema for type-aware key encoding
            add_cross_company: If True, adds cross-company=true to query string (auto-detected if False)

        Returns:
            Complete action URL with properly encoded keys and cross-company parameter if needed
        """
        base = base_url.rstrip("/")

        # Ensure action_name is properly prefixed
        if action_name.startswith("/Microsoft.Dynamics.DataEntities."):
            action_path = action_name
        elif action_name.startswith("Microsoft.Dynamics.DataEntities."):
            action_path = "/" + action_name
        else:
            action_path = "/Microsoft.Dynamics.DataEntities." + action_name

        if entity_name and entity_key:
            # Bound action on specific entity
            encoded_key = QueryBuilder.encode_key(entity_key, entity_schema)
            if isinstance(entity_key, dict):
                # For composite keys, formatting is handled by ODataSerializer
                url = f"{base}/data/{entity_name}({encoded_key}){action_path}"
            else:
                # For simple string keys, wrap in quotes
                url = f"{base}/data/{entity_name}('{encoded_key}'){action_path}"

            # Add cross-company parameter if dataAreaId is in the key
            # (unless explicitly disabled via add_cross_company=False)
            if add_cross_company or QueryBuilder.has_data_area_id_in_key(entity_key):
                url += "?cross-company=true"

            return url
        elif entity_name:
            # Bound action on entity set
            return f"{base}/data/{entity_name}{action_path}"
        else:
            # Unbound action
            return f"{base}/data{action_path}"
