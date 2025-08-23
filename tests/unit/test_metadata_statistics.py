#!/usr/bin/env python3
"""Unit tests for metadata cache statistics functionality."""

import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from d365fo_client.metadata_v2 import MetadataCacheV2, MetadataDatabaseV2
from d365fo_client.models import EnvironmentVersionInfo


class TestMetadataStatistics(unittest.IsolatedAsyncioTestCase):
    """Test cases for metadata statistics functionality"""

    async def asyncSetUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)
        self.db_path = self.cache_dir / "test_metadata_v2.db"

        # Initialize database
        self.db = MetadataDatabaseV2(self.db_path)
        await self.db.initialize()

        # Create test environment
        self.env_id = await self.db.get_or_create_environment(
            "https://test.dynamics.com"
        )

    async def asyncTearDown(self):
        """Clean up test environment"""
        # Add a small delay and retry mechanism for cleanup
        for i in range(3):
            try:
                self.temp_dir.cleanup()
                break
            except PermissionError:
                if i < 2:
                    time.sleep(0.1)  # Wait a bit before retrying
                else:
                    raise

    async def test_empty_database_statistics(self):
        """Test statistics on empty database"""
        stats = await self.db.get_statistics()

        # Check basic structure
        self.assertIsInstance(stats, dict)

        # Check that all table counts are present
        expected_tables = [
            "metadata_environments_count",
            "metadata_versions_count",
            "data_entities_count",
            "public_entities_count",
            "entity_properties_count",
            "navigation_properties_count",
            "relation_constraints_count",
            "property_groups_count",
            "property_group_members_count",
            "entity_actions_count",
            "action_parameters_count",
            "enumerations_count",
            "enumeration_members_count",
            "labels_cache_count",
        ]

        for table in expected_tables:
            self.assertIn(table, stats)
            self.assertIsInstance(stats[table], int)

        # We should have at least one environment (created in setUp)
        self.assertGreaterEqual(stats["metadata_environments_count"], 1)

        # Other tables should be empty
        self.assertEqual(stats["data_entities_count"], 0)
        self.assertEqual(stats["public_entities_count"], 0)

        # Check environments list
        self.assertIn("environments", stats)
        self.assertIn("total_environments", stats)
        self.assertIsInstance(stats["environments"], list)
        self.assertGreaterEqual(stats["total_environments"], 1)

    async def test_environment_specific_statistics(self):
        """Test environment-specific statistics"""
        # Create a test version
        version_info = MetadataVersionInfo(
            environment_id=self.env_id,
            version_hash="test_hash_123",
            application_version="10.0.1000.123",
            platform_version="Update123",
            package_info=[{"name": "TestPackage", "version": "1.0.0"}],
            is_active=True,
        )

        version_id = await self.db.create_version(self.env_id, version_info)

        # Get environment-specific statistics
        stats = await self.db.get_statistics(self.env_id)

        # Check active version information
        self.assertIn("active_version", stats)
        active_version = stats["active_version"]
        self.assertIsNotNone(active_version)
        self.assertEqual(active_version["application_version"], "10.0.1000.123")
        self.assertEqual(active_version["platform_version"], "Update123")
        self.assertEqual(active_version["version_hash"], "test_hash_123")

        # Check version-specific counts (should be 0 for empty database)
        self.assertIn("active_version_data_entities", stats)
        self.assertIn("active_version_public_entities", stats)
        self.assertIn("active_version_enumerations", stats)
        self.assertIn("active_version_properties", stats)
        self.assertIn("active_version_actions", stats)

        # All should be 0 since we haven't added any entities
        self.assertEqual(stats["active_version_data_entities"], 0)
        self.assertEqual(stats["active_version_public_entities"], 0)
        self.assertEqual(stats["active_version_enumerations"], 0)
        self.assertEqual(stats["active_version_properties"], 0)
        self.assertEqual(stats["active_version_actions"], 0)

    async def test_database_file_size_statistics(self):
        """Test database file size is included in statistics"""
        stats = await self.db.get_statistics()

        # Check file size statistics
        self.assertIn("database_size_bytes", stats)
        self.assertIn("database_size_mb", stats)

        # File should exist and have some size
        if stats["database_size_bytes"] is not None:
            self.assertGreater(stats["database_size_bytes"], 0)
            self.assertGreater(stats["database_size_mb"], 0)

    async def test_fts_search_index_statistics(self):
        """Test FTS search index statistics"""
        stats = await self.db.get_statistics()

        # Should include search index count
        self.assertIn("metadata_search_count", stats)

        # For empty database, should be 0 or error message
        search_count = stats["metadata_search_count"]
        if isinstance(search_count, int):
            self.assertEqual(search_count, 0)
        else:
            # Should be an error string
            self.assertIsInstance(search_count, str)
            self.assertIn("Error", search_count)

    async def test_cache_statistics_method(self):
        """Test MetadataCache statistics method"""
        cache = MetadataCache("https://test.dynamics.com", self.cache_dir)
        await cache.initialize()

        stats = await cache.get_statistics()

        # Should return same structure as database statistics
        self.assertIsInstance(stats, dict)
        self.assertIn("metadata_environments_count", stats)
        self.assertIn("total_environments", stats)

        # Should have environment information
        self.assertGreaterEqual(stats["total_environments"], 1)

    async def test_multiple_environments_statistics(self):
        """Test statistics with multiple environments"""
        # Create additional environments
        env_2 = await self.db.get_or_create_environment("https://test2.dynamics.com")
        env_3 = await self.db.get_or_create_environment("https://test3.dynamics.com")

        stats = await self.db.get_statistics()

        # Should have 3 environments total
        self.assertEqual(stats["total_environments"], 3)

        # Environments list should contain all 3
        environments = stats["environments"]
        self.assertEqual(len(environments), 3)

        # Check that URLs are present
        urls = [env["base_url"] for env in environments]
        self.assertIn("https://test.dynamics.com", urls)
        self.assertIn("https://test2.dynamics.com", urls)
        self.assertIn("https://test3.dynamics.com", urls)

    async def test_statistics_performance(self):
        """Test that statistics queries complete in reasonable time"""
        import time

        start_time = time.time()
        stats = await self.db.get_statistics()
        end_time = time.time()

        # Should complete within 1 second for empty database
        query_time = end_time - start_time
        self.assertLess(query_time, 1.0, "Statistics query took too long")

        # Should return valid data
        self.assertIsInstance(stats, dict)
        self.assertGreater(len(stats), 0)


async def run_tests():
    """Run all tests"""
    print("Running Metadata Statistics Tests...")
    print("=" * 50)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMetadataStatistics)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASS' if success else 'FAIL'}")

    return success


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)
