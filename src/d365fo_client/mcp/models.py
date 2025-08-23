"""MCP-specific models and data structures."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Resource Models


@dataclass
class EntityProperty:
    name: str
    type: str
    is_key: bool
    is_required: bool
    max_length: Optional[int] = None
    label: Optional[str] = None
    description: Optional[str] = None


@dataclass
class EntityMetadata:
    name: str
    entity_set_name: str
    keys: List[str]
    properties: List[EntityProperty]
    is_read_only: bool
    label_text: Optional[str] = None


@dataclass
class EntityResourceContent:
    metadata: Optional[EntityMetadata]
    sample_data: Optional[List[Dict[str, Any]]] = None
    record_count: Optional[int] = None
    last_updated: Optional[str] = None


class MetadataType(Enum):
    ENTITIES = "entities"
    ACTIONS = "actions"
    ENUMERATIONS = "enumerations"
    LABELS = "labels"


@dataclass
class MetadataStatistics:
    categories: Dict[str, int]
    capabilities: Dict[str, int]


@dataclass
class MetadataResourceContent:
    type: MetadataType
    count: int
    last_updated: str
    items: List[Dict[str, Any]]
    statistics: Optional[MetadataStatistics] = None


@dataclass
class VersionInfo:
    application: str
    platform: str
    build: str


@dataclass
class ConnectivityStatus:
    data_endpoint: bool
    metadata_endpoint: bool
    last_tested: str


@dataclass
class CacheInfo:
    size: int
    last_updated: str
    hit_rate: float


@dataclass
class CacheStatus:
    metadata: CacheInfo
    labels: CacheInfo


@dataclass
class EnvironmentResourceContent:
    base_url: str
    version: VersionInfo
    connectivity: ConnectivityStatus
    cache: CacheStatus


@dataclass
class QueryParameter:
    name: str
    type: str
    required: bool
    description: str
    default_value: Optional[Any] = None


@dataclass
class QueryResourceContent:
    entity_name: str
    select: Optional[List[str]] = None
    filter: Optional[str] = None
    expand: Optional[List[str]] = None
    order_by: Optional[List[str]] = None
    top: Optional[int] = None
    skip: Optional[int] = None
    template: bool = False
    parameters: Optional[List[QueryParameter]] = None


# Tool Input/Output Models


@dataclass
class TestConnectionInput:
    base_url: Optional[str] = None
    timeout: Optional[int] = None


@dataclass
class EndpointStatus:
    data: bool
    metadata: bool


@dataclass
class TestConnectionOutput:
    success: bool
    endpoints: EndpointStatus
    response_time: float
    error: Optional[str] = None


@dataclass
class EnvironmentInfoOutput:
    base_url: str
    versions: VersionInfo
    connectivity: bool
    cache_status: CacheStatus
    statistics: Optional[Dict[str, int]] = None


@dataclass
class SyncMetadataInput:
    force_refresh: bool = False
    include_labels: bool = True
    include_actions: bool = True


@dataclass
class SyncStatistics:
    entities_downloaded: int
    actions_downloaded: int
    labels_downloaded: int


@dataclass
class SyncMetadataOutput:
    success: bool
    sync_time: float
    statistics: SyncStatistics
    cache_location: str


@dataclass
class SearchEntitiesInput:
    pattern: str
    entity_category: Optional[str] = None
    data_service_enabled: Optional[bool] = None
    data_management_enabled: Optional[bool] = None
    is_read_only: Optional[bool] = None
    limit: int = 100


@dataclass
class SearchEntitiesOutput:
    entities: List[Dict[str, Any]]
    total_count: int
    search_time: float


@dataclass
class QueryEntitiesInput:
    entity_name: str
    select: Optional[List[str]] = None
    filter: Optional[str] = None
    expand: Optional[List[str]] = None
    order_by: Optional[List[str]] = None
    top: Optional[int] = None
    skip: Optional[int] = None
    count: bool = False
    search: Optional[str] = None


@dataclass
class QueryEntitiesOutput:
    data: List[Dict[str, Any]]
    count: Optional[int] = None
    next_link: Optional[str] = None
    query_time: float = 0.0
    total_records: Optional[int] = None


@dataclass
class GetEntityRecordInput:
    entity_name: str
    key: Union[str, Dict[str, Any]]
    select: Optional[List[str]] = None
    expand: Optional[List[str]] = None


@dataclass
class GetEntityRecordOutput:
    record: Optional[Dict[str, Any]]
    found: bool
    retrieval_time: float


@dataclass
class CreateEntityRecordInput:
    entity_name: str
    data: Dict[str, Any]
    return_record: bool = False


@dataclass
class CreateEntityRecordOutput:
    success: bool
    record_id: Optional[str] = None
    created_record: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[str]] = None


@dataclass
class UpdateEntityRecordInput:
    entity_name: str
    key: Union[str, Dict[str, Any]]
    data: Dict[str, Any]
    return_record: bool = False
    if_match: Optional[str] = None


@dataclass
class UpdateEntityRecordOutput:
    success: bool
    updated_record: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[str]] = None
    conflict_detected: bool = False


@dataclass
class DeleteEntityRecordInput:
    entity_name: str
    key: Union[str, Dict[str, Any]]
    if_match: Optional[str] = None


@dataclass
class DeleteEntityRecordOutput:
    success: bool
    conflict_detected: bool = False
    error: Optional[str] = None


@dataclass
class GetLabelInput:
    label_id: str
    language: str = "en-US"
    fallback_to_english: bool = True


@dataclass
class GetLabelOutput:
    label_id: str
    text: str
    language: str
    found: bool


@dataclass
class GetLabelsBatchInput:
    label_ids: List[str]
    language: str = "en-US"
    fallback_to_english: bool = True


@dataclass
class GetLabelsBatchOutput:
    labels: Dict[str, str]
    missing_labels: List[str]
    retrieval_time: float


# Error Models


@dataclass
class D365FOErrorDetails:
    http_status: int
    error_code: str
    error_message: str
    correlation_id: Optional[str] = None


@dataclass
class MCPErrorDetails:
    d365fo_error: Optional[D365FOErrorDetails] = None
    validation_errors: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class MCPError:
    code: str
    message: str
    timestamp: str
    details: Optional[MCPErrorDetails] = None
    tool: Optional[str] = None
    retryable: bool = False


# Configuration Models


@dataclass
class PerformanceConfig:
    max_concurrent_requests: int = 10
    connection_pool_size: int = 5
    request_timeout: int = 30
    batch_size: int = 100


@dataclass
class CacheConfig:
    metadata_cache_dir: str
    label_cache_expiry_minutes: int = 120
    use_label_cache: bool = True
    cache_size_limit_mb: int = 100


@dataclass
class SecurityConfig:
    encrypt_cached_tokens: bool = True
    token_expiry_buffer_minutes: int = 5
    max_retry_attempts: int = 3


@dataclass
class MCPServerConfig:
    name: str = "d365fo-mcp-server"
    version: str = "1.0.0"
    description: str = "MCP Server for Microsoft Dynamics 365 Finance & Operations"
    performance: PerformanceConfig = None
    cache: CacheConfig = None
    security: SecurityConfig = None

    def __post_init__(self):
        if self.performance is None:
            self.performance = PerformanceConfig()
        if self.cache is None:
            self.cache = CacheConfig(metadata_cache_dir="~/.d365fo-mcp/cache")
        if self.security is None:
            self.security = SecurityConfig()
