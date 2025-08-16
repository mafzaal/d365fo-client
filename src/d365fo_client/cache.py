"""Label caching functionality for D365 F&O client."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import LabelInfo


class LabelCache:
    """Simple in-memory label cache with expiration"""
    
    def __init__(self, expiry_minutes: int = 60):
        """Initialize label cache
        
        Args:
            expiry_minutes: Cache expiration time in minutes
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._expiry_minutes = expiry_minutes
        self._last_updated: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if cache is expired
        
        Returns:
            True if cache is expired
        """
        if not self._last_updated:
            return True
        return datetime.now() - self._last_updated > timedelta(minutes=self._expiry_minutes)
    
    def get(self, label_id: str, language: str = "en-US") -> Optional[str]:
        """Get label text from cache
        
        Args:
            label_id: Label identifier
            language: Language code
            
        Returns:
            Label text or None if not found/expired
        """
        if self.is_expired():
            return None
        
        key = f"{label_id}|{language}"
        return self._cache.get(key, {}).get('value')
    
    def set(self, label_id: str, language: str, value: str):
        """Set label text in cache
        
        Args:
            label_id: Label identifier
            language: Language code
            value: Label text value
        """
        key = f"{label_id}|{language}"
        self._cache[key] = {
            'value': value,
            'cached_at': datetime.now()
        }
        self._last_updated = datetime.now()
    
    def set_batch(self, labels: List[LabelInfo]):
        """Set multiple labels in cache
        
        Args:
            labels: List of LabelInfo objects
        """
        for label in labels:
            self.set(label.id, label.language, label.value)
    
    def clear(self):
        """Clear the cache"""
        self._cache.clear()
        self._last_updated = None
    
    def size(self) -> int:
        """Get cache size
        
        Returns:
            Number of cached labels
        """
        return len(self._cache)
    
    def get_info(self) -> Dict[str, Any]:
        """Get cache information
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": self.size(),
            "expired": self.is_expired(),
            "last_updated": self._last_updated.isoformat() if self._last_updated else None,
            "expiry_minutes": self._expiry_minutes
        }