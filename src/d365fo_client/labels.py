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
        """Get multiple labels by calling get_label_text for each ID
        
        Args:
            label_ids: List of label IDs
            language: Language code
            
        Returns:
            Dictionary mapping label ID to label text
        """
        if not label_ids:
            return {}
        
        results = {}
        
        # Use get_label_text for each label ID to leverage caching and error handling
        for label_id in label_ids:
            label_text = await self.get_label_text(label_id, language)
            if label_text is not None:
                results[label_id] = label_text
        
        return results
    

    

    

    

    
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