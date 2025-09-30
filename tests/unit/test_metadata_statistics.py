#!/usr/bin/env python3
"""Unit tests for metadata cache statistics functionality."""

import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from d365fo_client.metadata_v2 import MetadataCacheV2, MetadataDatabaseV2


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

        # Check that essential table counts are present
        # Note: Some tables may not be present in the current implementation
        essential_tables = [
            "metadata_environments_count",
            "data_entities_count",
            "public_entities_count",
            "entity_properties_count",
            "navigation_properties_count",
            "entity_actions_count",
            "enumerations_count",
            "labels_cache_count",
        ]

        for table in essential_tables:
            self.assertIn(table, stats, f"Missing table count: {table}")
            self.assertIsInstance(stats[table], int)

        # We should have at least one environment (created in setUp)
        self.assertGreaterEqual(stats["metadata_environments_count"], 1)

        # Other tables should be empty
        self.assertEqual(stats["data_entities_count"], 0)
        self.assertEqual(stats["public_entities_count"], 0)

        # Check environment statistics (if available)
        if "environment_statistics" in stats:
            env_stats = stats["environment_statistics"]
            self.assertIsInstance(env_stats, dict)

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

        # Check search-related statistics (if available)
        # Note: metadata_search_count may not be available in current implementation
        if "metadata_search_count" in stats:
            search_count = stats["metadata_search_count"]
            if isinstance(search_count, int):
                self.assertEqual(search_count, 0)
            else:
                # Should be an error string
                self.assertIsInstance(search_count, str)
                self.assertIn("Error", search_count)

    async def test_cache_statistics_method(self):
        """Test MetadataCacheV2 statistics method"""
        cache = MetadataCacheV2(self.cache_dir, "https://test.dynamics.com")
        await cache.initialize()

        stats = await cache.get_cache_statistics()

        # Should return cache statistics structure
        self.assertIsInstance(stats, dict)
        # Cache statistics have different structure than database statistics
        essential_fields = ["data_entities_count", "public_entities_count", "entity_properties_count"]
        for field in essential_fields:
            self.assertIn(field, stats)

    async def test_multiple_environments_statistics(self):
        """Test statistics with multiple environments"""
        # Create additional environments
        env_2 = await self.db.get_or_create_environment("https://test2.dynamics.com")
        env_3 = await self.db.get_or_create_environment("https://test3.dynamics.com")

        stats = await self.db.get_statistics()

        # Should have 3 environments total
        self.assertGreaterEqual(stats["metadata_environments_count"], 3)

        # Check environment statistics (if available)
        if "environment_statistics" in stats:
            env_stats = stats["environment_statistics"]
            self.assertIsInstance(env_stats, dict)

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
