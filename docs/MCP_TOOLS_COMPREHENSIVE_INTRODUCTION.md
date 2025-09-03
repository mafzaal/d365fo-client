# Comprehensive Introduction to D365FO MCP Tools

This document provides a detailed introduction to all available Model Context Protocol (MCP) tools in the d365fo-client, organized by category. Each tool description includes its purpose, key features, use cases, and practical examples.

## Table of Contents

1. [Connection & Environment Tools](#connection--environment-tools)
2. [CRUD Operations Tools](#crud-operations-tools)
3. [Metadata Discovery Tools](#metadata-discovery-tools)
4. [Label Management Tools](#label-management-tools)
5. [Profile Management Tools](#profile-management-tools)
6. [Database Analysis Tools](#database-analysis-tools)
7. [Synchronization Tools](#synchronization-tools)

---

## Connection & Environment Tools

### 1. `d365fo_test_connection`

**Purpose**: Test connectivity and authentication to a D365 Finance & Operations environment.

**Key Features**:
- Validates network connectivity to D365FO endpoints
- Tests authentication mechanisms (default credentials or client credentials)
- Measures response times and connection health
- Provides detailed error diagnostics for troubleshooting
- Supports multiple profile configurations

**When to Use**:
- Setting up new environment connections
- Troubleshooting connectivity issues
- Validating authentication configurations
- Performing health checks before starting operations
- Testing profile configurations after changes

**Example Use Cases**:
```json
// Test default profile connection
{
  "tool": "d365fo_test_connection"
}

// Test specific profile with custom timeout
{
  "tool": "d365fo_test_connection",
  "arguments": {
    "profile": "production",
    "timeout": 60
  }
}
```

**Response Information**:
- Connection success/failure status
- Response time metrics
- Authentication status
- Endpoint availability
- Error details and suggestions for resolution

---

### 2. `d365fo_get_environment_info`

**Purpose**: Retrieve comprehensive information about the D365FO environment including versions, configurations, and capabilities.

**Key Features**:
- Displays D365FO application version and build information
- Shows platform versions and update status
- Provides metadata cache information and statistics
- Lists available modules and configurations
- Reports system health and connectivity status

**When to Use**:
- Understanding environment capabilities before development
- Documenting system configurations
- Verifying environment compatibility
- Troubleshooting version-specific issues
- Generating environment reports

**Example Use Cases**:
```json
// Get environment info for default profile
{
  "tool": "d365fo_get_environment_info"
}

// Get info for specific environment
{
  "tool": "d365fo_get_environment_info",
  "arguments": {
    "profile": "development"
  }
}
```

**Response Information**:
- Base URL and environment identification
- Application and platform version details
- Available modules and their versions
- Metadata cache status and statistics
- System health indicators

---

## CRUD Operations Tools

### 3. `d365fo_query_entities`

**Purpose**: Query and retrieve multiple records from D365FO data entities using advanced OData filtering, sorting, and pagination.

**Key Features**:
- Full OData query support (select, filter, expand, orderby, top, skip, count)
- Advanced filtering with multiple operators and conditions
- Field selection for optimized data transfer
- Navigation property expansion for related data
- Pagination support for large datasets
- Performance metrics and query optimization

**When to Use**:
- Searching for specific records across entities
- Generating reports and data analysis
- Bulk data retrieval operations
- Exploring data relationships through expansions
- Building dashboards and business intelligence solutions

**Example Use Cases**:
```json
// Find active customers with credit limit > 10000
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "CustomersV3",
    "filter": "CreditLimit gt 10000 and Blocked eq false",
    "select": ["CustomerAccount", "Name", "CreditLimit", "PrimaryContactEmail"],
    "orderBy": ["CreditLimit desc"],
    "top": 50
  }
}

// Get sales orders with line details
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "SalesOrderHeadersV2",
    "filter": "SalesOrderStatus eq 'Confirmed'",
    "expand": ["SalesOrderLines"],
    "count": true
  }
}
```

**Advanced Features**:
- Complex filtering with logical operators (and, or, not)
- Date/time filtering with proper formatting
- Substring and pattern matching
- Multi-level expansions for hierarchical data
- Conditional counting for pagination

---

### 4. `d365fo_get_entity_record`

**Purpose**: Retrieve a single specific record using its primary key for precise data access.

**Key Features**:
- Direct key-based record access for optimal performance
- Support for both simple and composite primary keys
- Optional field selection to reduce payload size
- Navigation property expansion for related records
- Optimistic concurrency control with ETag support

**When to Use**:
- Retrieving known specific records by ID
- Getting detailed information about individual entities
- Accessing master data records
- Retrieving records for update or delete operations
- Building detail views and forms

**Example Use Cases**:
```json
// Get specific customer by account
{
  "tool": "d365fo_get_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "key": "CUST001",
    "select": ["CustomerAccount", "Name", "CreditLimit", "PaymentTerms"]
  }
}

// Get sales order with composite key
{
  "tool": "d365fo_get_entity_record",
  "arguments": {
    "entityName": "SalesOrderHeadersV2",
    "key": {
      "DataArea": "USMF",
      "SalesOrderNumber": "SO-12345"
    },
    "expand": ["SalesOrderLines", "CustomerAccount"]
  }
}
```

---

### 5. `d365fo_create_entity_record`

**Purpose**: Create new records in D365FO entities with full validation and business logic execution.

**Key Features**:
- Complete data validation and constraint checking
- Automatic number sequence generation
- Business logic and workflow trigger execution
- Related record creation through navigation properties
- Optimistic return of created record with generated values

**When to Use**:
- Creating new master data records
- Generating transactions and documents
- Bulk data import operations
- Integration scenarios with external systems
- Automated business process execution

**Example Use Cases**:
```json
// Create new customer
{
  "tool": "d365fo_create_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "data": {
      "CustomerAccount": "NEWCUST001",
      "Name": "New Customer Corp",
      "CustomerGroupId": "DEFAULT",
      "PaymentTerms": "Net30",
      "CreditLimit": 50000
    },
    "returnRecord": true
  }
}

// Create sales order with validation
{
  "tool": "d365fo_create_entity_record",
  "arguments": {
    "entityName": "SalesOrderHeadersV2",
    "data": {
      "CustomerAccount": "CUST001",
      "OrderDate": "2024-03-15",
      "RequestedShippingDate": "2024-03-20",
      "SalesOrderLines": [
        {
          "ItemNumber": "ITEM001",
          "OrderedSalesQuantity": 10,
          "SalesPrice": 25.00
        }
      ]
    }
  }
}
```

---

### 6. `d365fo_update_entity_record`

**Purpose**: Update existing records with partial or complete field modifications, including validation and business logic execution.

**Key Features**:
- Partial updates - only modified fields need to be provided
- Optimistic concurrency control with ETag validation
- Business rule validation and execution
- Workflow and approval process triggering
- Related record updates through navigation properties

**When to Use**:
- Modifying existing master data
- Updating transaction status and values
- Bulk update operations
- Workflow and approval processes
- Data correction and maintenance

**Example Use Cases**:
```json
// Update customer credit limit
{
  "tool": "d365fo_update_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "key": "CUST001",
    "data": {
      "CreditLimit": 75000,
      "PaymentTerms": "Net45"
    },
    "returnRecord": true
  }
}

// Update sales order with concurrency check
{
  "tool": "d365fo_update_entity_record",
  "arguments": {
    "entityName": "SalesOrderHeadersV2",
    "key": {"DataArea": "USMF", "SalesOrderNumber": "SO-12345"},
    "data": {
      "SalesOrderStatus": "Confirmed",
      "ConfirmedShippingDate": "2024-03-18"
    },
    "ifMatch": "W/\"12345\""
  }
}
```

---

### 7. `d365fo_delete_entity_record`

**Purpose**: Permanently delete records from D365FO entities with proper validation and cascading rules.

**Key Features**:
- Referential integrity checking before deletion
- Cascading delete rules enforcement
- Business logic validation for delete operations
- Optimistic concurrency control with ETag validation
- Audit trail and logging support

**When to Use**:
- Removing obsolete master data records
- Cleaning up test or temporary data
- Implementing data retention policies
- Error correction and data cleanup
- Bulk delete operations with proper validation

**Example Use Cases**:
```json
// Delete customer record
{
  "tool": "d365fo_delete_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "key": "OLDCUST001"
  }
}

// Delete with concurrency control
{
  "tool": "d365fo_delete_entity_record",
  "arguments": {
    "entityName": "SalesOrderHeadersV2",
    "key": {"DataArea": "USMF", "SalesOrderNumber": "SO-99999"},
    "ifMatch": "W/\"54321\""
  }
}
```

---

### 8. `d365fo_call_action`

**Purpose**: Execute OData actions and functions for complex business operations beyond basic CRUD.

**Key Features**:
- Support for unbound, entity-bound, and collection-bound actions
- Parameter passing for complex operations
- Business logic execution and workflow triggering
- Custom and system action execution
- Return value handling for complex response types

**When to Use**:
- Executing posting operations (journals, invoices, etc.)
- Running validation and calculation functions
- Triggering business processes and workflows
- Performing bulk operations and batch processing
- Accessing system utilities and maintenance functions

**Example Use Cases**:
```json
// Execute posting action
{
  "tool": "d365fo_call_action",
  "arguments": {
    "actionName": "Microsoft.Dynamics.DataEntities.PostGeneralJournal",
    "entityName": "GeneralJournalHeaders",
    "entityKey": "GJHDR-001",
    "parameters": {
      "validateOnly": false
    }
  }
}

// Call validation function
{
  "tool": "d365fo_call_action",
  "arguments": {
    "actionName": "Microsoft.Dynamics.DataEntities.ValidateCustomerCredit",
    "parameters": {
      "customerAccount": "CUST001",
      "creditAmount": 25000
    }
  }
}
```

---

## Metadata Discovery Tools

### 9. `d365fo_search_entities`

**Purpose**: Discover and search D365FO data entities using keyword-based search with advanced filtering options.

**Key Features**:
- Keyword-based entity name searching
- Category filtering (Master, Transaction, Document, Reference, Parameter)
- Service enablement filtering (OData API access, Data Management Framework)
- Read-only vs. writable entity filtering
- Full-text search capabilities with relevance scoring
- Comprehensive entity metadata in results

**When to Use**:
- Discovering available entities for integration projects
- Finding entities related to specific business areas
- Understanding entity capabilities and restrictions
- Building entity catalogs and documentation
- Planning data migration and integration strategies

**Search Strategy Examples**:
```json
// Find customer-related entities
{
  "tool": "d365fo_search_entities",
  "arguments": {
    "pattern": "customer",
    "entity_category": "Master",
    "data_service_enabled": true,
    "limit": 20
  }
}

// Find all transaction entities for sales
{
  "tool": "d365fo_search_entities",
  "arguments": {
    "pattern": "sales",
    "entity_category": "Transaction",
    "is_read_only": false
  }
}
```

**Multi-keyword Search Strategy**:
For complex searches like "data management entities", perform multiple searches:
1. Search for "data" → get data-related entities
2. Search for "management" → get management-related entities  
3. Analyze combined results for entities matching both concepts

---

### 10. `d365fo_get_entity_schema`

**Purpose**: Retrieve detailed schema information for specific entities including properties, keys, relationships, and metadata.

**Key Features**:
- Complete property definitions with data types and constraints
- Primary and foreign key identification
- Navigation property mapping for related entities
- Label resolution for user-friendly names
- Validation rules and business constraints
- OData action and function listings

**When to Use**:
- Understanding entity structure before development
- Building integration mappings and transformations
- Validating data requirements and constraints
- Generating documentation and entity references
- Planning CRUD operations and data flows

**Example Use Cases**:
```json
// Get full customer entity schema
{
  "tool": "d365fo_get_entity_schema",
  "arguments": {
    "entityName": "CustomersV3",
    "include_properties": true,
    "resolve_labels": true,
    "language": "en-US"
  }
}

// Get minimal schema for development
{
  "tool": "d365fo_get_entity_schema",
  "arguments": {
    "entityName": "SalesOrderHeadersV2",
    "include_properties": true,
    "resolve_labels": false
  }
}
```

---

### 11. `d365fo_search_actions`

**Purpose**: Discover available OData actions and functions for business operations and system functions.

**Key Features**:
- Keyword-based action name searching
- Binding type filtering (Unbound, EntitySet-bound, Entity-bound)
- Entity-specific action filtering
- Function vs. action type distinction
- Parameter and return type information
- Detailed action metadata and usage guidance

**When to Use**:
- Finding available business operations for entities
- Discovering system utility functions
- Planning workflow and process automation
- Building action catalogs and documentation
- Understanding entity operation capabilities

**Search Strategy Examples**:
```json
// Find posting-related actions
{
  "tool": "d365fo_search_actions",
  "arguments": {
    "pattern": "post",
    "bindingKind": "BoundToEntity",
    "limit": 50
  }
}

// Find validation functions
{
  "tool": "d365fo_search_actions",
  "arguments": {
    "pattern": "validate",
    "isFunction": true,
    "entityName": "CustomersV3"
  }
}
```

**Multi-keyword Search Strategy**:
For complex searches like "approval workflow actions":
1. Search for "approval" → get approval-related actions
2. Search for "workflow" → get workflow-related actions
3. Combine results to find approval workflow actions

---

### 12. `d365fo_search_enumerations`

**Purpose**: Discover system enumerations (enums) that define lists of named constants and their values.

**Key Features**:
- Keyword-based enumeration name searching
- Complete enumeration metadata
- Member value listings with labels
- Multi-language label support
- Usage context and relationships
- Value mapping and conversion information

**When to Use**:
- Understanding valid values for enum fields
- Building dropdown lists and validation rules
- Creating data mapping and transformation logic
- Documenting system configurations and options
- Planning data import and integration mappings

**Search Strategy Examples**:
```json
// Find customer status enumerations
{
  "tool": "d365fo_search_enumerations",
  "arguments": {
    "pattern": "customer",
    "limit": 30
  }
}

// Find all Yes/No enumerations
{
  "tool": "d365fo_search_enumerations",
  "arguments": {
    "pattern": "yes",
    "limit": 20
  }
}
```

---

### 13. `d365fo_get_enumeration_fields`

**Purpose**: Retrieve detailed information about enumeration members including values, labels, and descriptions.

**Key Features**:
- Complete member listings with numeric values
- Multi-language label resolution
- Member descriptions and usage context
- Value ordering and grouping information
- Deprecated and obsolete member identification

**When to Use**:
- Building dropdown lists and selection controls
- Creating data validation rules
- Implementing value mapping and conversion logic
- Documenting enumeration usage and values
- Planning data migration and transformation

**Example Use Cases**:
```json
// Get Yes/No enumeration values
{
  "tool": "d365fo_get_enumeration_fields",
  "arguments": {
    "enumeration_name": "NoYes",
    "resolve_labels": true,
    "language": "en-US"
  }
}

// Get customer blocking reasons
{
  "tool": "d365fo_get_enumeration_fields",
  "arguments": {
    "enumeration_name": "CustVendorBlocked",
    "resolve_labels": true
  }
}
```

---

### 14. `d365fo_get_installed_modules`

**Purpose**: Retrieve information about installed modules in the D365FO environment including versions and configurations.

**Key Features**:
- Complete module listings with versions
- Publisher and licensing information
- Installation dates and update history
- Module dependencies and relationships
- Configuration and customization details

**When to Use**:
- Understanding environment capabilities and features
- Planning module-specific development
- Documenting system configurations
- Troubleshooting module-related issues
- Planning upgrades and updates

**Example Use Cases**:
```json
// Get all installed modules
{
  "tool": "d365fo_get_installed_modules"
}
```

---

## Label Management Tools

### 15. `d365fo_get_label`

**Purpose**: Retrieve human-readable label text for specific label IDs with multi-language support.

**Key Features**:
- Single label retrieval with caching
- Multi-language support with fallback options
- Label ID validation and error handling
- Performance optimization through caching
- Context-aware label resolution

**When to Use**:
- Displaying user-friendly field and entity names
- Building multi-language user interfaces
- Creating documentation with proper terminology
- Implementing label-based validation messages
- Developing localized applications

**Example Use Cases**:
```json
// Get label in English
{
  "tool": "d365fo_get_label",
  "arguments": {
    "labelId": "@SYS1234",
    "language": "en-US",
    "fallbackToEnglish": true
  }
}

// Get label in French with fallback
{
  "tool": "d365fo_get_label",
  "arguments": {
    "labelId": "@SYS5678",
    "language": "fr-FR",
    "fallbackToEnglish": true
  }
}
```

---

### 16. `d365fo_get_labels_batch`

**Purpose**: Retrieve multiple labels in a single efficient request for batch processing and performance optimization.

**Key Features**:
- Batch label retrieval with single API call
- Performance optimization for multiple labels
- Missing label identification and handling
- Consistent language and fallback processing
- Bulk caching and performance metrics

**When to Use**:
- Loading labels for entire forms or pages
- Batch processing of label-dependent operations
- Performance optimization for label-heavy interfaces
- Bulk label validation and verification
- Creating label translation and localization tools

**Example Use Cases**:
```json
// Get multiple labels for a form
{
  "tool": "d365fo_get_labels_batch",
  "arguments": {
    "labelIds": ["@SYS1234", "@SYS5678", "@SYS9012"],
    "language": "en-US",
    "fallbackToEnglish": true
  }
}

// Batch validation of label existence
{
  "tool": "d365fo_get_labels_batch",
  "arguments": {
    "labelIds": ["@CUSTOM001", "@CUSTOM002", "@CUSTOM003"],
    "language": "de-DE"
  }
}
```

---

## Profile Management Tools

### 17. `d365fo_list_profiles`

**Purpose**: List all configured D365FO environment profiles with their basic information and status.

**Key Features**:
- Complete profile listing with metadata
- Default profile identification
- Authentication mode and security information
- Profile status and validation indicators
- Summary statistics and counts

**When to Use**:
- Managing multiple D365FO environments
- Understanding available connection configurations
- Troubleshooting profile-related issues
- Creating environment documentation
- Planning multi-environment development strategies

**Example Use Cases**:
```json
// List all available profiles
{
  "tool": "d365fo_list_profiles"
}
```

---

### 18. `d365fo_get_profile`

**Purpose**: Retrieve detailed configuration information for a specific profile including authentication and security settings.

**Key Features**:
- Complete profile configuration details
- Authentication method and credential information
- Security and SSL settings
- Cache and performance configurations
- Credential source and management information

**When to Use**:
- Reviewing profile configurations
- Troubleshooting connection issues
- Documenting environment settings
- Validating security configurations
- Planning profile modifications

**Example Use Cases**:
```json
// Get production profile details
{
  "tool": "d365fo_get_profile",
  "arguments": {
    "profileName": "production"
  }
}

// Get development profile configuration
{
  "tool": "d365fo_get_profile",
  "arguments": {
    "profileName": "development"
  }
}
```

---

### 19. `d365fo_create_profile`

**Purpose**: Create new environment profiles with comprehensive configuration options for authentication, security, and performance.

**Key Features**:
- Multiple authentication modes (default credentials, client credentials)
- Flexible credential source configuration (environment variables, Azure Key Vault)
- SSL and security settings
- Cache and performance optimization options
- Default profile designation

**When to Use**:
- Setting up new D365FO environment connections
- Creating environment-specific configurations
- Implementing security and authentication policies
- Planning multi-environment development
- Automating environment setup processes

**Example Use Cases**:
```json
// Create basic profile with default authentication
{
  "tool": "d365fo_create_profile",
  "arguments": {
    "name": "sandbox",
    "baseUrl": "https://sandbox.dynamics.com",
    "authMode": "default",
    "description": "Sandbox environment for testing",
    "setAsDefault": false
  }
}

// Create profile with client credentials from environment
{
  "tool": "d365fo_create_profile",
  "arguments": {
    "name": "production",
    "baseUrl": "https://prod.dynamics.com",
    "authMode": "client_credentials",
    "credentialSource": {
      "sourceType": "environment",
      "clientIdVar": "PROD_CLIENT_ID",
      "clientSecretVar": "PROD_CLIENT_SECRET",
      "tenantIdVar": "PROD_TENANT_ID"
    },
    "description": "Production environment",
    "setAsDefault": true
  }
}

// Create profile with Azure Key Vault credentials
{
  "tool": "d365fo_create_profile",
  "arguments": {
    "name": "secure-prod",
    "baseUrl": "https://prod.dynamics.com",
    "authMode": "client_credentials",
    "credentialSource": {
      "sourceType": "keyvault",
      "vaultUrl": "https://myvault.vault.azure.net",
      "clientIdSecretName": "D365FO-CLIENT-ID",
      "clientSecretSecretName": "D365FO-CLIENT-SECRET",
      "tenantIdSecretName": "D365FO-TENANT-ID",
      "keyvaultAuthMode": "default"
    },
    "description": "Production with Key Vault security"
  }
}
```

---

### 20. `d365fo_update_profile`

**Purpose**: Modify existing profile configurations including authentication, security, and performance settings.

**Key Features**:
- Partial update support - only modified fields need to be provided
- Authentication method changes
- Credential source modifications
- Security and SSL setting updates
- Cache and performance tuning

**When to Use**:
- Updating environment URLs or endpoints
- Changing authentication methods or credentials
- Modifying security and SSL configurations
- Tuning performance and cache settings
- Implementing security policy changes

**Example Use Cases**:
```json
// Update base URL and timeout
{
  "tool": "d365fo_update_profile",
  "arguments": {
    "name": "development",
    "baseUrl": "https://new-dev.dynamics.com",
    "timeout": 120
  }
}

// Switch to Key Vault authentication
{
  "tool": "d365fo_update_profile",
  "arguments": {
    "name": "production",
    "authMode": "client_credentials",
    "credentialSource": {
      "sourceType": "keyvault",
      "vaultUrl": "https://secure-vault.vault.azure.net",
      "keyvaultAuthMode": "default"
    }
  }
}
```

---

### 21. `d365fo_delete_profile`

**Purpose**: Remove environment profiles from the configuration with proper cleanup and validation.

**Key Features**:
- Profile existence validation before deletion
- Cleanup of associated caches and configurations
- Prevention of default profile deletion without replacement
- Audit trail and logging support

**When to Use**:
- Removing obsolete environment configurations
- Cleaning up test or temporary profiles
- Implementing environment lifecycle management
- Security cleanup when environments are decommissioned

**Example Use Cases**:
```json
// Delete temporary profile
{
  "tool": "d365fo_delete_profile",
  "arguments": {
    "profileName": "temp-testing"
  }
}
```

---

### 22. `d365fo_set_default_profile`

**Purpose**: Designate a specific profile as the default for operations that don't specify a profile explicitly.

**Key Features**:
- Default profile designation and validation
- Automatic fallback configuration
- Profile existence verification
- Configuration persistence

**When to Use**:
- Setting up primary environment for development
- Changing default environment contexts
- Implementing environment switching strategies
- Simplifying profile management workflows

**Example Use Cases**:
```json
// Set production as default
{
  "tool": "d365fo_set_default_profile",
  "arguments": {
    "profileName": "production"
  }
}
```

---

### 23. `d365fo_get_default_profile`

**Purpose**: Retrieve information about the currently configured default profile.

**Key Features**:
- Default profile identification
- Basic configuration information
- Status and availability verification

**When to Use**:
- Verifying current default configuration
- Troubleshooting profile-related issues
- Understanding current environment context
- Building profile management interfaces

**Example Use Cases**:
```json
// Get current default profile
{
  "tool": "d365fo_get_default_profile"
}
```

---

### 24. `d365fo_validate_profile`

**Purpose**: Validate profile configurations for completeness, correctness, and security compliance.

**Key Features**:
- Configuration completeness validation
- Authentication method verification
- URL and endpoint validation
- Security setting compliance checking
- Credential source accessibility testing

**When to Use**:
- Verifying profile configurations before use
- Troubleshooting connection and authentication issues
- Implementing configuration validation policies
- Automating profile quality assurance

**Example Use Cases**:
```json
// Validate production profile
{
  "tool": "d365fo_validate_profile",
  "arguments": {
    "profileName": "production"
  }
}
```

---

### 25. `d365fo_test_profile_connection`

**Purpose**: Test connectivity and authentication for a specific profile without affecting other operations.

**Key Features**:
- Profile-specific connection testing
- Authentication validation
- Performance metrics and timing
- Error diagnosis and reporting
- Non-intrusive testing approach

**When to Use**:
- Validating new profile configurations
- Troubleshooting profile-specific connectivity issues
- Performance testing and optimization
- Pre-deployment connection verification

**Example Use Cases**:
```json
// Test specific profile connection
{
  "tool": "d365fo_test_profile_connection",
  "arguments": {
    "profileName": "staging"
  }
}
```

---

## Database Analysis Tools

### 26. `d365fo_execute_sql_query`

**Purpose**: Execute SELECT queries against the metadata database to analyze cached metadata and generate insights.

**Key Features**:
- Secure SQL query execution with safety validation
- Multiple output formats (table, JSON, CSV)
- Query performance metrics and optimization
- Result limiting and pagination support
- Access to comprehensive metadata tables

**Safety Features**:
- Only SELECT statements allowed
- SQL injection protection
- Query timeout limits (30 seconds)
- Result size limits (1000 rows)
- Restricted table access for sensitive data

**Available Tables**:
- `metadata_environments`: Environment details and configurations
- `global_versions`: Global version registry with hashes
- `environment_versions`: Links between environments and versions
- `data_entities`: D365FO data entities metadata
- `public_entities`: Public entity schemas and configurations
- `entity_properties`: Detailed property information
- `entity_actions`: Available OData actions
- `enumerations`: System enumerations
- `enumeration_members`: Enumeration values and labels
- `metadata_search_v2`: FTS5 search index

**When to Use**:
- Analyzing metadata patterns and trends
- Generating custom reports and statistics
- Understanding data relationships and dependencies
- Performance analysis and optimization
- Creating dashboards and business intelligence

**Example Use Cases**:
```json
// Find most used entity categories
{
  "tool": "d365fo_execute_sql_query",
  "arguments": {
    "query": "SELECT entity_category, COUNT(*) as count FROM data_entities GROUP BY entity_category ORDER BY count DESC",
    "format": "table",
    "limit": 100
  }
}

// Analyze entities with most properties
{
  "tool": "d365fo_execute_sql_query",
  "arguments": {
    "query": "SELECT pe.name, COUNT(ep.id) as property_count FROM public_entities pe LEFT JOIN entity_properties ep ON pe.id = ep.entity_id GROUP BY pe.id ORDER BY property_count DESC LIMIT 10",
    "format": "json"
  }
}

// Environment version analysis
{
  "tool": "d365fo_execute_sql_query",
  "arguments": {
    "query": "SELECT me.environment_name, gv.version_hash, ev.detected_at FROM metadata_environments me JOIN environment_versions ev ON me.id = ev.environment_id JOIN global_versions gv ON ev.global_version_id = gv.id",
    "format": "csv"
  }
}
```

---

### 27. `d365fo_get_database_schema`

**Purpose**: Retrieve comprehensive schema information for the metadata database including tables, columns, indexes, and relationships.

**Key Features**:
- Complete database schema documentation
- Table and column definitions with data types
- Index information and performance characteristics
- Foreign key relationships and constraints
- Table statistics and usage information

**When to Use**:
- Understanding database structure for query development
- Planning metadata analysis and reporting
- Documenting database architecture
- Troubleshooting database-related issues
- Building database tools and utilities

**Example Use Cases**:
```json
// Get complete database schema
{
  "tool": "d365fo_get_database_schema",
  "arguments": {
    "include_statistics": true,
    "include_indexes": true,
    "include_relationships": true
  }
}

// Get schema for specific table
{
  "tool": "d365fo_get_database_schema",
  "arguments": {
    "table_name": "data_entities",
    "include_statistics": true
  }
}
```

---

### 28. `d365fo_get_table_info`

**Purpose**: Get detailed information about specific database tables including structure, relationships, and sample data.

**Key Features**:
- Detailed column definitions and constraints
- Primary and foreign key information
- Index characteristics and performance data
- Table statistics (row counts, sizes, update times)
- Optional sample data preview
- Relationship mapping to other tables

**When to Use**:
- Exploring specific tables before writing queries
- Understanding table structure and relationships
- Analyzing data quality and completeness
- Planning query optimization strategies
- Documenting table usage and patterns

**Example Use Cases**:
```json
// Get detailed info for entities table
{
  "tool": "d365fo_get_table_info",
  "arguments": {
    "table_name": "data_entities",
    "include_sample_data": true,
    "include_relationships": true
  }
}

// Analyze properties table structure
{
  "tool": "d365fo_get_table_info",
  "arguments": {
    "table_name": "entity_properties",
    "include_sample_data": false,
    "include_relationships": true
  }
}
```

---

### 29. `d365fo_get_database_statistics`

**Purpose**: Generate comprehensive database statistics and analytics for performance monitoring and analysis.

**Key Features**:
- Overall database size and utilization metrics
- Per-table statistics (row counts, sizes, growth trends)
- Global version statistics and reference counts
- Environment statistics and distribution
- Cache performance and hit rate analysis
- Storage utilization and optimization recommendations

**When to Use**:
- Monitoring database health and performance
- Planning storage and capacity requirements
- Analyzing metadata cache effectiveness
- Generating database health reports
- Optimizing database performance and configuration

**Example Use Cases**:
```json
// Get comprehensive database statistics
{
  "tool": "d365fo_get_database_statistics",
  "arguments": {
    "include_table_stats": true,
    "include_version_stats": true,
    "include_performance_stats": true
  }
}

// Get basic database overview
{
  "tool": "d365fo_get_database_statistics",
  "arguments": {
    "include_table_stats": false,
    "include_performance_stats": false
  }
}
```

---

## Synchronization Tools

### 30. `d365fo_start_sync`

**Purpose**: Initiate metadata synchronization sessions to download and cache D365FO metadata with various strategies and options.

**Key Features**:
- Multiple sync strategies (full, entities_only, labels_only, incremental)
- Session-based tracking with unique identifiers
- Version detection and validation
- Strategy optimization based on requirements
- Background execution with progress monitoring

**Sync Strategies**:
- **full**: Complete metadata download (entities, labels, enumerations, actions)
- **entities_only**: Quick refresh of entity metadata only
- **labels_only**: Download only label data for localization
- **full_without_labels**: All metadata except labels (faster, common choice)
- **sharing_mode**: Copy from compatible cached versions
- **incremental**: Update only changes (fallback to full if needed)

**When to Use**:
- Initial environment setup and configuration
- Refreshing metadata after system updates
- Synchronizing specific metadata types
- Implementing automated sync schedules
- Recovering from metadata corruption or issues

**Example Use Cases**:
```json
// Start full sync without labels (recommended)
{
  "tool": "d365fo_start_sync",
  "arguments": {
    "strategy": "full_without_labels"
  }
}

// Sync only entities for quick refresh
{
  "tool": "d365fo_start_sync",
  "arguments": {
    "strategy": "entities_only",
    "profile": "development"
  }
}

// Sync specific global version
{
  "tool": "d365fo_start_sync",
  "arguments": {
    "strategy": "full",
    "global_version_id": 12345,
    "profile": "production"
  }
}
```

---

### 31. `d365fo_get_sync_progress`

**Purpose**: Monitor detailed progress of sync sessions including phases, completion percentages, and time estimates.

**Key Features**:
- Real-time progress monitoring with percentage completion
- Current phase and activity identification
- Estimated remaining time calculations
- Item counts and processing statistics
- Error detection and reporting
- Session status and cancellation capability

**Progress Information**:
- Overall completion percentage
- Current sync phase (detection, entities, labels, etc.)
- Items processed vs. total items
- Processing speed and throughput
- Estimated completion time
- Error counts and details

**When to Use**:
- Monitoring long-running sync operations
- Troubleshooting sync issues and bottlenecks
- Planning sync timing and scheduling
- Providing user feedback during sync operations
- Implementing sync monitoring dashboards

**Example Use Cases**:
```json
// Monitor sync session progress
{
  "tool": "d365fo_get_sync_progress",
  "arguments": {
    "session_id": "sync_12345678-1234-1234-1234-123456789012"
  }
}

// Check progress for specific profile
{
  "tool": "d365fo_get_sync_progress",
  "arguments": {
    "session_id": "sync_87654321-4321-4321-4321-210987654321",
    "profile": "production"
  }
}
```

---

### 32. `d365fo_cancel_sync`

**Purpose**: Cancel running sync sessions when needed for maintenance, error recovery, or strategy changes.

**Key Features**:
- Graceful cancellation with proper cleanup
- Session state validation before cancellation
- Partial progress preservation where possible
- Cancellation status and confirmation
- Error handling for non-cancellable sessions

**When to Use**:
- Stopping incorrect or unnecessary sync operations
- Emergency cancellation for system maintenance
- Changing sync strategies mid-operation
- Recovering from problematic sync sessions
- Implementing sync timeout and management policies

**Example Use Cases**:
```json
// Cancel running sync session
{
  "tool": "d365fo_cancel_sync",
  "arguments": {
    "session_id": "sync_12345678-1234-1234-1234-123456789012"
  }
}

// Cancel with specific profile
{
  "tool": "d365fo_cancel_sync",
  "arguments": {
    "session_id": "sync_87654321-4321-4321-4321-210987654321",
    "profile": "development"
  }
}
```

---

### 33. `d365fo_list_sync_sessions`

**Purpose**: List all currently active sync sessions with their status, progress, and details.

**Key Features**:
- Complete active session listing
- Session status and progress summaries
- Running vs. completed session identification
- Session metadata and timing information
- Multi-profile session management

**When to Use**:
- Understanding current sync activity across environments
- Managing multiple concurrent sync operations
- Troubleshooting sync conflicts and resource usage
- Implementing sync coordination and scheduling
- Building sync management interfaces

**Example Use Cases**:
```json
// List all active sync sessions
{
  "tool": "d365fo_list_sync_sessions"
}

// List sessions for specific profile
{
  "tool": "d365fo_list_sync_sessions",
  "arguments": {
    "profile": "production"
  }
}
```

---

### 34. `d365fo_get_sync_history`

**Purpose**: Retrieve historical information about completed sync sessions including success rates, performance metrics, and error analysis.

**Key Features**:
- Historical session data with success/failure rates
- Performance metrics and duration analysis
- Error patterns and troubleshooting information
- Success rate trends and reliability statistics
- Configurable history depth and filtering

**When to Use**:
- Analyzing sync performance and reliability
- Troubleshooting recurring sync issues
- Planning sync schedules and strategies
- Generating sync reports and analytics
- Implementing sync monitoring and alerting

**Example Use Cases**:
```json
// Get last 20 sync sessions
{
  "tool": "d365fo_get_sync_history",
  "arguments": {
    "limit": 20
  }
}

// Get comprehensive sync history
{
  "tool": "d365fo_get_sync_history",
  "arguments": {
    "limit": 100,
    "profile": "production"
  }
}
```

---

## Best Practices and Usage Guidelines

### General Best Practices

1. **Profile Management**: Always use specific profiles for different environments (dev, test, prod) to maintain proper isolation and security.

2. **Error Handling**: All tools return structured error information. Always check the success status and handle errors appropriately.

3. **Performance Optimization**: Use field selection (`select` parameter) and pagination (`top`, `skip`) for large datasets to optimize performance.

4. **Security**: Use client credentials authentication for production environments and store sensitive information in Azure Key Vault.

5. **Monitoring**: Use sync and database tools to monitor system health and performance regularly.

### Tool Selection Guidelines

- **For Data Access**: Use CRUD tools (`d365fo_query_entities`, `d365fo_get_entity_record`) for operational data access
- **For Discovery**: Use metadata tools (`d365fo_search_entities`, `d365fo_get_entity_schema`) for system exploration
- **For Operations**: Use action tools (`d365fo_call_action`) for business process execution
- **For Analysis**: Use database tools (`d365fo_execute_sql_query`) for metadata analysis and reporting
- **For Maintenance**: Use sync tools (`d365fo_start_sync`) for system maintenance and updates

### Integration Patterns

1. **Discovery → Schema → Operations**: First discover entities, then get their schemas, finally perform operations
2. **Profile → Connection → Operations**: Always validate profiles and connections before performing operations
3. **Sync → Cache → Query**: Ensure metadata is synchronized before relying on cached data
4. **Validate → Execute → Monitor**: Validate inputs, execute operations, and monitor results

This comprehensive guide provides the foundation for effectively using all MCP tools in the d365fo-client system for integration, analysis, and automation scenarios.