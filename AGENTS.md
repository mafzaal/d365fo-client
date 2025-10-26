# AI Agent Guide for D365FO MCP Server

This guide is specifically designed for AI agents and assistants to effectively interact with Microsoft Dynamics 365 Finance & Operations through the d365fo-client MCP server. It provides structured workflows, best practices, and common patterns for successful automation and integration.

## Architecture Overview

The d365fo-client MCP server provides **49 comprehensive tools** organized across **9 functional categories**, implemented using a modern FastMCP mixin-based architecture for enhanced performance and maintainability. All tools are available through standardized MCP protocol interactions regardless of the underlying implementation.

## Quick Start for AI Agents

### Essential First Steps

1. **Test Connectivity**: Always start with `d365fo_test_connection` to verify environment access
2. **Get Environment Info**: Use `d365fo_get_environment_info` to understand the D365FO environment capabilities
3. **Explore Available Entities**: Use `d365fo_search_entities` to discover relevant data entities for your tasks

```json
// Step 1: Test connection
{
  "tool": "d365fo_test_connection",
  "arguments": {}
}

// Step 2: Get environment information
{
  "tool": "d365fo_get_environment_info",
  "arguments": {}
}

// Step 3: Search for relevant entities
{
  "tool": "d365fo_search_entities",
  "arguments": {
    "pattern": "customer",
    "limit": 10
  }
}
```

## Core Workflows for AI Agents

### 1. Data Discovery and Exploration

**Use Case**: Understanding available data structures and relationships

```json
// Discover entities by business area
{
  "tool": "d365fo_search_entities",
  "arguments": {
    "pattern": "sales|customer|invoice",
    "category": "Master",
    "limit": 20
  }
}

// Get detailed schema for specific entity
{
  "tool": "d365fo_get_entity_schema",
  "arguments": {
    "entityName": "CustomersV3",
    "includeProperties": true,
    "includeKeys": true,
    "resolveLabels": true
  }
}

// Search for related actions
{
  "tool": "d365fo_search_actions",
  "arguments": {
    "pattern": "customer",
    "limit": 10
  }
}
```

### 2. Data Querying and Analysis

**Use Case**: Retrieving and analyzing business data

```json
// Query customers with filtering
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "CustomersV3",
    "select": ["CustomerAccount", "Name", "CustomerGroup", "Email"],
    "filter": "CustomerGroup eq 'VIP'",
    "top": 50
  }
}

// Get specific customer record
{
  "tool": "d365fo_get_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "key": "US-001",
    "select": ["CustomerAccount", "Name", "Address", "ContactInfo"]
  }
}

// Query related sales orders
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "SalesOrderHeaders",
    "select": ["SalesOrderNumber", "CustomerAccount", "TotalAmount", "OrderDate"],
    "filter": "CustomerAccount eq 'US-001'",
    "orderby": "OrderDate desc",
    "top": 20
  }
}
```

### 3. Data Management Operations

**Use Case**: Creating, updating, and managing business records

```json
// Create new customer
{
  "tool": "d365fo_create_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "data": {
      "CustomerAccount": "US-999",
      "Name": "New Customer Corp",
      "CustomerGroup": "Standard",
      "Email": "contact@newcustomer.com"
    }
  }
}

// Update customer information
{
  "tool": "d365fo_update_entity_record",
  "arguments": {
    "entityName": "CustomersV3",
    "key": "US-999",
    "data": {
      "Email": "updated@newcustomer.com",
      "Name": "Updated Customer Corp"
    }
  }
}

// Execute business action
{
  "tool": "d365fo_call_action",
  "arguments": {
    "entityName": "CustomersV3",
    "actionName": "ValidateCustomer",
    "parameters": {
      "CustomerAccount": "US-999"
    }
  }
}
```

### 4. Metadata and System Management

**Use Case**: Understanding system configuration and capabilities

```json
// Search system enumerations
{
  "tool": "d365fo_search_enumerations",
  "arguments": {
    "search": "status",
    "limit": 10
  }
}

// Get enumeration values
{
  "tool": "d365fo_get_enumeration_fields",
  "arguments": {
    "enumerationName": "CustVendorBlocked",
    "resolveLabels": true
  }
}

// Get installed modules
{
  "tool": "d365fo_get_installed_modules",
  "arguments": {}
}
```

### 5. Reporting and Document Management

**Use Case**: Generating and downloading business documents

```json
// Download customer invoice
{
  "tool": "d365fo_download_customer_invoice",
  "arguments": {
    "invoiceId": "INV-001",
    "format": "PDF",
    "profile": "default"
  }
}

// Download sales confirmation
{
  "tool": "d365fo_download_sales_confirmation",
  "arguments": {
    "salesOrderNumber": "SO-001",
    "format": "PDF",
    "profile": "default"
  }
}

// Generate custom SRS report
{
  "tool": "d365fo_download_srs_report",
  "arguments": {
    "reportName": "CustomerStatement",
    "parameters": {
      "CustomerAccount": "US-001",
      "FromDate": "2024-01-01",
      "ToDate": "2024-12-31"
    },
    "format": "PDF"
  }
}
```

## Advanced Patterns for AI Agents

### Profile-Based Multi-Environment Operations

**Use Case**: Working with multiple D365FO environments (dev, test, prod)

```json
// List available profiles
{
  "tool": "d365fo_list_profiles",
  "arguments": {}
}

// Test specific environment
{
  "tool": "d365fo_test_profile_connection",
  "arguments": {
    "profileName": "production"
  }
}

// Query data from specific environment
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "CustomersV3",
    "profile": "production",
    "top": 10
  }
}
```

### Database Analysis and Insights

**Use Case**: Advanced data analysis and metadata exploration

```json
// Get database schema overview
{
  "tool": "d365fo_get_database_schema",
  "arguments": {
    "includeEntityRelationships": true,
    "profile": "default"
  }
}

// Execute analytical queries
{
  "tool": "d365fo_execute_sql_query",
  "arguments": {
    "query": "SELECT name, entity_category, data_service_enabled FROM data_entities WHERE entity_category = 'Master' ORDER BY name LIMIT 20",
    "profile": "default"
  }
}

// Get performance statistics
{
  "tool": "d365fo_get_database_statistics",
  "arguments": {
    "includePerformanceMetrics": true,
    "profile": "default"
  }
}
```

### Synchronization and Cache Management

**Use Case**: Managing metadata synchronization and cache optimization

```json
// Start metadata sync
{
  "tool": "d365fo_start_sync",
  "arguments": {
    "strategy": "incremental",
    "profile": "default"
  }
}

// Monitor sync progress
{
  "tool": "d365fo_get_sync_progress",
  "arguments": {
    "sessionId": "sync-session-123",
    "profile": "default"
  }
}

// Get sync history
{
  "tool": "d365fo_get_sync_history",
  "arguments": {
    "limit": 10,
    "profile": "default"
  }
}
```

## Best Practices for AI Agents

### 1. Error Handling and Resilience

- **Always check connection first**: Use `d365fo_test_connection` before starting workflows
- **Handle authentication errors**: Retry with different profiles if authentication fails
- **Validate entity names**: Use `d365fo_search_entities` to verify entity existence before operations
- **Check for required fields**: Use `d365fo_get_entity_schema` to understand mandatory fields before creating records

### 2. Performance Optimization

- **Use appropriate filters**: Apply `$filter` parameters to reduce data transfer
- **Limit result sets**: Always use `top` parameter for large queries
- **Select specific fields**: Use `select` parameter to retrieve only needed columns
- **Cache metadata**: Leverage the built-in metadata caching for repeated operations

### 3. Data Integrity

- **Validate before updates**: Check existing record state before modifications
- **Use ETags for concurrency**: Leverage optimistic concurrency control where available
- **Understand relationships**: Use `d365fo_get_entity_schema` to understand foreign key relationships
- **Test in non-production**: Always test complex operations in development environments first

### 4. Security and Compliance

- **Use appropriate profiles**: Separate development, test, and production profiles
- **Validate permissions**: Check that the current user has appropriate permissions for operations
- **Audit operations**: Log significant data changes for compliance requirements
- **Secure credentials**: Use profile-based authentication rather than embedding credentials

## Common Integration Scenarios

### Customer Relationship Management

```json
// Complete customer onboarding workflow
[
  {
    "tool": "d365fo_search_entities",
    "arguments": {"pattern": "customer", "category": "Master"}
  },
  {
    "tool": "d365fo_get_entity_schema",
    "arguments": {"entityName": "CustomersV3", "includeProperties": true}
  },
  {
    "tool": "d365fo_create_entity_record",
    "arguments": {
      "entityName": "CustomersV3",
      "data": {
        "CustomerAccount": "NEW-001",
        "Name": "New Customer",
        "CustomerGroup": "Standard"
      }
    }
  },
  {
    "tool": "d365fo_get_entity_record",
    "arguments": {"entityName": "CustomersV3", "key": "NEW-001"}
  }
]
```

### Financial Reporting

```json
// Generate comprehensive financial report
[
  {
    "tool": "d365fo_query_entities",
    "arguments": {
      "entityName": "GeneralJournalEntries",
      "filter": "AccountingDate ge datetime'2024-01-01' and AccountingDate le datetime'2024-12-31'",
      "select": ["AccountNum", "TransactionAmount", "AccountingDate"],
      "top": 1000
    }
  },
  {
    "tool": "d365fo_download_srs_report",
    "arguments": {
      "reportName": "FinancialStatement",
      "parameters": {"FiscalYear": "2024"},
      "format": "PDF"
    }
  }
]
```

### Supply Chain Management

```json
// Inventory and procurement analysis
[
  {
    "tool": "d365fo_query_entities",
    "arguments": {
      "entityName": "InventoryOnHand",
      "select": ["ItemNumber", "AvailableQuantity", "WarehouseId"],
      "filter": "AvailableQuantity lt 10"
    }
  },
  {
    "tool": "d365fo_query_entities",
    "arguments": {
      "entityName": "PurchaseOrders",
      "filter": "PurchaseOrderStatus eq 'Open'",
      "select": ["PurchaseOrderNumber", "VendorAccount", "TotalAmount"]
    }
  }
]
```

## Troubleshooting Guide for AI Agents

### Common Issues and Solutions

1. **Connection Failures**
   ```json
   // Test with explicit timeout
   {
     "tool": "d365fo_test_connection",
     "arguments": {"timeout": 120}
   }
   ```

2. **Entity Not Found Errors**
   ```json
   // Search for similar entities
   {
     "tool": "d365fo_search_entities",
     "arguments": {"pattern": "partial_name"}
   }
   ```

3. **Authentication Issues**
   ```json
   // List and test profiles
   {
     "tool": "d365fo_list_profiles",
     "arguments": {}
   }
   ```

4. **Data Validation Errors**
   ```json
   // Get entity schema for validation rules
   {
     "tool": "d365fo_get_entity_schema",
     "arguments": {"entityName": "EntityName", "includeProperties": true}
   }
   ```

### Performance Monitoring

```json
// Monitor server performance
{
  "tool": "d365fo_get_server_performance",
  "arguments": {}
}

// Check database statistics
{
  "tool": "d365fo_get_database_statistics",
  "arguments": {"includePerformanceMetrics": true}
}
```

## Tool Reference Quick Guide

### Essential Tools for Every AI Agent
- `d365fo_test_connection` - Always start here
- `d365fo_get_environment_info` - Understand the environment
- `d365fo_search_entities` - Discover available data
- `d365fo_query_entities` - Primary data retrieval
- `d365fo_get_entity_schema` - Understand data structures

### Data Operations
- `d365fo_get_entity_record` - Retrieve specific records
- `d365fo_create_entity_record` - Create new records
- `d365fo_update_entity_record` - Modify existing records
- `d365fo_delete_entity_record` - Remove records
- `d365fo_call_action` - Execute business logic

### Advanced Operations
- `d365fo_execute_sql_query` - Custom analytical queries
- `d365fo_download_srs_report` - Generate reports
- `d365fo_start_sync` - Manage metadata synchronization
- `d365fo_get_labels_batch` - Multi-language support

### Profile Management
- `d365fo_list_profiles` - See available environments
- `d365fo_test_profile_connection` - Validate environment access
- `d365fo_create_profile` - Set up new environments

## Success Patterns

1. **Start Small**: Begin with simple queries before complex operations
2. **Understand the Schema**: Always explore entity schemas before data operations
3. **Use Filters Wisely**: Apply appropriate filters to manage data volume
4. **Test Incrementally**: Validate each step of complex workflows
5. **Monitor Performance**: Use performance tools to optimize operations
6. **Handle Errors Gracefully**: Implement robust error handling and recovery
7. **Document Workflows**: Keep track of successful patterns for reuse

This guide provides AI agents with the knowledge and patterns needed to effectively leverage the full capabilities of the D365FO MCP server for automation, integration, and analysis tasks.