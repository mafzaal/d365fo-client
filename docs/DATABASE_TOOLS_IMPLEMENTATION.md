# Database Schema Exposure and SQL Query Tools for MCP Server

## Overview

This document describes the implementation of database schema exposure and SQL query execution capabilities for the d365fo-client MCP Server. These new features allow AI assistants and other MCP clients to analyze the metadata database structure and execute SELECT queries to gain insights from cached D365 Finance & Operations metadata.

## Architecture

### 1. Database Tools (`DatabaseTools`)

A new tool handler class that provides secure SQL query execution capabilities:

#### Key Features:
- **SQL Query Execution**: Execute SELECT queries against the metadata database
- **Query Safety Validation**: Comprehensive security checks to prevent dangerous operations
- **Multiple Output Formats**: Support for table, JSON, and CSV output formats
- **Performance Monitoring**: Query execution time tracking and result set size management
- **Database Schema Discovery**: Retrieve detailed table schemas, indexes, and relationships

#### Safety Mechanisms:
- **Whitelist-based Operation Control**: Only SELECT queries are allowed
- **SQL Injection Protection**: Pattern-based detection of dangerous SQL constructs
- **Result Set Limits**: Maximum 1000 rows per query to prevent memory issues
- **Query Timeout**: 30-second execution timeout
- **Sensitive Table Protection**: Restricted access to tables containing sensitive data

### 2. Database Resource Handler (`DatabaseResourceHandler`)

A new resource handler that exposes database schema information as MCP resources:

#### Available Resources:
- `d365fo://database/schema` - Complete database schema with all tables
- `d365fo://database/statistics` - Database performance statistics and metrics
- `d365fo://database/tables` - List of all tables with basic information
- `d365fo://database/indexes` - All database indexes and their characteristics  
- `d365fo://database/relationships` - Foreign key relationships between tables
- `d365fo://database/tables/{table_name}` - Detailed information for specific tables

## Tools Reference

### 1. `d365fo_execute_sql_query`

Execute SELECT queries against the D365FO metadata database.

**Purpose**: Analyze metadata patterns, generate reports, and gain insights into D365FO structure.

**Parameters**:
- `query` (required): SQL SELECT query to execute
- `limit` (optional): Maximum rows to return (default: 100, max: 1000)
- `format` (optional): Output format - "table", "json", or "csv" (default: "table")
- `profile` (optional): Configuration profile to use

**Example Usage**:
```sql
-- Get most used entities by category
SELECT entity_category, COUNT(*) as count 
FROM data_entities 
GROUP BY entity_category 
ORDER BY count DESC

-- Find entities with most properties
SELECT pe.name, COUNT(ep.id) as property_count 
FROM public_entities pe 
LEFT JOIN entity_properties ep ON pe.id = ep.entity_id 
GROUP BY pe.id 
ORDER BY property_count DESC 
LIMIT 10

-- Analyze environment versions
SELECT me.environment_name, gv.version_hash, ev.detected_at 
FROM metadata_environments me 
JOIN environment_versions ev ON me.id = ev.environment_id 
JOIN global_versions gv ON ev.global_version_id = gv.id
```

**Safety Features**:
- Only SELECT operations allowed
- Dangerous SQL patterns blocked (DROP, DELETE, UPDATE, etc.)
- Query complexity analysis
- Result set size limits
- Execution timeout protection

### 2. `d365fo_get_database_schema`

Get comprehensive database schema information.

**Purpose**: Understand database structure before writing SQL queries.

**Parameters**:
- `table_name` (optional): Get schema for specific table only
- `include_statistics` (optional): Include table row counts and sizes (default: true)
- `include_indexes` (optional): Include index information (default: true)
- `include_relationships` (optional): Include foreign key relationships (default: true)
- `profile` (optional): Configuration profile to use

**Output**: Complete schema information including:
- Table structures with column definitions
- Primary and foreign key constraints
- Index definitions and characteristics
- Table statistics (row counts, sizes)
- Relationship mappings between tables

### 3. `d365fo_get_table_info`

Get detailed information about a specific database table.

**Purpose**: Explore specific tables before writing queries.

**Parameters**:
- `table_name` (required): Name of the table to analyze
- `include_sample_data` (optional): Include sample data (first 5 rows) (default: false)
- `include_relationships` (optional): Include relationship information (default: true)
- `profile` (optional): Configuration profile to use

**Output**: Detailed table information including:
- Column definitions with types and constraints
- Primary and foreign key information
- Index characteristics
- Table statistics
- Optional sample data
- Relationships to other tables

### 4. `d365fo_get_database_statistics`

Get comprehensive database statistics and analytics.

**Purpose**: Understand overall database state and health.

**Parameters**:
- `include_table_stats` (optional): Include per-table statistics (default: true)
- `include_version_stats` (optional): Include version statistics (default: true)
- `include_performance_stats` (optional): Include performance metrics (default: true)
- `profile` (optional): Configuration profile to use

**Output**: Comprehensive statistics including:
- Database size and table counts
- Record counts by table
- Global version statistics
- Environment statistics
- Storage utilization analysis
- Performance metrics

## Database Tables Reference

### Core Environment Management
- **`metadata_environments`**: D365FO environments and their details
- **`global_versions`**: Global version registry with hash and reference counts
- **`environment_versions`**: Links between environments and global versions
- **`global_version_modules`**: Module information for each global version

### Entity Metadata
- **`data_entities`**: D365FO data entities metadata
- **`public_entities`**: Public entity schemas and configurations
- **`entity_properties`**: Detailed property information for entities
- **`navigation_properties`**: Navigation property definitions
- **`relation_constraints`**: Relationship constraints between entities

### Actions and Operations
- **`entity_actions`**: Available OData actions for entities
- **`action_parameters`**: Parameters for entity actions

### Enumerations
- **`enumerations`**: System enumerations and their metadata
- **`enumeration_members`**: Individual enumeration values and labels

### Caching and Search
- **`labels_cache`**: Cached label translations (restricted access)
- **`metadata_search_v2`**: FTS5 search index for metadata

## Resources Reference

### Database Schema Resources

All database resources use the URI pattern `d365fo://database/{resource_type}` and return JSON-formatted data.

#### `d365fo://database/schema`
Complete database schema with all tables, columns, indexes, and relationships.

#### `d365fo://database/statistics`  
Database performance statistics, table sizes, and utilization metrics.

#### `d365fo://database/tables`
List of all database tables with basic information (name, row count, column count, primary keys).

#### `d365fo://database/indexes`
All database indexes with their characteristics, columns, and performance implications.

#### `d365fo://database/relationships`
Foreign key relationships between tables with referential integrity information.

#### `d365fo://database/tables/{table_name}`
Detailed schema and sample data for a specific table.

## Security Considerations

### SQL Injection Prevention
- Parameterized query validation
- Pattern-based detection of dangerous SQL constructs
- Whitelist-based operation control
- Input sanitization and validation

### Access Control
- Read-only database access enforced
- Sensitive table access restrictions
- Query complexity analysis and limits
- Rate limiting capabilities

### Data Protection
- No access to sensitive authentication data
- Labels cache access restricted
- Query result size limitations
- Audit logging of database operations

## Performance Optimization

### Query Execution
- 30-second timeout protection
- Result set size limits (max 1000 rows)
- Memory-efficient result processing
- Query performance monitoring

### Caching Strategy
- Schema information caching
- Result set caching for common queries
- Connection pooling and reuse
- Efficient data serialization

### Resource Management
- Memory usage monitoring
- Connection lifecycle management
- Background cleanup processes
- Performance metrics collection

## Use Cases

### 1. Metadata Analysis
- Analyze entity usage patterns across environments
- Identify most complex entities (highest property counts)
- Study relationship patterns between entities
- Monitor metadata growth over time

### 2. Environment Comparison
- Compare metadata across different D365FO environments
- Identify version differences and incompatibilities
- Analyze module deployment patterns
- Track metadata synchronization status

### 3. Performance Monitoring
- Monitor database growth and utilization
- Identify performance bottlenecks
- Analyze query patterns and optimization opportunities
- Track cache hit rates and efficiency

### 4. Data Quality Analysis
- Identify entities with missing or incomplete metadata
- Analyze label coverage and translation completeness
- Detect orphaned or unused metadata entries
- Validate referential integrity

### 5. Integration Planning
- Understand entity relationships for integration design
- Identify key entities for data migration
- Analyze action availability for automation
- Plan API usage strategies

## Example Queries

### Entity Analysis
```sql
-- Top 10 entities by property count
SELECT pe.name, COUNT(ep.id) as property_count
FROM public_entities pe
LEFT JOIN entity_properties ep ON pe.id = ep.entity_id
GROUP BY pe.id, pe.name
ORDER BY property_count DESC
LIMIT 10;

-- Entities by category with OData availability
SELECT 
    entity_category,
    data_service_enabled,
    COUNT(*) as count
FROM data_entities
GROUP BY entity_category, data_service_enabled
ORDER BY entity_category, data_service_enabled;
```

### Environment Analysis
```sql
-- Environment version history
SELECT 
    me.environment_name,
    gv.version_hash,
    ev.detected_at,
    ev.sync_status
FROM metadata_environments me
JOIN environment_versions ev ON me.id = ev.environment_id
JOIN global_versions gv ON ev.global_version_id = gv.id
ORDER BY me.environment_name, ev.detected_at DESC;

-- Module distribution across versions
SELECT 
    gvm.module_name,
    gvm.version,
    COUNT(DISTINCT gv.id) as version_count
FROM global_version_modules gvm
JOIN global_versions gv ON gvm.global_version_id = gv.id
GROUP BY gvm.module_name, gvm.version
ORDER BY version_count DESC;
```

### Relationship Analysis
```sql
-- Most referenced tables
SELECT 
    rc.table as referenced_table,
    COUNT(*) as reference_count
FROM relation_constraints rc
GROUP BY rc.table
ORDER BY reference_count DESC
LIMIT 10;

-- Entity action analysis
SELECT 
    binding_kind,
    COUNT(*) as action_count,
    COUNT(DISTINCT entity_id) as entity_count
FROM entity_actions
GROUP BY binding_kind;
```

## Integration with Existing MCP Server

The database tools and resources are fully integrated with the existing MCP server architecture:

### Tool Registration
Database tools are automatically registered and available alongside existing tools (connection, CRUD, metadata, labels, profiles).

### Resource Discovery
Database resources are included in the resource listing and follow the same URI patterns as other resources.

### Error Handling
Comprehensive error handling with structured error responses and detailed logging.

### Configuration Management
Database tools respect the same profile-based configuration system as other tools.

### Performance Monitoring
Database operations are tracked and included in overall server performance metrics.

## Future Enhancements

### Advanced Query Features
- Stored procedure support for complex analytics
- Query result caching and optimization
- Advanced security controls and user permissions
- Query result visualization capabilities

### Enhanced Analytics
- Automated metadata quality scoring
- Trend analysis and alerting
- Performance benchmarking and optimization
- Integration with external analytics tools

### Additional Database Support
- Support for external database connections
- Multi-database query federation
- Real-time data synchronization monitoring
- Advanced backup and recovery analytics

## Conclusion

The database schema exposure and SQL query tools provide powerful capabilities for analyzing D365 Finance & Operations metadata. These tools enable AI assistants and other MCP clients to gain deep insights into system structure, performance, and data quality while maintaining strict security controls and performance optimization.

The implementation follows established patterns in the d365fo-client codebase and integrates seamlessly with existing MCP server functionality, providing a comprehensive solution for metadata analysis and reporting.