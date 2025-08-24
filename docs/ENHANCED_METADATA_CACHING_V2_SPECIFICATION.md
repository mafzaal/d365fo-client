# Enhanced Metadata Caching System Implementation Specification

## Overview

This specification defines a comprehensive enhancement to the d365fo-client metadata caching system that implements module-based version detection, cross-environment metadata sharing, and intelligent cache management. The new system will be organized in a dedicated package and will deprecate the current implementation over time.

## Goals

1. **Precise Version Detection**: Use `GetInstalledModules` OData action for accurate environment versioning
2. **Cross-Environment Sharing**: Share metadata between environments with identical module versions
3. **Intelligent Caching**: Metadata never expires until module versions change
4. **Performance Optimization**: Fast version-based lookups and minimal storage overhead
5. **Scalable Architecture**: Support unlimited environments with efficient resource usage

## Module Version Data Structure

Based on the `GetInstalledModules` response format, each module entry follows this pattern:
```
"Name: {ModuleName} | Version: {Version} | Module: {ModuleId} | Publisher: {Publisher} | DisplayName: {DisplayName}"
```

### Enhanced Data Models

#### File: `src/d365fo_client/models.py`

```python
@dataclass
class ModuleVersionInfo:
    """Information about installed D365 module based on GetInstalledModules response"""
    name: str                    # Module name (e.g., "AccountsPayableMobile")
    version: str                 # Version string (e.g., "10.34.2105.34092")
    module_id: str              # Module identifier (e.g., "AccountsPayableMobile")
    publisher: str              # Publisher (e.g., "Microsoft Corporation")
    display_name: str           # Human-readable name (e.g., "Accounts Payable Mobile")
    
    @classmethod
    def parse_from_string(cls, module_string: str) -> 'ModuleVersionInfo':
        """Parse module info from GetInstalledModules string format
        
        Args:
            module_string: String in format "Name: X | Version: Y | Module: Z | Publisher: W | DisplayName: V"
            
        Returns:
            ModuleVersionInfo instance
            
        Raises:
            ValueError: If string format is invalid
        """
        try:
            parts = module_string.split(' | ')
            if len(parts) != 5:
                raise ValueError(f"Invalid module string format: {module_string}")
            
            name = parts[0].replace('Name: ', '')
            version = parts[1].replace('Version: ', '')
            module_id = parts[2].replace('Module: ', '')
            publisher = parts[3].replace('Publisher: ', '')
            display_name = parts[4].replace('DisplayName: ', '')
            
            return cls(
                name=name,
                version=version,
                module_id=module_id,
                publisher=publisher,
                display_name=display_name
            )
        except Exception as e:
            raise ValueError(f"Failed to parse module string '{module_string}': {e}")
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'version': self.version,
            'module_id': self.module_id,
            'publisher': self.publisher,
            'display_name': self.display_name
        }

@dataclass
class EnvironmentVersionInfo:
    """Enhanced environment version with precise module tracking"""
    environment_id: int
    version_hash: str                        # Fast hash based on all module versions
    modules_hash: str                        # Hash of sorted module list for deduplication
    application_version: Optional[str] = None  # Fallback version info
    platform_version: Optional[str] = None    # Fallback version info
    modules: List[ModuleVersionInfo] = field(default_factory=list)
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    def __post_init__(self):
        """Ensure version hashes are computed if not provided"""
        if not self.modules_hash and self.modules:
            self.modules_hash = self._compute_modules_hash()
        if not self.version_hash:
            self.version_hash = self.modules_hash[:16]  # Use first 16 chars for compatibility
    
    def _compute_modules_hash(self) -> str:
        """Compute hash based on sorted module versions for consistent deduplication"""
        if not self.modules:
            return hashlib.sha256("empty".encode()).hexdigest()
        
        # Sort modules by module_id for consistent hashing
        sorted_modules = sorted(self.modules, key=lambda m: m.module_id)
        
        # Create hash input from essential version data
        hash_data = []
        for module in sorted_modules:
            hash_data.append(f"{module.module_id}:{module.version}")
        
        hash_input = "|".join(hash_data)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'environment_id': self.environment_id,
            'version_hash': self.version_hash,
            'modules_hash': self.modules_hash,
            'application_version': self.application_version,
            'platform_version': self.platform_version,
            'modules': [module.to_dict() for module in self.modules],
            'computed_at': self.computed_at.isoformat(),
            'is_active': self.is_active
        }

@dataclass
class GlobalVersionInfo:
    """Global version registry for cross-environment sharing"""
    id: int
    version_hash: str
    modules_hash: str
    first_seen_at: datetime
    last_used_at: datetime
    reference_count: int
    sample_modules: List[ModuleVersionInfo] = field(default_factory=list)  # Sample for debugging

@dataclass
class CacheStatistics:
    """Enhanced cache statistics with version sharing metrics"""
    total_environments: int
    unique_versions: int
    shared_versions: int
    cache_hit_ratio: float
    storage_efficiency: float  # Ratio of shared vs duplicate storage
    last_sync_times: Dict[str, datetime]
    version_distribution: Dict[str, int]  # version_hash -> environment_count
```

## New Package Structure

### Directory: `src/d365fo_client/metadata_v2/`

Organize the new implementation in a dedicated package to allow gradual migration:

```
src/d365fo_client/metadata_v2/
├── __init__.py                    # Public API exports
├── version_detector.py            # Module version detection
├── global_manager.py              # Cross-environment version management
├── database_v2.py                 # Enhanced database schema and operations
├── cache_v2.py                    # New cache implementation
├── sync_manager_v2.py             # Intelligent sync manager
├── search_engine_v2.py            # Version-aware search
├── migration.py                   # Migration utilities from v1 to v2
└── utils.py                       # Utility functions
```

### File: `src/d365fo_client/metadata_v2/__init__.py`

```python
"""
Enhanced metadata caching system v2 with module-based versioning.

This package provides the next-generation metadata caching system that:
- Uses GetInstalledModules for precise version detection
- Shares metadata across environments with identical module versions
- Provides intelligent sync with minimal network overhead
- Offers version-aware search and queries

Usage:
    from d365fo_client.metadata_v2 import MetadataCacheV2, VersionDetector
    
    cache = MetadataCacheV2(environment_url, cache_dir)
    await cache.initialize()
    
    # Automatic version detection and smart sync
    sync_result = await cache.sync_if_needed()
    
    # Version-aware queries
    entities = await cache.search_entities("customer")
"""

from .version_detector import ModuleVersionDetector, VersionDetectionError
from .global_manager import GlobalVersionManager, VersionSharingManager
from .database_v2 import MetadataDatabaseV2, DatabaseSchemaV2
from .cache_v2 import MetadataCacheV2, CacheConfigV2
from .sync_manager_v2 import SmartSyncManagerV2, SyncStrategyV2
from .search_engine_v2 import VersionAwareSearchEngine
from .migration import MetadataMigrationManager
from .utils import CacheUtils, VersionUtils

__all__ = [
    'MetadataCacheV2',
    'ModuleVersionDetector', 
    'GlobalVersionManager',
    'SmartSyncManagerV2',
    'VersionAwareSearchEngine',
    'MetadataMigrationManager',
    'CacheConfigV2',
    'VersionDetectionError'
]

# Version compatibility
__version__ = "2.0.0"
__compatibility__ = {
    'replaces': 'metadata_cache.MetadataCache',
    'migration_required': True,
    'deprecation_timeline': '2025-Q4'
}
```

## Core Implementation Components

### 1. Module Version Detection

#### File: `src/d365fo_client/metadata_v2/version_detector.py`

```python
"""Module-based version detection using GetInstalledModules action."""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..models import ModuleVersionInfo, EnvironmentVersionInfo
from ..exceptions import MetadataError

logger = logging.getLogger(__name__)

class VersionDetectionError(MetadataError):
    """Raised when version detection fails"""
    pass

class ModuleVersionDetector:
    """Detects environment version using GetInstalledModules action"""
    
    def __init__(self, api_operations):
        """Initialize with API operations instance"""
        self.api = api_operations
        self._cache_ttl = 300  # Cache version detection for 5 minutes
        self._cached_version: Optional[Tuple[EnvironmentVersionInfo, datetime]] = None
    
    async def get_environment_version(self, use_cache: bool = True) -> EnvironmentVersionInfo:
        """Get current environment version based on installed modules
        
        Args:
            use_cache: Whether to use cached version if available
            
        Returns:
            EnvironmentVersionInfo with complete module details
            
        Raises:
            VersionDetectionError: If version detection fails
        """
        # Check cache first
        if use_cache and self._cached_version:
            cached_version, cached_at = self._cached_version
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age < self._cache_ttl:
                logger.debug(f"Using cached version detection (age: {age:.1f}s)")
                return cached_version
        
        try:
            logger.info("Detecting environment version using GetInstalledModules")
            
            # Call GetInstalledModules action on SystemNotifications entity
            modules_response = await self.api.call_action(
                "GetInstalledModules",
                entity_name="SystemNotifications"
            )
            
            # Parse module information
            modules = self._parse_modules_response(modules_response)
            
            # Get fallback version info
            app_version, platform_version = await self._get_fallback_versions()
            
            # Create version info
            version_info = EnvironmentVersionInfo(
                environment_id=0,  # Will be set by cache manager
                version_hash="",   # Will be computed in __post_init__
                modules_hash="",   # Will be computed in __post_init__
                application_version=app_version,
                platform_version=platform_version,
                modules=modules,
                computed_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            # Cache the result
            self._cached_version = (version_info, datetime.now(timezone.utc))
            
            logger.info(f"Version detection complete: {len(modules)} modules, "
                       f"hash: {version_info.version_hash}")
            
            return version_info
            
        except Exception as e:
            logger.error(f"Version detection failed: {e}")
            raise VersionDetectionError(f"Failed to detect environment version: {e}")
    
    def _parse_modules_response(self, response: Dict) -> List[ModuleVersionInfo]:
        """Parse GetInstalledModules response into ModuleVersionInfo objects
        
        Args:
            response: Response from GetInstalledModules action
            
        Returns:
            List of ModuleVersionInfo objects
            
        Raises:
            VersionDetectionError: If response format is invalid
        """
        try:
            if not response.get('success', False):
                raise VersionDetectionError("GetInstalledModules action failed")
            
            result = response.get('result', {})
            module_strings = result.get('value', [])
            
            if not isinstance(module_strings, list):
                raise VersionDetectionError("Invalid response format: expected list of strings")
            
            modules = []
            for module_string in module_strings:
                try:
                    module = ModuleVersionInfo.parse_from_string(module_string)
                    modules.append(module)
                except ValueError as e:
                    logger.warning(f"Failed to parse module string: {e}")
                    continue
            
            if not modules:
                raise VersionDetectionError("No valid modules found in response")
            
            logger.debug(f"Parsed {len(modules)} modules from {len(module_strings)} strings")
            return modules
            
        except Exception as e:
            if isinstance(e, VersionDetectionError):
                raise
            raise VersionDetectionError(f"Failed to parse modules response: {e}")
    
    async def _get_fallback_versions(self) -> Tuple[Optional[str], Optional[str]]:
        """Get fallback application and platform versions"""
        app_version = None
        platform_version = None
        
        try:
            app_version = await self.api.get_application_version()
        except Exception as e:
            logger.warning(f"Failed to get application version: {e}")
        
        try:
            platform_version = await self.api.get_platform_build_version()
        except Exception as e:
            logger.warning(f"Failed to get platform version: {e}")
        
        return app_version, platform_version
    
    async def compare_versions(self, version1: EnvironmentVersionInfo, 
                             version2: EnvironmentVersionInfo) -> Dict[str, Any]:
        """Compare two environment versions and return differences
        
        Args:
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'identical': version1.modules_hash == version2.modules_hash,
            'hash_match': version1.version_hash == version2.version_hash,
            'module_count_diff': len(version2.modules) - len(version1.modules),
            'added_modules': [],
            'removed_modules': [],
            'updated_modules': [],
            'identical_modules': []
        }
        
        # Create module dictionaries for comparison
        v1_modules = {m.module_id: m for m in version1.modules}
        v2_modules = {m.module_id: m for m in version2.modules}
        
        # Find differences
        for module_id, module in v2_modules.items():
            if module_id not in v1_modules:
                comparison['added_modules'].append(module.to_dict())
            elif v1_modules[module_id].version != module.version:
                comparison['updated_modules'].append({
                    'module_id': module_id,
                    'old_version': v1_modules[module_id].version,
                    'new_version': module.version
                })
            else:
                comparison['identical_modules'].append(module_id)
        
        for module_id in v1_modules:
            if module_id not in v2_modules:
                comparison['removed_modules'].append(v1_modules[module_id].to_dict())
        
        return comparison
    
    def clear_cache(self):
        """Clear cached version detection"""
        self._cached_version = None
        logger.debug("Version detection cache cleared")
```

### 2. Global Version Management

#### File: `src/d365fo_client/metadata_v2/global_manager.py`

```python
"""Global version management for cross-environment metadata sharing."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import aiosqlite

from ..models import EnvironmentVersionInfo, GlobalVersionInfo, ModuleVersionInfo
from .database_v2 import MetadataDatabaseV2

logger = logging.getLogger(__name__)

class GlobalVersionManager:
    """Manages global version registry for metadata sharing"""
    
    def __init__(self, database: MetadataDatabaseV2):
        """Initialize with database instance"""
        self.db = database
        self._lock = asyncio.Lock()
    
    async def find_compatible_version(self, modules_hash: str) -> Optional[GlobalVersionInfo]:
        """Find existing global version with matching modules hash
        
        Args:
            modules_hash: Hash of module versions to match
            
        Returns:
            GlobalVersionInfo if found, None otherwise
        """
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute(
                """SELECT id, version_hash, modules_hash, first_seen_at, 
                          last_used_at, reference_count
                   FROM global_versions 
                   WHERE modules_hash = ?
                   ORDER BY last_used_at DESC
                   LIMIT 1""",
                (modules_hash,)
            )
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            return GlobalVersionInfo(
                id=row[0],
                version_hash=row[1],
                modules_hash=row[2],
                first_seen_at=datetime.fromisoformat(row[3]),
                last_used_at=datetime.fromisoformat(row[4]),
                reference_count=row[5]
            )
    
    async def create_global_version(self, env_version: EnvironmentVersionInfo) -> GlobalVersionInfo:
        """Create new global version entry
        
        Args:
            env_version: Environment version to create global version from
            
        Returns:
            Created GlobalVersionInfo
        """
        async with self._lock:
            async with aiosqlite.connect(self.db.db_path) as db:
                now = datetime.now(timezone.utc)
                
                cursor = await db.execute(
                    """INSERT INTO global_versions 
                       (version_hash, modules_hash, first_seen_at, last_used_at, reference_count)
                       VALUES (?, ?, ?, ?, 1)""",
                    (env_version.version_hash, env_version.modules_hash, now, now)
                )
                
                global_version_id = cursor.lastrowid
                
                # Store sample modules for debugging (first 10)
                sample_modules = env_version.modules[:10]
                for i, module in enumerate(sample_modules):
                    await db.execute(
                        """INSERT INTO global_version_modules
                           (global_version_id, module_id, module_name, version, 
                            publisher, display_name, sort_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (global_version_id, module.module_id, module.name, 
                         module.version, module.publisher, module.display_name, i)
                    )
                
                await db.commit()
                
                logger.info(f"Created global version {global_version_id} "
                           f"with hash {env_version.version_hash[:8]}")
                
                return GlobalVersionInfo(
                    id=global_version_id,
                    version_hash=env_version.version_hash,
                    modules_hash=env_version.modules_hash,
                    first_seen_at=now,
                    last_used_at=now,
                    reference_count=1,
                    sample_modules=sample_modules
                )
    
    async def link_environment_to_version(self, environment_id: int, 
                                        global_version: GlobalVersionInfo) -> bool:
        """Link environment to existing global version
        
        Args:
            environment_id: Environment ID to link
            global_version: Global version to link to
            
        Returns:
            True if linking successful, False if already linked
        """
        async with aiosqlite.connect(self.db.db_path) as db:
            # Check if already linked
            cursor = await db.execute(
                """SELECT 1 FROM environment_versions 
                   WHERE environment_id = ? AND global_version_id = ? AND is_active = 1""",
                (environment_id, global_version.id)
            )
            
            if await cursor.fetchone():
                logger.debug(f"Environment {environment_id} already linked to version {global_version.id}")
                return False
            
            # Deactivate old links
            await db.execute(
                """UPDATE environment_versions 
                   SET is_active = 0 
                   WHERE environment_id = ?""",
                (environment_id,)
            )
            
            # Create new link
            await db.execute(
                """INSERT INTO environment_versions
                   (environment_id, global_version_id, detected_at, is_active)
                   VALUES (?, ?, ?, 1)""",
                (environment_id, global_version.id, datetime.now(timezone.utc))
            )
            
            # Update reference count and last used time
            await db.execute(
                """UPDATE global_versions 
                   SET reference_count = reference_count + 1,
                       last_used_at = ?
                   WHERE id = ?""",
                (datetime.now(timezone.utc), global_version.id)
            )
            
            await db.commit()
            
            logger.info(f"Linked environment {environment_id} to global version {global_version.id}")
            return True
    
    async def get_or_create_global_version(self, env_version: EnvironmentVersionInfo) -> Tuple[GlobalVersionInfo, bool]:
        """Get existing or create new global version
        
        Args:
            env_version: Environment version to find or create
            
        Returns:
            Tuple of (GlobalVersionInfo, was_created)
        """
        # Try to find existing version
        existing = await self.find_compatible_version(env_version.modules_hash)
        if existing:
            return existing, False
        
        # Create new version
        new_version = await self.create_global_version(env_version)
        return new_version, True
    
    async def cleanup_unused_versions(self, retention_days: int = 30) -> int:
        """Remove unused global versions older than retention period
        
        Args:
            retention_days: Days to retain unused versions
            
        Returns:
            Number of versions cleaned up
        """
        cutoff_date = datetime.now(timezone.utc).replace(
            day=datetime.now(timezone.utc).day - retention_days
        )
        
        async with aiosqlite.connect(self.db.db_path) as db:
            # Find unused versions
            cursor = await db.execute(
                """SELECT id FROM global_versions 
                   WHERE reference_count = 0 AND last_used_at < ?""",
                (cutoff_date,)
            )
            
            unused_ids = [row[0] for row in await cursor.fetchall()]
            
            if not unused_ids:
                return 0
            
            # Clean up metadata for unused versions
            for version_id in unused_ids:
                await self._cleanup_version_metadata(db, version_id)
            
            # Remove global version entries
            placeholders = ','.join('?' * len(unused_ids))
            await db.execute(
                f"DELETE FROM global_versions WHERE id IN ({placeholders})",
                unused_ids
            )
            
            await db.commit()
            
            logger.info(f"Cleaned up {len(unused_ids)} unused global versions")
            return len(unused_ids)
    
    async def _cleanup_version_metadata(self, db: aiosqlite.Connection, global_version_id: int):
        """Clean up all metadata associated with a global version"""
        # This will be implemented to cascade delete all related metadata
        # tables that reference the global version
        
        tables_to_clean = [
            'global_version_modules',
            'environment_versions',
            # Add other tables that reference global_version_id
        ]
        
        for table in tables_to_clean:
            try:
                await db.execute(
                    f"DELETE FROM {table} WHERE global_version_id = ?",
                    (global_version_id,)
                )
            except Exception as e:
                logger.warning(f"Failed to clean table {table}: {e}")
    
    async def get_sharing_statistics(self) -> Dict[str, Any]:
        """Get statistics about version sharing
        
        Returns:
            Dictionary with sharing metrics
        """
        async with aiosqlite.connect(self.db.db_path) as db:
            stats = {}
            
            # Total global versions
            cursor = await db.execute("SELECT COUNT(*) FROM global_versions")
            stats['total_global_versions'] = (await cursor.fetchone())[0]
            
            # Active environment links
            cursor = await db.execute(
                "SELECT COUNT(*) FROM environment_versions WHERE is_active = 1"
            )
            stats['active_environment_links'] = (await cursor.fetchone())[0]
            
            # Sharing efficiency
            cursor = await db.execute(
                """SELECT gv.reference_count, COUNT(*) as version_count
                   FROM global_versions gv
                   GROUP BY gv.reference_count
                   ORDER BY gv.reference_count"""
            )
            
            sharing_distribution = {}
            total_environments = 0
            shared_environments = 0
            
            async for row in cursor:
                ref_count, version_count = row
                sharing_distribution[ref_count] = version_count
                total_environments += ref_count * version_count
                if ref_count > 1:
                    shared_environments += ref_count * version_count
            
            stats['sharing_distribution'] = sharing_distribution
            stats['total_environments'] = total_environments
            stats['shared_environments'] = shared_environments
            stats['sharing_efficiency'] = (
                shared_environments / total_environments if total_environments > 0 else 0
            )
            
            return stats

class VersionSharingManager:
    """High-level manager for version sharing operations"""
    
    def __init__(self, global_manager: GlobalVersionManager, database: MetadataDatabaseV2):
        self.global_manager = global_manager
        self.db = database
    
    async def process_environment_version(self, environment_id: int, 
                                        env_version: EnvironmentVersionInfo) -> Dict[str, Any]:
        """Process environment version and determine sharing strategy
        
        Args:
            environment_id: Environment ID
            env_version: Detected environment version
            
        Returns:
            Dictionary with processing results and recommendations
        """
        # Set environment ID
        env_version.environment_id = environment_id
        
        # Find or create global version
        global_version, was_created = await self.global_manager.get_or_create_global_version(env_version)
        
        # Link environment to global version
        was_linked = await self.global_manager.link_environment_to_version(
            environment_id, global_version
        )
        
        result = {
            'environment_id': environment_id,
            'version_hash': env_version.version_hash,
            'modules_hash': env_version.modules_hash,
            'global_version_id': global_version.id,
            'was_created': was_created,
            'was_linked': was_linked,
            'reference_count': global_version.reference_count + (1 if was_linked else 0),
            'can_share_metadata': not was_created,
            'modules_count': len(env_version.modules),
            'recommendation': self._get_sync_recommendation(was_created, global_version)
        }
        
        return result
    
    def _get_sync_recommendation(self, was_created: bool, global_version: GlobalVersionInfo) -> str:
        """Get recommendation for sync strategy"""
        if was_created:
            return "full_sync_required"
        elif global_version.reference_count == 1:
            return "link_to_existing"
        else:
            return "share_existing_metadata"
```

### 3. Enhanced Database Schema

#### File: `src/d365fo_client/metadata_v2/database_v2.py`

```python
"""Enhanced database schema with global version management."""

import logging
from pathlib import Path
from typing import Optional
import aiosqlite

from .database_v2 import MetadataDatabaseV2

logger = logging.getLogger(__name__)

class DatabaseSchemaV2:
    """Database schema manager for metadata v2"""
    
    @staticmethod
    async def create_schema(db: aiosqlite.Connection):
        """Create complete database schema for metadata v2"""
        
        # Core environment tracking (enhanced)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metadata_environments (
                id INTEGER PRIMARY KEY,
                base_url TEXT NOT NULL UNIQUE,
                environment_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sync_at TIMESTAMP,
                last_version_check TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Global version registry (NEW)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_versions (
                id INTEGER PRIMARY KEY,
                version_hash TEXT UNIQUE NOT NULL,
                modules_hash TEXT UNIQUE NOT NULL,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reference_count INTEGER DEFAULT 0,
                metadata_size_bytes INTEGER DEFAULT 0,
                created_by_environment_id INTEGER REFERENCES metadata_environments(id)
            )
        """)
        
        # Environment to global version mapping (NEW)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS environment_versions (
                environment_id INTEGER REFERENCES metadata_environments(id),
                global_version_id INTEGER REFERENCES global_versions(id),
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                sync_status TEXT DEFAULT 'pending',  -- pending|syncing|completed|failed
                last_sync_duration_ms INTEGER,
                PRIMARY KEY (environment_id, global_version_id)
            )
        """)
        
        # Sample modules for global versions (NEW)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_version_modules (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER REFERENCES global_versions(id),
                module_id TEXT NOT NULL,
                module_name TEXT,
                version TEXT,
                publisher TEXT,
                display_name TEXT,
                sort_order INTEGER DEFAULT 0
            )
        """)
        
        # Enhanced metadata versioning
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metadata_versions (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                application_version TEXT,
                platform_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sync_completed_at TIMESTAMP,
                entity_count INTEGER DEFAULT 0,
                action_count INTEGER DEFAULT 0,
                enumeration_count INTEGER DEFAULT 0,
                label_count INTEGER DEFAULT 0
            )
        """)
        
        # Version-aware metadata tables (enhanced with global_version_id)
        
        # Data entities
        await db.execute("""
            CREATE TABLE IF NOT EXISTS data_entities (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                public_entity_name TEXT,
                public_collection_name TEXT,
                label_id TEXT,
                label_text TEXT,
                entity_category TEXT,
                data_service_enabled BOOLEAN DEFAULT 1,
                data_management_enabled BOOLEAN DEFAULT 1,
                is_read_only BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Public entities
        await db.execute("""
            CREATE TABLE IF NOT EXISTS public_entities (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                entity_set_name TEXT,
                label_id TEXT,
                label_text TEXT,
                is_read_only BOOLEAN DEFAULT 0,
                configuration_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Entity properties (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entity_properties (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                type_name TEXT,
                data_type TEXT,
                odata_xpp_type TEXT,
                label_id TEXT,
                label_text TEXT,
                is_key BOOLEAN DEFAULT 0,
                is_mandatory BOOLEAN DEFAULT 0,
                configuration_enabled BOOLEAN DEFAULT 1,
                allow_edit BOOLEAN DEFAULT 1,
                allow_edit_on_create BOOLEAN DEFAULT 1,
                is_dimension BOOLEAN DEFAULT 0,
                dimension_relation TEXT,
                is_dynamic_dimension BOOLEAN DEFAULT 0,
                dimension_legal_entity_property TEXT,
                dimension_type_property TEXT,
                property_order INTEGER DEFAULT 0
            )
        """)
        
        # Navigation properties (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS navigation_properties (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                related_entity TEXT,
                related_relation_name TEXT,
                cardinality TEXT DEFAULT 'Single'
            )
        """)
        
        # Relation constraints (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS relation_constraints (
                id INTEGER PRIMARY KEY,
                navigation_property_id INTEGER NOT NULL REFERENCES navigation_properties(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                constraint_type TEXT NOT NULL,
                property_name TEXT,
                referenced_property TEXT,
                related_property TEXT,
                fixed_value INTEGER,
                fixed_value_str TEXT
            )
        """)
        
        # Property groups (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS property_groups (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL
            )
        """)
        
        # Property group members (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS property_group_members (
                id INTEGER PRIMARY KEY,
                property_group_id INTEGER NOT NULL REFERENCES property_groups(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                property_name TEXT NOT NULL,
                member_order INTEGER DEFAULT 0
            )
        """)
        
        # Entity actions (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entity_actions (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                binding_kind TEXT DEFAULT 'BoundToEntitySet',
                entity_name TEXT,
                entity_set_name TEXT,
                return_type_name TEXT,
                return_is_collection BOOLEAN DEFAULT 0,
                return_odata_xpp_type TEXT,
                field_lookup TEXT
            )
        """)
        
        # Action parameters (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS action_parameters (
                id INTEGER PRIMARY KEY,
                action_id INTEGER NOT NULL REFERENCES entity_actions(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                type_name TEXT,
                is_collection BOOLEAN DEFAULT 0,
                odata_xpp_type TEXT,
                parameter_order INTEGER DEFAULT 0
            )
        """)
        
        # Enumerations (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS enumerations (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                label_id TEXT,
                label_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Enumeration members (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS enumeration_members (
                id INTEGER PRIMARY KEY,
                enumeration_id INTEGER NOT NULL REFERENCES enumerations(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                value INTEGER NOT NULL,
                label_id TEXT,
                label_text TEXT,
                configuration_enabled BOOLEAN DEFAULT 1,
                member_order INTEGER DEFAULT 0
            )
        """)
        
        # Labels cache (version-aware)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS labels_cache (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER REFERENCES global_versions(id),
                label_id TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en-US',
                label_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                hit_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(global_version_id, label_id, language)
            )
        """)
        
        # FTS5 search index (version-aware)
        await db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS metadata_search_v2 USING fts5(
                name,
                entity_type,
                description,
                properties,
                labels,
                global_version_id UNINDEXED,
                entity_id UNINDEXED,
                content='',
                contentless_delete=1
            )
        """)
        
        await db.commit()
        logger.info("Database schema v2 created successfully")
    
    @staticmethod
    async def create_indexes(db: aiosqlite.Connection):
        """Create optimized indexes for version-aware queries"""
        
        indexes = [
            # Global version indexes
            "CREATE INDEX IF NOT EXISTS idx_global_versions_hash ON global_versions(version_hash)",
            "CREATE INDEX IF NOT EXISTS idx_global_versions_modules_hash ON global_versions(modules_hash)",
            "CREATE INDEX IF NOT EXISTS idx_global_versions_last_used ON global_versions(last_used_at)",
            
            # Environment version indexes
            "CREATE INDEX IF NOT EXISTS idx_env_versions_active ON environment_versions(environment_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_env_versions_global ON environment_versions(global_version_id, is_active)",
            
            # Version-aware entity indexes
            "CREATE INDEX IF NOT EXISTS idx_data_entities_version ON data_entities(global_version_id, name)",
            "CREATE INDEX IF NOT EXISTS idx_public_entities_version ON public_entities(global_version_id, name)",
            "CREATE INDEX IF NOT EXISTS idx_entity_properties_version ON entity_properties(global_version_id, entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_navigation_props_version ON navigation_properties(global_version_id, entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_entity_actions_version ON entity_actions(global_version_id, entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_enumerations_version ON enumerations(global_version_id, name)",
            
            # Labels indexes
            "CREATE INDEX IF NOT EXISTS idx_labels_version_lookup ON labels_cache(global_version_id, label_id, language)",
            "CREATE INDEX IF NOT EXISTS idx_labels_expires ON labels_cache(expires_at)",
            
            # Search performance indexes
            "CREATE INDEX IF NOT EXISTS idx_data_entities_search ON data_entities(global_version_id, data_service_enabled, entity_category)",
            "CREATE INDEX IF NOT EXISTS idx_public_entities_search ON public_entities(global_version_id, is_read_only)",
        ]
        
        for index_sql in indexes:
            try:
                await db.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
        
        await db.commit()
        logger.info("Database indexes v2 created successfully")

class MetadataDatabaseV2:
    """Enhanced metadata database with global version support"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_database_directory()
    
    def _ensure_database_directory(self):
        """Ensure database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database with v2 schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await DatabaseSchemaV2.create_schema(db)
            await DatabaseSchemaV2.create_indexes(db)
            
            # Enable foreign key constraints
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("PRAGMA journal_mode = WAL")
            await db.commit()
        
        logger.info(f"Metadata database v2 initialized: {self.db_path}")
    
    async def get_or_create_environment(self, base_url: str) -> int:
        """Get or create environment ID"""
        async with aiosqlite.connect(self.db_path) as db:
            # Try to find existing environment
            cursor = await db.execute(
                "SELECT id FROM metadata_environments WHERE base_url = ?",
                (base_url,)
            )
            
            row = await cursor.fetchone()
            if row:
                return row[0]
            
            # Create new environment
            environment_name = self._extract_environment_name(base_url)
            cursor = await db.execute(
                """INSERT INTO metadata_environments (base_url, environment_name)
                   VALUES (?, ?)""",
                (base_url, environment_name)
            )
            
            environment_id = cursor.lastrowid
            await db.commit()
            
            logger.info(f"Created environment {environment_id}: {environment_name}")
            return environment_id
    
    def _extract_environment_name(self, base_url: str) -> str:
        """Extract environment name from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        hostname = parsed.hostname or base_url
        return hostname.split('.')[0] if '.' in hostname else hostname
    
    async def get_global_version_metadata_counts(self, global_version_id: int) -> Dict[str, int]:
        """Get metadata counts for a global version"""
        async with aiosqlite.connect(self.db_path) as db:
            counts = {}
            
            tables = [
                ('data_entities', 'entities'),
                ('public_entities', 'public_entities'),
                ('entity_properties', 'properties'),
                ('entity_actions', 'actions'),
                ('enumerations', 'enumerations'),
                ('labels_cache', 'labels')
            ]
            
            for table, key in tables:
                cursor = await db.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE global_version_id = ?",
                    (global_version_id,)
                )
                counts[key] = (await cursor.fetchone())[0]
            
            return counts
```

## Implementation Timeline and Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. Create `metadata_v2` package structure
2. Implement `ModuleVersionInfo` and enhanced models
3. Create `ModuleVersionDetector` with `GetInstalledModules` integration
4. Design and implement enhanced database schema

### Phase 2: Core Systems (Week 3-4)
1. Implement `GlobalVersionManager` for cross-environment sharing
2. Create `VersionSharingManager` for high-level operations
3. Build `MetadataDatabaseV2` with version-aware operations
4. Implement basic version detection and comparison

### Phase 3: Cache and Sync (Week 5-6)
1. Develop `MetadataCacheV2` with version-aware caching
2. Create `SmartSyncManagerV2` with intelligent sync strategies
3. Implement `VersionAwareSearchEngine`
4. Add comprehensive error handling and logging

### Phase 4: Migration and Testing (Week 7-8)
1. Create `MetadataMigrationManager` for v1 to v2 migration
2. Implement backward compatibility layer
3. Comprehensive unit and integration testing
4. Performance benchmarking and optimization

### Phase 5: Deployment and Deprecation (Week 9-12)
1. Update client configuration to support both v1 and v2
2. Add feature flags for gradual rollout
3. Documentation and migration guides
4. Begin v1 deprecation process

## Backward Compatibility and Migration

### Configuration Migration
```python
# Old configuration
config = FOClientConfig(
    enable_metadata_cache=True,
    metadata_sync_interval_minutes=60
)

# New configuration (backward compatible)
config = FOClientConfig(
    enable_metadata_cache=True,  # Still works, uses v1
    enable_metadata_cache_v2=True,  # Opt-in to v2
    metadata_version="v2",  # Explicit version selection
    auto_migrate_cache=True  # Automatic migration from v1
)
```

### API Compatibility
```python
# Both versions expose same interface
from d365fo_client.metadata_cache import MetadataCache  # v1
from d365fo_client.metadata_v2 import MetadataCacheV2  # v2

# Factory function for smooth transition
def create_metadata_cache(config: FOClientConfig) -> Union[MetadataCache, MetadataCacheV2]:
    if config.metadata_version == "v2" or config.enable_metadata_cache_v2:
        return MetadataCacheV2(config.base_url, config.metadata_cache_dir, config)
    else:
        return MetadataCache(config.base_url, config.metadata_cache_dir, config)
```

## Testing Strategy

### Unit Tests
- `ModuleVersionInfo.parse_from_string()` with various input formats
- Version hash computation and comparison
- Global version management operations
- Database schema creation and migrations

### Integration Tests
- End-to-end version detection using `GetInstalledModules`
- Cross-environment metadata sharing scenarios
- Performance testing with large metadata sets
- Migration from v1 to v2 cache

### Performance Benchmarks
- Version detection speed vs current implementation
- Storage efficiency with shared metadata
- Query performance with version-aware indexes
- Memory usage optimization

## Success Criteria

1. **Accuracy**: Version detection based on actual module versions (100% accurate)
2. **Efficiency**: 50%+ reduction in metadata sync operations for duplicate environments
3. **Performance**: Sub-100ms version detection, version-aware queries under 50ms
4. **Storage**: 60%+ storage efficiency for environments with shared metadata
5. **Compatibility**: Zero breaking changes to existing API
6. **Migration**: Seamless migration from v1 to v2 with < 5 minute downtime

This specification provides a comprehensive roadmap for implementing the enhanced metadata caching system while maintaining backward compatibility and ensuring a smooth migration path.

## Sample GetInstalledModules Response

For reference, here's the structure of the `GetInstalledModules` response that the implementation will parse:

```json
{
  "success": true,
  "actionName": "GetInstalledModules",
  "result": {
    "@odata.context": "https://usnconeboxax1aos.cloud.onebox.dynamics.com/data/$metadata#Collection(Edm.String)",
    "value": [
      "Name: AccountsPayableMobile | Version: 10.34.2105.34092 | Module: AccountsPayableMobile | Publisher: Microsoft Corporation | DisplayName: Accounts Payable Mobile",
      "Name: AdvancedQualityManagement | Version: 10.34.2105.34092 | Module: AdvancedQualityManagement | Publisher: Microsoft Corporation | DisplayName: Advanced Quality Management",
      "Name: ApplicationCommon | Version: 10.34.2105.34092 | Module: ApplicationCommon | Publisher: Microsoft | DisplayName: Application Common",
      "Name: ApplicationFoundation | Version: 7.0.7521.60 | Module: ApplicationFoundation | Publisher: Microsoft Corporation | DisplayName: Application Foundation"
    ]
  },
  "executionTime": 1.039,
  "parameters": {},
  "binding": {
    "entityName": "SystemNotifications",
    "entityKey": null,
    "bindingKind": "BoundToEntitySet"
  }
}
```

Each module string follows the pattern:
`"Name: {name} | Version: {version} | Module: {module_id} | Publisher: {publisher} | DisplayName: {display_name}"`

The `ModuleVersionInfo.parse_from_string()` method will parse these strings to extract individual components for precise version tracking and comparison.