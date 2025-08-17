# Metadata Cache Statistics

## Overview

The `MetadataDatabase` and `MetadataCache` classes now include comprehensive statistics functionality that provides detailed insights into metadata storage, cache performance, and database health.

## Features

### Database Statistics (`MetadataDatabase.get_statistics()`)

Provides comprehensive statistics about the metadata database including:

- **Table Record Counts**: Count of records in each metadata table
- **Database File Information**: File size in bytes and MB
- **Environment Summary**: List of all environments with version counts
- **FTS Search Index Status**: Search index entry count and health
- **Environment-Specific Metrics**: Active version details and entity counts per environment

### Cache Statistics (`MetadataCache.get_statistics()`)

Provides cache-level statistics including all database statistics plus:

- **Cache Configuration**: TTL settings, memory limits, FTS status
- **Cache Layer Health**: Memory cache, disk cache, and database availability
- **Environment Context**: Current environment ID and URL

## Usage Examples

### Basic Database Statistics

```python
from pathlib import Path
from d365fo_client.metadata_cache import MetadataDatabase

# Initialize database
db_path = Path("metadata_cache/metadata.db")
db = MetadataDatabase(db_path)
await db.initialize()

# Get overall statistics
stats = await db.get_statistics()

print(f"Database size: {stats['database_size_mb']} MB")
print(f"Total environments: {stats['total_environments']}")
print(f"Data entities: {stats['data_entities_count']}")
print(f"Public entities: {stats['public_entities_count']}")
```

### Environment-Specific Statistics

```python
# Get environment ID
env_id = await db.get_or_create_environment("https://mycompany.dynamics.com")

# Get environment-specific statistics
env_stats = await db.get_statistics(env_id)

# Check active version
active_version = env_stats['active_version']
if active_version:
    print(f"Application Version: {active_version['application_version']}")
    print(f"Platform Version: {active_version['platform_version']}")
    print(f"Data Entities: {env_stats['active_version_data_entities']}")
    print(f"Public Entities: {env_stats['active_version_public_entities']}")
```

### Cache-Level Statistics

```python
from d365fo_client.metadata_cache import MetadataCache

# Initialize cache
cache = MetadataCache(
    environment_url="https://mycompany.dynamics.com",
    cache_dir=Path("metadata_cache"),
    config={
        'cache_ttl_seconds': 600,
        'max_memory_cache_size': 2000,
        'enable_fts_search': True
    }
)
await cache.initialize()

# Get cache statistics
cache_stats = await cache.get_statistics()

print(f"Environment URL: {cache.environment_url}")
print(f"Cache TTL: {cache.cache_ttl} seconds")
print(f"Memory cache available: {cache._memory_cache is not None}")
print(f"Total entities: {cache_stats['data_entities_count'] + cache_stats['public_entities_count']}")
```

## Statistics Data Structure

### General Statistics

```python
{
    # Table counts
    'metadata_environments_count': int,
    'metadata_versions_count': int,
    'data_entities_count': int,
    'public_entities_count': int,
    'entity_properties_count': int,
    'navigation_properties_count': int,
    'relation_constraints_count': int,
    'property_groups_count': int,
    'property_group_members_count': int,
    'entity_actions_count': int,
    'action_parameters_count': int,
    'enumerations_count': int,
    'enumeration_members_count': int,
    'labels_cache_count': int,
    'metadata_search_count': int | str,  # int for count, str for error
    
    # Database information
    'database_size_bytes': int | None,
    'database_size_mb': float | None,
    'total_environments': int,
    
    # Environment list
    'environments': [
        {
            'base_url': str,
            'environment_name': str,
            'version_count': int,
            'latest_version': str | None
        }
    ]
}
```

### Environment-Specific Statistics

When calling `get_statistics(environment_id)`, additional fields are included:

```python
{
    # ... all general statistics ...
    
    # Active version information
    'active_version': {
        'version_hash': str,
        'application_version': str,
        'platform_version': str,
        'created_at': str  # ISO format
    } | None,
    
    # Active version entity counts
    'active_version_data_entities': int,
    'active_version_public_entities': int,
    'active_version_enumerations': int,
    'active_version_properties': int,
    'active_version_actions': int
}
```

## Monitoring and Health Checks

### Production Monitoring Function

```python
async def monitor_metadata_cache(cache: MetadataCache) -> Dict[str, Any]:
    """Monitor metadata cache health and performance"""
    
    stats = await cache.get_statistics()
    
    health_metrics = {
        'status': 'healthy',
        'warnings': [],
        'metrics': {}
    }
    
    # Check database size
    db_size_mb = stats.get('database_size_mb', 0)
    health_metrics['metrics']['database_size_mb'] = db_size_mb
    
    if db_size_mb > 1000:  # Over 1GB
        health_metrics['warnings'].append(f"Large database size: {db_size_mb} MB")
    
    # Check if we have data
    total_entities = (stats.get('data_entities_count', 0) + 
                     stats.get('public_entities_count', 0))
    health_metrics['metrics']['total_entities'] = total_entities
    
    if total_entities == 0:
        health_metrics['warnings'].append("No entities found - cache may be empty")
        health_metrics['status'] = 'warning'
    
    # Check search index
    search_count = stats.get('metadata_search_count', 0)
    if isinstance(search_count, str) and 'Error' in search_count:
        health_metrics['warnings'].append(f"Search index error: {search_count}")
        health_metrics['status'] = 'warning'
    
    # Check active version
    active_version = stats.get('active_version')
    if not active_version:
        health_metrics['warnings'].append("No active metadata version")
        health_metrics['status'] = 'warning'
    
    return health_metrics
```

### Key Monitoring Metrics

1. **Database Size Growth**: Monitor `database_size_mb` for storage management
2. **Entity Counts**: Track `data_entities_count` and `public_entities_count` for completeness
3. **Search Index Health**: Check `metadata_search_count` for search functionality
4. **Version Freshness**: Monitor `active_version.created_at` for staleness
5. **Cache Performance**: Use environment-specific counts to validate cache effectiveness

## Performance Considerations

- Statistics queries are optimized with appropriate indexes
- Results can be cached for monitoring dashboards (statistics change infrequently)
- Environment-specific queries are more expensive than general statistics
- FTS search index statistics may be slower on very large databases

## Error Handling

The statistics methods handle errors gracefully:

- **Database Access Errors**: Return `None` for size fields if file cannot be accessed
- **FTS Index Errors**: Return error string instead of count for `metadata_search_count`
- **Missing Active Version**: Return `None` for `active_version` field
- **SQL Errors**: Propagate as `MetadataError` exceptions

## Integration with Logging

Statistics can be integrated with application logging for monitoring:

```python
import logging

logger = logging.getLogger(__name__)

async def log_cache_statistics(cache: MetadataCache):
    """Log cache statistics for monitoring"""
    try:
        stats = await cache.get_statistics()
        
        logger.info(
            "Metadata cache statistics",
            extra={
                'environment_url': cache.environment_url,
                'database_size_mb': stats.get('database_size_mb'),
                'total_entities': stats.get('data_entities_count', 0) + stats.get('public_entities_count', 0),
                'search_index_entries': stats.get('metadata_search_count'),
                'environments_count': stats.get('total_environments')
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
```

## Testing

The statistics functionality includes comprehensive unit tests:

```bash
# Run all statistics tests
uv run pytest tests/test_metadata_statistics.py -v

# Run specific test
uv run pytest tests/test_metadata_statistics.py::TestMetadataStatistics::test_empty_database_statistics -v
```

Test coverage includes:
- Empty database statistics
- Environment-specific statistics  
- File size calculations
- FTS search index status
- Multiple environments
- Performance validation
- Error handling scenarios