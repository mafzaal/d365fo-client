"""Main F&O client implementation."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .auth import AuthenticationManager
from .crud import CrudOperations
from .exceptions import FOClientError
from .labels import LabelOperations, resolve_labels_generic
from .metadata_api import MetadataAPIOperations
from .metadata_v2 import MetadataCacheV2, SmartSyncManagerV2
from .models import (
    ActionInfo,
    DataEntityInfo,
    EnumerationInfo,
    FOClientConfig,
    PublicEntityInfo,
    QueryOptions,
)
from .query import QueryBuilder
from .session import SessionManager


class FOClient:
    """Main F&O OData Client

    A comprehensive client for connecting to D365 F&O and performing:
    - Metadata download, storage, and search
    - OData action method calls
    - CRUD operations on data entities
    - OData query parameters support
    - Label text retrieval and caching
    - Multilingual label support
    - Entity metadata with resolved labels
    """

    def __init__(self, config: Union[FOClientConfig, str, Dict[str, Any]]):
        """Initialize F&O client

        Args:
            config: FOClientConfig object, base_url string, or config dict
        """
        # Convert config to FOClientConfig if needed
        if isinstance(config, str):
            config = FOClientConfig(base_url=config)
        elif isinstance(config, dict):
            config = FOClientConfig(**config)

        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.auth_manager = AuthenticationManager(config)
        self.session_manager = SessionManager(config, self.auth_manager)

        # Initialize new metadata cache and sync components
        self.metadata_cache = None
        self.sync_manager = None
        self._metadata_initialized = False
        self._background_sync_task = None

        # Initialize operations
        self.metadata_url = f"{config.base_url.rstrip('/')}/Metadata"
        self.crud_ops = CrudOperations(self.session_manager, config.base_url)

        # Initialize label operations - will be updated when metadata cache v2 is initialized
        self.label_ops = LabelOperations(self.session_manager, self.metadata_url, None)
        self.metadata_api_ops = MetadataAPIOperations(
            self.session_manager, self.metadata_url, self.label_ops
        )

    async def close(self):
        """Close the client session"""
        # Cancel background sync task if running
        if self._background_sync_task and not self._background_sync_task.done():
            self._background_sync_task.cancel()
            try:
                await self._background_sync_task
            except asyncio.CancelledError:
                pass

        await self.session_manager.close()

    async def _ensure_metadata_initialized(self):
        """Ensure metadata cache and sync manager are initialized"""
        if not self._metadata_initialized and self.config.enable_metadata_cache:
            try:

                cache_dir = Path(self.config.metadata_cache_dir)

                # Initialize metadata cache v2
                self.metadata_cache = MetadataCacheV2(
                    cache_dir, self.config.base_url, self.metadata_api_ops
                )
                # Initialize label operations v2 with cache support
                self.label_ops.set_label_cache(self.metadata_cache)

                await self.metadata_cache.initialize()

                # Initialize sync manager v2
                self.sync_manager = SmartSyncManagerV2(
                    self.metadata_cache, self.metadata_api_ops
                )

                self._metadata_initialized = True
                self.logger.debug("Metadata cache v2 with label caching initialized")

            except Exception as e:
                self.logger.warning(f"Failed to initialize metadata cache v2: {e}")
                # Continue without metadata cache
                self.config.enable_metadata_cache = False

    async def _trigger_background_sync_if_needed(self):
        """Trigger background sync if metadata is stale or missing"""
        if not self.config.enable_metadata_cache or not self._metadata_initialized:
            return

        try:
            # Check if we need to sync using the new v2 API
            sync_needed, global_version_id = (
                await self.metadata_cache.check_version_and_sync(self.metadata_api_ops)
            )

            if sync_needed and global_version_id:
                # Only start sync if not already running
                if not self._background_sync_task or self._background_sync_task.done():
                    self._background_sync_task = asyncio.create_task(
                        self._background_sync_worker(global_version_id)
                    )
                    self.logger.debug("Background metadata sync triggered")
        except Exception as e:
            self.logger.warning(f"Failed to check sync status: {e}")

    async def _background_sync_worker(self, global_version_id: int):
        """Background worker for metadata synchronization"""
        try:
            self.logger.info(
                f"Starting background metadata sync for version {global_version_id}"
            )

            # Use self as the fo_client for sync - SmartSyncManagerV2 expects a client with metadata API operations
            result = await self.sync_manager.sync_metadata(global_version_id)

            if result.success:
                self.logger.info(
                    f"Background sync completed: "
                    f"{result.entity_count} entities, "
                    f"{result.enumeration_count} enumerations, "
                    f"{result.duration_ms:.2f}ms"
                )
            else:
                self.logger.warning(f"Background sync failed: {result.error}")

        except Exception as e:
            self.logger.error(f"Background sync error: {e}")
            # Don't re-raise to avoid breaking the background task

    async def _get_from_cache_first(
        self,
        cache_method,
        fallback_method,
        *args,
        use_cache_first: Optional[bool] = None,
        **kwargs,
    ):
        """Helper method to implement cache-first pattern

        Args:
            cache_method: Method to call on cache
            fallback_method: Method to call as fallback
            use_cache_first: Override config setting
            *args: Arguments to pass to methods
            **kwargs: Keyword arguments to pass to methods
        """
        # Use provided parameter or config default
        if use_cache_first is None:
            use_cache_first = self.config.use_cache_first

        # If cache-first is disabled, go straight to fallback
        if not use_cache_first or not self.config.enable_metadata_cache:
            return (
                await fallback_method(*args, **kwargs)
                if asyncio.iscoroutinefunction(fallback_method)
                else fallback_method(*args, **kwargs)
            )

        # Ensure metadata is initialized
        await self._ensure_metadata_initialized()

        if not self._metadata_initialized:
            # Cache not available, use fallback
            return (
                await fallback_method(*args, **kwargs)
                if asyncio.iscoroutinefunction(fallback_method)
                else fallback_method(*args, **kwargs)
            )

        try:
            # Try cache first
            result = (
                await cache_method(*args, **kwargs)
                if asyncio.iscoroutinefunction(cache_method)
                else cache_method(*args, **kwargs)
            )

            # If cache returns empty result, trigger sync and try fallback
            if not result or (isinstance(result, list) and len(result) == 0):
                await self._trigger_background_sync_if_needed()
                return (
                    await fallback_method(*args, **kwargs)
                    if asyncio.iscoroutinefunction(fallback_method)
                    else fallback_method(*args, **kwargs)
                )

            return result

        except Exception as e:
            self.logger.warning(f"Cache lookup failed, using fallback: {e}")
            # Trigger sync if cache failed
            await self._trigger_background_sync_if_needed()
            return (
                await fallback_method(*args, **kwargs)
                if asyncio.iscoroutinefunction(fallback_method)
                else fallback_method(*args, **kwargs)
            )

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    # Connection and Testing Methods

    async def test_connection(self) -> bool:
        """Test connection to F&O

        Returns:
            True if connection is successful
        """
        try:
            session = await self.session_manager.get_session()
            url = f"{self.config.base_url}/data"

            async with session.get(url) as response:
                return response.status == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    async def test_metadata_connection(self) -> bool:
        """Test connection to the Metadata endpoint

        Returns:
            True if metadata endpoint is accessible
        """
        try:
            session = await self.session_manager.get_session()

            # Try the PublicEntities endpoint first as it's more reliable
            url = f"{self.metadata_url}/PublicEntities"
            params = {"$top": 1}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return True

        except Exception as e:
            print(f"Metadata connection test failed: {e}")
            return False

    # Metadata Operations

    async def download_metadata(self, force_refresh: bool = False) -> bool:
        """Download/sync metadata using new sync manager v2

        Args:
            force_refresh: Force full synchronization even if cache is fresh

        Returns:
            True if successful
        """
        # Ensure metadata components are initialized
        await self._ensure_metadata_initialized()

        if not self._metadata_initialized:
            self.logger.error("Metadata cache v2 could not be initialized")
            return False

        try:
            self.logger.info("Starting metadata synchronization")

            # Check version and determine if sync is needed
            sync_needed, global_version_id = (
                await self.metadata_cache.check_version_and_sync(self.metadata_api_ops)
            )

            if not sync_needed and not force_refresh:
                self.logger.info("Metadata is up-to-date, no sync needed")
                return True

            if not global_version_id:
                self.logger.error("Could not determine environment version")
                return False

            # Perform sync using the new sync manager
            from .models import SyncStrategy

            strategy = SyncStrategy.FULL if force_refresh else SyncStrategy.INCREMENTAL

            result = await self.sync_manager.sync_metadata(global_version_id, strategy)

            if result.success:
                self.logger.info(
                    f"Metadata sync completed: "
                    f"{result.entity_count} entities, "
                    f"{result.enumeration_count} enumerations, "
                    f"{result.action_count} actions, "
                    f"{result.duration_ms:.2f}ms"
                )
                return True
            else:
                self.logger.error(f"Metadata sync failed: {result.error}")
                return False

        except Exception as e:
            self.logger.error(f"Error during metadata sync: {e}")
            return False

    async def search_entities(
        self, pattern: str = "", use_cache_first: Optional[bool] = True
    ) -> List[DataEntityInfo]:
        """Search entities by name pattern with cache-first approach

        Args:
            pattern: Search pattern (regex supported)
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            List of matching entity names
        """

        async def cache_search():
            if self.metadata_cache:
                # Convert regex pattern to SQL LIKE pattern for v2 cache
                if pattern:
                    # Simple conversion: replace * with % for SQL LIKE
                    sql_pattern = (
                        pattern.replace("*", "%")
                        .replace("?", "")
                        .replace(".", "")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    # If no wildcards, add % at both ends for substring search
                    if "%" not in sql_pattern and "_" not in sql_pattern:
                        sql_pattern = f"%{sql_pattern}%"
                else:
                    sql_pattern = None

                return await self.metadata_cache.get_data_entities(
                    name_pattern=sql_pattern
                )
            return []

        async def fallback_search():
            # Use metadata API operations as fallback
            return await self.metadata_api_ops.search_data_entities(pattern)

        return await self._get_from_cache_first(
            cache_search,
            fallback_search,
            use_cache_first=use_cache_first or self.config.use_cache_first,
        )

    async def get_entity_info(
        self, entity_name: str, use_cache_first: Optional[bool] = True
    ) -> Optional[PublicEntityInfo]:
        """Get detailed entity information with cache-first approach

        Args:
            entity_name: Name of the entity
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            PublicEntityInfo object or None if not found
        """
        return await self.get_public_entity_info(
            entity_name, use_cache_first=use_cache_first
        )

    async def search_actions(
        self,
        pattern: str = "",
        entity_name: Optional[str] = None,
        binding_kind: Optional[str] = None,
        use_cache_first: Optional[bool] = True,
    ) -> List[ActionInfo]:
        """Search actions by name pattern and/or entity with cache-first approach

        Args:
            pattern: Search pattern for action name (regex supported)
            entity_name: Filter actions that are bound to a specific entity
            binding_kind: Filter by binding type (Unbound, BoundToEntitySet, BoundToEntityInstance)
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            List of matching ActionInfo objects with full details
        """
        await self._ensure_metadata_initialized()

        async def cache_search():
            # TODO: v2 cache doesn't have action search yet - will be implemented in future phase
            # For now, always return empty to force fallback to API
            return []

        async def fallback_search():
            # Actions are not directly available through metadata API
            # They are part of entity definitions
            # Return empty list for backward compatibility
            return []

        actions = await self._get_from_cache_first(
            cache_search,
            fallback_search,
            use_cache_first=use_cache_first or self.config.use_cache_first,
        )

        return await resolve_labels_generic(actions, self.label_ops)

    async def get_action_info(
        self,
        action_name: str,
        entity_name: Optional[str] = None,
        use_cache_first: Optional[bool] = None,
    ) -> Optional[ActionInfo]:
        """Get detailed action information with cache-first approach

        Args:
            action_name: Name of the action
            entity_name: Optional entity name for bound actions
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            ActionInfo object or None if not found
        """

        async def cache_lookup():
            # TODO: v2 cache doesn't have action lookup yet - will be implemented in future phase
            # For now, always return None to force fallback to API
            return None

        async def fallback_lookup():
            # Actions are not directly available through metadata API
            # They are part of entity definitions
            # Return None for backward compatibility
            return None

        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup, use_cache_first=use_cache_first
        )

    # CRUD Operations

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
        return await self.crud_ops.get_entities(entity_name, options)

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
        return await self.crud_ops.get_entity(entity_name, key, options)

    async def get_entity_by_key(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        select: Optional[List[str]] = None,
        expand: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get single entity by key with optional field selection and expansion

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            select: Optional list of fields to select
            expand: Optional list of navigation properties to expand

        Returns:
            Entity data or None if not found
        """
        try:
            options = (
                QueryOptions(select=select, expand=expand) if select or expand else None
            )
            return await self.crud_ops.get_entity(entity_name, key, options)
        except Exception as e:
            # If the entity is not found, return None instead of raising exception
            if "404" in str(e):
                return None
            raise

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
        return await self.crud_ops.create_entity(entity_name, data)

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
        return await self.crud_ops.update_entity(entity_name, key, data, method)

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
        return await self.crud_ops.delete_entity(entity_name, key)

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
        return await self.crud_ops.call_action(
            action_name, parameters, entity_name, entity_key
        )

    # Label Operations

    async def get_label_text(
        self, label_id: str, language: str = "en-US"
    ) -> Optional[str]:
        """Get actual label text for a specific label ID

        Args:
            label_id: Label ID (e.g., "@SYS13342")
            language: Language code (e.g., "en-US")

        Returns:
            Label text or None if not found
        """
        return await self.label_ops.get_label_text(label_id, language)

    async def get_labels_batch(
        self, label_ids: List[str], language: str = "en-US"
    ) -> Dict[str, str]:
        """Get multiple labels in a single request

        Args:
            label_ids: List of label IDs
            language: Language code

        Returns:
            Dictionary mapping label ID to label text
        """
        return await self.label_ops.get_labels_batch(label_ids, language)

    # Enhanced Entity Operations with Labels

    async def get_entity_info_with_labels(
        self, entity_name: str, language: str = "en-US"
    ) -> Optional[PublicEntityInfo]:
        """Get entity metadata with resolved label text from Metadata API

        Args:
            entity_name: Name of the entity
            language: Language code for label resolution

        Returns:
            PublicEntityInfo object with resolved labels
        """
        # Use the existing get_public_entity_info method which already handles labels
        return await self.get_public_entity_info(entity_name, language=language)

    # Metadata API Operations

    async def get_data_entities(
        self, options: Optional[QueryOptions] = None
    ) -> List[DataEntityInfo]:
        """Get data entities - updated to return list for v2 sync compatibility

        Args:
            options: OData query options (ignored for now)

        Returns:
            List of DataEntityInfo objects
        """
        # For sync manager compatibility, return list of DataEntityInfo objects
        return await self.metadata_api_ops.search_data_entities("")  # Get all entities

    async def get_data_entities_raw(
        self, options: Optional[QueryOptions] = None
    ) -> Dict[str, Any]:
        """Get data entities raw response from DataEntities metadata endpoint

        Args:
            options: OData query options

        Returns:
            Response containing data entities
        """
        return await self.metadata_api_ops.get_data_entities(options)

    async def get_data_entities_list(self) -> List[DataEntityInfo]:
        """Get data entities as list - compatibility method for SmartSyncManagerV2

        Returns:
            List of DataEntityInfo objects
        """
        return await self.metadata_api_ops.search_data_entities("")  # Get all entities

    async def search_data_entities(
        self,
        pattern: str = "",
        entity_category: Optional[str] = None,
        data_service_enabled: Optional[bool] = None,
        data_management_enabled: Optional[bool] = None,
        is_read_only: Optional[bool] = None,
        use_cache_first: Optional[bool] = True,
    ) -> List[DataEntityInfo]:
        """Search data entities with filtering and cache-first approach

        Args:
            pattern: Search pattern for entity name (regex supported)
            entity_category: Filter by entity category (e.g., 'Master', 'Transaction')
            data_service_enabled: Filter by data service enabled status
            data_management_enabled: Filter by data management enabled status
            is_read_only: Filter by read-only status
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            List of matching data entities
        """

        async def cache_search():
            if self.metadata_cache:
                # Convert regex pattern to SQL LIKE pattern for v2 cache
                sql_pattern = None
                if pattern:
                    # Simple conversion: replace * with % for SQL LIKE
                    sql_pattern = pattern.replace("*", "%")
                    # If no wildcards, add % at both ends for substring search
                    if "%" not in sql_pattern and "_" not in sql_pattern:
                        sql_pattern = f"%{sql_pattern}%"

                return await self.metadata_cache.get_data_entities(
                    name_pattern=sql_pattern,
                    entity_category=entity_category,
                    data_service_enabled=data_service_enabled,
                    # Note: v2 cache doesn't support data_management_enabled or is_read_only filters yet
                )
            return []

        async def fallback_search():
            return await self.metadata_api_ops.search_data_entities(
                pattern,
                entity_category,
                data_service_enabled,
                data_management_enabled,
                is_read_only,
            )

        entities = await self._get_from_cache_first(
            cache_search,
            fallback_search,
            use_cache_first=use_cache_first or self.config.use_cache_first,
        )

        if self.metadata_cache:
            entities = await resolve_labels_generic(entities, self.label_ops)

        return entities

    async def get_data_entity_info(
        self,
        entity_name: str,
        resolve_labels: bool = True,
        language: str = "en-US",
        use_cache_first: Optional[bool] = None,
    ) -> Optional[DataEntityInfo]:
        """Get detailed information about a specific data entity with cache-first approach

        Args:
            entity_name: Name of the data entity
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            DataEntityInfo object or None if not found
        """

        async def cache_lookup():
            if self.metadata_cache:
                # Get all entities and filter by name (since v2 cache doesn't have get_single method yet)
                entities = await self.metadata_cache.get_data_entities(
                    name_pattern=entity_name
                )
                for entity in entities:
                    if entity.name == entity_name:
                        return entity
            return None

        async def fallback_lookup():
            return await self.metadata_api_ops.get_data_entity_info(
                entity_name, resolve_labels, language
            )

        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup, use_cache_first=use_cache_first
        )

    async def get_public_entities(
        self, options: Optional[QueryOptions] = None
    ) -> Dict[str, Any]:
        """Get public entities from PublicEntities metadata endpoint

        Args:
            options: OData query options

        Returns:
            Response containing public entities
        """
        return await self.metadata_api_ops.get_public_entities(options)

    async def search_public_entities(
        self,
        pattern: str = "",
        is_read_only: Optional[bool] = None,
        configuration_enabled: Optional[bool] = None,
        use_cache_first: Optional[bool] = None,
    ) -> List[PublicEntityInfo]:
        """Search public entities with filtering and cache-first approach

        Args:
            pattern: Search pattern for entity name (regex supported)
            is_read_only: Filter by read-only status
            configuration_enabled: Filter by configuration enabled status
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            List of matching public entities (without detailed properties)
        """

        async def cache_search():
            # TODO: v2 cache doesn't have public entity search yet - will be implemented in future phase
            # For now, always return empty to force fallback to API
            return []

        async def fallback_search():
            return await self.metadata_api_ops.search_public_entities(
                pattern, is_read_only, configuration_enabled
            )

        return await self._get_from_cache_first(
            cache_search, fallback_search, use_cache_first=use_cache_first
        )

    async def get_public_entity_info(
        self,
        entity_name: str,
        resolve_labels: bool = True,
        language: str = "en-US",
        use_cache_first: Optional[bool] = True,
    ) -> Optional[PublicEntityInfo]:
        """Get detailed information about a specific public entity with cache-first approach

        Args:
            entity_name: Name of the public entity
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            PublicEntityInfo object with full details or None if not found
        """

        async def cache_lookup():
            if self.metadata_cache:
                return await self.metadata_cache.get_public_entity_schema(entity_name)
            return None

        async def fallback_lookup():
            return await self.metadata_api_ops.get_public_entity_info(
                entity_name, resolve_labels, language
            )

        entity = await self._get_from_cache_first(
            cache_lookup,
            fallback_lookup,
            use_cache_first=use_cache_first or self.config.use_cache_first,
        )

        return await resolve_labels_generic(entity, self.label_ops)

    async def get_all_public_entities_with_details(
        self, resolve_labels: bool = False, language: str = "en-US"
    ) -> List[PublicEntityInfo]:
        """Get all public entities with full details in a single optimized call

        This method uses an optimized approach that gets all entity details in one API call
        instead of making individual requests for each entity.

        Args:
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            List of PublicEntityInfo objects with complete details
        """
        return await self.metadata_api_ops.get_all_public_entities_with_details(
            resolve_labels, language
        )

    async def get_public_enumerations(
        self, options: Optional[QueryOptions] = None
    ) -> List[EnumerationInfo]:
        """Get public enumerations from PublicEnumerations metadata endpoint

        Args:
            options: OData query options

        Returns:
            Response containing public enumerations
        """
        self._ensure_metadata_initialized()

        return await self.metadata_api_ops.get_public_enumerations(options)

    async def search_public_enumerations(
        self, pattern: str = "", use_cache_first: Optional[bool] = True
    ) -> List[EnumerationInfo]:
        """Search public enumerations with filtering and cache-first approach

        Args:
            pattern: Search pattern for enumeration name (regex supported)
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            List of matching enumerations (without detailed members)
        """

        async def cache_search():
            # TODO: v2 cache doesn't have enumeration search yet - will be implemented in future phase
            # For now, always return empty to force fallback to API
            return []

        async def fallback_search():
            return await self.metadata_api_ops.search_public_enumerations(pattern)

        enums = await self._get_from_cache_first(
            cache_search,
            fallback_search,
            use_cache_first=use_cache_first or self.config.use_cache_first,
        )

        return await resolve_labels_generic(enums, self.label_ops)

    async def get_public_enumeration_info(
        self,
        enumeration_name: str,
        resolve_labels: bool = True,
        language: str = "en-US",
        use_cache_first: Optional[bool] = True,
    ) -> Optional[EnumerationInfo]:
        """Get detailed information about a specific public enumeration with cache-first approach

        Args:
            enumeration_name: Name of the enumeration
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            use_cache_first: Override config setting for cache-first behavior

        Returns:
            EnumerationInfo object with full details or None if not found
        """

        async def cache_lookup():
            if self.metadata_cache:
                return await self.metadata_cache.get_enumeration_info(enumeration_name)
            return None

        async def fallback_lookup():
            return await self.metadata_api_ops.get_public_enumeration_info(
                enumeration_name, resolve_labels, language
            )

        enum = await self._get_from_cache_first(
            cache_lookup,
            fallback_lookup,
            use_cache_first=use_cache_first or self.config.use_cache_first,
        )
        return await resolve_labels_generic(enum, self.label_ops) if enum else None

    async def get_all_public_enumerations_with_details(
        self, resolve_labels: bool = False, language: str = "en-US"
    ) -> List[EnumerationInfo]:
        """Get all public enumerations with full details in a single optimized call

        This method uses an optimized approach that gets all enumeration details in one API call
        instead of making individual requests for each enumeration.

        Args:
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            List of EnumerationInfo objects with complete details
        """
        return await self.metadata_api_ops.get_all_public_enumerations_with_details(
            resolve_labels, language
        )

    # Utility Methods

    def get_label_cache_info(self) -> Dict[str, Any]:
        """Get label cache information and statistics

        Returns:
            Dictionary with label cache information
        """
        if not self.config.enable_metadata_cache or not self._metadata_initialized:
            return {
                "enabled": False,
                "cache_type": "none",
                "message": "Metadata cache not enabled or not initialized",
            }

        if hasattr(self.metadata_cache, "get_label_cache_statistics"):
            # Using v2 cache with label support
            try:
                import asyncio

                # Get the current event loop or create a new one
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    # If we're in an async context, we can't run async code synchronously
                    return {
                        "enabled": True,
                        "cache_type": "metadata_v2",
                        "message": "Label caching enabled with v2 cache (statistics available via async method)",
                    }
                else:
                    # If we're not in an async context, we can get the statistics
                    stats = loop.run_until_complete(
                        self.metadata_cache.get_label_cache_statistics()
                    )
                    return {
                        "enabled": True,
                        "cache_type": "metadata_v2",
                        "statistics": stats,
                    }
            except Exception as e:
                return {
                    "enabled": True,
                    "cache_type": "metadata_v2",
                    "error": f"Error getting statistics: {e}",
                }
        else:
            # Legacy cache or no label caching
            return {
                "enabled": False,
                "cache_type": "legacy" if self.metadata_cache else "none",
                "message": "Label caching not supported by current cache implementation",
            }

    async def get_label_cache_info_async(self) -> Dict[str, Any]:
        """Get label cache information and statistics (async version)

        Returns:
            Dictionary with label cache information
        """
        if not self.config.enable_metadata_cache or not self._metadata_initialized:
            return {
                "enabled": False,
                "cache_type": "none",
                "message": "Metadata cache not enabled or not initialized",
            }

        if hasattr(self.metadata_cache, "get_label_cache_statistics"):
            # Using v2 cache with label support
            try:
                stats = await self.metadata_cache.get_label_cache_statistics()
                return {
                    "enabled": True,
                    "cache_type": "metadata_v2",
                    "statistics": stats,
                }
            except Exception as e:
                return {
                    "enabled": True,
                    "cache_type": "metadata_v2",
                    "error": f"Error getting statistics: {e}",
                }
        else:
            # Legacy cache or no label caching
            return {
                "enabled": False,
                "cache_type": "legacy" if self.metadata_cache else "none",
                "message": "Label caching not supported by current cache implementation",
            }

    def get_entity_url(
        self, entity_name: str, key: Optional[Union[str, Dict[str, Any]]] = None
    ) -> str:
        """Get entity URL

        Args:
            entity_name: Entity set name
            key: Optional entity key (string for simple keys, dict for composite keys)

        Returns:
            Complete entity URL
        """
        return QueryBuilder.build_entity_url(self.config.base_url, entity_name, key)

    def get_action_url(
        self,
        action_name: str,
        entity_name: Optional[str] = None,
        entity_key: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> str:
        """Get action URL

        Args:
            action_name: Action name
            entity_name: Optional entity name for bound actions
            entity_key: Optional entity key for bound actions (string for simple keys, dict for composite keys)

        Returns:
            Complete action URL
        """
        return QueryBuilder.build_action_url(
            self.config.base_url, action_name, entity_name, entity_key
        )

    async def get_metadata_info(self) -> Dict[str, Any]:
        """Get metadata cache information

        Returns:
            Dictionary with metadata information
        """
        # Start with basic info
        info = {
            "cache_directory": self.config.metadata_cache_dir,
            "cache_version": "2.0",
            "statistics": None,
        }

        await self._ensure_metadata_initialized()

        # Add new metadata cache v2 info if available
        if self.metadata_cache:
            try:
                stats = await self.metadata_cache.get_cache_statistics()
                cache_info = {
                    "advanced_cache_enabled": True,
                    "cache_v2_enabled": True,
                    "cache_initialized": self._metadata_initialized,
                    "sync_manager_available": self.sync_manager is not None,
                    "background_sync_running": (
                        (
                            self._background_sync_task
                            and not self._background_sync_task.done()
                        )
                        if self._background_sync_task
                        else False
                    ),
                    "statistics": stats,
                }
                info.update(cache_info)
            except Exception as e:
                self.logger.warning(f"Error getting cache v2 info: {e}")
                # Even on error, include basic cache info
                info.update(
                    {
                        "advanced_cache_enabled": True,
                        "cache_v2_enabled": True,
                        "cache_initialized": self._metadata_initialized,
                        "sync_manager_available": False,
                        "background_sync_running": False,
                    }
                )
        else:
            info.update(
                {
                    "advanced_cache_enabled": False,
                    "cache_v2_enabled": False,
                    "cache_initialized": False,
                    "sync_manager_available": False,
                    "background_sync_running": False,
                }
            )

        return info

    # Application Version Operations

    async def get_entity_schema(self, entity_name: str) -> Optional[PublicEntityInfo]:
        """Get entity schema - compatibility method for SmartSyncManagerV2

        Args:
            entity_name: Name of the public entity

        Returns:
            PublicEntityInfo object with schema details or None if not found
        """
        return await self.metadata_api_ops.get_public_entity_info(
            entity_name, resolve_labels=False
        )

    async def get_application_version(self) -> str:
        """Get the current application version of the D365 F&O environment

        This method calls the GetApplicationVersion action bound to the DataManagementEntities
        collection to retrieve the application version information.

        Returns:
            str: The application version string

        Raises:
            FOClientError: If the action call fails
        """
        try:
            return await self.metadata_api_ops.get_application_version()

        except Exception as e:
            raise FOClientError(f"Failed to get application version: {e}")

    async def get_platform_build_version(self) -> str:
        """Get the current platform build version of the D365 F&O environment

        This method calls the GetPlatformBuildVersion action bound to the DataManagementEntities
        collection to retrieve the platform build version information.

        Returns:
            str: The platform build version string

        Raises:
            FOClientError: If the action call fails
        """
        try:
            return await self.metadata_api_ops.get_platform_build_version()

        except Exception as e:
            raise FOClientError(f"Failed to get platform build version: {e}")

    async def get_application_build_version(self) -> str:
        """Get the current application build version of the D365 F&O environment

        This method calls the GetApplicationBuildVersion action bound to the DataManagementEntities
        collection to retrieve the application build version information.

        Returns:
            str: The application build version string

        Raises:
            FOClientError: If the action call fails
        """
        try:
            result = await self.call_action(
                "GetApplicationBuildVersion",
                parameters=None,
                entity_name="DataManagementEntities",
            )

            # The action returns a simple string value
            if isinstance(result, str):
                return result
            elif isinstance(result, dict) and "value" in result:
                return str(result["value"])
            else:
                return str(result) if result is not None else ""

        except Exception as e:
            raise FOClientError(f"Failed to get application build version: {e}")

    async def get_installed_modules(self) -> List[str]:
        """Get the list of installed modules in the D365 F&O environment

        This method calls the GetInstalledModules action bound to the DataManagementEntities
        collection to retrieve the list of installed modules with their details.

        Returns:
            List[str]: List of module strings in format:
                "Name: {name} | Version: {version} | Module: {module_id} | Publisher: {publisher} | DisplayName: {display_name}"

        Raises:
            FOClientError: If the action call fails
        """
        try:
            return await self.metadata_api_ops.get_installed_modules()

        except Exception as e:
            raise FOClientError(f"Failed to get installed modules: {e}")

    async def query_data_management_entities(
        self,
        category_filters: Optional[List[int]] = None,
        config_key_filters: Optional[List[str]] = None,
        country_region_code_filters: Optional[List[str]] = None,
        is_shared_filters: Optional[List[int]] = None,
        module_filters: Optional[List[str]] = None,
        tag_filters: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query data management entities using the OData query action

        This method calls the 'query' action bound to the DataManagementEntities
        collection to retrieve filtered data management entities based on various criteria.

        Args:
            category_filters: Filter by entity category IDs (integers - e.g., [0, 1, 2])
                             0=Master, 1=Configuration, 2=Transaction, 3=Reference, 4=Document, 5=Parameters
            config_key_filters: Filter by configuration keys (strings)
            country_region_code_filters: Filter by country/region codes (strings)
            is_shared_filters: Filter by shared status (integers - 0=No, 1=Yes)
            module_filters: Filter by module names (strings)
            tag_filters: Filter by tags (strings)

        Returns:
            List[Dict[str, Any]]: List of data management entity information

        Raises:
            FOClientError: If the action call fails

        Note:
            All parameters must be passed as arrays/lists since they are collection parameters in the OData action.
            The categoryFilters and isSharedFilters parameters expect integers, while other filters expect strings.
            To query all entities, use empty lists [] for required parameters or omit optional ones.

            Category enum values:
            - 0 = Master
            - 1 = Configuration
            - 2 = Transaction
            - 3 = Reference
            - 4 = Document
            - 5 = Parameters

            IsShared enum values:
            - 0 = No
            - 1 = Yes
        """
        try:
            # Prepare parameters for the query action
            # All parameters are collections (arrays) as per the OData action definition
            parameters = {}

            # Required parameters with default empty arrays if not provided
            parameters["categoryFilters"] = (
                category_filters if category_filters is not None else []
            )
            parameters["isSharedFilters"] = (
                is_shared_filters if is_shared_filters is not None else []
            )

            # Optional collection parameters
            if config_key_filters is not None:
                parameters["configKeyFilters"] = config_key_filters
            else:
                parameters["configKeyFilters"] = []

            if country_region_code_filters is not None:
                parameters["countryRegionCodeFilters"] = country_region_code_filters
            else:
                parameters["countryRegionCodeFilters"] = []

            if module_filters is not None:
                parameters["moduleFilters"] = module_filters
            else:
                parameters["moduleFilters"] = []

            if tag_filters is not None:
                parameters["tagFilters"] = tag_filters
            else:
                parameters["tagFilters"] = []

            # Call the query action bound to DataManagementEntities
            result = await self.call_action(
                "query", parameters=parameters, entity_name="DataManagementEntities"
            )

            # The action returns a collection of DataManagementEntity objects
            if isinstance(result, dict):
                if "value" in result:
                    # Standard OData response format
                    return result["value"]
                elif "@odata.context" in result:
                    # Response might be the entities directly
                    entities = []
                    for key, value in result.items():
                        if not key.startswith("@"):
                            entities.append(value)
                    return entities
                else:
                    # Response is the result directly
                    return [result] if result else []
            elif isinstance(result, list):
                # Direct list of entities
                return result
            else:
                # Unexpected format, return empty list
                self.logger.warning(f"Unexpected query response format: {type(result)}")
                return []

        except Exception as e:
            raise FOClientError(f"Failed to query data management entities: {e}")

    async def query_data_management_entities_by_category(
        self,
        categories: List[str],
        is_shared: Optional[bool] = None,
        modules: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query data management entities by category names (convenience method)

        This is a convenience method that converts category names to their integer enum values
        and calls the main query_data_management_entities method.

        Args:
            categories: List of category names (e.g., ['Master', 'Transaction'])
                       Valid values: Master, Configuration, Transaction, Reference, Document, Parameters
            is_shared: Optional boolean filter for shared status (True/False)
            modules: Optional list of module names to filter by

        Returns:
            List[Dict[str, Any]]: List of data management entity information

        Raises:
            FOClientError: If the action call fails
            ValueError: If invalid category names are provided
        """
        # Mapping of category names to enum values
        category_map = {
            "Master": 0,
            "Configuration": 1,
            "Transaction": 2,
            "Reference": 3,
            "Document": 4,
            "Parameters": 5,
        }

        # Convert category names to enum values
        category_filters = []
        for category in categories:
            if category not in category_map:
                raise ValueError(
                    f"Invalid category '{category}'. Valid categories: {list(category_map.keys())}"
                )
            category_filters.append(category_map[category])

        # Convert is_shared boolean to enum value
        is_shared_filters = None
        if is_shared is not None:
            is_shared_filters = [1 if is_shared else 0]

        # Call the main query method with converted values
        return await self.query_data_management_entities(
            category_filters=category_filters,
            is_shared_filters=is_shared_filters,
            module_filters=modules,
        )


# Convenience function for creating client
def create_client(base_url: str, **kwargs) -> FOClient:
    """Create F&O client with convenience parameters

    Args:
        base_url: F&O base URL
        **kwargs: Additional configuration parameters

    Returns:
        Configured FOClient instance
    """
    config = FOClientConfig(base_url=base_url, **kwargs)
    return FOClient(config)
