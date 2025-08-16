"""Data models and data classes for D365 F&O client."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .utils import get_default_cache_directory


@dataclass
class FOClientConfig:
    """Configuration for F&O Client"""
    base_url: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    use_default_credentials: bool = True
    verify_ssl: bool = False
    metadata_cache_dir: str = None
    timeout: int = 30
    # Label cache configuration
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60
    
    def __post_init__(self):
        """Post-initialization to set default cache directory if not provided."""
        if self.metadata_cache_dir is None:
            self.metadata_cache_dir = get_default_cache_directory()


@dataclass
class QueryOptions:
    """OData query options"""
    select: Optional[List[str]] = None
    filter: Optional[str] = None
    expand: Optional[List[str]] = None
    orderby: Optional[List[str]] = None
    top: Optional[int] = None
    skip: Optional[int] = None
    count: bool = False
    search: Optional[str] = None


@dataclass
class LabelInfo:
    """Information about a label"""
    id: str
    language: str
    value: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'id': self.id,
            'language': self.language, 
            'value': self.value
        }


@dataclass
class EntityPropertyInfo:
    """Information about an entity property with label"""
    name: str
    type_name: str
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    is_key: bool = False
    is_mandatory: bool = False
    allow_edit: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type_name': self.type_name,
            'label_id': self.label_id,
            'label_text': self.label_text,
            'is_key': self.is_key,
            'is_mandatory': self.is_mandatory,
            'allow_edit': self.allow_edit
        }


@dataclass
class EntityInfo:
    """Entity metadata information"""
    name: str
    keys: List[str]
    properties: List[Dict[str, Any]]
    actions: List[str]
    # Enhanced with label information
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    entity_set_name: Optional[str] = None
    is_read_only: bool = False
    enhanced_properties: List[EntityPropertyInfo] = None
    
    def __post_init__(self):
        if self.enhanced_properties is None:
            self.enhanced_properties = []


@dataclass
class ActionInfo:
    """Action metadata information"""
    name: str
    is_bound: bool
    entity_set_path: str
    parameters: List[Dict[str, Any]]
    return_type: str
    annotations: List[Dict[str, Any]]