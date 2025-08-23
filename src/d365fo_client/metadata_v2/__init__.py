"""
Enhanced metadata caching system v2 with module-based versioning.

This package provides the next-generation metadata caching system that:
- Uses GetInstalledModules for precise version detection
- Shares metadata across environments with identical module versions
- Provides intelligent sync with minimal network overhead
- Offers version-aware search and queries

Usage:
    from d365fo_client.metadata_v2 import MetadataCacheV2, ModuleVersionDetector

    cache = MetadataCacheV2(cache_dir, base_url)
    await cache.initialize()

    # Automatic version detection and smart sync
    sync_needed, version_id = await cache.check_version_and_sync(fo_client)
    if sync_needed:
        sync_manager = SmartSyncManagerV2(cache)
        result = await sync_manager.sync_metadata(fo_client, version_id)

    # Version-aware queries
    entities = await cache.get_data_entities(name_pattern="%customer%")
"""

from .cache_v2 import MetadataCacheV2
from .database_v2 import DatabaseSchemaV2, MetadataDatabaseV2
from .global_version_manager import GlobalVersionManager
from .sync_manager_v2 import SmartSyncManagerV2

# Core components (implemented)
from .version_detector import ModuleVersionDetector

# Search engine (Phase 2 - implemented)
from .search_engine_v2 import VersionAwareSearchEngine

# Future components (not yet implemented)
# from .migration_manager import MetadataMigrationManager  # Phase 4

__all__ = [
    # Implemented components
    "MetadataCacheV2",
    "ModuleVersionDetector",
    "GlobalVersionManager",
    "SmartSyncManagerV2",
    "MetadataDatabaseV2",
    "DatabaseSchemaV2",
    "VersionAwareSearchEngine",
    # Future components
    # 'MetadataMigrationManager',
]

# Version compatibility
__version__ = "2.0.0-alpha"
__compatibility__ = {
    "replaces": "metadata_cache.MetadataCache",
    "migration_required": True,
    "deprecation_timeline": "2025-Q4",
}
