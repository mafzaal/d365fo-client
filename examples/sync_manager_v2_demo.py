"""
Demo script showing how to use SmartSyncManagerV2 for metadata synchronization.

This script demonstrates the new v2 sync manager that is independent of FOClient
and can download and store all metadata types locally.
"""

import asyncio
import logging
import os
from pathlib import Path

from d365fo_client.client import FOClient
from d365fo_client.models import FOClientConfig, SyncStrategy
from d365fo_client.metadata_v2.cache_v2 import MetadataCacheV2
from d365fo_client.metadata_v2.sync_manager_v2 import SmartSyncManagerV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_sync_manager_v2():
    """Demonstrate SmartSyncManagerV2 functionality"""
    
    # Base URL configuration
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    
    # Configuration with default credentials (preferred approach)
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        use_label_cache=True,
        enable_metadata_cache=True
    )

    fo_client = FOClient(config)
    
    # Initialize cache and sync manager
    cache_dir = Path("./example_cache_v2")
    cache = MetadataCacheV2(cache_dir, base_url, fo_client.metadata_api_ops)
    await cache.initialize()

    sync_manager = SmartSyncManagerV2(cache, fo_client.metadata_api_ops)

    # Add progress callback to track sync progress
    def progress_callback(progress):
        logger.info(f"Sync Progress: {progress.phase} - {progress.current_operation} "
                   f"({progress.completed_steps}/{progress.total_steps})")
    
    sync_manager.add_progress_callback(progress_callback)
    
    try:
        # Check current version and determine if sync is needed
        logger.info("Checking environment version...")
        sync_needed, global_version_id = await cache.check_version_and_sync()
        
        if global_version_id is None:
            logger.error("Failed to detect environment version")
            return
        
        logger.info(f"Global version ID: {global_version_id}, Sync needed: {sync_needed}")
        
        if sync_needed:
            # Recommend sync strategy
            strategy = await sync_manager.recommend_sync_strategy(global_version_id)
            logger.info(f"Recommended sync strategy: {strategy}")
            
            # Perform synchronization
            logger.info("Starting metadata synchronization...")
            result = await sync_manager.sync_metadata(global_version_id, strategy)
            
            if result.success:
                logger.info(f"Sync completed successfully!")
                logger.info(f"  - Entities: {result.entity_count}")
                logger.info(f"  - Actions: {result.action_count}")
                logger.info(f"  - Enumerations: {result.enumeration_count}")
                logger.info(f"  - Duration: {result.duration_ms}ms")
            else:
                logger.error(f"Sync failed: {result.error}")
        else:
            logger.info("Metadata is up to date, no sync needed")
        
        # Demonstrate cache usage
        logger.info("\nRetrieving cached data entities...")
        entities = await cache.get_data_entities(
            global_version_id=global_version_id,
            data_service_enabled=True
        )
        logger.info(f"Found {len(entities)} OData-enabled entities")
        
        # Show some example entities
        for i, entity in enumerate(entities[:5]):
            logger.info(f"  {i+1}. {entity.name} -> {entity.public_entity_name} ({entity.entity_category})")
        
        # Test enumeration retrieval
        logger.info("\nTesting enumeration retrieval...")
        enum_info = await cache.get_enumeration_info("NoYes", global_version_id)
        if enum_info:
            logger.info(f"Enumeration '{enum_info.name}' has {len(enum_info.members)} members")
            for member in enum_info.members[:3]:  # Show first 3 members
                logger.info(f"  - {member.name} = {member.value}")
        
        # Show cache statistics
        logger.info("\nCache statistics:")
        stats = await cache.get_cache_statistics()
        for key, value in stats.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for subkey, subvalue in value.items():
                    logger.info(f"    {subkey}: {subvalue}")
            else:
                logger.info(f"  {key}: {value}")

        await fo_client.close()

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_entities_only_sync():
    """Demonstrate fast entities-only sync strategy"""
    
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True
    )
    
    fo_client = FOClient(config)
    
    cache_dir = Path("./example_cache_v2_fast")
    cache = MetadataCacheV2(cache_dir, base_url, fo_client.metadata_api_ops)
    await cache.initialize()
    
    sync_manager = SmartSyncManagerV2(cache, fo_client.metadata_api_ops)
    
    logger.info("Performing entities-only sync (fast mode)...")
    
    try:
        # Check version
        sync_needed, global_version_id = await cache.check_version_and_sync()
        
        if global_version_id and sync_needed:
            # Force entities-only strategy
            result = await sync_manager.sync_metadata(global_version_id, SyncStrategy.ENTITIES_ONLY)
            
            logger.info(f"Fast sync completed: {result.entity_count} entities in {result.duration_ms}ms")
        
    except Exception as e:
        logger.error(f"Fast sync demo failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fast":
        asyncio.run(demo_entities_only_sync())
    else:
        asyncio.run(demo_sync_manager_v2())