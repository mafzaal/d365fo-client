"""Main F&O client implementation."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union

from .models import (
    FOClientConfig, QueryOptions, LabelInfo, EntityInfo, ActionInfo, EntityPropertyInfo,
    DataEntityInfo, PublicEntityInfo, EnumerationInfo, SearchQuery
)
from .auth import AuthenticationManager
from .session import SessionManager
from .metadata_api import MetadataAPIOperations
from .metadata_cache import MetadataCache
from .metadata_sync import MetadataSyncManager
from .crud import CrudOperations
from .labels import LabelOperations
from .query import QueryBuilder
from .exceptions import FOClientError, ConfigurationError


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
        
        # Initialize label operations - will be updated with metadata_cache when available
        self.label_ops = LabelOperations(self.session_manager, self.metadata_url, None)
        self.metadata_api_ops = MetadataAPIOperations(self.session_manager, self.metadata_url, self.label_ops)
    
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
                from pathlib import Path
                cache_dir = Path(self.config.metadata_cache_dir)
                
                # Initialize metadata cache
                self.metadata_cache = MetadataCache(self.config.base_url, cache_dir)
                await self.metadata_cache.initialize()
                
                # Update label operations to use metadata cache
                self.label_ops.metadata_cache = self.metadata_cache
                
                # Initialize sync manager
                self.sync_manager = MetadataSyncManager(self.metadata_cache, self.metadata_api_ops)
                
                self._metadata_initialized = True
                self.logger.debug("Metadata cache and sync manager initialized")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize metadata cache: {e}")
                # Continue without metadata cache
                self.config.enable_metadata_cache = False
    
    async def _trigger_background_sync_if_needed(self):
        """Trigger background sync if metadata is stale or missing"""
        if not self.config.enable_metadata_cache or not self._metadata_initialized:
            return
            
        try:
            # Check if we need to sync
            if await self.sync_manager.needs_sync():
                # Only start sync if not already running
                if not self._background_sync_task or self._background_sync_task.done():
                    self._background_sync_task = asyncio.create_task(
                        self._background_sync_worker()
                    )
                    self.logger.debug("Background metadata sync triggered")
        except Exception as e:
            self.logger.warning(f"Failed to check sync status: {e}")
    
    async def _background_sync_worker(self):
        """Background worker for metadata synchronization"""
        try:
            self.logger.info("Starting background metadata sync")
            result = await self.sync_manager.sync_metadata()
            
            if result.success:
                self.logger.info(f"Background sync completed: {result.sync_type}, "
                               f"{result.entities_synced} entities, "
                               f"{result.duration_ms:.2f}ms")
            else:
                self.logger.warning(f"Background sync failed: {result.errors}")
                
        except Exception as e:
            self.logger.error(f"Background sync error: {e}")
    
    async def _get_from_cache_first(self, cache_method, fallback_method, *args, use_cache_first: Optional[bool] = None, **kwargs):
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
            return await fallback_method(*args, **kwargs) if asyncio.iscoroutinefunction(fallback_method) else fallback_method(*args, **kwargs)
        
        # Ensure metadata is initialized
        await self._ensure_metadata_initialized()
        
        if not self._metadata_initialized:
            # Cache not available, use fallback
            return await fallback_method(*args, **kwargs) if asyncio.iscoroutinefunction(fallback_method) else fallback_method(*args, **kwargs)
        
        try:
            # Try cache first
            result = await cache_method(*args, **kwargs) if asyncio.iscoroutinefunction(cache_method) else cache_method(*args, **kwargs)
            
            # If cache returns empty result, trigger sync and try fallback
            if not result or (isinstance(result, list) and len(result) == 0):
                await self._trigger_background_sync_if_needed()
                return await fallback_method(*args, **kwargs) if asyncio.iscoroutinefunction(fallback_method) else fallback_method(*args, **kwargs)
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Cache lookup failed, using fallback: {e}")
            # Trigger sync if cache failed
            await self._trigger_background_sync_if_needed()
            return await fallback_method(*args, **kwargs) if asyncio.iscoroutinefunction(fallback_method) else fallback_method(*args, **kwargs)
    
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
        """Download/sync metadata using new sync manager
        
        Args:
            force_refresh: Force full synchronization even if cache is fresh
            
        Returns:
            True if successful
        """
        # Ensure metadata components are initialized
        await self._ensure_metadata_initialized()
        
        if not self._metadata_initialized:
            self.logger.error("Metadata cache could not be initialized")
            return False
        
        try:
            self.logger.info("Starting metadata synchronization")
            result = await self.sync_manager.sync_metadata(force_full=force_refresh)
            
            if result.success:
                self.logger.info(f"Metadata sync completed: {result.sync_type}, "
                               f"{result.entities_synced} entities, "
                               f"{result.enumerations_synced} enumerations, "
                               f"{result.duration_ms:.2f}ms")
                return True
            else:
                self.logger.error(f"Metadata sync failed: {result.errors}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during metadata sync: {e}")
            return False
    
    async def search_entities(self, pattern: str = "", use_cache_first: Optional[bool] = None) -> List[str]:
        """Search entities by name pattern with cache-first approach
        
        Args:
            pattern: Search pattern (regex supported)
            use_cache_first: Override config setting for cache-first behavior
            
        Returns:
            List of matching entity names
        """
        async def cache_search():
            if self.metadata_cache:
                # Use the new search API with both public and data entities
                query = SearchQuery(
                    text=pattern,
                    entity_types=["public_entity", "data_entity"],
                    limit=1000
                )
                results = await self.metadata_cache.search(query)
                return [result.name for result in results.results]
            return []
            
        async def fallback_search():
            # Use metadata API operations as fallback
            public_entities = await self.metadata_api_ops.search_public_entities(pattern)
            data_entities = await self.metadata_api_ops.search_data_entities(pattern)
            
            # Combine and deduplicate entity names
            entity_names = set()
            entity_names.update(entity.name for entity in public_entities)
            entity_names.update(entity.name for entity in data_entities)
            return sorted(list(entity_names))
        
        return await self._get_from_cache_first(
            cache_search, fallback_search, 
            use_cache_first=use_cache_first
        )
    
    async def get_entity_info(self, entity_name: str, use_cache_first: Optional[bool] = None) -> Optional[EntityInfo]:
        """Get detailed entity information with cache-first approach
        
        Args:
            entity_name: Name of the entity
            use_cache_first: Override config setting for cache-first behavior
            
        Returns:
            EntityInfo object or None if not found
        """
        async def cache_lookup():
            if self.metadata_cache:
                # Try to get entity from cache (public entity first, then data entity)
                entity = await self.metadata_cache.get_entity(entity_name, "public")
                if not entity:
                    entity = await self.metadata_cache.get_entity(entity_name, "data")
                
                if entity:
                    # Convert to EntityInfo format for backward compatibility
                    return EntityInfo(
                        name=entity.name,
                        keys=[prop.name for prop in getattr(entity, 'properties', []) if getattr(prop, 'is_key', False)],
                        properties=[{
                            'name': prop.name,
                            'type': getattr(prop, 'type_name', ''),
                            'nullable': 'true' if not getattr(prop, 'is_mandatory', False) else 'false'
                        } for prop in getattr(entity, 'properties', [])],
                        actions=[]  # Actions are handled separately in new system
                    )
            return None
            
        async def fallback_lookup():
            # Use metadata API operations as fallback
            public_entity = await self.metadata_api_ops.get_public_entity_info(entity_name, resolve_labels=False)
            if public_entity:
                return EntityInfo(
                    name=public_entity.name,
                    keys=[prop.name for prop in public_entity.properties if prop.is_key],
                    properties=[{
                        'name': prop.name,
                        'type': prop.type_name,
                        'nullable': 'true' if not prop.is_mandatory else 'false'
                    } for prop in public_entity.properties],
                    actions=[]
                )
            
            # Try data entity if public entity not found
            data_entity = await self.metadata_api_ops.get_data_entity_info(entity_name, resolve_labels=False)
            if data_entity:
                return EntityInfo(
                    name=data_entity.name,
                    keys=[],  # Data entities don't have key info in the same way
                    properties=[],  # Data entities have different property structure
                    actions=[]
                )
            
            return None
        
        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup,
            use_cache_first=use_cache_first
        )
    
    async def search_actions(self, pattern: str = "", use_cache_first: Optional[bool] = None) -> List[str]:
        """Search actions by name pattern with cache-first approach
        
        Note: Actions are not directly searchable in the new metadata system as they
        are embedded within entity information. This method provides limited functionality
        for backward compatibility.
        
        Args:
            pattern: Search pattern (regex supported)
            use_cache_first: Override config setting for cache-first behavior
            
        Returns:
            List of matching action names (limited functionality)
        """
        async def cache_search():
            # Actions are not directly searchable in new cache system
            # They are embedded in entity information
            return []
            
        async def fallback_search():
            # Actions are not directly available through metadata API
            # They are part of entity definitions
            # Return empty list for backward compatibility
            return []
        
        return await self._get_from_cache_first(
            cache_search, fallback_search,
            use_cache_first=use_cache_first
        )
    
    async def get_action_info(self, action_name: str, use_cache_first: Optional[bool] = None) -> Optional[ActionInfo]:
        """Get detailed action information with cache-first approach
        
        Note: Actions are not directly accessible in the new metadata system as they
        are embedded within entity information. This method provides limited functionality
        for backward compatibility.
        
        Args:
            action_name: Name of the action
            use_cache_first: Override config setting for cache-first behavior
            
        Returns:
            ActionInfo object or None if not found (limited functionality)
        """
        async def cache_lookup():
            # Actions are not directly accessible in new cache system
            # They are embedded in entity information
            return None
            
        async def fallback_lookup():
            # Actions are not directly available through metadata API
            # They are part of entity definitions
            # Return None for backward compatibility
            return None
        
        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup,
            use_cache_first=use_cache_first
        )
    
    # CRUD Operations
    
    async def get_entities(self, entity_name: str, 
                          options: Optional[QueryOptions] = None) -> Dict[str, Any]:
        """Get entities with OData query options
        
        Args:
            entity_name: Name of the entity set
            options: OData query options
            
        Returns:
            Response containing entities
        """
        return await self.crud_ops.get_entities(entity_name, options)
    
    async def get_entity(self, entity_name: str, key: str, 
                        options: Optional[QueryOptions] = None) -> Dict[str, Any]:
        """Get single entity by key
        
        Args:
            entity_name: Name of the entity set
            key: Entity key value
            options: OData query options
            
        Returns:
            Entity data
        """
        return await self.crud_ops.get_entity(entity_name, key, options)
    
    async def create_entity(self, entity_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity
        
        Args:
            entity_name: Name of the entity set
            data: Entity data to create
            
        Returns:
            Created entity data
        """
        return await self.crud_ops.create_entity(entity_name, data)
    
    async def update_entity(self, entity_name: str, key: str, data: Dict[str, Any], 
                           method: str = 'PATCH') -> Dict[str, Any]:
        """Update existing entity
        
        Args:
            entity_name: Name of the entity set
            key: Entity key value
            data: Updated entity data
            method: HTTP method (PATCH or PUT)
            
        Returns:
            Updated entity data
        """
        return await self.crud_ops.update_entity(entity_name, key, data, method)
    
    async def delete_entity(self, entity_name: str, key: str) -> bool:
        """Delete entity
        
        Args:
            entity_name: Name of the entity set
            key: Entity key value
            
        Returns:
            True if successful
        """
        return await self.crud_ops.delete_entity(entity_name, key)
    
    async def call_action(self, action_name: str, parameters: Optional[Dict[str, Any]] = None,
                         entity_name: Optional[str] = None, 
                         entity_key: Optional[str] = None) -> Any:
        """Call OData action method
        
        Args:
            action_name: Name of the action
            parameters: Action parameters
            entity_name: Entity name for bound actions
            entity_key: Entity key for bound actions
            
        Returns:
            Action result
        """
        return await self.crud_ops.call_action(action_name, parameters, entity_name, entity_key)
    
    # Label Operations
    
    async def get_label_text(self, label_id: str, language: str = "en-US") -> Optional[str]:
        """Get actual label text for a specific label ID
        
        Args:
            label_id: Label ID (e.g., "@SYS13342")
            language: Language code (e.g., "en-US")
            
        Returns:
            Label text or None if not found
        """
        return await self.label_ops.get_label_text(label_id, language)
    
    async def get_labels_batch(self, label_ids: List[str], 
                              language: str = "en-US") -> Dict[str, str]:
        """Get multiple labels in a single request
        
        Args:
            label_ids: List of label IDs
            language: Language code
            
        Returns:
            Dictionary mapping label ID to label text
        """
        return await self.label_ops.get_labels_batch(label_ids, language)
    
    # Enhanced Entity Operations with Labels
    
    async def get_entity_info_with_labels(self, entity_name: str, 
                                         language: str = "en-US") -> Optional[EntityInfo]:
        """Get entity metadata with resolved label text from Metadata API
        
        Args:
            entity_name: Name of the entity
            language: Language code for label resolution
            
        Returns:
            EntityInfo object with resolved labels
        """
        try:
            session = await self.session_manager.get_session()
            
            # Get entity metadata from Metadata API
            url = f"{self.metadata_url}/PublicEntities('{entity_name}')"
        
            
            async with session.get(url) as response:
                if response.status == 200:
                    entity_data = await response.json()
                    
                    # Create basic EntityInfo structure
                    entity_info = EntityInfo(
                        name=entity_data.get('Name', entity_name),
                        keys=[],  # Will be populated from properties
                        properties=[],  # Will be populated from properties
                        actions=[],  # Not available from PublicEntities
                        label_id=entity_data.get('LabelId'),
                        entity_set_name=entity_data.get('EntitySetName'),
                        is_read_only=entity_data.get('IsReadOnly', False)
                    )
                    
                    # Process properties
                    properties = entity_data.get('Properties', [])
                    for prop_data in properties:
                        prop_info = EntityPropertyInfo(
                            name=prop_data.get('Name', ''),
                            type_name=prop_data.get('TypeName', ''),
                            label_id=prop_data.get('LabelId'),
                            is_key=prop_data.get('IsKey', False),
                            is_mandatory=prop_data.get('IsMandatory', False),
                            allow_edit=prop_data.get('AllowEdit', True)
                        )
                        entity_info.enhanced_properties.append(prop_info)
                        
                        # Add to keys list if it's a key
                        if prop_info.is_key:
                            entity_info.keys.append(prop_info.name)
                        
                        # Add to basic properties structure
                        entity_info.properties.append({
                            'name': prop_info.name,
                            'type': prop_info.type_name,
                            'nullable': 'true' if not prop_info.is_mandatory else 'false'
                        })
                    
                    # Resolve all label IDs to text
                    await self.label_ops.resolve_entity_labels(entity_info, language)
                    
                    return entity_info
                else:
                    print(f"Error fetching entity metadata: {response.status} - {await response.text()} ")
                    
        except Exception as e:
            print(f"Exception fetching entity metadata: {e}")
        
        return None
    
    # Metadata API Operations
    
    async def get_data_entities(self, options: Optional[QueryOptions] = None) -> Dict[str, Any]:
        """Get data entities from DataEntities metadata endpoint
        
        Args:
            options: OData query options
            
        Returns:
            Response containing data entities
        """
        return await self.metadata_api_ops.get_data_entities(options)
    
    async def search_data_entities(self, pattern: str = "", entity_category: Optional[str] = None,
                                  data_service_enabled: Optional[bool] = None,
                                  data_management_enabled: Optional[bool] = None,
                                  is_read_only: Optional[bool] = None,
                                  use_cache_first: Optional[bool] = None) -> List[DataEntityInfo]:
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
            if self.metadata_cache and hasattr(self.metadata_cache, 'search_data_entities'):
                return await self.metadata_cache.search_data_entities(
                    pattern, entity_category, data_service_enabled,
                    data_management_enabled, is_read_only
                )
            return []
            
        async def fallback_search():
            return await self.metadata_api_ops.search_data_entities(
                pattern, entity_category, data_service_enabled, 
                data_management_enabled, is_read_only
            )
        
        return await self._get_from_cache_first(
            cache_search, fallback_search,
            use_cache_first=use_cache_first
        )
    
    async def get_data_entity_info(self, entity_name: str, resolve_labels: bool = True,
                                  language: str = "en-US", use_cache_first: Optional[bool] = None) -> Optional[DataEntityInfo]:
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
            if self.metadata_cache and hasattr(self.metadata_cache, 'get_data_entity_info'):
                return await self.metadata_cache.get_data_entity_info(entity_name, resolve_labels, language)
            return None
            
        async def fallback_lookup():
            return await self.metadata_api_ops.get_data_entity_info(entity_name, resolve_labels, language)
        
        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup,
            use_cache_first=use_cache_first
        )
    
    async def get_public_entities(self, options: Optional[QueryOptions] = None) -> Dict[str, Any]:
        """Get public entities from PublicEntities metadata endpoint
        
        Args:
            options: OData query options
            
        Returns:
            Response containing public entities
        """
        return await self.metadata_api_ops.get_public_entities(options)
    
    async def search_public_entities(self, pattern: str = "", is_read_only: Optional[bool] = None,
                                   configuration_enabled: Optional[bool] = None,
                                   use_cache_first: Optional[bool] = None) -> List[PublicEntityInfo]:
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
            if self.metadata_cache and hasattr(self.metadata_cache, 'search_public_entities'):
                return await self.metadata_cache.search_public_entities(pattern, is_read_only, configuration_enabled)
            return []
            
        async def fallback_search():
            return await self.metadata_api_ops.search_public_entities(pattern, is_read_only, configuration_enabled)
        
        return await self._get_from_cache_first(
            cache_search, fallback_search,
            use_cache_first=use_cache_first
        )
    
    async def get_public_entity_info(self, entity_name: str, resolve_labels: bool = True,
                                   language: str = "en-US", use_cache_first: Optional[bool] = None) -> Optional[PublicEntityInfo]:
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
            if self.metadata_cache and hasattr(self.metadata_cache, 'get_public_entity_info'):
                return await self.metadata_cache.get_public_entity_info(entity_name, resolve_labels, language)
            return None
            
        async def fallback_lookup():
            return await self.metadata_api_ops.get_public_entity_info(entity_name, resolve_labels, language)
        
        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup,
            use_cache_first=use_cache_first
        )
    
    async def get_all_public_entities_with_details(self, resolve_labels: bool = False, 
                                                 language: str = "en-US") -> List[PublicEntityInfo]:
        """Get all public entities with full details in a single optimized call
        
        This method uses an optimized approach that gets all entity details in one API call
        instead of making individual requests for each entity.
        
        Args:
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            
        Returns:
            List of PublicEntityInfo objects with complete details
        """
        return await self.metadata_api_ops.get_all_public_entities_with_details(resolve_labels, language)
    
    async def get_public_enumerations(self, options: Optional[QueryOptions] = None) -> Dict[str, Any]:
        """Get public enumerations from PublicEnumerations metadata endpoint
        
        Args:
            options: OData query options
            
        Returns:
            Response containing public enumerations
        """
        return await self.metadata_api_ops.get_public_enumerations(options)
    
    async def search_public_enumerations(self, pattern: str = "", use_cache_first: Optional[bool] = None) -> List[EnumerationInfo]:
        """Search public enumerations with filtering and cache-first approach
        
        Args:
            pattern: Search pattern for enumeration name (regex supported)
            use_cache_first: Override config setting for cache-first behavior
            
        Returns:
            List of matching enumerations (without detailed members)
        """
        async def cache_search():
            if self.metadata_cache and hasattr(self.metadata_cache, 'search_public_enumerations'):
                return await self.metadata_cache.search_public_enumerations(pattern)
            return []
            
        async def fallback_search():
            return await self.metadata_api_ops.search_public_enumerations(pattern)
        
        return await self._get_from_cache_first(
            cache_search, fallback_search,
            use_cache_first=use_cache_first
        )
    
    async def get_public_enumeration_info(self, enumeration_name: str, resolve_labels: bool = True,
                                        language: str = "en-US", use_cache_first: Optional[bool] = None) -> Optional[EnumerationInfo]:
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
            if self.metadata_cache and hasattr(self.metadata_cache, 'get_public_enumeration_info'):
                return await self.metadata_cache.get_public_enumeration_info(enumeration_name, resolve_labels, language)
            return None
            
        async def fallback_lookup():
            return await self.metadata_api_ops.get_public_enumeration_info(enumeration_name, resolve_labels, language)
        
        return await self._get_from_cache_first(
            cache_lookup, fallback_lookup,
            use_cache_first=use_cache_first
        )
    
    async def get_all_public_enumerations_with_details(self, resolve_labels: bool = False, 
                                                     language: str = "en-US") -> List[EnumerationInfo]:
        """Get all public enumerations with full details in a single optimized call
        
        This method uses an optimized approach that gets all enumeration details in one API call
        instead of making individual requests for each enumeration.
        
        Args:
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            
        Returns:
            List of EnumerationInfo objects with complete details
        """
        return await self.metadata_api_ops.get_all_public_enumerations_with_details(resolve_labels, language)
    
    # Utility Methods
    
    def get_label_cache_info(self) -> Dict[str, Any]:
        """Get information about the label cache
        
        Returns:
            Dictionary with cache information
        """
        if not self.metadata_cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
        }
    
    def get_entity_url(self, entity_name: str, key: Optional[str] = None) -> str:
        """Get entity URL
        
        Args:
            entity_name: Entity set name
            key: Optional entity key
            
        Returns:
            Complete entity URL
        """
        return QueryBuilder.build_entity_url(self.config.base_url, entity_name, key)
    
    def get_action_url(self, action_name: str, entity_name: Optional[str] = None, 
                      entity_key: Optional[str] = None) -> str:
        """Get action URL
        
        Args:
            action_name: Action name
            entity_name: Optional entity name for bound actions
            entity_key: Optional entity key for bound actions
            
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
        # Start with basic info (no longer using old MetadataManager)
        info = {
            "cache_directory": self.config.metadata_cache_dir,
            "statistics": None
        }
        await self._ensure_metadata_initialized()
        # Add new metadata cache info if available
        if self.metadata_cache:
            try:
                stats = await self.metadata_cache.get_statistics()
                cache_info = {
                    "advanced_cache_enabled": True,
                    "cache_initialized": self._metadata_initialized,
                    "sync_manager_available": self.sync_manager is not None,
                    "background_sync_running": (
                        self._background_sync_task and 
                        not self._background_sync_task.done()
                    ) if self._background_sync_task else False,
                    "statistics": stats
                }
                info.update(cache_info)
            except Exception as e:
                self.logger.warning(f"Error getting cache info: {e}")
                # Even on error, include basic cache info
                info.update({
                    "advanced_cache_enabled": True,
                    "cache_initialized": self._metadata_initialized,
                    "sync_manager_available": False,
                    "background_sync_running": False
                })
        else:
            info.update({
                "advanced_cache_enabled": False,
                "cache_initialized": False,
                "sync_manager_available": False,
                "background_sync_running": False
            })
            
        return info
    
    # Application Version Operations
    
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
                entity_name="DataManagementEntities"
            )
            
            # The action returns a simple string value
            if isinstance(result, str):
                return result
            elif isinstance(result, dict) and 'value' in result:
                return str(result['value'])
            else:
                return str(result) if result is not None else ""
                
        except Exception as e:
            raise FOClientError(f"Failed to get application build version: {e}")


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