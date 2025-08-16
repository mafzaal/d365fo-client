"""Data models and data classes for D365 F&O client."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .utils import get_environment_cache_directory


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
            self.metadata_cache_dir = get_environment_cache_directory(self.base_url)


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


@dataclass
class DataEntityInfo:
    """Information about a data entity from DataEntities endpoint"""
    name: str
    public_entity_name: str
    public_collection_name: str
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    data_service_enabled: bool = True
    data_management_enabled: bool = True
    entity_category: Optional[str] = None
    is_read_only: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'public_entity_name': self.public_entity_name,
            'public_collection_name': self.public_collection_name,
            'label_id': self.label_id,
            'label_text': self.label_text,
            'data_service_enabled': self.data_service_enabled,
            'data_management_enabled': self.data_management_enabled,
            'entity_category': self.entity_category,
            'is_read_only': self.is_read_only
        }


@dataclass
class PublicEntityPropertyInfo:
    """Detailed property information from PublicEntities endpoint"""
    name: str
    type_name: str
    data_type: str
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    is_key: bool = False
    is_mandatory: bool = False
    configuration_enabled: bool = True
    allow_edit: bool = True
    allow_edit_on_create: bool = True
    is_dimension: bool = False
    dimension_relation: Optional[str] = None
    is_dynamic_dimension: bool = False
    dimension_legal_entity_property: Optional[str] = None
    dimension_type_property: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type_name': self.type_name,
            'data_type': self.data_type,
            'label_id': self.label_id,
            'label_text': self.label_text,
            'is_key': self.is_key,
            'is_mandatory': self.is_mandatory,
            'configuration_enabled': self.configuration_enabled,
            'allow_edit': self.allow_edit,
            'allow_edit_on_create': self.allow_edit_on_create,
            'is_dimension': self.is_dimension,
            'dimension_relation': self.dimension_relation,
            'is_dynamic_dimension': self.is_dynamic_dimension,
            'dimension_legal_entity_property': self.dimension_legal_entity_property,
            'dimension_type_property': self.dimension_type_property
        }


@dataclass
class PublicEntityInfo:
    """Enhanced entity information from PublicEntities endpoint"""
    name: str
    entity_set_name: str
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    is_read_only: bool = False
    configuration_enabled: bool = True
    properties: List[PublicEntityPropertyInfo] = None
    navigation_properties: List[Dict[str, Any]] = None
    property_groups: List[Dict[str, Any]] = None
    actions: List[str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = []
        if self.navigation_properties is None:
            self.navigation_properties = []
        if self.property_groups is None:
            self.property_groups = []
        if self.actions is None:
            self.actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'entity_set_name': self.entity_set_name,
            'label_id': self.label_id,
            'label_text': self.label_text,
            'is_read_only': self.is_read_only,
            'configuration_enabled': self.configuration_enabled,
            'properties': [prop.to_dict() for prop in self.properties],
            'navigation_properties': self.navigation_properties,
            'property_groups': self.property_groups,
            'actions': self.actions
        }


@dataclass
class EnumerationMemberInfo:
    """Information about an enumeration member"""
    name: str
    value: int
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    configuration_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'label_id': self.label_id,
            'label_text': self.label_text,
            'configuration_enabled': self.configuration_enabled
        }


@dataclass
class EnumerationInfo:
    """Information about an enumeration from PublicEnumerations endpoint"""
    name: str
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    members: List[EnumerationMemberInfo] = None
    
    def __post_init__(self):
        if self.members is None:
            self.members = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'label_id': self.label_id,
            'label_text': self.label_text,
            'members': [member.to_dict() for member in self.members]
        }