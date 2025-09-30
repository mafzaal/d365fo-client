"""Tests for V2 metadata caching system."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from d365fo_client.metadata_v2 import MetadataCacheV2, VersionAwareSearchEngine
from d365fo_client.models import (
    DataEntityInfo,
    NavigationPropertyInfo,
    PublicEntityInfo,
    PublicEntityPropertyInfo,
    SearchQuery,
)


@pytest.fixture
async def temp_cache_dir():
    """Create temporary cache directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
async def metadata_cache(temp_cache_dir):
    """Create metadata cache instance"""
    cache = MetadataCacheV2(
        cache_dir=temp_cache_dir,
        base_url="https://test.dynamics.com"
    )
    await cache.initialize()
    return cache


@pytest.mark.asyncio
async def test_metadata_cache_initialization(metadata_cache):
    """Test metadata cache initialization"""
    assert metadata_cache is not None
    assert metadata_cache.base_url == "https://test.dynamics.com"
    assert metadata_cache._environment_id is not None


@pytest.mark.asyncio
async def test_database_schema_creation(metadata_cache):
    """Test database schema is created correctly"""
    db_path = metadata_cache.database.db_path
    assert db_path.exists()

    # Check if tables were created
    import aiosqlite

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]

        expected_tables = [
            "metadata_environments",
            "global_versions",
            "environment_versions",
            "global_version_modules",
            "metadata_versions",
            "data_entities",
            "public_entities",
            "entity_properties",
            "navigation_properties",
            "relation_constraints",
            "property_groups",
            "entity_actions",
            "action_parameters",
            "enumerations",
            "enumeration_members",
            "labels_cache",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"


@pytest.mark.asyncio
async def test_entity_caching(metadata_cache):
    """Test entity caching functionality"""
    # Create test entity
    test_entity = PublicEntityInfo(
        name="TestEntity",
        entity_set_name="TestEntities",
        label_id="@TEST123",
        is_read_only=False,
        configuration_enabled=True,
    )

    # Add test property
    test_property = PublicEntityPropertyInfo(
        name="TestProperty",
        type_name="String",
        data_type="String",
        label_id="@PROP123",
        is_key=True,
        is_mandatory=True,
    )
    test_entity.properties.append(test_property)

    # Store entity in database (would normally be done by sync manager)
    import aiosqlite

    async with aiosqlite.connect(metadata_cache.database.db_path) as db:
        # Create test global version first
        global_version_cursor = await db.execute(
            """INSERT INTO global_versions (version_hash, modules_hash) VALUES (?, ?)""",
            ("test_hash", "test_modules_hash"),
        )
        global_version_id = global_version_cursor.lastrowid

        # Create test metadata version
        version_cursor = await db.execute(
            """INSERT INTO metadata_versions
               (global_version_id, sync_completed_at)
               VALUES (?, ?)""",
            (global_version_id, "2024-01-01T00:00:00Z"),
        )
        await db.commit()
        version_id = version_cursor.lastrowid

        # Insert test entity
        entity_cursor = await db.execute(
            """INSERT INTO public_entities
               (global_version_id, name, entity_set_name, label_id, is_read_only, configuration_enabled)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                global_version_id,
                test_entity.name,
                test_entity.entity_set_name,
                test_entity.label_id,
                test_entity.is_read_only,
                test_entity.configuration_enabled,
            ),
        )
        entity_id = entity_cursor.lastrowid

        # Insert test property
        await db.execute(
            """INSERT INTO entity_properties
               (global_version_id, entity_id, name, type_name, data_type, label_id, is_key, is_mandatory)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                global_version_id,
                entity_id,
                test_property.name,
                test_property.type_name,
                test_property.data_type,
                test_property.label_id,
                test_property.is_key,
                test_property.is_mandatory,
            ),
        )
        await db.commit()

    # Verify data was inserted correctly by checking database directly
    async with aiosqlite.connect(metadata_cache.database.db_path) as db:
        # Check entity was inserted
        cursor = await db.execute(
            "SELECT name, entity_set_name FROM public_entities WHERE name = ?",
            ("TestEntity",)
        )
        entity_row = await cursor.fetchone()
        assert entity_row is not None
        assert entity_row[0] == "TestEntity"
        assert entity_row[1] == "TestEntities"

        # Check property was inserted
        cursor = await db.execute(
            "SELECT name, is_key FROM entity_properties WHERE name = ?",
            ("TestProperty",)
        )
        property_row = await cursor.fetchone()
        assert property_row is not None
        assert property_row[0] == "TestProperty"
        assert property_row[1] == 1  # SQLite stores boolean as 1/0


@pytest.mark.asyncio
async def test_search_engine(metadata_cache):
    """Test search engine functionality"""
    search_engine = VersionAwareSearchEngine(metadata_cache)

    # Test simple search (should work even with empty database)
    query = SearchQuery(
        text="test",
        limit=10,
        use_fulltext=False,  # Use pattern search for empty database
    )

    results = await search_engine.search(query)

    assert results is not None
    assert isinstance(results.results, list)
    assert results.total_count >= 0
    assert results.query_time_ms >= 0


@pytest.mark.asyncio
async def test_cache_key_generation(metadata_cache):
    """Test cache key generation through environment IDs"""
    # Test that different environments get different IDs
    assert metadata_cache._environment_id is not None

    # Create another cache for different environment
    cache2 = MetadataCacheV2(
        cache_dir=metadata_cache.cache_dir,
        base_url="https://different.dynamics.com"
    )
    await cache2.initialize()

    # Should have different environment IDs
    assert metadata_cache._environment_id != cache2._environment_id


@pytest.mark.asyncio
async def test_environment_management(temp_cache_dir):
    """Test environment management"""
    cache1 = MetadataCacheV2(temp_cache_dir, "https://env1.dynamics.com")
    await cache1.initialize()

    cache2 = MetadataCacheV2(temp_cache_dir, "https://env2.dynamics.com")
    await cache2.initialize()

    # Should have different environment IDs
    assert cache1._environment_id != cache2._environment_id

    # But should share the same database file
    assert cache1.database.db_path == cache2.database.db_path


def test_model_serialization():
    """Test model to_dict() methods"""
    entity = PublicEntityInfo(name="TestEntity", entity_set_name="TestEntities")

    entity_dict = entity.to_dict()

    assert isinstance(entity_dict, dict)
    assert entity_dict["name"] == "TestEntity"
    assert entity_dict["entity_set_name"] == "TestEntities"
    assert "properties" in entity_dict
    assert "navigation_properties" in entity_dict
    assert "actions" in entity_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
