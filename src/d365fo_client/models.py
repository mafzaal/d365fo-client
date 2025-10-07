"""Data models and data classes for D365 F&O client."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .utils import get_default_cache_directory

if TYPE_CHECKING:
    from typing import ForwardRef
    from .credential_sources import CredentialSource


def _ensure_str_for_json(field):
    """Ensure field is JSON-serializable as string.
    
    StrEnum fields automatically serialize as strings, but this handles
    the edge case where a field might be None or already a string.
    """
    return field  # StrEnum automatically converts to string, None stays None


class EntityCategory(StrEnum):
    """D365 F&O Entity Categories"""

    MASTER = "Master"
    CONFIGURATION = "Configuration"
    TRANSACTION = "Transaction"
    REFERENCE = "Reference"
    DOCUMENT = "Document"
    PARAMETERS = "Parameters"


class ODataXppType(StrEnum):
    """D365 F&O OData XPP Types"""

    CONTAINER = "Container"
    DATE = "Date"
    ENUM = "Enum"
    GUID = "Guid"
    INT32 = "Int32"
    INT64 = "Int64"
    REAL = "Real"
    RECORD = "Record"
    STRING = "String"
    TIME = "Time"
    UTC_DATETIME = "UtcDateTime"
    VOID = "Void"


class ODataBindingKind(StrEnum):
    """D365 F&O Action Binding Types"""

    BOUND_TO_ENTITY_INSTANCE = "BoundToEntityInstance"
    BOUND_TO_ENTITY_SET = "BoundToEntitySet"
    UNBOUND = "Unbound"


class Cardinality(StrEnum):
    """Navigation Property Cardinality"""

    SINGLE = "Single"
    MULTIPLE = "Multiple"


@dataclass
class FOClientConfig:
    """Configuration for F&O Client

    This class handles all configuration options for connecting to and interacting
    with Microsoft Dynamics 365 Finance & Operations environments.

    Authentication is handled through credential_source:
    - If None: Uses Azure Default Credentials (DefaultAzureCredential)
    - If provided: Uses the specified credential source (environment vars, Key Vault, etc.)
    """

    # Core connection settings
    base_url: str
    verify_ssl: bool = False
    timeout: int = 30

    # Authentication - unified through credential source
    credential_source: Optional["CredentialSource"] = None

    # Cache configuration
    metadata_cache_dir: Optional[str] = None
    enable_metadata_cache: bool = True
    use_cache_first: bool = True
    cache_ttl_seconds: int = 300
    max_memory_cache_size: int = 1000
    enable_fts_search: bool = True

    # Label cache settings
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60

    # Sync configuration
    metadata_sync_interval_minutes: int = 60
    language: str = "en-US"

    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Set default cache directory if not provided
        if self.metadata_cache_dir is None:
            self.metadata_cache_dir = get_default_cache_directory()

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.base_url:
            raise ValueError("base_url is required")

        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        if self.timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        if self.label_cache_expiry_minutes <= 0:
            raise ValueError("label_cache_expiry_minutes must be greater than 0")

        if self.metadata_sync_interval_minutes <= 0:
            raise ValueError("metadata_sync_interval_minutes must be greater than 0")

        if self.cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be greater than 0")

        if self.max_memory_cache_size <= 0:
            raise ValueError("max_memory_cache_size must be greater than 0")

    @property
    def uses_default_credentials(self) -> bool:
        """Check if using Azure Default Credentials."""
        return self.credential_source is None

    @property
    def uses_credential_source(self) -> bool:
        """Check if using a specific credential source."""
        return self.credential_source is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        from dataclasses import asdict
        data = asdict(self)

        # Handle credential_source serialization
        if self.credential_source is not None:
            data["credential_source"] = self.credential_source.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FOClientConfig":
        """Create from dictionary with validation and migration."""
        # Migrate legacy credential fields to credential_source
        migrated_data = cls._migrate_legacy_credentials(data.copy())

        # Handle credential_source deserialization
        if "credential_source" in migrated_data and migrated_data["credential_source"] is not None:
            from .credential_sources import CredentialSource
            credential_source_data = migrated_data["credential_source"]
            try:
                migrated_data["credential_source"] = CredentialSource.from_dict(credential_source_data)
            except Exception:
                migrated_data["credential_source"] = None

        # Filter out unknown and deprecated fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in migrated_data.items() if k in valid_fields}

        return cls(**filtered_data)

    @classmethod
    def _migrate_legacy_credentials(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy credential fields to credential_source."""
        # Check for legacy credential fields
        legacy_fields = ["client_id", "client_secret", "tenant_id", "auth_mode", "use_default_credentials"]
        has_legacy_creds = any(field in data for field in legacy_fields)

        if has_legacy_creds and "credential_source" not in data:
            # Determine if we should use default credentials
            use_default = data.get("use_default_credentials", True)
            # Check if explicit credentials are provided
            client_id = data.get("client_id")
            client_secret = data.get("client_secret")
            tenant_id = data.get("tenant_id")

            has_explicit_creds = all([client_id, client_secret, tenant_id])

            if not use_default and has_explicit_creds:
                # Create environment credential source for backward compatibility
                from .credential_sources import EnvironmentCredentialSource
                data["credential_source"] = EnvironmentCredentialSource().to_dict()
            # If use_default or no explicit creds, credential_source remains None (default creds)

        # Remove legacy fields
        for field in legacy_fields:
            data.pop(field, None)

        return data


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
        return {"id": self.id, "language": self.language, "value": self.value}


@dataclass
class ActionParameterTypeInfo:
    """Type information for action parameters"""

    type_name: str
    is_collection: bool = False
    odata_xpp_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_name": self.type_name,
            "is_collection": self.is_collection,
            "odata_xpp_type": self.odata_xpp_type,
        }


@dataclass
class ActionParameterInfo:
    """Information about an action parameter"""

    name: str
    type: ActionParameterTypeInfo
    parameter_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.to_dict(),
            "parameter_order": self.parameter_order,
        }


@dataclass
class ActionReturnTypeInfo:
    """Return type information for actions"""

    type_name: str
    is_collection: bool = False
    odata_xpp_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_name": self.type_name,
            "is_collection": self.is_collection,
            "odata_xpp_type": self.odata_xpp_type,
        }


@dataclass
class PublicEntityActionInfo:
    """Detailed action information from PublicEntities endpoint"""

    name: str
    binding_kind: ODataBindingKind
    parameters: List[ActionParameterInfo] = None
    return_type: Optional[ActionReturnTypeInfo] = None
    field_lookup: Optional[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "binding_kind": self.binding_kind,  # StrEnum automatically serializes as string
            "parameters": [param.to_dict() for param in self.parameters],
            "return_type": self.return_type.to_dict() if self.return_type else None,
            "field_lookup": self.field_lookup,
        }


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
    entity_category: Optional[EntityCategory] = None
    is_read_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "public_entity_name": self.public_entity_name,
            "public_collection_name": self.public_collection_name,
            "label_id": self.label_id,
            "label_text": self.label_text,
            "data_service_enabled": self.data_service_enabled,
            "data_management_enabled": self.data_management_enabled,
            "entity_category": self.entity_category,  # StrEnum automatically serializes as string
            "is_read_only": self.is_read_only,
        }


@dataclass
class PublicEntityPropertyInfo:
    """Detailed property information from PublicEntities endpoint"""

    name: str
    type_name: str
    data_type: str
    odata_xpp_type: Optional[str] = None  # Map to D365 internal types
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
    property_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_name": self.type_name,
            "data_type": self.data_type,
            "odata_xpp_type": self.odata_xpp_type,
            "label_id": self.label_id,
            "label_text": self.label_text,
            "is_key": self.is_key,
            "is_mandatory": self.is_mandatory,
            "configuration_enabled": self.configuration_enabled,
            "allow_edit": self.allow_edit,
            "allow_edit_on_create": self.allow_edit_on_create,
            "is_dimension": self.is_dimension,
            "dimension_relation": self.dimension_relation,
            "is_dynamic_dimension": self.is_dynamic_dimension,
            "dimension_legal_entity_property": self.dimension_legal_entity_property,
            "dimension_type_property": self.dimension_type_property,
            "property_order": self.property_order,
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
    properties: List[PublicEntityPropertyInfo] = field(default_factory=list)
    navigation_properties: List["NavigationPropertyInfo"] = field(default_factory=list)
    property_groups: List["PropertyGroupInfo"] = field(default_factory=list)
    actions: List["PublicEntityActionInfo"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_set_name": self.entity_set_name,
            "label_id": self.label_id,
            "label_text": self.label_text,
            "is_read_only": self.is_read_only,
            "configuration_enabled": self.configuration_enabled,
            "properties": [prop.to_dict() for prop in self.properties],
            "navigation_properties": [
                nav.to_dict() for nav in self.navigation_properties
            ],
            "property_groups": [group.to_dict() for group in self.property_groups],
            "actions": [action.to_dict() for action in self.actions],
        }


@dataclass
class EnumerationMemberInfo:
    """Information about an enumeration member"""

    name: str
    value: int
    label_id: Optional[str] = None
    label_text: Optional[str] = None
    configuration_enabled: bool = True
    member_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "label_id": self.label_id,
            "label_text": self.label_text,
            "configuration_enabled": self.configuration_enabled,
            "member_order": self.member_order,
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
            "name": self.name,
            "label_id": self.label_id,
            "label_text": self.label_text,
            "members": [member.to_dict() for member in self.members],
        }


# Enhanced Complex Type Models


@dataclass
class RelationConstraintInfo:
    """Base relation constraint information"""

    constraint_type: str = field(init=False)  # "Referential"|"Fixed"|"RelatedFixed" - set by __post_init__ in subclasses

    def to_dict(self) -> Dict[str, Any]:
        return {"constraint_type": self.constraint_type}


@dataclass
class ReferentialConstraintInfo(RelationConstraintInfo):
    """Referential constraint (foreign key relationship)"""

    property: str
    referenced_property: str

    def __post_init__(self):
        self.constraint_type = "Referential"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {"property": self.property, "referenced_property": self.referenced_property}
        )
        return result


@dataclass
class FixedConstraintInfo(RelationConstraintInfo):
    """Fixed value constraint"""

    property: str
    value: Optional[int] = None
    value_str: Optional[str] = None

    def __post_init__(self):
        self.constraint_type = "Fixed"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "property": self.property,
                "value": self.value,
                "value_str": self.value_str,
            }
        )
        return result


@dataclass
class RelatedFixedConstraintInfo(RelationConstraintInfo):
    """Related fixed constraint"""

    related_property: str
    value: Optional[int] = None
    value_str: Optional[str] = None

    def __post_init__(self):
        self.constraint_type = "RelatedFixed"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "related_property": self.related_property,
                "value": self.value,
                "value_str": self.value_str,
            }
        )
        return result


@dataclass
class NavigationPropertyInfo:
    """Navigation property with full constraint support"""

    name: str
    related_entity: str
    related_relation_name: Optional[str] = None
    cardinality: Cardinality = Cardinality.SINGLE
    constraints: List["RelationConstraintInfo"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "related_entity": self.related_entity,
            "related_relation_name": self.related_relation_name,
            "cardinality": self.cardinality,  # StrEnum automatically serializes as string
            "constraints": [constraint.to_dict() for constraint in self.constraints],
        }


@dataclass
class PropertyGroupInfo:
    """Property group information"""

    name: str
    properties: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "properties": self.properties}


@dataclass
class ActionTypeInfo:
    """Action type with D365-specific type mapping"""

    type_name: str
    is_collection: bool = False
    odata_xpp_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_name": self.type_name,
            "is_collection": self.is_collection,
            "odata_xpp_type": self.odata_xpp_type,
        }


# @dataclass
# class ActionParameterInfo:
#     """Enhanced action parameter information"""

#     name: str
#     type: "ActionTypeInfo"
#     parameter_order: int = 0

#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             "name": self.name,
#             "type": self.type.to_dict(),
#             "parameter_order": self.parameter_order,
#         }


@dataclass
class ActionInfo:
    """Complete action information with binding support"""

    name: str
    binding_kind: ODataBindingKind = ODataBindingKind.BOUND_TO_ENTITY_SET
    entity_name: Optional[str] = None  # For bound actions (public entity name)
    entity_set_name: Optional[str] = (
        None  # For bound actions (entity set name for OData URLs)
    )
    parameters: List["ActionParameterInfo"] = field(default_factory=list)
    return_type: Optional["ActionReturnTypeInfo"] = None
    field_lookup: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "binding_kind": self.binding_kind,  # StrEnum automatically serializes as string
            "entity_name": self.entity_name,
            "entity_set_name": self.entity_set_name,
            "parameters": [param.to_dict() for param in self.parameters],
            "return_type": self.return_type.to_dict() if self.return_type else None,
            "field_lookup": self.field_lookup,
        }


# Cache and Search Models


@dataclass
class MetadataVersionInfo:
    """Metadata version information"""

    environment_id: int
    version_hash: str
    application_version: Optional[str] = None
    platform_version: Optional[str] = None
    package_info: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class SearchQuery:
    """Advanced search query parameters"""

    text: str
    entity_types: Optional[List[str]] = (
        None  # data_entity|public_entity|enumeration|action
    )
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50
    offset: int = 0
    use_fulltext: bool = True
    include_properties: bool = False
    include_actions: bool = False


@dataclass
class SearchResult:
    """Individual search result"""

    name: str
    entity_type: str
    description: Optional[str] = None
    relevance: float = 0.0
    snippet: Optional[str] = None
    entity_set_name: Optional[str] = None
    label_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "relevance": self.relevance,
            "snippet": self.snippet,
            "entity_set_name": self.entity_set_name,
            "label_text": self.label_text,
        }


@dataclass
class SearchResults:
    """Search results container"""

    results: List[SearchResult]
    total_count: int = 0
    query_time_ms: float = 0.0
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [result.to_dict() for result in self.results],
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "cache_hit": self.cache_hit,
        }


# ============================================================================
# JSON Service Models
# ============================================================================


@dataclass
class JsonServiceRequest:
    """Request for D365 F&O JSON service endpoint"""
    
    service_group: str
    service_name: str
    operation_name: str
    parameters: Optional[Dict[str, Any]] = None
    
    def get_endpoint_path(self) -> str:
        """Get the endpoint path for the service"""
        return f"/api/services/{self.service_group}/{self.service_name}/{self.operation_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_group": self.service_group,
            "service_name": self.service_name,
            "operation_name": self.operation_name,
            "parameters": self.parameters
        }


@dataclass 
class JsonServiceResponse:
    """Response from D365 F&O JSON service endpoint"""
    
    success: bool
    data: Any
    status_code: int
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "status_code": self.status_code,
            "error_message": self.error_message
        }


# ============================================================================
# Enhanced V2 Models for Advanced Metadata Caching
# ============================================================================


@dataclass
class ModuleVersionInfo:
    """Information about installed D365 module based on GetInstalledModules response"""

    name: str  # Module name (e.g., "AccountsPayableMobile")
    version: str  # Version string (e.g., "10.34.2105.34092")
    module_id: str  # Module identifier (e.g., "AccountsPayableMobile")
    publisher: str  # Publisher (e.g., "Microsoft Corporation")
    display_name: str  # Human-readable name (e.g., "Accounts Payable Mobile")

    @classmethod
    def parse_from_string(cls, module_string: str) -> "ModuleVersionInfo":
        """Parse module info from GetInstalledModules string format

        Args:
            module_string: String in format "Name: X | Version: Y | Module: Z | Publisher: W | DisplayName: V"

        Returns:
            ModuleVersionInfo instance

        Raises:
            ValueError: If string format is invalid
        """
        try:
            parts = module_string.split(" | ")
            if len(parts) != 5:
                raise ValueError(
                    f"Invalid module string format: expected 5 parts, got {len(parts)}"
                )

            name = parts[0].replace("Name: ", "")
            version = parts[1].replace("Version: ", "")
            module_id = parts[2].replace("Module: ", "")
            publisher = parts[3].replace("Publisher: ", "")
            display_name = parts[4].replace("DisplayName: ", "")

            # Validate that all parts are non-empty
            if not all([name, version, module_id, publisher, display_name]):
                raise ValueError("All module string parts must be non-empty")

            return cls(
                name=name,
                version=version,
                module_id=module_id,
                publisher=publisher,
                display_name=display_name,
            )
        except Exception as e:
            raise ValueError(f"Failed to parse module string '{module_string}': {e}")

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "version": self.version,
            "module_id": self.module_id,
            "publisher": self.publisher,
            "display_name": self.display_name,
        }


@dataclass
class EnvironmentVersionInfo:
    """Enhanced environment version with precise module tracking"""

    environment_id: int
    version_hash: str  # Fast hash based on all module versions
    modules_hash: str  # Hash of sorted module list for deduplication
    application_version: Optional[str] = None  # Fallback version info
    platform_version: Optional[str] = None  # Fallback version info
    modules: List[ModuleVersionInfo] = field(default_factory=list)
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    def __post_init__(self):
        """Ensure version hashes are computed if not provided"""
        if not self.modules_hash and self.modules:
            self.modules_hash = self._compute_modules_hash()
        if not self.version_hash:
            self.version_hash = self.modules_hash[
                :16
            ]  # Use first 16 chars for compatibility

    def _compute_modules_hash(self) -> str:
        """Compute hash based on sorted module versions for consistent deduplication"""
        if not self.modules:
            return hashlib.sha256("empty".encode()).hexdigest()

        # Sort modules by module_id for consistent hashing
        sorted_modules = sorted(self.modules, key=lambda m: m.module_id)

        # Create hash input from essential version data
        hash_data = []
        for module in sorted_modules:
            hash_data.append(f"{module.module_id}:{module.version}")

        hash_input = "|".join(hash_data)
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "environment_id": self.environment_id,
            "version_hash": self.version_hash,
            "modules_hash": self.modules_hash,
            "application_version": self.application_version,
            "platform_version": self.platform_version,
            "modules": [module.to_dict() for module in self.modules],
            "computed_at": self.computed_at.isoformat(),
            "is_active": self.is_active,
        }


@dataclass
class GlobalVersionInfo:
    """Global version registry for cross-environment sharing"""

    id: int
    version_hash: str
    modules_hash: str
    first_seen_at: datetime
    last_used_at: datetime
    reference_count: int
    modules: List[ModuleVersionInfo] = field(
        default_factory=list
    )  # Modules for debugging

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "version_hash": self.version_hash,
            "modules_hash": self.modules_hash,
            "first_seen_at": self.first_seen_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat(),
            "reference_count": self.reference_count,
            "modules": [module.to_dict() for module in self.modules],
        }


@dataclass
class CacheStatistics:
    """Enhanced cache statistics with version sharing metrics"""

    total_environments: int
    unique_versions: int
    shared_versions: int
    cache_hit_ratio: float
    storage_efficiency: float  # Ratio of shared vs duplicate storage
    last_sync_times: Dict[str, datetime]
    version_distribution: Dict[str, int]  # version_hash -> environment_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_environments": self.total_environments,
            "unique_versions": self.unique_versions,
            "shared_versions": self.shared_versions,
            "cache_hit_ratio": self.cache_hit_ratio,
            "storage_efficiency": self.storage_efficiency,
            "last_sync_times": {
                k: v.isoformat() for k, v in self.last_sync_times.items()
            },
            "version_distribution": self.version_distribution,
        }


@dataclass
class VersionDetectionResult:
    """Result of version detection operation"""

    success: bool
    version_info: Optional[EnvironmentVersionInfo] = None
    error_message: Optional[str] = None
    detection_time_ms: float = 0.0
    modules_count: int = 0
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "version_info": self.version_info.to_dict() if self.version_info else None,
            "error_message": self.error_message,
            "detection_time_ms": self.detection_time_ms,
            "modules_count": self.modules_count,
            "cache_hit": self.cache_hit,
        }


