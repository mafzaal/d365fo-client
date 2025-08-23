"""CRUD operations for D365 F&O client."""

from typing import Any, Dict, List, Optional, Union

import aiohttp

from .models import QueryOptions
from .query import QueryBuilder
from .session import SessionManager


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
        self, entity_name: str, options: Optional[QueryOptions] = None
    ) -> Dict[str, Any]:
        """Get entities with OData query options

        Args:
            entity_name: Name of the entity set
            options: OData query options

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
    ) -> Dict[str, Any]:
        """Get single entity by key

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            options: OData query options

        Returns:
            Entity data
        """
        session = await self.session_manager.get_session()
        query_string = QueryBuilder.build_query_string(options)
        url = QueryBuilder.build_entity_url(self.base_url, entity_name, key)
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
        self, entity_name: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create new entity

        Args:
            entity_name: Name of the entity set
            data: Entity data to create

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
    ) -> Dict[str, Any]:
        """Update existing entity

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            data: Updated entity data
            method: HTTP method (PATCH or PUT)

        Returns:
            Updated entity data
        """
        session = await self.session_manager.get_session()
        url = QueryBuilder.build_entity_url(self.base_url, entity_name, key)

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
        self, entity_name: str, key: Union[str, Dict[str, Any]]
    ) -> bool:
        """Delete entity

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)

        Returns:
            True if successful
        """
        session = await self.session_manager.get_session()
        url = QueryBuilder.build_entity_url(self.base_url, entity_name, key)

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
    ) -> Any:
        """Call OData action method

        Args:
            action_name: Name of the action
            parameters: Action parameters
            entity_name: Entity name for bound actions
            entity_key: Entity key for bound actions (string for simple keys, dict for composite keys)

        Returns:
            Action result
        """
        session = await self.session_manager.get_session()
        url = QueryBuilder.build_action_url(
            self.base_url, action_name, entity_name, entity_key
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
