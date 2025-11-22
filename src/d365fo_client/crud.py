"""CRUD operations for D365 F&O client."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .models import QueryOptions
from .query import QueryBuilder
from .session import SessionManager

if TYPE_CHECKING:
    from .models import PublicEntityInfo


class CrudOperations:
    """Handles CRUD operations for F&O entities"""

    def __init__(self, session_manager: SessionManager, base_url: str):
        """Initialize CRUD operations

        Args:
            session_manager: HTTP session manager
            base_url: Base F&O URL
        """
        self.session_manager = session_manager
        self.base_url = base_url

    async def get_entities(
        self,
        entity_name: str,
        options: Optional[QueryOptions] = None,
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> Dict[str, Any]:
        """Get entities with OData query options

        Args:
            entity_name: Name of the entity set
            options: OData query options
            entity_schema: Optional entity schema for validation/optimization

        Returns:
            Response containing entities
        """
        session = await self.session_manager.get_session()
        query_string = QueryBuilder.build_query_string(options)
        url = f"{self.base_url}/data/{entity_name}{query_string}"

        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(
                    f"GET {entity_name} failed: {response.status} - {error_text}"
                )

    async def get_entity(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        options: Optional[QueryOptions] = None,
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> Dict[str, Any]:
        """Get single entity by key

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            options: OData query options
            entity_schema: Optional entity schema for type-aware key encoding

        Returns:
            Entity data
        """
        session = await self.session_manager.get_session()
        
        # Use schema-aware URL building for proper key encoding
        # This will add cross-company=true if dataAreaId is in the key
        url = QueryBuilder.build_entity_url(
            self.base_url, entity_name, key, entity_schema
        )
        
        # Build and merge query string from options
        query_string = QueryBuilder.build_query_string(options)
        if query_string:
            # Merge query strings properly (handles ? and & separators)
            if "?" in url:
                # URL already has query params (e.g., cross-company)
                url += query_string.replace("?", "&")
            else:
                url += query_string

        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(
                    f"GET {entity_name}({key}) failed: {response.status} - {error_text}"
                )

    async def create_entity(
        self,
        entity_name: str,
        data: Dict[str, Any],
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> Dict[str, Any]:
        """Create new entity

        Args:
            entity_name: Name of the entity set
            data: Entity data to create
            entity_schema: Optional entity schema for validation

        Returns:
            Created entity data
        """
        session = await self.session_manager.get_session()
        url = f"{self.base_url}/data/{entity_name}"

        async with session.post(url, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(
                    f"CREATE {entity_name} failed: {response.status} - {error_text}"
                )

    async def update_entity(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        data: Dict[str, Any],
        method: str = "PATCH",
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> Dict[str, Any]:
        """Update existing entity

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            data: Updated entity data
            method: HTTP method (PATCH or PUT)
            entity_schema: Optional entity schema for type-aware key encoding and validation

        Returns:
            Updated entity data
        """
        session = await self.session_manager.get_session()
        # Use schema-aware URL building for proper key encoding
        url = QueryBuilder.build_entity_url(
            self.base_url, entity_name, key, entity_schema
        )

        async with session.request(method, url, json=data) as response:
            if response.status in [200, 204]:
                if response.status == 204:
                    return {"success": True}
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(
                    f"{method} {entity_name}({key}) failed: {response.status} - {error_text}"
                )

    async def delete_entity(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> bool:
        """Delete entity

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            entity_schema: Optional entity schema for type-aware key encoding

        Returns:
            True if successful
        """
        session = await self.session_manager.get_session()
        # Use schema-aware URL building for proper key encoding
        url = QueryBuilder.build_entity_url(
            self.base_url, entity_name, key, entity_schema
        )

        async with session.delete(url) as response:
            if response.status in [200, 204]:
                return True
            else:
                error_text = await response.text()
                raise Exception(
                    f"DELETE {entity_name}({key}) failed: {response.status} - {error_text}"
                )

    async def call_action(
        self,
        action_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        entity_name: Optional[str] = None,
        entity_key: Optional[Union[str, Dict[str, Any]]] = None,
        entity_schema: Optional["PublicEntityInfo"] = None,
    ) -> Any:
        """Call OData action method

        Args:
            action_name: Name of the action
            parameters: Action parameters
            entity_name: Entity name for bound actions
            entity_key: Entity key for bound actions (string for simple keys, dict for composite keys)
            entity_schema: Optional entity schema for type-aware key encoding in bound actions

        Returns:
            Action result
        """
        session = await self.session_manager.get_session()
        # Use schema-aware URL building for entity-bound actions
        url = QueryBuilder.build_action_url(
            self.base_url, action_name, entity_name, entity_key, entity_schema
        )

        # Prepare request body
        body = parameters or {}

        async with session.post(url, json=body) as response:
            if response.status in [200, 201, 204]:
                if response.status == 204:
                    return {"success": True}

                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return await response.json()
                else:
                    return await response.text()
            else:
                error_text = await response.text()
                raise Exception(
                    f"Action {action_name} failed: {response.status} - {error_text}"
                )
