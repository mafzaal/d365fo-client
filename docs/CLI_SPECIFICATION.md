# Command Line Interface Specification for d365fo-client

## Overview
This specification defines the command-line interface (CLI) for the `d365fo-client` package, transforming it from a simple demo utility into a comprehensive command-line tool for interacting with Microsoft Dynamics 365 Finance & Operations environments.

## Current State Analysis
Based on analysis of the existing codebase, the following core functionalities are available:

### Core Client Features
- **Connection Management**: Test connectivity to OData and Metadata APIs
- **Authentication**: Azure AD integration with default credentials support
- **Metadata Operations**: Download, cache, and search metadata
- **Entity Operations**: CRUD operations on data entities
- **Action Operations**: Call OData actions with parameters
- **Label Operations**: Retrieve and cache label text with multilingual support
- **Query Operations**: Advanced OData query support with $select, $filter, $top, $orderby

### Metadata APIs
- **Data Entities API**: Search and retrieve data entity information
- **Public Entities API**: Access public entity metadata and properties
- **Public Enumerations API**: Access enumeration definitions and values
- **Version Methods**: Get application, platform, and build versions

### Search and Discovery
- **Entity Search**: Find entities by name patterns
- **Action Search**: Discover available OData actions
- **Metadata Search**: Full-text search across cached metadata

## Proposed CLI Structure

### 1. Main Command Structure
```
d365fo-client [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

### 2. Global Options
All commands support these global options:

```
--base-url URL          D365 F&O environment base URL (required)
--auth-mode MODE        Authentication mode: default|explicit|interactive
--client-id ID          Azure AD client ID (for explicit auth)
--client-secret SECRET  Azure AD client secret (for explicit auth)
--tenant-id ID          Azure AD tenant ID (for explicit auth)
--verify-ssl BOOL       Enable/disable SSL verification (default: true)
--cache-dir PATH        Metadata cache directory
--label-cache BOOL      Enable label caching (default: true)
--label-expiry MINUTES  Label cache expiry in minutes (default: 60)
--language CODE         Language code for labels (default: en-US)
--output FORMAT         Output format: json|table|csv|yaml (default: table)
--verbose, -v           Enable verbose output
--quiet, -q             Suppress non-essential output
--config FILE           Configuration file path
--profile NAME          Configuration profile to use
```

### 3. Commands

#### 3.1 Connection and Environment Commands

##### `test` - Test connectivity to D365 F&O environment
```bash
d365fo-client --base-url <URL> test [OPTIONS]

Options:
  --odata-only         Test only OData API connectivity
  --metadata-only      Test only Metadata API connectivity
  --timeout SECONDS    Connection timeout (default: 30)

Examples:
  d365fo-client --base-url https://myenv.dynamics.com test
  d365fo-client --base-url https://myenv.dynamics.com test --odata-only
```

##### `version` - Get environment version information
```bash
d365fo-client --base-url <URL> version [OPTIONS]

Options:
  --application        Get application version only
  --platform          Get platform build version only
  --build             Get application build version only
  --all               Get all version information (default)

Examples:
  d365fo-client --base-url https://myenv.dynamics.com version
  d365fo-client --base-url https://myenv.dynamics.com version --application
```

#### 3.2 Metadata Management Commands

##### `metadata sync` - Download and cache metadata
```bash
d365fo-client --base-url <URL> metadata sync [OPTIONS]

Options:
  --force             Force refresh of metadata cache
  --entities-only     Download only entity metadata
  --actions-only      Download only action metadata
  --labels-only       Download only label metadata
  --progress          Show download progress

Examples:
  d365fo-client --base-url https://myenv.dynamics.com metadata sync
  d365fo-client --base-url https://myenv.dynamics.com metadata sync --force
```

##### `metadata search` - Search metadata by entity type
```bash
d365fo-client --base-url <URL> metadata search PATTERN [OPTIONS]

Options:
  --type TYPE         Metadata type: entities|actions|enums|all (default: all)
  --category CAT      Entity category filter (Master|Transaction|etc.)
  --limit NUMBER      Maximum results to return (default: 50)
  --details           Show detailed information

Examples:
  d365fo-client --base-url https://myenv.dynamics.com metadata search customer
  d365fo-client --base-url https://myenv.dynamics.com metadata search customer --type entities
  d365fo-client --base-url https://myenv.dynamics.com metadata search payment --type enums
```

##### `metadata info` - Get detailed metadata information
```bash
d365fo-client --base-url <URL> metadata info ENTITY_NAME [OPTIONS]

Options:
  --properties        Show entity properties
  --keys             Show key properties only
  --navigation       Show navigation properties
  --labels           Resolve and show labels

Examples:
  d365fo-client --base-url https://myenv.dynamics.com metadata info Customers
  d365fo-client --base-url https://myenv.dynamics.com metadata info Customers --properties
```

#### 3.3 Data Entity Operations

##### `entity get` - Retrieve data from a data entity
```bash
d365fo-client --base-url <URL> entity get ENTITY_NAME [KEY] [OPTIONS]

Options:
  --select FIELDS     Comma-separated fields to select
  --filter FILTER     OData filter expression
  --orderby FIELDS    Comma-separated fields to order by
  --top NUMBER        Maximum records to return
  --skip NUMBER       Number of records to skip
  --expand FIELDS     Navigation properties to expand
  --count             Include total count in response
  --format FORMAT     Output format override

Examples:
  # Get all customers (limited to 10)
  d365fo-client --base-url https://myenv.dynamics.com entity get Customers --top 10
  
  # Get specific customer by key
  d365fo-client --base-url https://myenv.dynamics.com entity get Customers "US-001"
  
  # Get customers with filtering and selection
  d365fo-client --base-url https://myenv.dynamics.com entity get Customers \
    --select "CustomerAccount,Name,CurrencyCode" \
    --filter "contains(Name,'Contoso')" \
    --orderby "Name" \
    --top 5
```

##### `entity create` - Create a new entity record
```bash
d365fo-client --base-url <URL> entity create ENTITY_NAME [OPTIONS]

Options:
  --data JSON         JSON data for the new record
  --file PATH         JSON file containing record data
  --interactive       Interactive mode for data entry

Examples:
  d365fo-client --base-url https://myenv.dynamics.com entity create Customers \
    --data '{"CustomerAccount":"US-999","Name":"Test Customer"}'
  
  d365fo-client --base-url https://myenv.dynamics.com entity create Customers \
    --file customer_data.json
```

##### `entity update` - Update an existing entity record
```bash
d365fo-client --base-url <URL> entity update ENTITY_NAME KEY [OPTIONS]

Options:
  --data JSON         JSON data for updates
  --file PATH         JSON file containing update data
  --patch             Use PATCH method (default: PUT)

Examples:
  d365fo-client --base-url https://myenv.dynamics.com entity update Customers "US-001" \
    --data '{"Name":"Updated Customer Name"}'
```

##### `entity delete` - Delete an entity record
```bash
d365fo-client --base-url <URL> entity delete ENTITY_NAME KEY [OPTIONS]

Options:
  --confirm           Skip confirmation prompt
  --force             Force deletion

Examples:
  d365fo-client --base-url https://myenv.dynamics.com entity delete Customers "US-999"
```

#### 3.4 OData Action Operations

##### `action list` - List available OData actions
```bash
d365fo-client --base-url <URL> action list [PATTERN] [OPTIONS]

Options:
  --entity ENTITY     Filter actions by entity
  --bound-only        Show only bound actions
  --unbound-only      Show only unbound actions
  --parameters        Show action parameters

Examples:
  d365fo-client --base-url https://myenv.dynamics.com action list
  d365fo-client --base-url https://myenv.dynamics.com action list calculate
  d365fo-client --base-url https://myenv.dynamics.com action list --entity Customers
```

##### `action call` - Call an OData action
```bash
d365fo-client --base-url <URL> action call ACTION_NAME [OPTIONS]

Options:
  --entity ENTITY     Entity name (for bound actions)
  --key KEY          Entity key (for bound actions)
  --parameters JSON   Action parameters as JSON
  --file PATH        JSON file containing parameters
  --dry-run          Validate parameters without executing

Examples:
  # Call unbound action
  d365fo-client --base-url https://myenv.dynamics.com action call GetApplicationVersion
  
  # Call bound action with parameters
  d365fo-client --base-url https://myenv.dynamics.com action call CalculateTax \
    --entity SalesOrders \
    --key "SO-001" \
    --parameters '{"TaxGroup":"ALL"}'
```

#### 3.5 Label Operations

##### `label get` - Retrieve label text
```bash
d365fo-client --base-url <URL> label get LABEL_ID [OPTIONS]

Options:
  --language CODE     Language code (default: en-US)
  --batch             Process multiple label IDs from file
  --file PATH         File containing label IDs (one per line)

Examples:
  d365fo-client --base-url https://myenv.dynamics.com label get "@SYS78125"
  d365fo-client --base-url https://myenv.dynamics.com label get "@SYS78125" --language "fr-FR"
  d365fo-client --base-url https://myenv.dynamics.com label get --batch --file label_ids.txt
```

##### `label search` - Search labels by text pattern
```bash
d365fo-client --base-url <URL> label search PATTERN [OPTIONS]

Options:
  --language CODE     Language code (default: en-US)
  --limit NUMBER      Maximum results (default: 50)
  --exact             Exact match only

Examples:
  d365fo-client --base-url https://myenv.dynamics.com label search "customer"
  d365fo-client --base-url https://myenv.dynamics.com label search "customer" --exact
```

#### 3.6 Configuration Management

##### `config` - Manage configuration profiles
```bash
d365fo-client config SUBCOMMAND [OPTIONS]

Subcommands:
  list                List all configuration profiles
  show PROFILE        Show profile configuration
  create PROFILE      Create new profile
  update PROFILE      Update existing profile
  delete PROFILE      Delete profile
  set-default PROFILE Set default profile

Examples:
  d365fo-client config create production --base-url https://prod.dynamics.com
  d365fo-client config list
  d365fo-client config set-default production
```

### 4. Configuration File Support

#### 4.1 Configuration File Format (YAML)
```yaml
# ~/.d365fo-client/config.yaml
default_profile: development

profiles:
  development:
    base_url: "https://dev.dynamics.com"
    auth_mode: "default"
    verify_ssl: false
    cache_dir: "~/.d365fo-client/cache/dev"
    label_cache: true
    label_expiry: 60
    language: "en-US"
    output_format: "table"
  
  production:
    base_url: "https://prod.dynamics.com"
    auth_mode: "explicit"
    client_id: "${D365FO_CLIENT_ID}"
    client_secret: "${D365FO_CLIENT_SECRET}"
    tenant_id: "${D365FO_TENANT_ID}"
    verify_ssl: true
    cache_dir: "~/.d365fo-client/cache/prod"
    label_cache: true
    label_expiry: 120
    language: "en-US"
    output_format: "json"

global:
  verbose: false
  timeout: 30
  max_retries: 3
```

#### 4.2 Environment Variable Support
```bash
D365FO_BASE_URL
D365FO_CLIENT_ID
D365FO_CLIENT_SECRET
D365FO_TENANT_ID
D365FO_CACHE_DIR
D365FO_OUTPUT_FORMAT
D365FO_LANGUAGE
D365FO_PROFILE
```

### 5. Output Formats

#### 5.1 Table Format (Default)
```
Entity Name    | Category    | Label                | Properties
---------------|-------------|----------------------|-----------
Customers      | Master      | Customer master      | 45
Vendors        | Master      | Vendor master        | 38
SalesOrders    | Transaction | Sales orders         | 67
```

#### 5.2 JSON Format
```json
{
  "entities": [
    {
      "name": "Customers",
      "category": "Master",
      "label": "Customer master",
      "property_count": 45
    }
  ],
  "total_count": 1,
  "execution_time": "0.234s"
}
```

#### 5.3 CSV Format
```csv
EntityName,Category,Label,Properties
Customers,Master,Customer master,45
Vendors,Master,Vendor master,38
SalesOrders,Transaction,Sales orders,67
```

#### 5.4 YAML Format
```yaml
entities:
  - name: Customers
    category: Master
    label: Customer master
    property_count: 45
total_count: 1
execution_time: 0.234s
```

### 6. Error Handling and Logging

#### 6.1 Error Response Format
```json
{
  "error": {
    "type": "AuthenticationError",
    "message": "Failed to authenticate with Azure AD",
    "details": "Invalid client credentials",
    "timestamp": "2025-08-16T10:30:00Z",
    "request_id": "abc123"
  }
}
```

#### 6.2 Logging Levels
- `--quiet`: Only errors
- Default: Warnings and errors
- `--verbose`: Info, warnings, and errors
- `--debug`: All log levels including debug

### 7. Examples and Use Cases

#### 7.1 Daily Operations
```bash
# Setup environment
d365fo-client config create myenv --base-url https://myenv.dynamics.com

# Test connectivity
d365fo-client --profile myenv test

# Sync metadata
d365fo-client --profile myenv metadata sync

# Search for customer entities
d365fo-client --profile myenv metadata search customer --type entities

# Get customer data
d365fo-client --profile myenv entity get Customers --top 10 --output json

# Get specific customer
d365fo-client --profile myenv entity get Customers "US-001"

# Call version action
d365fo-client --profile myenv action call GetApplicationVersion
```

#### 7.2 Data Migration Scenarios
```bash
# Export data to JSON
d365fo-client --profile source entity get Customers --output json > customers.json

# Import data to target environment
d365fo-client --profile target entity create Customers --file customers.json
```

#### 7.3 Metadata Analysis
```bash
# Get all customer-related entities
d365fo-client --profile myenv metadata search customer --type entities --output csv > customer_entities.csv

# Get detailed entity information
d365fo-client --profile myenv metadata info Customers --properties --output yaml > customers_metadata.yaml
```

### 8. Implementation Plan

#### Phase 1: Core CLI Framework
1. Argument parsing and command structure
2. Configuration file support
3. Profile management
4. Output formatting
5. Error handling

#### Phase 2: Basic Commands
1. Test connectivity
2. Version information
3. Basic metadata sync
4. Simple entity operations

#### Phase 3: Advanced Features
1. Advanced metadata search
2. Complex OData queries
3. Action operations
4. Label operations
5. Batch operations

#### Phase 4: Enhanced Features
1. Interactive mode
2. Progress indicators
3. Performance metrics
4. Advanced filtering
5. Export/import utilities

### 9. Technical Considerations

#### 9.1 Backward Compatibility
- Maintain existing `--demo` option for backward compatibility
- Keep existing example_usage() function
- Preserve existing API when adding CLI features

#### 9.2 Performance
- Implement caching for frequently accessed data
- Support parallel operations where applicable
- Add timeout configurations
- Implement retry mechanisms

#### 9.3 Security
- Secure credential storage
- Environment variable support
- Profile-based configuration
- SSL/TLS validation

#### 9.4 Testing
- Unit tests for all CLI commands
- Integration tests with mock D365 environments
- Configuration file validation tests
- Output format validation tests

This specification provides a comprehensive foundation for transforming the current simple demo utility into a powerful command-line tool for D365 Finance & Operations operations.