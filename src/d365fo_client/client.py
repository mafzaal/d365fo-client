"""Main F&O client implementation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from d365fo_client.utils import get_default_cache_directory

from .auth import AuthenticationManager
from .crud import CrudOperations
from .exceptions import FOClientError
from .labels import LabelOperations, resolve_labels_generic
from .metadata_api import MetadataAPIOperations
from .metadata_v2 import MetadataCacheV2, SmartSyncManagerV2
from .metadata_v2.sync_session_manager import SyncSessionManager
from .models import (
    ActionInfo,
    DataEntityInfo,
    EnumerationInfo,
    FOClientConfig,
    JsonServiceRequest,
    JsonServiceResponse,
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
        self._sync_session_manager = None
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

    async def initialize_metadata(self):
        await self._ensure_metadata_initialized()

    async def _ensure_metadata_initialized(self):
        """Ensure metadata cache and sync manager are initialized"""
        if not self._metadata_initialized and self.config.enable_metadata_cache:
            try:

                cache_dir = Path(
                    self.config.metadata_cache_dir or get_default_cache_directory()
                )

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

                # Initialize sync message with session
                self._sync_session_manager = SyncSessionManager(
                    self.metadata_cache, self.metadata_api_ops
                )

                self._metadata_initialized = True
                self.logger.debug("Metadata cache v2 with label caching initialized")

            except Exception as e:
                self.logger.warning(f"Failed to initialize metadata cache v2: {e}")
                # Continue without metadata cache
                self.config.enable_metadata_cache = False

    async def _trigger_background_sync_if_needed(self):
        """Trigger background sync if metadata is stale or missing (non-blocking)"""
        if not self.config.enable_metadata_cache or not self._metadata_initialized:
            return

        # Don't trigger sync if already running
        if self._is_background_sync_running():
            return

        try:
            # Check if we need to sync using the new v2 API
            # This should be a quick check, not actual sync work
            sync_needed, global_version_id = (
                await self.metadata_cache.check_version_and_sync(self.metadata_api_ops)
            )

            if sync_needed and global_version_id:
                # Start sync in background without awaiting it
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

            await self.sync_session_manager.start_sync_session(
                global_version_id=global_version_id, initiated_by="background_task"
            )

        except Exception as e:
            self.logger.error(f"Background sync error: {e}")
            # Don't re-raise to avoid breaking the background task

    def _is_background_sync_running(self) -> bool:
        """Check if background sync task is currently running

        Returns:
            True if background sync is actively running, False otherwise
        """
        return (
            self._background_sync_task is not None
            and not self._background_sync_task.done()
        )

    @property
    def sync_session_manager(self) -> SyncSessionManager:
        """Get sync session manager (lazy initialization).

        Returns:
            SyncSessionManager instance for enhanced sync progress tracking

        Raises:
            RuntimeError: If metadata cache is not initialized
        """
        if self._sync_session_manager is None:
            if not self.metadata_cache:
                raise RuntimeError(
                    "Metadata cache must be initialized before accessing sync session manager"
                )

            self._sync_session_manager = SyncSessionManager(
                cache=self.metadata_cache, metadata_api=self.metadata_api_ops
            )

        return self._sync_session_manager

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

        # If cache-first is disabled, metadata cache is disabled, or background sync is running, go straight to fallback
        if (
            not use_cache_first
            or not self.config.enable_metadata_cache
            or self._is_background_sync_running()
        ):
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
                # Trigger background sync without awaiting (fire-and-forget)
                asyncio.create_task(self._trigger_background_sync_if_needed())
                return (
                    await fallback_method(*args, **kwargs)
                    if asyncio.iscoroutinefunction(fallback_method)
                    else fallback_method(*args, **kwargs)
                )

            return result

        except Exception as e:
            self.logger.warning(f"Cache lookup failed, using fallback: {e}")
            # Trigger sync if cache failed (fire-and-forget)
            asyncio.create_task(self._trigger_background_sync_if_needed())
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
            from .sync_models import SyncStrategy

            strategy = SyncStrategy.FULL if force_refresh else SyncStrategy.INCREMENTAL

            result = await self.sync_manager.sync_metadata(global_version_id, strategy)

            if result.success:
                self.logger.info(
                    f"Metadata sync completed: "
                    f"{result.entities_synced} entities, "
                    f"{result.enumerations_synced} enumerations, "
                    f"{result.actions_synced} actions, "
                    f"{result.duration_ms:.2f}ms"
                )
                return True
            else:
                error_msg = result.errors[0] if result.errors else "Unknown error"
                self.logger.error(f"Metadata sync failed: {error_msg}")
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
            use_cache_first=use_cache_first,
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
            # Use the v2 cache action search functionality
            if not self.metadata_cache:
                return []

            # Convert regex pattern to SQL LIKE pattern for cache
            cache_pattern = None
            if pattern:
                # Convert simple regex to SQL LIKE pattern
                cache_pattern = pattern.replace(".*", "%").replace(".", "_")
                if not cache_pattern.startswith("%") and not cache_pattern.endswith(
                    "%"
                ):
                    cache_pattern = f"%{cache_pattern}%"

            return await self.metadata_cache.search_actions(
                pattern=cache_pattern,
                entity_name=entity_name,
                binding_kind=binding_kind,
            )

        async def fallback_search():
            # Use the new metadata API operations for action search
            return await self.metadata_api_ops.search_actions(
                pattern, entity_name, binding_kind
            )

        actions = await self._get_from_cache_first(
            cache_search,
            fallback_search,
            use_cache_first=use_cache_first,
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
            # Use the v2 cache action lookup functionality
            if not self.metadata_cache:
                return None

            return await self.metadata_cache.get_action_info(
                action_name=action_name,
                entity_name=entity_name,
            )

        async def fallback_lookup():
            # Use the new metadata API operations for action lookup
            return await self.metadata_api_ops.get_action_info(action_name, entity_name)

        action = await self._get_from_cache_first(
            cache_lookup, fallback_lookup, use_cache_first=use_cache_first
        )

        return await resolve_labels_generic(action, self.label_ops) if action else None

    # CRUD Operations

    async def get_entities(
        self,
        entity_name: str,
        options: Optional[QueryOptions] = None,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """Get entities with OData query options

        Args:
            entity_name: Name of the entity set
            options: OData query options
            skip_validation: Skip schema validation for performance

        Returns:
            Response containing entities
        """
        entity_schema = None
        if not skip_validation:
            entity_schema = await self.get_public_entity_schema_by_entityset(
                entity_name
            )
            if not entity_schema:
                raise FOClientError(
                    f"Entity '{entity_name}' not found or not accessible for OData operations"
                )

        return await self.crud_ops.get_entities(entity_name, options, entity_schema)

    async def get_entity(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        options: Optional[QueryOptions] = None,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """Get single entity by key with schema validation

        Args:
            entity_name: Name of the entity set (entityset/collection name)
            key: Entity key value (string for simple keys, dict for composite keys)
            options: OData query options
            skip_validation: Skip schema validation for performance (batch operations)

        Returns:
            Entity data

        Raises:
            FOClientError: If entity not found or not accessible
        """
        entity_schema = None
        if not skip_validation:
            entity_schema = await self.get_public_entity_schema_by_entityset(
                entity_name
            )
            if not entity_schema:
                raise FOClientError(
                    f"Entity '{entity_name}' not found or not accessible for OData operations"
                )

        return await self.crud_ops.get_entity(entity_name, key, options, entity_schema)

    async def get_entity_by_key(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        select: Optional[List[str]] = None,
        expand: Optional[List[str]] = None,
        skip_validation: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get single entity by key with optional field selection and expansion

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            select: Optional list of fields to select
            expand: Optional list of navigation properties to expand
            skip_validation: Skip schema validation for performance

        Returns:
            Entity data or None if not found
        """
        try:
            options = (
                QueryOptions(select=select, expand=expand) if select or expand else None
            )
            return await self.get_entity(entity_name, key, options, skip_validation)
        except Exception as e:
            # If the entity is not found, return None instead of raising exception
            if "404" in str(e):
                return None
            raise

    async def create_entity(
        self, entity_name: str, data: Dict[str, Any], skip_validation: bool = False
    ) -> Dict[str, Any]:
        """Create new entity with schema validation

        Args:
            entity_name: Name of the entity set
            data: Entity data to create
            skip_validation: Skip schema validation for performance (batch operations)

        Returns:
            Created entity data

        Raises:
            FOClientError: If entity not found, read-only, or validation fails
        """
        entity_schema = None
        if not skip_validation:
            entity_schema = await self.get_public_entity_schema_by_entityset(
                entity_name
            )
            if not entity_schema:
                raise FOClientError(
                    f"Entity '{entity_name}' not found or not accessible for OData operations"
                )
            if entity_schema.is_read_only:
                raise FOClientError(
                    f"Entity '{entity_name}' is read-only and cannot accept create operations"
                )

        return await self.crud_ops.create_entity(entity_name, data, entity_schema)

    async def update_entity(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        data: Dict[str, Any],
        method: str = "PATCH",
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """Update existing entity with schema validation

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            data: Updated entity data
            method: HTTP method (PATCH or PUT)
            skip_validation: Skip schema validation for performance (batch operations)

        Returns:
            Updated entity data

        Raises:
            FOClientError: If entity not found, read-only, or validation fails
        """
        entity_schema = None
        if not skip_validation:
            entity_schema = await self.get_public_entity_schema_by_entityset(
                entity_name
            )
            if not entity_schema:
                raise FOClientError(
                    f"Entity '{entity_name}' not found or not accessible for OData operations"
                )
            if entity_schema.is_read_only:
                raise FOClientError(
                    f"Entity '{entity_name}' is read-only and cannot accept update operations"
                )

        return await self.crud_ops.update_entity(
            entity_name, key, data, method, entity_schema
        )

    async def delete_entity(
        self,
        entity_name: str,
        key: Union[str, Dict[str, Any]],
        skip_validation: bool = False,
    ) -> bool:
        """Delete entity with schema validation

        Args:
            entity_name: Name of the entity set
            key: Entity key value (string for simple keys, dict for composite keys)
            skip_validation: Skip schema validation for performance (batch operations)

        Returns:
            True if successful

        Raises:
            FOClientError: If entity not found, read-only, or validation fails
        """
        entity_schema = None
        if not skip_validation:
            entity_schema = await self.get_public_entity_schema_by_entityset(
                entity_name
            )
            if not entity_schema:
                raise FOClientError(
                    f"Entity '{entity_name}' not found or not accessible for OData operations"
                )
            if entity_schema.is_read_only:
                raise FOClientError(
                    f"Entity '{entity_name}' is read-only and cannot accept delete operations"
                )

        return await self.crud_ops.delete_entity(entity_name, key, entity_schema)

    async def call_action(
        self,
        action_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        entity_name: Optional[str] = None,
        entity_key: Optional[Union[str, Dict[str, Any]]] = None,
        skip_validation: bool = False,
    ) -> Any:
        """Call OData action method

        Args:
            action_name: Name of the action
            parameters: Action parameters
            entity_name: Entity name for bound actions
            entity_key: Entity key for bound actions (string for simple keys, dict for composite keys)
            skip_validation: Skip schema validation for performance

        Returns:
            Action result
        """
        entity_schema = None
        if not skip_validation and entity_name:
            entity_schema = await self.get_public_entity_schema_by_entityset(
                entity_name
            )
            if not entity_schema:
                raise FOClientError(
                    f"Entity '{entity_name}' not found or not accessible for OData operations"
                )

        return await self.crud_ops.call_action(
            action_name, parameters, entity_name, entity_key, entity_schema
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
    ) -> Dict[str, Any]:
        """Get data entities from DataEntities metadata endpoint

        Args:
            options: OData query options

        Returns:
            Response containing data entities
        """
        return await self.metadata_api_ops.get_data_entities(options)

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
            use_cache_first=use_cache_first,
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
            use_cache_first=use_cache_first,
        )

        return await resolve_labels_generic(entity, self.label_ops)  # type: ignore

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
        await self._ensure_metadata_initialized()

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
            use_cache_first=use_cache_first,
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
            use_cache_first=use_cache_first,
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

                # Always check if we're in an async context first
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, can't run async code synchronously
                    return {
                        "enabled": True,
                        "cache_type": "metadata_v2",
                        "message": "Label caching enabled with v2 cache (statistics available via async method)",
                    }
                except RuntimeError:
                    # No running loop, we can safely create one
                    pass

                # Create a new event loop for synchronous execution
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        stats = loop.run_until_complete(
                            self.metadata_cache.get_label_cache_statistics()
                        )
                        return {
                            "enabled": True,
                            "cache_type": "metadata_v2",
                            "statistics": stats,
                        }
                    finally:
                        loop.close()
                        # Remove the loop to clean up
                        try:
                            asyncio.set_event_loop(None)
                        except:
                            pass
                except Exception as e:
                    return {
                        "enabled": True,
                        "cache_type": "metadata_v2",
                        "error": f"Error getting statistics: {e}",
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
                    "sync_manager_available": self.sync_manager is not None
                    or self._sync_session_manager is not None,
                    "background_sync_running": self._is_background_sync_running(),
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

    async def post_json_service(
        self,
        service_group: str,
        service_name: str,
        operation_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> JsonServiceResponse:
        """Call D365 F&O JSON service endpoint using POST method

        This method provides a generic way to call D365 F&O JSON services that use the
        /api/services/{ServiceGroup}/{ServiceName}/{OperationName} endpoint pattern.

        Args:
            service_group: Service group name (e.g., "SysSqlDiagnosticService")
            service_name: Service name (e.g., "SysSqlDiagnosticServiceOperations")
            operation_name: Operation name (e.g., "GetAxSqlExecuting")
            parameters: Optional parameters to send in the POST body

        Returns:
            JsonServiceResponse containing the result data and metadata

        Raises:
            FOClientError: If the service call fails

        Example:
            # Call a service without parameters
            response = await client.post_json_service(
                "SysSqlDiagnosticService",
                "SysSqlDiagnosticServiceOperations",
                "GetAxSqlExecuting"
            )

            # Call a service with parameters
            response = await client.post_json_service(
                "SysSqlDiagnosticService",
                "SysSqlDiagnosticServiceOperations",
                "GetAxSqlResourceStats",
                {
                    "start": "2023-01-01T00:00:00Z",
                    "end": "2023-01-02T00:00:00Z"
                }
            )
        """
        try:
            # Create service request
            request = JsonServiceRequest(
                service_group=service_group,
                service_name=service_name,
                operation_name=operation_name,
                parameters=parameters,
            )

            # Get the endpoint path
            endpoint_path = request.get_endpoint_path()
            url = f"{self.config.base_url.rstrip('/')}{endpoint_path}"

            # Get session and make request
            session = await self.session_manager.get_session()

            # Prepare headers
            headers = {"Content-Type": "application/json"}

            # Prepare request body
            body = parameters or {}

            async with session.post(url, json=body, headers=headers) as response:
                status_code = response.status

                # Handle success cases
                if status_code in [200, 201]:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            data = await response.json()
                        else:
                            data = await response.text()

                        return JsonServiceResponse(
                            success=True,
                            data=data,
                            status_code=status_code,
                        )
                    except Exception as parse_error:
                        # If we can't parse the response, still return success with raw text
                        text_data = await response.text()
                        return JsonServiceResponse(
                            success=True,
                            data=text_data,
                            status_code=status_code,
                            error_message=f"Response parsing warning: {parse_error}",
                        )

                # Handle error cases
                else:
                    error_text = await response.text()
                    return JsonServiceResponse(
                        success=False,
                        data=None,
                        status_code=status_code,
                        error_message=f"HTTP {status_code}: {error_text}",
                    )

        except Exception as e:
            # Handle network errors and other exceptions
            return JsonServiceResponse(
                success=False,
                data=None,
                status_code=0,
                error_message=f"Request failed: {e}",
            )

    async def call_json_service(
        self,
        request: JsonServiceRequest,
    ) -> JsonServiceResponse:
        """Call D365 F&O JSON service using a JsonServiceRequest object

        This is an alternative interface to post_json_service that accepts a request object.

        Args:
            request: JsonServiceRequest containing service details and parameters

        Returns:
            JsonServiceResponse containing the result data and metadata

        Example:
            request = JsonServiceRequest(
                service_group="SysSqlDiagnosticService",
                service_name="SysSqlDiagnosticServiceOperations",
                operation_name="GetAxSqlExecuting"
            )
            response = await client.call_json_service(request)
        """
        return await self.post_json_service(
            request.service_group,
            request.service_name,
            request.operation_name,
            request.parameters,
        )

    async def get_public_entity_schema_by_entityset(
        self, entityset_name: str, use_cache_first: Optional[bool] = True
    ) -> Optional[PublicEntityInfo]:
        """Get public entity schema by entityset name (public collection name).

        This method resolves the entityset name to the actual public entity name
        and retrieves the full schema with cache-first optimization.

        Args:
            entityset_name: Public collection name or entity set name
                           (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
            use_cache_first: Use metadata cache before F&O API (default: True)

        Returns:
            PublicEntityInfo with full schema, or None if entity not found

        Resolution Logic:
            1. Try direct lookup in public entities (entityset_name == entity name)
            2. Search data entities for public_collection_name match
            3. Resolve to public_entity_name and fetch schema
            4. Use cache-first pattern for all lookups
        """

        async def cache_lookup():
            if not self.metadata_cache:
                return None

            # Try direct public entity lookup first (entityset_name might be the entity name)
            entity_schema = await self.metadata_cache.get_public_entity_schema(
                entityset_name
            )
            if entity_schema:
                self.logger.debug(
                    f"Found entity schema directly for '{entityset_name}'"
                )
                return entity_schema

            # Try resolving via data entity metadata
            # Search for entities matching the entityset name
            data_entities = await self.metadata_cache.get_data_entities(
                name_pattern=entityset_name
            )

            for data_entity in data_entities:
                # Check if public_collection_name matches
                if data_entity.public_collection_name == entityset_name:
                    self.logger.debug(
                        f"Resolved '{entityset_name}' to entity '{data_entity.public_entity_name or data_entity.name}'"
                    )
                    # Found match - get schema by public_entity_name
                    return await self.metadata_cache.get_public_entity_schema(
                        data_entity.public_entity_name or data_entity.name
                    )

                # Also check if entity name matches (for direct name usage)
                if data_entity.name == entityset_name:
                    self.logger.debug(f"Found entity by name '{entityset_name}'")
                    return await self.metadata_cache.get_public_entity_schema(
                        data_entity.public_entity_name or data_entity.name
                    )

                # Check if public_entity_name matches
                if data_entity.public_entity_name == entityset_name:
                    self.logger.debug(
                        f"Found entity by public_entity_name '{entityset_name}'"
                    )
                    return await self.metadata_cache.get_public_entity_schema(
                        entityset_name
                    )

            return None

        async def fallback_lookup():
            # Try direct public entity lookup first
            try:
                entity_schema = await self.metadata_api_ops.get_public_entity_info(
                    entityset_name, resolve_labels=False
                )
                if entity_schema:
                    self.logger.debug(
                        f"Found entity schema via API for '{entityset_name}'"
                    )
                    return entity_schema
            except Exception as e:
                self.logger.debug(
                    f"Direct API lookup failed for '{entityset_name}': {e}"
                )

            # Search data entities to find the mapping
            try:
                data_entities = await self.metadata_api_ops.search_data_entities("")

                for data_entity in data_entities:
                    # Check if public_collection_name matches
                    if data_entity.public_collection_name == entityset_name:
                        self.logger.debug(
                            f"Resolved '{entityset_name}' to entity '{data_entity.public_entity_name or data_entity.name}' via API"
                        )
                        # Found match - get schema by public_entity_name
                        return await self.metadata_api_ops.get_public_entity_info(
                            data_entity.public_entity_name or data_entity.name,
                            resolve_labels=False,
                        )

                    # Also check if entity name matches
                    if data_entity.name == entityset_name:
                        return await self.metadata_api_ops.get_public_entity_info(
                            data_entity.public_entity_name or data_entity.name,
                            resolve_labels=False,
                        )

                    # Check if public_entity_name matches
                    if data_entity.public_entity_name == entityset_name:
                        return await self.metadata_api_ops.get_public_entity_info(
                            entityset_name, resolve_labels=False
                        )
            except Exception as e:
                self.logger.debug(
                    f"Data entity search failed for '{entityset_name}': {e}"
                )

            return None

        return await self._get_from_cache_first(
            cache_lookup,
            fallback_lookup,
            use_cache_first=use_cache_first,
        )

    async def get_entity_schema(
        self, entity_name: str, use_cache_first: Optional[bool] = True
    ) -> Optional[PublicEntityInfo]:
        """Get entity schema with cache-first optimization.

        This is an enhanced version that uses the cache-first pattern for better performance.

        Args:
            entity_name: Name of the public entity
            use_cache_first: Use metadata cache before F&O API (default: True)

        Returns:
            PublicEntityInfo object with schema details or None if not found
        """
        return await self.get_public_entity_info(
            entity_name, resolve_labels=False, use_cache_first=use_cache_first
        )

    async def download_srs_report(
        self,
        document_id: str,
        legal_entity: str,
        controller_name: str = "SalesInvoiceController",
        data_table: str = "CustInvoiceJour",
        data_field: str = "InvoiceId",
        document_type: str = "SalesInvoice",
        save_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Download SRS report as PDF from D365 F&O

        This method downloads SQL Server Reporting Services (SSRS/SRS) reports from D365 F&O
        by calling the RunCopilotReport action on the SrsFinanceCopilots entity. The report
        is returned as base64-encoded PDF data which is decoded and saved to the specified path.

        Args:
            document_id: The ID/key of the document to download (e.g., invoice number, order ID)
            legal_entity: The legal entity/company code (DataAreaId) for the document
            controller_name: The SSRS controller class name. Common controllers:
                - SalesInvoiceController: Customer invoices (CustInvoiceJour)
                - FreeTextInvoiceController: Free text invoices (CustInvoiceJour)
                - CustDebitCreditNoteController: Debit/Credit notes (CustInvoiceJour)
                - SalesConfirmController: Sales confirmations (CustConfirmJour)
                - PurchPurchaseOrderController: Purchase orders (VendPurchOrderJour)
            data_table: The table name containing the document record
            data_field: The field name that stores the document ID in the table
            document_type: Human-readable document type for filename generation
            save_path: Full path where PDF should be saved. If None, saves to ./Reports directory
                      with auto-generated filename. Can be Path object or string.

        Returns:
            str: Absolute path to the saved PDF file

        Raises:
            FOClientError: If report generation fails, no PDF data returned, or file save fails
            ValueError: If required parameters are missing or invalid

        Example:
            # Download customer invoice
            path = await client.download_srs_report(
                document_id="CIV-000708",
                legal_entity="USMF",
                controller_name="SalesInvoiceController",
                data_table="CustInvoiceJour",
                data_field="InvoiceId",
                document_type="CustomerInvoice",
                save_path="/reports/invoices/CIV-000708.pdf"
            )

            # Download with auto-generated filename
            path = await client.download_srs_report(
                document_id="FTI-00000021",
                legal_entity="USMF",
                controller_name="FreeTextInvoiceController"
            )
        """
        import base64
        from datetime import datetime

        # Validate required parameters
        if not document_id or not legal_entity:
            raise ValueError(
                f"document_id and legal_entity are required. "
                f"Got document_id='{document_id}', legal_entity='{legal_entity}'"
            )

        # Determine save path
        if save_path:
            save_file = Path(save_path)
            # Ensure parent directory exists
            save_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Auto-generate filename in ~/Reports directory
            save_directory = Path.home() / "Reports"
            save_directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{document_type}_{document_id}_{legal_entity}_{timestamp}.pdf"
            save_file = save_directory / filename

        try:
            # Build controller args
            controller_args = {
                "DataTableName": data_table,
                "DataTableFieldName": data_field,
                "DataTableFieldValue": document_id,
            }

            # Build action parameters
            parameters = {
                "_contractName": "SrsCopilotArgsContract",
                "_controllerArgsJson": json.dumps(controller_args),
                "_controllerName": controller_name,
                "_legalEntityName": legal_entity,
                "_reportParameterJson": "{}",
            }

            self.logger.info(
                f"Downloading SRS report: {document_type} '{document_id}' "
                f"for legal entity '{legal_entity}'"
            )

            # Call the action
            result = await self.call_action(
                action_name="RunCopilotReport",
                parameters=parameters,
                entity_name="SrsFinanceCopilots",
            )

            # Extract base64 PDF data from response
            # Response structure: {"result": {"value": "base64data..."}} or {"Result": {"Value": "..."}}
            base64_data = None
            if isinstance(result, dict):
                # Try standard case
                result_obj = result.get("result") or result.get("Result")
                if isinstance(result_obj, dict):
                    base64_data = result_obj.get("value") or result_obj.get("Value")
                # Fallback: check if value is at root
                if base64_data is None:
                    base64_data = result.get("value") or result.get("Value")

            if not base64_data:
                raise FOClientError(
                    f"No PDF content returned from SRS report generation for document '{document_id}'. "
                    f"The report may not exist or the document ID may be invalid."
                )

            # Decode base64 to PDF bytes
            try:
                pdf_bytes = base64.b64decode(base64_data)
            except Exception as e:
                raise FOClientError(
                    f"Failed to decode PDF data for document '{document_id}': {e}"
                )

            # Save PDF file
            try:
                save_file.write_bytes(pdf_bytes)
                absolute_path = str(save_file.resolve())
                self.logger.info(f"SRS report saved successfully: {absolute_path}")
                return absolute_path
            except Exception as e:
                raise FOClientError(f"Failed to save PDF file to '{save_file}': {e}")

        except FOClientError:
            # Re-raise FOClientError as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise FOClientError(
                f"Failed to download SRS report for document '{document_id}': {e}"
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
