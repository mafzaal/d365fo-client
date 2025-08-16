"""Main F&O client implementation."""

import os
from typing import Dict, List, Optional, Any, Union

from .models import (
    FOClientConfig, QueryOptions, LabelInfo, EntityInfo, ActionInfo, EntityPropertyInfo
)
from .auth import AuthenticationManager
from .session import SessionManager
from .metadata import MetadataManager
from .cache import LabelCache
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
        
        # Initialize components
        self.auth_manager = AuthenticationManager(config)
        self.session_manager = SessionManager(config, self.auth_manager)
        self.metadata_manager = MetadataManager(config.metadata_cache_dir)
        
        # Initialize label cache if enabled
        self.label_cache = (LabelCache(config.label_cache_expiry_minutes) 
                           if config.use_label_cache else None)
        
        # Initialize operations
        self.metadata_url = f"{config.base_url.rstrip('/')}/Metadata"
        self.crud_ops = CrudOperations(self.session_manager, config.base_url)
        self.label_ops = LabelOperations(self.session_manager, self.metadata_url, self.label_cache)
    
    async def close(self):
        """Close the client session"""
        await self.session_manager.close()
    
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
            
            # Fallback: try Labels with a specific filter
            url = f"{self.metadata_url}/Labels"
            params = {
                "$filter": "startswith(Id, '@SYS') and Language eq 'en-US'",
                "$top": 1
            }
            
            async with session.get(url, params=params) as response:
                return response.status == 200
                
        except Exception as e:
            print(f"Metadata connection test failed: {e}")
            return False
    
    # Metadata Operations
    
    async def download_metadata(self, force_refresh: bool = False) -> bool:
        """Download OData metadata from F&O
        
        Args:
            force_refresh: Force download even if metadata exists
            
        Returns:
            True if successful
        """
        metadata_file = self.metadata_manager.metadata_file
        
        if not force_refresh and os.path.exists(metadata_file):
            print("Metadata already exists. Use force_refresh=True to re-download.")
            return True
        
        try:
            session = await self.session_manager.get_session()
            url = f"{self.config.base_url}/data/$metadata"
            
            # Set headers to request XML format for metadata
            headers = session.headers.copy()
            headers['Accept'] = 'application/xml'

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    self.metadata_manager.save_metadata(content)
                    print(f"Metadata downloaded successfully to {metadata_file}")
                    return True
                else:
                    print(f"Failed to download metadata: {response.status} - {await response.text()}")
                    return False
        
        except Exception as e:
            print(f"Error downloading metadata: {e}")
            return False
    
    def search_entities(self, pattern: str = "") -> List[str]:
        """Search entities by name pattern
        
        Args:
            pattern: Search pattern (regex supported)
            
        Returns:
            List of matching entity names
        """
        return self.metadata_manager.search_entities(pattern)
    
    def get_entity_info(self, entity_name: str) -> Optional[EntityInfo]:
        """Get detailed entity information
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            EntityInfo object or None if not found
        """
        return self.metadata_manager.get_entity_info(entity_name)
    
    def search_actions(self, pattern: str = "") -> List[str]:
        """Search actions by name pattern
        
        Args:
            pattern: Search pattern (regex supported)
            
        Returns:
            List of matching action names
        """
        return self.metadata_manager.search_actions(pattern)
    
    def get_action_info(self, action_name: str) -> Optional[ActionInfo]:
        """Get detailed action information
        
        Args:
            action_name: Name of the action
            
        Returns:
            ActionInfo object or None if not found
        """
        return self.metadata_manager.get_action_info(action_name)
    
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
    
    # Utility Methods
    
    def get_label_cache_info(self) -> Dict[str, Any]:
        """Get information about the label cache
        
        Returns:
            Dictionary with cache information
        """
        if not self.label_cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
            **self.label_cache.get_info()
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
    
    def get_metadata_info(self) -> Dict[str, Any]:
        """Get metadata cache information
        
        Returns:
            Dictionary with metadata information
        """
        return self.metadata_manager.get_cache_info()


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