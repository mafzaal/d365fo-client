#!/usr/bin/env python3
"""
Example: Using Metadata Cache Statistics

This example demonstrates how to use the metadata cache statistics
functionality to monitor and debug metadata storage.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from d365fo_client.metadata_cache import MetadataDatabase, MetadataCache


async def example_statistics_usage():
    """Example of using metadata cache statistics"""
    
    # Example 1: Basic database statistics
    print("Example 1: Basic Database Statistics")
    print("-" * 40)
    
    cache_dir = Path("metadata_cache")
    db_path = cache_dir / "metadata.db"
    
    if db_path.exists():
        db = MetadataDatabase(db_path)
        await db.initialize()
        
        # Get overall statistics
        stats = await db.get_statistics()
        
        # Display key metrics
        print(f"Database size: {stats.get('database_size_mb', 0)} MB")
        print(f"Total environments: {stats.get('total_environments', 0)}")
        print(f"Data entities: {stats.get('data_entities_count', 0)}")
        print(f"Public entities: {stats.get('public_entities_count', 0)}")
        print(f"Search index entries: {stats.get('metadata_search_count', 0)}")
        
        # Show environment summary
        environments = stats.get('environments', [])
        for env in environments:
            print(f"\nEnvironment: {env['environment_name']}")
            print(f"  URL: {env['base_url']}")
            print(f"  Versions: {env['version_count']}")
    else:
        print("No metadata database found. Initialize cache first.")
    
    print("\n")
    
    # Example 2: Cache-level statistics with configuration
    print("Example 2: Cache Statistics and Configuration")
    print("-" * 45)
    
    # Create cache instance
    environment_url = "https://example.dynamics.com"
    cache = MetadataCache(environment_url, Path("example_cache"), config={
        'cache_ttl_seconds': 600,  # 10 minutes
        'max_memory_cache_size': 2000,
        'enable_fts_search': True
    })
    
    await cache.initialize()
    
    # Get statistics
    cache_stats = await cache.get_statistics()
    
    # Display cache information
    print(f"Environment URL: {cache.environment_url}")
    print(f"Environment ID: {cache._environment_id}")
    print(f"Cache TTL: {cache.cache_ttl} seconds")
    print(f"Memory cache size limit: {cache.max_memory_size}")
    print(f"FTS search enabled: {cache.enable_fts}")
    
    # Display data counts
    print(f"\nData Summary:")
    print(f"  Data entities: {cache_stats.get('data_entities_count', 0)}")
    print(f"  Public entities: {cache_stats.get('public_entities_count', 0)}")
    print(f"  Entity properties: {cache_stats.get('entity_properties_count', 0)}")
    print(f"  Entity actions: {cache_stats.get('entity_actions_count', 0)}")
    print(f"  Enumerations: {cache_stats.get('enumerations_count', 0)}")
    print(f"  Navigation properties: {cache_stats.get('navigation_properties_count', 0)}")
    print(f"  Labels cached: {cache_stats.get('labels_cache_count', 0)}")
    
    print("\n")


async def example_monitoring_function():
    """Example monitoring function for production use"""
    print("Example 3: Production Monitoring Function")
    print("-" * 42)
    
    async def monitor_metadata_cache(cache: MetadataCache) -> Dict[str, Any]:
        """Monitor metadata cache health and performance"""
        
        stats = await cache.get_statistics()
        
        # Calculate health metrics
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
        health_metrics['metrics']['search_index_entries'] = search_count
        
        if isinstance(search_count, str) and 'Error' in search_count:
            health_metrics['warnings'].append(f"Search index error: {search_count}")
            health_metrics['status'] = 'warning'
        
        # Check active version
        active_version = stats.get('active_version')
        if active_version:
            health_metrics['metrics']['active_version'] = {
                'application': active_version.get('application_version'),
                'platform': active_version.get('platform_version'),
                'age_hours': None  # Could calculate from created_at
            }
        else:
            health_metrics['warnings'].append("No active metadata version")
            health_metrics['status'] = 'warning'
        
        return health_metrics
    
    # Example usage
    cache = MetadataCache("https://example.dynamics.com", Path("example_cache"))
    await cache.initialize()
    
    health_report = await monitor_metadata_cache(cache)
    
    print("Health Report:")
    print(f"Status: {health_report['status']}")
    print(f"Warnings: {len(health_report['warnings'])}")
    
    for warning in health_report['warnings']:
        print(f"  - {warning}")
    
    print(f"\nKey Metrics:")
    metrics = health_report['metrics']
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")


async def main():
    """Main example function"""
    print("Metadata Cache Statistics Examples")
    print("=" * 50)
    
    try:
        await example_statistics_usage()
        await example_monitoring_function()
        
        print("\nExample completed successfully!")
        print("\nKey Benefits of Statistics:")
        print("- Monitor cache health and performance")
        print("- Debug metadata synchronization issues")
        print("- Track database growth and optimization needs")
        print("- Validate FTS search index integrity")
        print("- Environment and version management")
        
    except Exception as e:
        print(f"Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())