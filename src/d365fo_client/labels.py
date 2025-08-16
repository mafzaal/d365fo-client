"""Label operations for D365 F&O client."""

from typing import Dict, List, Optional, Any

from .models import LabelInfo, EntityInfo, EntityPropertyInfo
from .cache import LabelCache
from .session import SessionManager


class LabelOperations:
    """Handles label operations for F&O client"""
    
    def __init__(self, session_manager: SessionManager, metadata_url: str, 
                 label_cache: Optional[LabelCache] = None):
        """Initialize label operations
        
        Args:
            session_manager: HTTP session manager
            metadata_url: Metadata API URL
            label_cache: Optional label cache
        """
        self.session_manager = session_manager
        self.metadata_url = metadata_url
        self.label_cache = label_cache
    
    async def get_label_text(self, label_id: str, language: str = "en-US") -> Optional[str]:
        """Get actual label text for a specific label ID
        
        Args:
            label_id: Label ID (e.g., "@SYS13342")
            language: Language code (e.g., "en-US")
            
        Returns:
            Label text or None if not found
        """
        # Check cache first
        if self.label_cache:
            cached_value = self.label_cache.get(label_id, language)
            if cached_value is not None:
                return cached_value
        
        try:
            session = await self.session_manager.get_session()
            url = f"{self.metadata_url}/Labels(Id='{label_id}',Language='{language}')"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    label_text = data.get('Value', '')
                    
                    # Cache the result
                    if self.label_cache:
                        self.label_cache.set(label_id, language, label_text)
                    
                    return label_text
                else:
                    print(f"Error fetching label {label_id}: {response.status}")
                    
        except Exception as e:
            print(f"Exception fetching label {label_id}: {e}")
        
        return None
    
    async def get_labels_batch(self, label_ids: List[str], 
                              language: str = "en-US") -> Dict[str, str]:
        """Get multiple labels in a single request
        
        Args:
            label_ids: List of label IDs
            language: Language code
            
        Returns:
            Dictionary mapping label ID to label text
        """
        if not label_ids:
            return {}
        
        results = {}
        
        # Check cache for existing labels
        uncached_ids = []
        if self.label_cache:
            for label_id in label_ids:
                cached_value = self.label_cache.get(label_id, language)
                if cached_value is not None:
                    results[label_id] = cached_value
                else:
                    uncached_ids.append(label_id)
        else:
            uncached_ids = label_ids
        
        # Fetch uncached labels
        if uncached_ids:
            try:
                session = await self.session_manager.get_session()
                
                for label_id in uncached_ids:
                    url = f"{self.metadata_url}/Labels(Id='{label_id}',Language='{language}')"
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            label_text = data.get('Value', '')
                            results[label_id] = label_text
                            
                            # Cache the result
                            if self.label_cache:
                                self.label_cache.set(label_id, language, label_text)
                        else:
                            print(f"Error fetching label {label_id}: {response.status}")
                            
            except Exception as e:
                print(f"Exception fetching batch labels: {e}")
        
        return results
    
    async def search_labels(self, search_term: str, language: str = "en-US", 
                           limit: int = 50) -> List[LabelInfo]:
        """Search labels containing specific text
        
        Args:
            search_term: Text to search for in label values
            language: Language code
            limit: Maximum number of results
            
        Returns:
            List of LabelInfo objects
        """
        try:
            session = await self.session_manager.get_session()
            
            url = f"{self.metadata_url}/Labels"
            params = {
                "$filter": f"contains(Value, '{search_term}') and Language eq '{language}'",
                "$select": "Id,Language,Value",
                "$top": limit
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    labels = data.get('value', [])
                    
                    result = []
                    for label in labels:
                        label_info = LabelInfo(
                            id=label['Id'],
                            language=label['Language'],
                            value=label['Value']
                        )
                        result.append(label_info)
                    
                    return result
                else:
                    print(f"Error searching labels: {response.status}")
                    
        except Exception as e:
            print(f"Exception searching labels: {e}")
        
        return []
    
    async def get_labels_by_prefix(self, prefix: str, language: str = "en-US", 
                                  limit: int = 100) -> List[LabelInfo]:
        """Get labels that start with a specific prefix
        
        Args:
            prefix: Label ID prefix (e.g., "@SYS", "@SCM:")
            language: Language code
            limit: Maximum number of results
            
        Returns:
            List of LabelInfo objects
        """
        try:
            session = await self.session_manager.get_session()
            
            url = f"{self.metadata_url}/Labels"
            params = {
                "$filter": f"startswith(Id, '{prefix}') and Language eq '{language}'",
                "$select": "Id,Language,Value",
                "$orderby": "Id",
                "$top": limit
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    labels = data.get('value', [])
                    
                    result = []
                    for label in labels:
                        label_info = LabelInfo(
                            id=label['Id'],
                            language=label['Language'],
                            value=label['Value']
                        )
                        result.append(label_info)
                    
                    return result
                else:
                    print(f"Error fetching labels by prefix: {response.status}")
                    
        except Exception as e:
            print(f"Exception fetching labels by prefix: {e}")
        
        return []
    
    async def get_available_languages(self) -> List[str]:
        """Get list of available languages in the system
        
        Returns:
            List of language codes
        """
        try:
            session = await self.session_manager.get_session()
            
            url = f"{self.metadata_url}/Labels"
            params = {
                "$select": "Language",
                "$orderby": "Language"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    labels = data.get('value', [])
                    languages = list(set(label['Language'] for label in labels if label.get('Language')))
                    return sorted(languages)
                else:
                    print(f"Error fetching languages: {response.status}")
                    
        except Exception as e:
            print(f"Exception fetching languages: {e}")
        
        return []
    
    async def build_label_cache(self, prefixes: List[str] = None, 
                               language: str = "en-US") -> int:
        """Build a cache of commonly used labels
        
        Args:
            prefixes: List of label prefixes to cache (default: common system prefixes)
            language: Language code
            
        Returns:
            Number of labels cached
        """
        if not self.label_cache:
            print("Label caching is disabled")
            return 0
        
        if not prefixes:
            prefixes = ["@SYS", "@SCM", "@RET", "@HCM", "@MCR", "@GLS", "@Proj"]
        
        total_cached = 0
        
        for prefix in prefixes:
            try:
                labels = await self.get_labels_by_prefix(prefix, language, limit=1000)
                self.label_cache.set_batch(labels)
                total_cached += len(labels)
                print(f"Cached {len(labels)} labels for prefix {prefix}")
            except Exception as e:
                print(f"Error caching labels for prefix {prefix}: {e}")
        
        print(f"Total labels cached: {total_cached}")
        return total_cached
    
    async def resolve_entity_labels(self, entity_info: EntityInfo, language: str):
        """Resolve all label IDs in an entity to actual text
        
        Args:
            entity_info: Entity information object to update
            language: Language code
        """
        # Collect all label IDs
        label_ids = []
        if entity_info.label_id:
            label_ids.append(entity_info.label_id)
        
        for prop in entity_info.enhanced_properties:
            if prop.label_id:
                label_ids.append(prop.label_id)
        
        # Batch fetch all labels
        if label_ids:
            labels_map = await self.get_labels_batch(label_ids, language)
            
            # Apply resolved labels
            if entity_info.label_id:
                entity_info.label_text = labels_map.get(entity_info.label_id)
            
            for prop in entity_info.enhanced_properties:
                if prop.label_id:
                    prop.label_text = labels_map.get(prop.label_id)