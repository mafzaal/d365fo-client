#!/usr/bin/env python3
"""Test script to verify entity count fix - using mock data."""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Configure logging to see debug information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sync_entities_count_logic():
    """Test that sync session manager uses the correct method for getting entities."""
    
    logger.info("Testing sync session manager entity fetching logic...")
    
    # Import the sync session manager
    from src.d365fo_client.metadata_v2.sync_session_manager import SyncSessionManager
    from src.d365fo_client.models import DataEntityInfo
    
    # Create mock objects
    mock_cache = MagicMock()
    mock_metadata_api = MagicMock()
    
    # Create test data
    test_entities = [
        DataEntityInfo(
            name="TestEntity1",
            public_entity_name="TestEntity1",
            public_collection_name="TestEntities1",
            label_id="@SYS123",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category=None,
            is_read_only=False
        ),
        DataEntityInfo(
            name="TestEntity2", 
            public_entity_name="TestEntity2",
            public_collection_name="TestEntities2",
            label_id="@SYS124",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category=None,
            is_read_only=False
        ),
        # Add many more to simulate realistic count
        *[DataEntityInfo(
            name=f"TestEntity{i}",
            public_entity_name=f"TestEntity{i}",
            public_collection_name=f"TestEntities{i}",
            label_id=f"@SYS{100+i}",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category=None,
            is_read_only=False
        ) for i in range(3, 1000)]  # Create 997 more entities for total of 999
    ]
    
    # Mock the methods
    mock_metadata_api.search_data_entities = AsyncMock(return_value=test_entities[:1])  # Return only 1 (old behavior)
    mock_metadata_api.get_all_data_entities = AsyncMock(return_value=test_entities)  # Return all 999 (new behavior)
    
    # Create sync session manager
    sync_manager = SyncSessionManager(mock_cache, mock_metadata_api)
    
    # Test the _get_data_entities method
    logger.info("Testing sync session manager _get_data_entities method...")
    entities = await sync_manager._get_data_entities()
    entity_count = len(entities)
    
    logger.info(f"Sync session manager returned: {entity_count} entities")
    
    # Verify which method was called
    if mock_metadata_api.get_all_data_entities.called:
        logger.info("✅ SUCCESS: Sync manager is using get_all_data_entities() method")
        logger.info(f"   This method returned {entity_count} entities")
    elif mock_metadata_api.search_data_entities.called:
        logger.error("❌ FAILURE: Sync manager is still using search_data_entities() method")
        logger.error(f"   This method would only return {len(await mock_metadata_api.search_data_entities())} entity")
    else:
        logger.warning("⚠️  UNEXPECTED: Neither method was called")
    
    # Test results
    if entity_count == 999:
        logger.info("✅ SUCCESS: Entity count matches expected (999)")
    else:
        logger.error(f"❌ FAILURE: Expected 999 entities, got {entity_count}")
    
    # Show sample entity names
    logger.info(f"\nSample entity names (first 5):")
    for i, entity in enumerate(entities[:5]):
        logger.info(f"  {i+1}. {entity.name}")
        
    if len(entities) > 5:
        logger.info(f"  ... and {len(entities) - 5} more entities")

if __name__ == "__main__":
    asyncio.run(test_sync_entities_count_logic())