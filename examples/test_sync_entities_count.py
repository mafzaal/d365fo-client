#!/usr/bin/env python3
"""Test script to verify entity count fix in sync session manager."""

import asyncio
import logging
import os

from d365fo_client.sync_models import SyncSession
from src.d365fo_client.client import FOClient
from src.d365fo_client.models import FOClientConfig

# Configure logging to see debug information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_sync_entities_count():
    """Test that sync session manager gets all entities, not just a few."""

    # Create a basic config - use environment variables if available
    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        verify_ssl=False,  # For testing
        timeout=60,
        metadata_cache_dir="./example_cache",
    )

    client = FOClient(config)

    try:
        # Initialize the client and metadata
        await client.initialize_metadata()

        logger.info("Testing entity count comparison...")

        # Test 1: Get entities via direct metadata API search (old way)
        logger.info("1. Getting entities via search_data_entities() (old way)...")
        search_entities = await client.metadata_api_ops.search_data_entities()
        search_count = len(search_entities)
        logger.info(f"   Search method returned: {search_count} entities")

        # Test 2: Get entities via new get_all_data_entities method
        logger.info("2. Getting entities via get_all_data_entities() (new way)...")
        all_entities = await client.metadata_api_ops.get_all_data_entities()
        all_count = len(all_entities)
        logger.info(f"   Get all method returned: {all_count} entities")

        # Test 3: Get entities via sync session manager method
        logger.info("3. Getting entities via sync session manager...")
        sync_entities = await client.sync_session_manager._get_data_entities()
        sync_count = len(sync_entities)
        logger.info(f"   Sync session manager returned: {sync_count} entities")

        # Compare results
        logger.info("\n--- Results Comparison ---")
        logger.info(f"Search method (old):       {search_count} entities")
        logger.info(f"Get all method (new):      {all_count} entities")
        logger.info(f"Sync manager (fixed):      {sync_count} entities")

        if sync_count == all_count and all_count >= search_count:
            logger.info("✅ SUCCESS: Sync manager now returns all entities!")
        elif sync_count == search_count:
            logger.error("❌ FAILURE: Sync manager still using limited search method")
        else:
            logger.warning(f"⚠️  UNEXPECTED: Different counts - investigating needed")

        # Show a sample of entity names
        logger.info(f"\nSample entity names from sync manager (first 10):")
        for i, entity in enumerate(sync_entities[:10]):
            logger.info(f"  {i+1}. {entity.name}")

        if len(sync_entities) > 10:
            logger.info(f"  ... and {len(sync_entities) - 10} more entities")

            sync_needed, detected_version_id = (
                await client.metadata_cache.check_version_and_sync()
            )
            if sync_needed:
                logger.info(
                    f"Metadata out of date, detected {detected_version_id}). Starting sync..."
                )
            # Start a sync session and monitor its progress
            session_id = await client.sync_session_manager.start_sync_session(
                detected_version_id
            )
            sync_session = client.sync_session_manager.get_sync_session(session_id)

            while True:
                logger.info(f"Sync session progress: {sync_session.progress_percent}%")
                await asyncio.sleep(5)
                sync_session = client.sync_session_manager.get_sync_session(session_id)
                if sync_session is None or sync_session.status in [
                    "completed",
                    "failed",
                    "canceled",
                ]:
                    break

            logger.info("Sync session completed successfully.")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_sync_entities_count())
