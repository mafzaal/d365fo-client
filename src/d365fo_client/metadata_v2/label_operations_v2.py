"""Label operations for metadata cache v2."""

import logging
from typing import Dict, List, Optional

from .cache_v2 import MetadataCacheV2
from ..models import LabelInfo
from ..session import SessionManager

logger = logging.getLogger(__name__)


class LabelOperationsV2:
    """Label operations that work with MetadataCacheV2"""
    
    def __init__(self, session_manager: SessionManager, metadata_url: str, 
                 metadata_cache: MetadataCacheV2):
        """Initialize label operations v2
        
        Args:
            session_manager: HTTP session manager
            metadata_url: Metadata API URL
            metadata_cache: Metadata cache v2 instance
        """
        self.session_manager = session_manager
        self.metadata_url = metadata_url
        self.metadata_cache = metadata_cache
    
    async def get_label_text(self, label_id: str, language: str = "en-US") -> Optional[str]:
        """Get actual label text for a specific label ID
        
        Args:
            label_id: Label ID (e.g., "@SYS13342")
            language: Language code (e.g., "en-US")
            
        Returns:
            Label text or None if not found
        """
        # Check cache first
        cached_value = await self.metadata_cache.get_label(label_id, language)
        if cached_value is not None:
            return cached_value
        
        # Fetch from API if not in cache
        try:
            session = await self.session_manager.get_session()
            url = f"{self.metadata_url}/Labels(Id='{label_id}',Language='{language}')"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    label_text = data.get('Value', '')
                    
                    # Cache the result
                    await self.metadata_cache.set_label(label_id, label_text, language)
                    
                    return label_text
                else:
                    logger.warning(f"Error fetching label {label_id}: {response.status}")
                    
        except Exception as e:
            logger.warning(f"Exception fetching label {label_id}: {e}")
        
        return None
    
    async def get_labels_batch(self, label_ids: List[str], 
                              language: str = "en-US") -> Dict[str, str]:
        """Get multiple labels efficiently using batch operations
        
        Args:
            label_ids: List of label IDs
            language: Language code
            
        Returns:
            Dictionary mapping label ID to label text
        """
        if not label_ids:
            return {}
        
        # First, check cache for all labels
        cached_results = await self.metadata_cache.get_labels_batch(label_ids, language)
        
        # Find uncached labels
        uncached_ids = [label_id for label_id in label_ids if label_id not in cached_results]
        
        # Fetch uncached labels from API
        if uncached_ids:
            fetched_labels = []
            for label_id in uncached_ids:
                try:
                    session = await self.session_manager.get_session()
                    url = f"{self.metadata_url}/Labels(Id='{label_id}',Language='{language}')"
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            label_text = data.get('Value', '')
                            cached_results[label_id] = label_text
                            
                            # Prepare for batch cache storage
                            fetched_labels.append(LabelInfo(id=label_id, language=language, value=label_text))
                        else:
                            logger.warning(f"Error fetching label {label_id}: {response.status}")
                            
                except Exception as e:
                    logger.warning(f"Exception fetching label {label_id}: {e}")
            
            # Batch cache all fetched labels
            if fetched_labels:
                await self.metadata_cache.set_labels_batch(fetched_labels)
        
        return cached_results