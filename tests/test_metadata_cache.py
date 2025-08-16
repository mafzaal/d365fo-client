"""Tests for advanced metadata caching system."""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from d365fo_client.metadata_cache import MetadataCache, MetadataSearchEngine
from d365fo_client.models import (
    DataEntityInfo, PublicEntityInfo, SearchQuery, 
    PublicEntityPropertyInfo, NavigationPropertyInfo
)


@pytest.fixture
async def temp_cache_dir():
    """Create temporary cache directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
async def metadata_cache(temp_cache_dir):
    """Create metadata cache instance"""
    cache = MetadataCache(
        environment_url="https://test.dynamics.com",
        cache_dir=temp_cache_dir,
        config={
            'cache_ttl_seconds': 60,
            'max_memory_cache_size': 100,
            'enable_fts_search': True
        }
    )
    await cache.initialize()
    return cache


@pytest.mark.asyncio
async def test_metadata_cache_initialization(metadata_cache):
    """Test metadata cache initialization"""
    assert metadata_cache is not None
    assert metadata_cache.environment_url == "https://test.dynamics.com"
    assert metadata_cache._environment_id is not None


@pytest.mark.asyncio  
async def test_database_schema_creation(metadata_cache):
    """Test database schema is created correctly"""
    db_path = metadata_cache._database.db_path
    assert db_path.exists()
    
    # Check if tables were created
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        
        expected_tables = [
            'metadata_environments',
            'metadata_versions', 
            'data_entities',
            'public_entities',
            'entity_properties',
            'navigation_properties',
            'relation_constraints',
            'property_groups',
            'entity_actions',
            'action_parameters',
            'enumerations',
            'enumeration_members',
            'labels_cache',
            'metadata_search'
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
        configuration_enabled=True
    )
    
    # Add test property
    test_property = PublicEntityPropertyInfo(
        name="TestProperty",
        type_name="String",
        data_type="String",
        label_id="@PROP123",
        is_key=True,
        is_mandatory=True
    )
    test_entity.properties.append(test_property)
    
    # Store entity in database (would normally be done by sync manager)
    import aiosqlite
    async with aiosqlite.connect(metadata_cache._database.db_path) as db:
        # Get active version
        version_cursor = await db.execute(
            "SELECT id FROM metadata_versions WHERE environment_id = ? AND is_active = 1",
            (metadata_cache._environment_id,)
        )
        version_row = await version_cursor.fetchone()
        
        if not version_row:
            # Create test version
            version_cursor = await db.execute(
                """INSERT INTO metadata_versions 
                   (environment_id, version_hash, application_version, is_active)
                   VALUES (?, ?, ?, ?)""",
                (metadata_cache._environment_id, "test_hash", "10.0.test", 1)
            )
            await db.commit()
            version_id = version_cursor.lastrowid
        else:
            version_id = version_row[0]
        
        # Insert test entity
        entity_cursor = await db.execute(
            """INSERT INTO public_entities 
               (version_id, name, entity_set_name, label_id, is_read_only, configuration_enabled)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (version_id, test_entity.name, test_entity.entity_set_name,
             test_entity.label_id, test_entity.is_read_only, 
             test_entity.configuration_enabled)
        )
        entity_id = entity_cursor.lastrowid
        
        # Insert test property
        await db.execute(
            """INSERT INTO entity_properties 
               (entity_id, name, type_name, data_type, label_id, is_key, is_mandatory)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entity_id, test_property.name, test_property.type_name,
             test_property.data_type, test_property.label_id,
             test_property.is_key, test_property.is_mandatory)
        )
        await db.commit()
    
    # Test entity retrieval
    retrieved_entity = await metadata_cache.get_entity("TestEntity", "public")
    
    assert retrieved_entity is not None
    assert retrieved_entity.name == "TestEntity"
    assert retrieved_entity.entity_set_name == "TestEntities"
    assert len(retrieved_entity.properties) == 1
    assert retrieved_entity.properties[0].name == "TestProperty"
    assert retrieved_entity.properties[0].is_key is True


@pytest.mark.asyncio
async def test_search_engine(metadata_cache):
    """Test search engine functionality"""
    search_engine = MetadataSearchEngine(metadata_cache)
    
    # Test simple search (should work even with empty database)
    query = SearchQuery(
        text="test",
        limit=10,
        use_fulltext=False  # Use pattern search for empty database
    )
    
    results = await search_engine.search(query)
    
    assert results is not None
    assert isinstance(results.results, list)
    assert results.total_count >= 0
    assert results.query_time_ms >= 0


@pytest.mark.asyncio
async def test_cache_key_generation(metadata_cache):
    """Test cache key generation"""
    key1 = metadata_cache._build_cache_key("entity", "TestEntity", type="public")
    key2 = metadata_cache._build_cache_key("entity", "TestEntity", type="public")
    key3 = metadata_cache._build_cache_key("entity", "TestEntity", type="data")
    
    assert key1 == key2  # Same parameters should generate same key
    assert key1 != key3  # Different parameters should generate different key


@pytest.mark.asyncio
async def test_environment_management(temp_cache_dir):
    """Test environment management"""
    cache1 = MetadataCache("https://env1.dynamics.com", temp_cache_dir)
    await cache1.initialize()
    
    cache2 = MetadataCache("https://env2.dynamics.com", temp_cache_dir)
    await cache2.initialize()
    
    # Should have different environment IDs
    assert cache1._environment_id != cache2._environment_id
    
    # But should share the same database file
    assert cache1._database.db_path == cache2._database.db_path


def test_model_serialization():
    """Test model to_dict() methods"""
    entity = PublicEntityInfo(
        name="TestEntity",
        entity_set_name="TestEntities"
    )
    
    entity_dict = entity.to_dict()
    
    assert isinstance(entity_dict, dict)
    assert entity_dict['name'] == "TestEntity"
    assert entity_dict['entity_set_name'] == "TestEntities"
    assert 'properties' in entity_dict
    assert 'navigation_properties' in entity_dict
    assert 'actions' in entity_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])