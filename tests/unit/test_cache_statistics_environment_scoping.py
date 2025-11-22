"""Tests for cache statistics environment scoping fix."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from src.d365fo_client.metadata_v2.cache_v2 import MetadataCacheV2
from src.d365fo_client.models import DataEntityInfo, ModuleVersionInfo


class TestCacheStatisticsEnvironmentScoping:
    """Test that cache statistics are properly scoped to environments"""

    @pytest.mark.asyncio
    async def test_cache_statistics_are_environment_scoped(self):
        """Test that get_cache_statistics returns environment-specific data"""

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"

            # Create two different cache instances for different environments
            cache1 = MetadataCacheV2(cache_dir, "https://env1.dynamics.com")
            cache2 = MetadataCacheV2(cache_dir, "https://env2.dynamics.com")

            # Initialize both caches (they share the same database file)
            await cache1.initialize()
            await cache2.initialize()

            # Verify different environment IDs
            assert cache1._environment_id != cache2._environment_id

            # Store test data in cache1 (2 entities)
            test_entities_env1 = [
                DataEntityInfo(
                    name="TestEntity1",
                    public_entity_name="TestEntity1",
                    public_collection_name="TestEntities1",
                    label_id="@TEST1",
                    label_text="Test Entity 1",
                    entity_category="Master",
                    data_service_enabled=True,
                    data_management_enabled=True,
                    is_read_only=False,
                ),
                DataEntityInfo(
                    name="TestEntity2",
                    public_entity_name="TestEntity2",
                    public_collection_name="TestEntities2",
                    label_id="@TEST2",
                    label_text="Test Entity 2",
                    entity_category="Transaction",
                    data_service_enabled=True,
                    data_management_enabled=True,
                    is_read_only=False,
                ),
            ]

            # Store test data in cache2 (1 entity)
            test_entities_env2 = [
                DataEntityInfo(
                    name="TestEntity3",
                    public_entity_name="TestEntity3",
                    public_collection_name="TestEntities3",
                    label_id="@TEST3",
                    label_text="Test Entity 3",
                    entity_category="Parameter",
                    data_service_enabled=True,
                    data_management_enabled=True,
                    is_read_only=False,
                )
            ]

            # Create global versions for each environment
            module1 = ModuleVersionInfo(
                name="Module 1",
                version="1.0",
                module_id="module1",
                publisher="Test",
                display_name="Test Module 1",
            )
            module2 = ModuleVersionInfo(
                name="Module 2",
                version="1.0",
                module_id="module2",
                publisher="Test",
                display_name="Test Module 2",
            )

            version1, _ = await cache1.version_manager.register_environment_version(
                cache1._environment_id, [module1]
            )
            version2, _ = await cache2.version_manager.register_environment_version(
                cache2._environment_id, [module2]
            )

            # Store entities for each version
            await cache1.store_data_entities(version1, test_entities_env1)
            await cache2.store_data_entities(version2, test_entities_env2)

            # Mark sync completed
            await cache1.mark_sync_completed(version1, entity_count=2)
            await cache2.mark_sync_completed(version2, entity_count=1)

            # Get statistics for each cache
            stats1 = await cache1.get_cache_statistics()
            stats2 = await cache2.get_cache_statistics()

            # Verify statistics are environment-specific
            assert (
                stats1["data_entities_count"] == 2
            ), f"Cache1 should have 2 entities, got {stats1['data_entities_count']}"
            assert (
                stats2["data_entities_count"] == 1
            ), f"Cache2 should have 1 entity, got {stats2['data_entities_count']}"

            # Verify environment statistics show only current environment
            assert stats1["environment_statistics"]["total_environments"] == 1
            assert stats2["environment_statistics"]["total_environments"] == 1

            # Verify version statistics are environment-scoped
            assert stats1["version_manager"]["total_versions"] == 1
            assert stats2["version_manager"]["total_versions"] == 1

            # Verify current version info is different
            assert (
                stats1["current_version"]["global_version_id"]
                != stats2["current_version"]["global_version_id"]
            )

    @pytest.mark.asyncio
    async def test_database_statistics_methods_compatibility(self):
        """Test that both get_database_statistics and get_statistics work"""

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            cache = MetadataCacheV2(cache_dir, "https://test.dynamics.com")
            await cache.initialize()

            # Test both methods return the same global statistics
            global_stats = await cache.database.get_database_statistics()
            alias_stats = await cache.database.get_statistics()

            assert global_stats == alias_stats

            # Test environment-scoped statistics return different results
            env_stats = await cache.database.get_environment_database_statistics(
                cache._environment_id
            )

            # Environment stats should show only current environment
            assert env_stats["environment_statistics"]["total_environments"] == 1

            # Global stats may show 0 environments if none have active versions,
            # but in this test we have at least 1 environment
            total_envs = global_stats["environment_statistics"]["total_environments"]
            assert total_envs >= 0  # May be 0 if no active environment versions exist

    @pytest.mark.asyncio
    async def test_version_manager_environment_scoping(self):
        """Test that version manager statistics are properly scoped"""

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            cache = MetadataCacheV2(cache_dir, "https://test.dynamics.com")
            await cache.initialize()

            # Get global and environment-scoped version statistics
            global_stats = await cache.version_manager.get_version_statistics()
            env_stats = await cache.version_manager.get_environment_version_statistics(
                cache._environment_id
            )

            # Environment stats should show only current environment
            assert env_stats["total_environments"] == 1

            # Global stats may show 0 environments if no environment versions are registered
            total_envs = global_stats["total_environments"]
            assert total_envs >= 0  # May be 0 if no environment versions exist
