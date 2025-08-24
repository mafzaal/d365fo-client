"""OData query utilities for D365 F&O client."""

from typing import Any, Dict, Optional, Union
from urllib.parse import quote, urlencode

from .models import QueryOptions


class QueryBuilder:
    """Utility class for building OData queries"""

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
    def encode_key(key: Union[str, Dict[str, Any]]) -> str:
        """Encode entity key for URL

        Args:
            key: Entity key value (string for simple keys, dict for composite keys)

        Returns:
            URL-encoded key
        """
        if isinstance(key, dict):
            # Format composite key: key1=value1,key2=value2
            key_parts = []
            for key_name, key_value in key.items():
                encoded_value = quote(str(key_value), safe="")
                key_parts.append(f"{key_name}='{encoded_value}'")
            return ",".join(key_parts)
        else:
            # Simple string key
            return quote(str(key), safe="")

    @staticmethod
    def build_entity_url(
        base_url: str,
        entity_name: str,
        key: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> str:
        """Build entity URL

        Args:
            base_url: Base F&O URL
            entity_name: Entity set name
            key: Optional entity key (string for simple keys, dict for composite keys)

        Returns:
            Complete entity URL
        """
        base = f"{base_url.rstrip('/')}/data/{entity_name}"
        if key:
            encoded_key = QueryBuilder.encode_key(key)
            if isinstance(key, dict):
                # For composite keys, don't wrap in additional quotes
                return f"{base}({encoded_key})"
            else:
                # For simple string keys, wrap in quotes
                return f"{base}('{encoded_key}')"
        return base

    @staticmethod
    def build_action_url(
        base_url: str,
        action_name: str,
        entity_name: Optional[str] = None,
        entity_key: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> str:
        """Build action URL

        Args:
            base_url: Base F&O URL
            action_name: Action name
            entity_name: Optional entity name for bound actions
            entity_key: Optional entity key for bound actions (string for simple keys, dict for composite keys)

        Returns:
            Complete action URL
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
            encoded_key = QueryBuilder.encode_key(entity_key)
            if isinstance(entity_key, dict):
                # For composite keys, don't wrap in additional quotes
                return f"{base}/data/{entity_name}({encoded_key}){action_path}"
            else:
                # For simple string keys, wrap in quotes
                return f"{base}/data/{entity_name}('{encoded_key}'){action_path}"
        elif entity_name:
            # Bound action on entity set
            return f"{base}/data/{entity_name}{action_path}"
        else:
            # Unbound action
            return f"{base}/data{action_path}"
