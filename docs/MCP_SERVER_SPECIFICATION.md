# MCP Server Specification for d365fo-client

## Overview

This document provides a comprehensive specification for implementing a Model Context Protocol (MCP) server for the d365fo-client Python package. The MCP server will expose the full capabilities of the d365fo-client to AI assistants and other MCP-compatible tools, enabling sophisticated Microsoft Dynamics 365 Finance & Operations integration workflows.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Resource Definitions](#resource-definitions)
3. [Tool Definitions](#tool-definitions)
4. [Prompt Definitions](#prompt-definitions)
5. [Configuration Management](#configuration-management)
6. [Error Handling](#error-handling)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)
9. [Implementation Guidelines](#implementation-guidelines)
10. [Testing Strategy](#testing-strategy)

## Architecture Overview

### Core Components

```
MCP Server for d365fo-client
├── Server Core
│   ├── MCP Protocol Handler
│   ├── D365FO Client Manager
│   ├── Session Pool Manager
│   └── Configuration Manager
├── Resource Handlers
│   ├── Entity Resource Handler
│   ├── Metadata Resource Handler
│   ├── Action Resource Handler
│   └── Label Resource Handler
├── Tool Handlers
│   ├── Connection Tools
│   ├── CRUD Operation Tools
│   ├── Query Tools
│   ├── Metadata Tools
│   ├── Action Tools
│   └── Utility Tools
└── Utility Components
    ├── Authentication Manager
    ├── Cache Manager
    ├── Error Handler
    └── Logging Manager
```

### Design Principles

1. **Stateless Operations**: Each tool call should be independent
2. **Resource Efficiency**: Reuse client connections where possible
3. **Error Resilience**: Graceful handling of D365FO environment issues
4. **Type Safety**: Full type validation for all inputs and outputs
5. **Extensibility**: Easy addition of new tools and resources
6. **Performance**: Optimal caching and session management

## Resource Definitions

### 1. Entity Resources

Resources representing D365FO data entities with their metadata and current state.

```python
from dataclasses import dataclass
from typing import Optional, List, Any, Dict
from datetime import datetime

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

@dataclass
class EntityResource:
    uri: str  # f"d365fo://entities/{entity_name}"
    name: str
    description: str
    mime_type: str = "application/json"
    content: Optional[EntityResourceContent] = None
```

#### Example Resource URIs:
- `d365fo://entities/Customers` - Customer entity metadata and sample data
- `d365fo://entities/SalesOrders` - Sales order entity information
- `d365fo://entities/Products` - Product entity details

### 2. Metadata Resources

Resources representing D365FO system metadata, including entity schemas, actions, and enumerations.

```python
from enum import Enum
from typing import Union, Dict, Any

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
class MetadataResource:
    uri: str  # f"d365fo://metadata/{metadata_type}"
    name: str
    description: str
    mime_type: str = "application/json"
    content: Optional[MetadataResourceContent] = None
```

#### Example Resource URIs:
- `d365fo://metadata/entities` - All data entities metadata
- `d365fo://metadata/actions` - Available OData actions
- `d365fo://metadata/enumerations` - System enumerations
- `d365fo://metadata/labels` - System labels and translations

### 3. Environment Resources

Resources representing D365FO environment information and status.

```python
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
class EnvironmentResource:
    uri: str  # f"d365fo://environment/{aspect}"
    name: str
    description: str
    mime_type: str = "application/json"
    content: Optional[EnvironmentResourceContent] = None
```

#### Example Resource URIs:
- `d365fo://environment/status` - Environment health and connectivity
- `d365fo://environment/version` - Version information
- `d365fo://environment/cache` - Cache status and statistics

### 4. Query Resources

Resources representing saved or templated OData queries.

```python
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

@dataclass
class QueryResource:
    uri: str  # f"d365fo://queries/{query_name}"
    name: str
    description: str
    mime_type: str = "application/json"
    content: Optional[QueryResourceContent] = None
```

## Tool Definitions

### 1. Connection and Testing Tools

#### Tool: `d365fo_test_connection`
Test connectivity to D365FO environment.

```python
@dataclass
class TestConnectionInput:
    base_url: Optional[str] = None  # Override default base URL
    timeout: Optional[int] = None  # Connection timeout in seconds

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
```

#### Tool: `d365fo_get_environment_info`
Get comprehensive environment information.

```python
@dataclass
class VersionInfo:
    application: str
    platform: str
    build: str

@dataclass
class CacheStatus:
    metadata: bool
    labels: bool

@dataclass
class StatisticsInfo:
    entity_count: int
    action_count: int
    label_count: int

@dataclass
class EnvironmentInfoOutput:
    base_url: str
    versions: VersionInfo
    connectivity: bool
    cache_status: CacheStatus
    statistics: Optional[StatisticsInfo] = None
```

### 2. Metadata Management Tools

#### Tool: `d365fo_sync_metadata`
Download and cache metadata from D365FO.

```python
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
```

#### Tool: `d365fo_search_entities`
Search for entities by name or pattern.

```python
from d365fo_client.models import EntityCategory

@dataclass
class SearchEntitiesInput:
    pattern: str
    entity_category: Optional[EntityCategory] = None
    data_service_enabled: Optional[bool] = None
    data_management_enabled: Optional[bool] = None
    is_read_only: Optional[bool] = None
    limit: int = 100

@dataclass
class SearchEntitiesOutput:
    entities: List[EntityInfo]
    total_count: int
    search_time: float
```

#### Tool: `d365fo_get_entity_schema`
Get detailed schema information for a specific entity.

```python
@dataclass
class GetEntitySchemaInput:
    entity_name: str
    include_properties: bool = True
    include_navigation_properties: bool = False
    resolve_labels: bool = True
    language: str = "en-US"

@dataclass
class NavigationProperty:
    name: str
    target_entity: str
    cardinality: str
    relationship_type: str

@dataclass
class EntityRelationship:
    name: str
    related_entity: str
    relationship_type: str
    foreign_key: str

@dataclass
class DetailedEntityInfo:
    name: str
    entity_set_name: str
    label_text: Optional[str]
    is_read_only: bool
    entity_category: Optional[str]

@dataclass
class GetEntitySchemaOutput:
    entity: DetailedEntityInfo
    properties: List[EntityPropertyInfo]
    navigation_properties: Optional[List[NavigationProperty]] = None
    actions: Optional[List[str]] = None
    relationships: Optional[List[EntityRelationship]] = None
```

### 3. CRUD Operation Tools

#### Tool: `d365fo_query_entities`
Query entities with advanced OData parameters.

```python
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
```

#### Tool: `d365fo_get_entity_record`
Get a specific entity record by key.

```python
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
```

#### Tool: `d365fo_create_entity_record`
Create a new entity record.

```python
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
```

#### Tool: `d365fo_update_entity_record`
Update an existing entity record.

```python
@dataclass
class UpdateEntityRecordInput:
    entity_name: str
    key: Union[str, Dict[str, Any]]
    data: Dict[str, Any]
    return_record: bool = False
    if_match: Optional[str] = None  # ETag for optimistic concurrency

@dataclass
class UpdateEntityRecordOutput:
    success: bool
    updated_record: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[str]] = None
    conflict_detected: bool = False
```

#### Tool: `d365fo_delete_entity_record`
Delete an entity record.

```python
@dataclass
class DeleteEntityRecordInput:
    entity_name: str
    key: Union[str, Dict[str, Any]]
    if_match: Optional[str] = None  # ETag for optimistic concurrency

@dataclass
class DeleteEntityRecordOutput:
    success: bool
    conflict_detected: bool = False
    error: Optional[str] = None
```

### 4. Action Execution Tools

#### Tool: `d365fo_search_actions`
Search for available OData actions.

```python
@dataclass
class SearchActionsInput:
    pattern: str
    entity_name: Optional[str] = None
    is_function: Optional[bool] = None
    limit: int = 100

@dataclass
class SearchActionsOutput:
    actions: List[ActionInfo]
    total_count: int
```

#### Tool: `d365fo_execute_action`
Execute an OData action or function.

```python
@dataclass
class ExecuteActionInput:
    action_name: str
    parameters: Optional[Dict[str, Any]] = None
    entity_name: Optional[str] = None  # For bound actions
    entity_key: Optional[Union[str, Dict[str, Any]]] = None  # For bound actions on specific records

@dataclass
class ExecuteActionOutput:
    success: bool
    result: Optional[Any] = None
    execution_time: float = 0.0
    error: Optional[str] = None
```

#### Tool: `d365fo_get_action_info`
Get detailed information about a specific action.

```python
@dataclass
class GetActionInfoInput:
    action_name: str
    include_parameters: bool = True
    include_return_type: bool = True

@dataclass
class GetActionInfoOutput:
    action: ActionInfo
    parameters: List[ActionParameterInfo]
    return_type: Optional[ActionReturnTypeInfo] = None
    is_function: bool = False
    is_bound: bool = False
```

### 5. Label and Localization Tools

#### Tool: `d365fo_get_label`
Get label text by label ID.

```python
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
```

#### Tool: `d365fo_get_labels_batch`
Get multiple labels in a single request.

```python
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
```

#### Tool: `d365fo_search_labels`
Search for labels by text pattern.

```python
@dataclass
class SearchLabelsInput:
    pattern: str
    language: str = "en-US"
    exact_match: bool = False
    limit: int = 100

@dataclass
class SearchLabelsOutput:
    labels: List[LabelInfo]
    total_count: int
    search_time: float
```

### 6. Utility and Analysis Tools

#### Tool: `d365fo_analyze_entity_relationships`
Analyze relationships between entities.

```python
@dataclass
class AnalyzeEntityRelationshipsInput:
    entity_name: str
    depth: int = 1
    include_incoming: bool = True
    include_outgoing: bool = True

@dataclass
class EntityRelationship:
    name: str
    related_entity: str
    relationship_type: str
    foreign_key: str
    cardinality: str

@dataclass
class RelationshipGroup:
    incoming: List[EntityRelationship]
    outgoing: List[EntityRelationship]

@dataclass
class AnalyzeEntityRelationshipsOutput:
    entity: str
    relationships: RelationshipGroup
    related_entities: List[str]
    analysis_time: float
```

#### Tool: `d365fo_validate_query`
Validate an OData query without executing it.

```python
from enum import Enum

class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ValidateQueryInput:
    entity_name: str
    select: Optional[List[str]] = None
    filter: Optional[str] = None
    expand: Optional[List[str]] = None
    order_by: Optional[List[str]] = None

@dataclass
class ValidateQueryOutput:
    valid: bool
    errors: List[str]
    warnings: List[str]
    estimated_complexity: ComplexityLevel
```

#### Tool: `d365fo_generate_entity_documentation`
Generate documentation for entities and their properties.

```python
class DocumentationFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"

@dataclass
class GenerateEntityDocumentationInput:
    entity_names: List[str]
    include_examples: bool = False
    include_relationships: bool = False
    format: DocumentationFormat = DocumentationFormat.MARKDOWN

@dataclass
class GenerateEntityDocumentationOutput:
    documentation: str
    format: DocumentationFormat
    generation_time: float
    entity_count: int
```

### 7. Performance and Monitoring Tools

#### Tool: `d365fo_get_cache_statistics`
Get cache performance statistics.

```python
@dataclass
class CacheStatistics:
    hit_rate: float
    size: int
    last_updated: str

@dataclass
class EntityCacheInfo:
    cached: List[str]
    total_queries: int

@dataclass
class GetCacheStatisticsOutput:
    metadata: CacheStatistics
    labels: CacheStatistics
    entities: EntityCacheInfo
```

#### Tool: `d365fo_benchmark_operations`
Benchmark common operations for performance analysis.

```python
class OperationType(Enum):
    CONNECTION = "connection"
    METADATA = "metadata"
    QUERY = "query"
    ACTION = "action"

@dataclass
class BenchmarkOperationsInput:
    operations: List[OperationType]
    iterations: int = 10
    entity_name: Optional[str] = None

@dataclass
class OperationBenchmarkResult:
    average_time: float
    min_time: float
    max_time: float
    success_rate: float

@dataclass
class BenchmarkOperationsOutput:
    results: Dict[str, OperationBenchmarkResult]
    total_time: float
```

## Prompt Definitions

### 1. Entity Analysis Prompt

**Name**: `d365fo_entity_analysis`
**Description**: Analyze D365FO entities for integration and data modeling purposes.

```python
from enum import Enum

class AnalysisType(Enum):
    SCHEMA = "schema"
    RELATIONSHIPS = "relationships"
    DATA_PATTERNS = "data_patterns"
    INTEGRATION_READINESS = "integration_readiness"

@dataclass
class EntityAnalysisPromptArgs:
    entity_names: Optional[List[str]] = None
    analysis_type: AnalysisType = AnalysisType.SCHEMA
    include_examples: bool = False
```

**Prompt Template**:
```
Analyze the following D365 Finance & Operations entities for {{analysisType}}:

{{#each entityNames}}
Entity: {{this}}
{{#if includeExamples}}
[Entity schema and sample data will be retrieved automatically]
{{/if}}
{{/each}}

Please provide:
1. Entity purpose and business context
2. Key fields and their business meaning
3. {{#eq analysisType "relationships"}}Related entities and relationship types{{/eq}}
4. {{#eq analysisType "integration_readiness"}}Integration considerations and recommendations{{/eq}}
5. {{#eq analysisType "data_patterns"}}Common data patterns and validation rules{{/eq}}
6. Best practices for working with these entities

Focus on practical integration scenarios and provide actionable insights.
```

### 2. OData Query Builder Prompt

**Name**: `d365fo_query_builder`
**Description**: Help build complex OData queries for D365FO entities.

```python
@dataclass
class QueryBuilderPromptArgs:
    entity_name: str
    requirements: str
    include_sample_data: bool = False
```

**Prompt Template**:
```
Help build an OData query for the D365 Finance & Operations entity: {{entityName}}

Requirements: {{requirements}}

{{#if includeSampleData}}
[Entity schema and sample data will be retrieved automatically]
{{/if}}

Please provide:
1. Complete OData query with proper syntax
2. Explanation of each query parameter
3. Expected result structure
4. Performance considerations
5. Alternative query approaches if applicable

Ensure the query follows D365FO OData best practices and is optimized for performance.
```

### 3. Integration Planning Prompt

**Name**: `d365fo_integration_planning`
**Description**: Plan integration scenarios with D365FO systems.

```python
class IntegrationDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"

@dataclass
class IntegrationPlanningPromptArgs:
    business_scenario: str
    entities: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    direction: IntegrationDirection = IntegrationDirection.BIDIRECTIONAL
```

**Prompt Template**:
```
Plan a D365 Finance & Operations integration for the following scenario:

Business Scenario: {{businessScenario}}
Integration Direction: {{direction}}

{{#if entities}}
Entities involved: {{#each entities}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}
{{/if}}

{{#if actions}}
Actions to consider: {{#each actions}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}
{{/if}}

[Relevant entity schemas and action definitions will be retrieved automatically]

Please provide:
1. Integration architecture recommendations
2. Data flow design
3. Error handling strategies
4. Performance considerations
5. Security recommendations
6. Testing approach
7. Monitoring and maintenance considerations

Focus on practical implementation details and industry best practices.
```

### 4. Troubleshooting Assistant Prompt

**Name**: `d365fo_troubleshooting`
**Description**: Assist with D365FO integration troubleshooting.

```python
@dataclass
class TroubleshootingPromptArgs:
    issue: str
    entity_name: Optional[str] = None
    action_name: Optional[str] = None
    error_message: Optional[str] = None
    include_environment_info: bool = False
```

**Prompt Template**:
```
Help troubleshoot a D365 Finance & Operations integration issue:

Issue: {{issue}}
{{#if entityName}}Entity: {{entityName}}{{/if}}
{{#if actionName}}Action: {{actionName}}{{/if}}
{{#if errorMessage}}Error Message: {{errorMessage}}{{/if}}

{{#if includeEnvironmentInfo}}
[Environment information and connectivity status will be retrieved automatically]
{{/if}}

Please provide:
1. Root cause analysis
2. Step-by-step troubleshooting guide
3. Common solutions for this type of issue
4. Prevention strategies
5. Relevant documentation references
6. Code examples if applicable

Focus on actionable solutions and preventive measures.
```

## Configuration Management

### Server Configuration

```yaml
# mcp-server-d365fo.yaml
server:
  name: "d365fo-mcp-server"
  version: "1.0.0"
  description: "MCP Server for Microsoft Dynamics 365 Finance & Operations"
  
d365fo:
  # Default connection settings
  default_environment:
    base_url: "${D365FO_BASE_URL}"
    use_default_credentials: true
    timeout: 60
    verify_ssl: true
  
  # Cache settings
  cache:
    metadata_cache_dir: "${HOME}/.d365fo-mcp/cache"
    label_cache_expiry_minutes: 120
    use_label_cache: true
    cache_size_limit_mb: 100
  
  # Performance settings
  performance:
    max_concurrent_requests: 10
    connection_pool_size: 5
    request_timeout: 30
    batch_size: 100
  
  # Security settings
  security:
    encrypt_cached_tokens: true
    token_expiry_buffer_minutes: 5
    max_retry_attempts: 3
  
  # Logging settings
  logging:
    level: "INFO"
    log_file: "${HOME}/.d365fo-mcp/logs/server.log"
    max_log_size_mb: 10
    backup_count: 5

# Resource limits
limits:
  max_entities_per_query: 1000
  max_batch_size: 100
  max_search_results: 500
  query_timeout_seconds: 300
  
# Tool-specific settings
tools:
  metadata_sync:
    auto_sync_on_startup: true
    sync_interval_hours: 24
  
  query_validation:
    enable_complexity_analysis: true
    warn_on_expensive_queries: true
  
  caching:
    enable_query_result_cache: true
    result_cache_ttl_minutes: 30
```

### Environment-Specific Profiles

```yaml
# profiles.yaml
profiles:
  development:
    base_url: "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    use_default_credentials: true
    verify_ssl: false
    timeout: 120
    
  test:
    base_url: "${D365FO_TEST_URL}"
    client_id: "${AZURE_CLIENT_ID}"
    client_secret: "${AZURE_CLIENT_SECRET}"
    tenant_id: "${AZURE_TENANT_ID}"
    
  production:
    base_url: "${D365FO_PROD_URL}"
    use_default_credentials: true
    verify_ssl: true
    timeout: 60
    rate_limit:
      requests_per_minute: 100
      burst_limit: 20
```

## Error Handling

### Error Response Format

```python
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
    details: Optional[MCPErrorDetails] = None
    timestamp: str
    tool: Optional[str] = None
    retryable: bool = False
```

### Error Categories

1. **Connection Errors** (`CONNECTION_ERROR`)
   - Network connectivity issues
   - Authentication failures
   - SSL/TLS certificate problems

2. **Configuration Errors** (`CONFIGURATION_ERROR`)
   - Invalid base URL
   - Missing required settings
   - Invalid authentication credentials

3. **Validation Errors** (`VALIDATION_ERROR`)
   - Invalid entity names
   - Malformed OData queries
   - Type validation failures

4. **D365FO Errors** (`D365FO_ERROR`)
   - OData API errors
   - Business logic validation failures
   - Insufficient permissions

5. **Cache Errors** (`CACHE_ERROR`)
   - Cache corruption
   - Cache write failures
   - Cache invalidation issues

6. **Resource Errors** (`RESOURCE_ERROR`)
   - Resource not found
   - Resource access denied
   - Resource temporarily unavailable

### Error Recovery Strategies

```python
from enum import Enum

class BackoffStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"

@dataclass
class RetryPolicy:
    max_attempts: int
    backoff_strategy: BackoffStrategy
    base_delay: float
    max_delay: float
    retryable_error_codes: List[str]

@dataclass
class FallbackBehavior:
    use_cache: bool
    return_partial_results: bool
    degraded_mode: bool

@dataclass
class CircuitBreaker:
    enabled: bool
    failure_threshold: int
    recovery_timeout: int

@dataclass
class ErrorRecoveryConfig:
    retry_policy: RetryPolicy
    fallback_behavior: FallbackBehavior
    circuit_breaker: CircuitBreaker
```

## Security Considerations

### Authentication and Authorization

1. **Credential Management**
   - Support for Azure Managed Identity
   - Client credentials flow for service principals
   - Secure token storage and rotation
   - Environment-based credential configuration

2. **Access Control**
   - Tool-level permission configuration
   - Entity-level access restrictions
   - Rate limiting per client/tool
   - Audit logging for all operations

3. **Data Protection**
   - Encryption of cached credentials
   - Secure transmission (HTTPS only)
   - PII data handling guidelines
   - Data residency considerations

### Security Configuration

```yaml
security:
  authentication:
    methods: ["managed_identity", "client_credentials"]
    token_encryption: true
    token_rotation_hours: 24
  
  authorization:
    enable_rbac: true
    default_permissions: ["read"]
    admin_permissions: ["read", "write", "delete", "admin"]
  
  data_protection:
    encrypt_cache: true
    mask_sensitive_fields: true
    audit_logging: true
    max_data_retention_days: 90
  
  network:
    require_https: true
    allowed_origins: []
    rate_limiting:
      requests_per_minute: 1000
      burst_limit: 100
```

## Performance Optimization

### Caching Strategy

1. **Multi-Level Caching**
   - Memory cache for frequently accessed data
   - Disk cache for metadata and schemas
   - Distributed cache for multi-instance deployments

2. **Cache Invalidation**
   - Time-based expiration
   - Event-driven invalidation
   - Manual cache refresh tools

3. **Query Optimization**
   - Query result caching
   - Intelligent query batching
   - Pagination for large result sets

### Connection Management

```python
@dataclass
class HealthCheck:
    enabled: bool
    interval_seconds: int
    timeout_seconds: int

@dataclass
class ConnectionPoolConfig:
    min_connections: int
    max_connections: int
    idle_timeout_seconds: int
    connection_timeout_seconds: int
    retry_policy: RetryPolicy
    health_check: HealthCheck
```

### Performance Monitoring

```python
@dataclass
class RequestMetrics:
    total: int
    successful: int
    failed: int
    average_response_time: float

@dataclass
class CacheMetrics:
    hit_rate: float
    miss_rate: float
    eviction_rate: float
    size: int

@dataclass
class ConnectionMetrics:
    active: int
    idle: int
    created: int
    destroyed: int

@dataclass
class ErrorMetrics:
    by_type: Dict[str, int]
    by_tool: Dict[str, int]
    retry_count: int

@dataclass
class PerformanceMetrics:
    requests: RequestMetrics
    cache: CacheMetrics
    connections: ConnectionMetrics
    errors: ErrorMetrics
```

## Implementation Guidelines

### Server Startup Sequence

1. **Initialization Phase**
   - Load configuration files
   - Validate environment variables
   - Initialize logging system
   - Set up error handlers

2. **D365FO Client Setup**
   - Initialize authentication manager
   - Create connection pools
   - Test connectivity
   - Load cached metadata

3. **MCP Server Setup**
   - Register resource handlers
   - Register tool handlers
   - Register prompt templates
   - Start server listener

4. **Health Checks**
   - Verify D365FO connectivity
   - Check cache integrity
   - Validate configuration
   - Log startup metrics

### Resource Implementation Pattern

```python
from mcp.server import Server
from mcp.types import Resource

class EntityResourceHandler:
    def __init__(self, client_manager):
        self.client_manager = client_manager
    
    async def list_resources(self) -> list[Resource]:
        """List available entity resources."""
        try:
            client = await self.client_manager.get_client()
            entities = client.search_entities("")
            
            resources = []
            for entity_name in entities:
                resources.append(Resource(
                    uri=f"d365fo://entities/{entity_name}",
                    name=f"Entity: {entity_name}",
                    description=f"D365FO entity {entity_name} with metadata and sample data",
                    mimeType="application/json"
                ))
            
            return resources
        except Exception as e:
            self.logger.error(f"Failed to list entity resources: {e}")
            raise
    
    async def read_resource(self, uri: str) -> str:
        """Read specific entity resource."""
        entity_name = self._extract_entity_name(uri)
        client = await self.client_manager.get_client()
        
        # Get entity metadata
        entity_info = client.get_entity_info(entity_name)
        
        # Get sample data (limited)
        sample_data = await client.get_entities(
            entity_name, 
            options=QueryOptions(top=5)
        )
        
        resource_content = {
            "metadata": entity_info.__dict__ if entity_info else None,
            "sampleData": sample_data.get("value", []),
            "recordCount": sample_data.get("@odata.count"),
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        return json.dumps(resource_content, indent=2)
```

### Tool Implementation Pattern

```python
from mcp.server.models import Tool
from mcp.types import TextContent

class QueryEntitiesTool:
    def __init__(self, client_manager):
        self.client_manager = client_manager
    
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="d365fo_query_entities",
            description="Query D365FO entities with OData parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity to query"
                    },
                    "select": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to select"
                    },
                    "filter": {
                        "type": "string",
                        "description": "OData filter expression"
                    },
                    "top": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000,
                        "description": "Number of records to return"
                    }
                },
                "required": ["entityName"]
            }
        )
    
    async def execute(self, arguments: dict) -> list[TextContent]:
        """Execute the query tool."""
        try:
            client = await self.client_manager.get_client()
            
            # Build query options
            options = QueryOptions(
                select=arguments.get("select"),
                filter=arguments.get("filter"),
                top=arguments.get("top", 100)
            )
            
            # Execute query
            start_time = time.time()
            result = await client.get_entities(
                arguments["entityName"], 
                options=options
            )
            query_time = time.time() - start_time
            
            # Format response
            response = {
                "data": result.get("value", []),
                "count": result.get("@odata.count"),
                "queryTime": round(query_time, 3),
                "totalRecords": len(result.get("value", []))
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "tool": "d365fo_query_entities",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
```

### Client Management

```python
class D365FOClientManager:
    """Manages D365FO client instances and connection pooling."""
    
    def __init__(self, config: dict):
        self.config = config
        self._client_pool = {}
        self._session_lock = asyncio.Lock()
    
    async def get_client(self, profile: str = "default") -> FOClient:
        """Get or create a client for the specified profile."""
        async with self._session_lock:
            if profile not in self._client_pool:
                client_config = self._build_client_config(profile)
                client = FOClient(client_config)
                
                # Test connection
                if not await client.test_connection():
                    raise ConnectionError(f"Failed to connect to D365FO: {profile}")
                
                self._client_pool[profile] = client
            
            return self._client_pool[profile]
    
    async def cleanup(self):
        """Close all client connections."""
        for client in self._client_pool.values():
            await client.close()
        self._client_pool.clear()
```

## Testing Strategy

### Unit Testing

1. **Tool Testing**
   - Mock D365FO client responses
   - Test input validation
   - Test error handling
   - Test output formatting

2. **Resource Testing**
   - Test resource listing
   - Test resource content generation
   - Test URI parsing
   - Test caching behavior

### Integration Testing

1. **Live Environment Testing**
   - Connect to D365FO test environment
   - Execute real operations
   - Validate responses
   - Test error scenarios

2. **Performance Testing**
   - Load testing with multiple concurrent requests
   - Memory usage monitoring
   - Connection pool testing
   - Cache effectiveness testing

### End-to-End Testing

1. **MCP Protocol Testing**
   - Test with MCP-compatible clients
   - Validate resource discovery
   - Test tool execution
   - Test prompt handling

2. **Scenario Testing**
   - Common integration workflows
   - Error recovery scenarios
   - Security boundary testing
   - Multi-environment testing

### Test Configuration

```yaml
# test-config.yaml
testing:
  environments:
    mock:
      type: "mock"
      responses_file: "tests/mock_responses.json"
    
    sandbox:
      type: "live"
      base_url: "${D365FO_TEST_URL}"
      use_default_credentials: true
    
    integration:
      type: "live"
      base_url: "${D365FO_INTEGRATION_URL}"
      client_id: "${TEST_CLIENT_ID}"
      client_secret: "${TEST_CLIENT_SECRET}"
      tenant_id: "${TEST_TENANT_ID}"
  
  performance:
    concurrent_users: 10
    test_duration_seconds: 300
    ramp_up_seconds: 60
  
  coverage:
    minimum_coverage: 85
    exclude_patterns: ["*/tests/*", "*/mocks/*"]
```


## Conclusion

This comprehensive MCP server specification provides a robust foundation for exposing d365fo-client capabilities through the Model Context Protocol. The implementation should prioritize:

1. **Reliability**: Robust error handling and recovery mechanisms
2. **Performance**: Efficient caching and connection management
3. **Security**: Proper authentication and authorization controls
4. **Usability**: Clear documentation and intuitive tool interfaces
5. **Maintainability**: Clean architecture and comprehensive testing

The server will enable AI assistants and other MCP clients to seamlessly interact with Microsoft Dynamics 365 Finance & Operations environments, supporting a wide range of integration and automation scenarios.