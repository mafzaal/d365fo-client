# Database Tools Quick Reference Guide

## Overview

The d365fo-client MCP Server now includes powerful database analysis tools that allow you to explore and query the metadata database used to cache D365 Finance & Operations information.

## Available Tools

### 1. Execute SQL Query (`d365fo_execute_sql_query`)

**What it does**: Run SELECT queries against the metadata database to analyze patterns and generate insights.

**Key Parameters**:
- `query`: Your SQL SELECT statement
- `limit`: Max rows to return (default: 100, max: 1000)
- `format`: Output format - "table", "json", or "csv"

**Example Usage**:
```json
{
  "tool": "d365fo_execute_sql_query",
  "arguments": {
    "query": "SELECT entity_category, COUNT(*) as count FROM data_entities GROUP BY entity_category ORDER BY count DESC",
    "format": "table",
    "limit": 50
  }
}
```

### 2. Get Database Schema (`d365fo_get_database_schema`)

**What it does**: Retrieve complete database structure information.

**Example Usage**:
```json
{
  "tool": "d365fo_get_database_schema",
  "arguments": {
    "include_statistics": true,
    "include_indexes": true,
    "include_relationships": true
  }
}
```

### 3. Get Table Info (`d365fo_get_table_info`)

**What it does**: Get detailed information about a specific table.

**Example Usage**:
```json
{
  "tool": "d365fo_get_table_info",
  "arguments": {
    "table_name": "data_entities",
    "include_sample_data": true,
    "include_relationships": true
  }
}
```

### 4. Get Database Statistics (`d365fo_get_database_statistics`)

**What it does**: Get comprehensive database performance and usage statistics.

**Example Usage**:
```json
{
  "tool": "d365fo_get_database_statistics",
  "arguments": {
    "include_table_stats": true,
    "include_version_stats": true,
    "include_performance_stats": true
  }
}
```

## Available Database Resources

Access these via MCP resource URIs:

- `d365fo://database/schema` - Complete database schema
- `d365fo://database/statistics` - Database statistics
- `d365fo://database/tables` - List of all tables
- `d365fo://database/indexes` - Index information
- `d365fo://database/relationships` - Foreign key relationships
- `d365fo://database/tables/{table_name}` - Specific table details

## Key Database Tables

### Entity Metadata
- **`data_entities`** - D365FO data entities with categories and capabilities
- **`public_entities`** - Public entity schemas and configurations
- **`entity_properties`** - Detailed field information for entities
- **`entity_actions`** - Available OData actions

### Environment Management
- **`metadata_environments`** - D365FO environments and URLs
- **`global_versions`** - Version registry with hashes
- **`environment_versions`** - Environment-version mappings

### System Data
- **`enumerations`** - System enumerations
- **`enumeration_members`** - Enumeration values
- **`metadata_search_v2`** - FTS5 search index

## Common Query Examples

### Entity Analysis
```sql
-- Most complex entities (by property count)
SELECT pe.name, COUNT(ep.id) as property_count
FROM public_entities pe
LEFT JOIN entity_properties ep ON pe.id = ep.entity_id
GROUP BY pe.id, pe.name
ORDER BY property_count DESC
LIMIT 10;

-- Entities by category and OData availability
SELECT entity_category, data_service_enabled, COUNT(*) as count
FROM data_entities
GROUP BY entity_category, data_service_enabled;
```

### Environment Analysis
```sql
-- Environment version information
SELECT me.environment_name, gv.version_hash, ev.detected_at
FROM metadata_environments me
JOIN environment_versions ev ON me.id = ev.environment_id
JOIN global_versions gv ON ev.global_version_id = gv.id;

-- Module distribution
SELECT module_name, version, COUNT(*) as usage_count
FROM global_version_modules
GROUP BY module_name, version
ORDER BY usage_count DESC;
```

### Relationship Analysis
```sql
-- Most referenced entities
SELECT pe.name, COUNT(np.id) as reference_count
FROM public_entities pe
LEFT JOIN navigation_properties np ON pe.name = np.related_entity
GROUP BY pe.id, pe.name
ORDER BY reference_count DESC;

-- Action binding analysis
SELECT binding_kind, COUNT(*) as action_count
FROM entity_actions
GROUP BY binding_kind;
```

## Safety Features

### What's Allowed
✅ SELECT queries only  
✅ JOINs, GROUP BY, ORDER BY  
✅ Aggregate functions (COUNT, SUM, AVG, etc.)  
✅ Subqueries and CTEs  
✅ LIMIT and filtering  

### What's Blocked
❌ INSERT, UPDATE, DELETE  
❌ DROP, CREATE, ALTER  
❌ SQL injection patterns  
❌ Access to sensitive tables  
❌ Queries without limits (auto-limited to 1000 rows)  

## Tips for Effective Use

1. **Start with Schema Exploration**: Use `d365fo_get_database_schema` to understand the structure
2. **Use Table Info for Details**: Get specific table information before writing complex queries
3. **Leverage Statistics**: Use database statistics to understand data distribution
4. **Format for Your Needs**: Choose JSON for programmatic use, table for human reading
5. **Mind the Limits**: Queries are limited to 1000 rows for performance
6. **Use Appropriate JOINs**: Many tables are related via foreign keys - check relationships first

## Error Handling

The tools provide detailed error messages for:
- SQL syntax errors
- Safety violations (non-SELECT operations)
- Table not found errors
- Query timeout issues
- Permission problems

All errors include context and suggestions for resolution.

## Performance Considerations

- Queries timeout after 30 seconds
- Results are limited to 1000 rows maximum
- Complex queries may take longer on large databases
- Use LIMIT clauses for better performance
- Index information is available to optimize queries

## Integration with Other Tools

These database tools complement existing MCP tools:
- Use with metadata search tools for comprehensive analysis
- Combine with entity schema tools for detailed exploration
- Leverage alongside label tools for complete metadata understanding
- Use with environment tools for cross-environment comparisons

The database tools provide the analytical foundation for deep insights into your D365 Finance & Operations metadata!