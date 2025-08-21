"""Advanced metadata caching with SQLite backend."""

import asyncio
import json
import re
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, TYPE_CHECKING
from urllib.parse import urlparse
import hashlib
import logging

try:
    import aiosqlite
except ImportError:
    aiosqlite = None

try:
    from cachetools import TTLCache
except ImportError:
    TTLCache = None

try:
    import diskcache as dc
except ImportError:
    dc = None

if TYPE_CHECKING:
    import aiosqlite as aiosqlite_types

from .models import (
    DataEntityInfo, PublicEntityInfo, EnumerationInfo, NavigationPropertyInfo,
    PropertyGroupInfo, ActionInfo, ActionParameterInfo, ActionTypeInfo,
    RelationConstraintInfo, ReferentialConstraintInfo, FixedConstraintInfo,
    RelatedFixedConstraintInfo, MetadataVersionInfo, SearchQuery, SearchResult,
    SearchResults, SyncResult, LabelInfo, PublicEntityPropertyInfo, 
    EnumerationMemberInfo
)
from .exceptions import MetadataError


logger = logging.getLogger(__name__)


class MetadataDatabase:
    """SQLite database for metadata storage with full schema support"""
    
    def __init__(self, db_path: Path):
        """Initialize metadata database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_directory()
        
    def _ensure_database_directory(self):
        """Ensure database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database schema"""
        if aiosqlite is None:
            raise MetadataError("aiosqlite is required for metadata caching. Install with: pip install aiosqlite")
        
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=10000")
            await db.execute("PRAGMA temp_store=MEMORY")
            
            # Create schema
            await self._create_schema(db)
            await db.commit()
    
    async def _create_schema(self, db: Any):
        """Create complete database schema"""
        
        # Environment and versioning tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metadata_environments (
                id INTEGER PRIMARY KEY,
                base_url TEXT NOT NULL UNIQUE,
                environment_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sync_at TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metadata_versions (
                id INTEGER PRIMARY KEY,
                environment_id INTEGER NOT NULL REFERENCES metadata_environments(id),
                version_hash TEXT NOT NULL,
                application_version TEXT,
                platform_version TEXT,
                package_info TEXT, -- JSON array of packages
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Core entity tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS data_entities (
                id INTEGER PRIMARY KEY,
                version_id INTEGER NOT NULL REFERENCES metadata_versions(id),
                name TEXT NOT NULL,
                public_entity_name TEXT,
                public_collection_name TEXT,
                label_id TEXT,
                entity_category TEXT,
                data_service_enabled BOOLEAN DEFAULT 1,
                data_management_enabled BOOLEAN DEFAULT 1,
                is_read_only BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS public_entities (
                id INTEGER PRIMARY KEY,
                version_id INTEGER NOT NULL REFERENCES metadata_versions(id),
                name TEXT NOT NULL,
                entity_set_name TEXT,
                label_id TEXT,
                is_read_only BOOLEAN DEFAULT 0,
                configuration_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Properties table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entity_properties (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                name TEXT NOT NULL,
                type_name TEXT,
                data_type TEXT,
                odata_xpp_type TEXT,
                label_id TEXT,
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
        
        # Navigation properties and constraints
        await db.execute("""
            CREATE TABLE IF NOT EXISTS navigation_properties (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                name TEXT NOT NULL,
                related_entity TEXT NOT NULL,
                related_relation_name TEXT,
                cardinality TEXT DEFAULT 'Single',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS relation_constraints (
                id INTEGER PRIMARY KEY,
                navigation_property_id INTEGER NOT NULL REFERENCES navigation_properties(id),
                constraint_type TEXT NOT NULL,
                property_name TEXT,
                referenced_property TEXT,
                fixed_value INTEGER,
                fixed_value_str TEXT,
                related_property TEXT
            )
        """)
        
        # Property groups
        await db.execute("""
            CREATE TABLE IF NOT EXISTS property_groups (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                name TEXT NOT NULL,
                group_order INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS property_group_members (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL REFERENCES property_groups(id),
                property_name TEXT NOT NULL,
                member_order INTEGER DEFAULT 0
            )
        """)
        
        # Actions and parameters
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entity_actions (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER REFERENCES public_entities(id),
                name TEXT NOT NULL,
                binding_kind TEXT,
                field_lookup TEXT,
                return_type_name TEXT,
                return_is_collection BOOLEAN DEFAULT 0,
                return_odata_xpp_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS action_parameters (
                id INTEGER PRIMARY KEY,
                action_id INTEGER NOT NULL REFERENCES entity_actions(id),
                name TEXT NOT NULL,
                type_name TEXT NOT NULL,
                is_collection BOOLEAN DEFAULT 0,
                odata_xpp_type TEXT,
                parameter_order INTEGER DEFAULT 0
            )
        """)
        
        # Enumerations
        await db.execute("""
            CREATE TABLE IF NOT EXISTS enumerations (
                id INTEGER PRIMARY KEY,
                version_id INTEGER NOT NULL REFERENCES metadata_versions(id),
                name TEXT NOT NULL,
                label_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS enumeration_members (
                id INTEGER PRIMARY KEY,
                enumeration_id INTEGER NOT NULL REFERENCES enumerations(id),
                name TEXT NOT NULL,
                value INTEGER NOT NULL,
                label_id TEXT,
                configuration_enabled BOOLEAN DEFAULT 1,
                member_order INTEGER DEFAULT 0
            )
        """)
        
        # Labels cache
        await db.execute("""
            CREATE TABLE IF NOT EXISTS labels_cache (
                id INTEGER PRIMARY KEY,
                label_id TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en-US',
                value TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                UNIQUE(label_id, language)
            )
        """)
        
        # FTS5 virtual table for search (content-based for direct data insertion)
        await db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS metadata_search USING fts5(
                entity_name,
                entity_type,
                entity_set_name,
                description,
                labels,
                properties_text,
                actions_text
            )
        """)
        
        # Create indexes
        await self._create_indexes(db)
    
    async def _create_indexes(self, db: Any):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_data_entities_name ON data_entities(name)",
            "CREATE INDEX IF NOT EXISTS idx_data_entities_version ON data_entities(version_id)",
            "CREATE INDEX IF NOT EXISTS idx_public_entities_name ON public_entities(name)",
            "CREATE INDEX IF NOT EXISTS idx_public_entities_version ON public_entities(version_id)",
            "CREATE INDEX IF NOT EXISTS idx_properties_entity ON entity_properties(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_navigation_entity ON navigation_properties(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_actions_entity ON entity_actions(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_action_params_action ON action_parameters(action_id)",
            "CREATE INDEX IF NOT EXISTS idx_labels_lookup ON labels_cache(label_id, language)",
            "CREATE INDEX IF NOT EXISTS idx_labels_expires ON labels_cache(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_entities_category_readonly ON data_entities(entity_category, is_read_only)",
            "CREATE INDEX IF NOT EXISTS idx_properties_key_mandatory ON entity_properties(is_key, is_mandatory)",
            "CREATE INDEX IF NOT EXISTS idx_versions_active ON metadata_versions(environment_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_environments_url ON metadata_environments(base_url)"
        ]
        
        for index_sql in indexes:
            await db.execute(index_sql)
    
    async def get_or_create_environment(self, base_url: str) -> int:
        """Get or create environment record"""
        async with aiosqlite.connect(self.db_path) as db:
            # Try to get existing environment
            cursor = await db.execute(
                "SELECT id FROM metadata_environments WHERE base_url = ?",
                (base_url,)
            )
            row = await cursor.fetchone()
            
            if row:
                return row[0]
            
            # Create new environment
            cursor = await db.execute(
                """INSERT INTO metadata_environments (base_url, environment_name, created_at)
                   VALUES (?, ?, ?)""",
                (base_url, self._extract_environment_name(base_url), datetime.now(timezone.utc))
            )
            await db.commit()
            return cursor.lastrowid
    
    def _extract_environment_name(self, base_url: str) -> str:
        """Extract environment name from URL"""
        try:
            parsed = urlparse(base_url)
            hostname = parsed.hostname or ""
            # Extract environment name from hostname (e.g., mycompany-test.dynamics.com -> mycompany-test)
            if hostname.endswith('.dynamics.com'):
                return hostname.replace('.dynamics.com', '')
            return hostname
        except Exception:
            return "unknown"
    
    async def create_version(self, environment_id: int, version_info: MetadataVersionInfo) -> int:
        """Create new metadata version"""
        async with aiosqlite.connect(self.db_path) as db:
            # Deactivate previous versions
            await db.execute(
                "UPDATE metadata_versions SET is_active = 0 WHERE environment_id = ?",
                (environment_id,)
            )
            
            # Create new version
            cursor = await db.execute(
                """INSERT INTO metadata_versions 
                   (environment_id, version_hash, application_version, platform_version, 
                    package_info, created_at, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (environment_id, version_info.version_hash, version_info.application_version,
                 version_info.platform_version, json.dumps(version_info.package_info or []),
                 datetime.now(timezone.utc))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_active_version(self, environment_id: int) -> Optional[MetadataVersionInfo]:
        """Get active metadata version"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT id, version_hash, application_version, platform_version, 
                          package_info, created_at
                   FROM metadata_versions 
                   WHERE environment_id = ? AND is_active = 1
                   ORDER BY created_at DESC LIMIT 1""",
                (environment_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return MetadataVersionInfo(
                environment_id=environment_id,
                version_hash=row[1],
                application_version=row[2],
                platform_version=row[3],
                package_info=json.loads(row[4]) if row[4] else None,
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                is_active=True
            )
    
    async def populate_fts_index(self, version_id: int):
        """Populate FTS5 search index with metadata for given version"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if we need to recreate the FTS5 table (handle content-less tables)
            try:
                # Try to clear existing FTS5 data
                await db.execute("DELETE FROM metadata_search")
            except Exception as e:
                if "contentless" in str(e):
                    logger.info("Recreating FTS5 table (was content-less)")
                    # Drop and recreate the table with proper schema
                    await db.execute("DROP TABLE IF EXISTS metadata_search")
                    await db.execute("""
                        CREATE VIRTUAL TABLE metadata_search USING fts5(
                            entity_name,
                            entity_type,
                            entity_set_name,
                            description,
                            labels,
                            properties_text,
                            actions_text
                        )
                    """)
                else:
                    raise
            
            # Populate with public entities
            cursor = await db.execute("""
                SELECT pe.name, pe.entity_set_name, pe.label_id,
                       GROUP_CONCAT(ep.name || ':' || COALESCE(ep.type_name, '')) as properties,
                       GROUP_CONCAT(ea.name) as actions
                FROM public_entities pe
                LEFT JOIN entity_properties ep ON pe.id = ep.entity_id
                LEFT JOIN entity_actions ea ON pe.id = ea.entity_id
                WHERE pe.version_id = ?
                GROUP BY pe.id, pe.name, pe.entity_set_name, pe.label_id
            """, (version_id,))
            
            async for entity in cursor:
                name, entity_set_name, label_id, properties, actions = entity
                await db.execute("""
                    INSERT INTO metadata_search(entity_name, entity_type, entity_set_name, 
                                              description, labels, properties_text, actions_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, 'public_entity', entity_set_name or "", label_id or "", 
                      label_id or "", properties or "", actions or ""))
            
            # Populate with data entities
            cursor = await db.execute("""
                SELECT name, public_collection_name, label_id, entity_category
                FROM data_entities
                WHERE version_id = ?
            """, (version_id,))
            
            async for entity in cursor:
                name, collection_name, label_id, category = entity
                description = f"{label_id or ''} {category or ''}".strip()
                await db.execute("""
                    INSERT INTO metadata_search(entity_name, entity_type, entity_set_name, 
                                              description, labels, properties_text, actions_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, 'data_entity', collection_name or "", description, 
                      label_id or "", "", ""))
            
            # Populate with enumerations
            cursor = await db.execute("""
                SELECT e.name, e.label_id,
                       GROUP_CONCAT(em.name || ':' || em.value) as members
                FROM enumerations e
                LEFT JOIN enumeration_members em ON e.id = em.enumeration_id
                WHERE e.version_id = ?
                GROUP BY e.id, e.name, e.label_id
            """, (version_id,))
            
            async for enum in cursor:
                name, label_id, members = enum
                await db.execute("""
                    INSERT INTO metadata_search(entity_name, entity_type, entity_set_name, 
                                              description, labels, properties_text, actions_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, 'enumeration', name, label_id or "", label_id or "", 
                      members or "", ""))
            
            await db.commit()
            logger.info("FTS5 search index populated successfully")
    
    async def rebuild_fts_index(self, environment_id: int):
        """Rebuild FTS5 search index for active version"""
        # Get active version
        version_info = await self.get_active_version(environment_id)
        if not version_info:
            logger.warning("No active metadata version found, cannot rebuild search index")
            return
        
        # Find the version ID
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id FROM metadata_versions WHERE environment_id = ? AND is_active = 1",
                (environment_id,)
            )
            row = await cursor.fetchone()
            if row:
                await self.populate_fts_index(row[0])
                logger.info("FTS5 search index rebuilt successfully")
            else:
                logger.warning("Could not find active version ID for FTS index rebuild")
    
    async def get_label(self, label_id: str, language: str = "en-US") -> Optional[LabelInfo]:
        """Get label from database
        
        Args:
            label_id: Label identifier
            language: Language code
            
        Returns:
            LabelInfo or None if not found or expired
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT label_id, language, value, cached_at, expires_at
                FROM labels_cache
                WHERE label_id = ? AND language = ? AND (expires_at IS NULL OR expires_at > ?)
            """, (label_id, language, datetime.now(timezone.utc).isoformat()))
            
            row = await cursor.fetchone()
            if row:
                label_id_db, language_db, value, cached_at, expires_at = row
                return LabelInfo(
                    id=label_id_db,
                    language=language_db,
                    value=value
                )
            return None
    
    async def set_label(self, label: LabelInfo, ttl_hours: int = 24):
        """Set label in database
        
        Args:
            label: LabelInfo object to store
            ttl_hours: Time to live in hours
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO labels_cache (label_id, language, value, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                label.id,
                label.language,
                label.value,
                datetime.now(timezone.utc).isoformat(),
                expires_at.isoformat()
            ))
            await db.commit()
    
    async def set_labels_batch(self, labels: List[LabelInfo], ttl_hours: int = 24):
        """Set multiple labels in database
        
        Args:
            labels: List of LabelInfo objects to store
            ttl_hours: Time to live in hours
        """
        if not labels:
            return
            
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        cached_at = datetime.now(timezone.utc).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            label_data = [
                (label.id, label.language, label.value, cached_at, expires_at.isoformat())
                for label in labels
            ]
            
            await db.executemany("""
                INSERT OR REPLACE INTO labels_cache (label_id, language, value, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, label_data)
            await db.commit()
    
    async def clear_expired_labels(self):
        """Clear expired labels from database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM labels_cache
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """, (datetime.now(timezone.utc).isoformat(),))
            await db.commit()
    
    async def get_labels_statistics(self) -> Dict[str, Any]:
        """Get label cache statistics
        
        Returns:
            Dictionary with label cache statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Total labels
            cursor = await db.execute("SELECT COUNT(*) FROM labels_cache")
            total_labels = (await cursor.fetchone())[0]
            
            # Expired labels
            cursor = await db.execute("""
                SELECT COUNT(*) FROM labels_cache
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """, (datetime.now(timezone.utc).isoformat(),))
            expired_labels = (await cursor.fetchone())[0]
            
            # Labels by language
            cursor = await db.execute("""
                SELECT language, COUNT(*) FROM labels_cache
                GROUP BY language
                ORDER BY COUNT(*) DESC
            """)
            languages = dict(await cursor.fetchall())
            
            return {
                "total_labels": total_labels,
                "expired_labels": expired_labels,
                "active_labels": total_labels - expired_labels,
                "languages": languages
            }

    async def get_statistics(self, environment_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics about database contents
        
        Args:
            environment_id: Optional environment ID to filter by
            
        Returns:
            Dictionary with table counts and metadata information
        """
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Basic table counts
            tables = [
                'metadata_environments',
                'metadata_versions', 
                'data_entities',
                'public_entities',
                'entity_properties',
                'navigation_properties',
                'relation_constraints',
                'property_groups',
                'property_group_members',
                'entity_actions',
                'action_parameters',
                'enumerations',
                'enumeration_members',
                'labels_cache'
            ]
            
            for table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                stats[f"{table}_count"] = count
            
            # FTS5 search index count (handle potential errors)
            try:
                cursor = await db.execute("SELECT COUNT(*) FROM metadata_search")
                count = (await cursor.fetchone())[0]
                stats["metadata_search_count"] = count
            except Exception as e:
                stats["metadata_search_count"] = f"Error: {str(e)}"
            
            # Environment-specific statistics
            if environment_id:
                # Active version info
                version_info = await self.get_active_version(environment_id)
                if version_info:
                    stats["active_version"] = {
                        "version_hash": version_info.version_hash,
                        "application_version": version_info.application_version,
                        "platform_version": version_info.platform_version,
                        "created_at": version_info.created_at.isoformat() if version_info.created_at else None
                    }
                    
                    # Get version-specific counts
                    cursor = await db.execute(
                        "SELECT id FROM metadata_versions WHERE environment_id = ? AND is_active = 1",
                        (environment_id,)
                    )
                    version_row = await cursor.fetchone()
                    
                    if version_row:
                        version_id = version_row[0]
                        
                        # Count entities for this version
                        cursor = await db.execute(
                            "SELECT COUNT(*) FROM data_entities WHERE version_id = ?",
                            (version_id,)
                        )
                        stats["active_version_data_entities"] = (await cursor.fetchone())[0]
                        
                        cursor = await db.execute(
                            "SELECT COUNT(*) FROM public_entities WHERE version_id = ?",
                            (version_id,)
                        )
                        stats["active_version_public_entities"] = (await cursor.fetchone())[0]
                        
                        cursor = await db.execute(
                            "SELECT COUNT(*) FROM enumerations WHERE version_id = ?",
                            (version_id,)
                        )
                        stats["active_version_enumerations"] = (await cursor.fetchone())[0]
                        
                        # Count properties for active version entities
                        cursor = await db.execute(
                            """SELECT COUNT(*) FROM entity_properties ep
                               JOIN public_entities pe ON ep.entity_id = pe.id
                               WHERE pe.version_id = ?""",
                            (version_id,)
                        )
                        stats["active_version_properties"] = (await cursor.fetchone())[0]
                        
                        # Count actions for active version entities
                        cursor = await db.execute(
                            """SELECT COUNT(*) FROM entity_actions ea
                               JOIN public_entities pe ON ea.entity_id = pe.id
                               WHERE pe.version_id = ?""",
                            (version_id,)
                        )
                        stats["active_version_actions"] = (await cursor.fetchone())[0]
                else:
                    stats["active_version"] = None
            
            # Database file size
            try:
                db_size = self.db_path.stat().st_size
                stats["database_size_bytes"] = db_size
                stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
            except Exception:
                stats["database_size_bytes"] = None
                stats["database_size_mb"] = None
            
            # Environment summary
            cursor = await db.execute(
                """SELECT me.base_url, me.environment_name, 
                          COUNT(mv.id) as version_count,
                          MAX(mv.created_at) as latest_version
                   FROM metadata_environments me
                   LEFT JOIN metadata_versions mv ON me.id = mv.environment_id
                   GROUP BY me.id, me.base_url, me.environment_name
                   ORDER BY me.id"""
            )
            
            environments = []
            async for row in cursor:
                env_info = {
                    "base_url": row[0],
                    "environment_name": row[1],
                    "version_count": row[2],
                    "latest_version": row[3]
                }
                environments.append(env_info)
            
            stats["environments"] = environments
            stats["total_environments"] = len(environments)
            
            # Add labels statistics
            labels_stats = await self.get_labels_statistics()
            stats.update(labels_stats)
            
            return stats


class MetadataCache:
    """Multi-tier metadata cache with SQLite backend"""
    
    def __init__(self, environment_url: str, cache_dir: Path, config: Optional[Dict[str, Any]] = None):
        """Initialize metadata cache
        
        Args:
            environment_url: D365 F&O environment URL
            cache_dir: Cache directory path
            config: Cache configuration options
        """
        self.environment_url = environment_url
        self.cache_dir = Path(cache_dir)
        self.config = config or {}
        
        # Initialize cache layers
        self._memory_cache = None
        self._disk_cache = None
        self._database = None
        self._environment_id: Optional[int] = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Configuration
        self.cache_ttl = self.config.get('cache_ttl_seconds', 300)
        self.max_memory_size = self.config.get('max_memory_cache_size', 1000)
        self.enable_fts = self.config.get('enable_fts_search', True)
        
        self._initialize_caches()
    
    def _initialize_caches(self):
        """Initialize cache layers"""
        # L1: Memory cache (TTL-based LRU)
        if TTLCache is not None:
            self._memory_cache = TTLCache(maxsize=self.max_memory_size, ttl=self.cache_ttl)
        else:
            logger.warning("cachetools not available, memory cache disabled")
        
        # L2: Disk cache (optional)
        if dc is not None:
            disk_cache_dir = self.cache_dir / "diskcache"
            self._disk_cache = dc.Cache(str(disk_cache_dir))
        else:
            logger.warning("diskcache not available, disk cache disabled")
        
        # L3: SQLite database
        db_path = self.cache_dir / "metadata.db"
        self._database = MetadataDatabase(db_path)
    
    async def initialize(self):
        """Initialize cache and database"""
        await self._database.initialize()
        self._environment_id = await self._database.get_or_create_environment(self.environment_url)
    
    def _build_cache_key(self, key_type: str, identifier: str, **kwargs) -> str:
        """Build cache key for lookups"""
        parts = [key_type, identifier]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return "|".join(parts)
    
    async def get_entity(self, entity_name: str, entity_type: str = "public") -> Optional[Union[DataEntityInfo, PublicEntityInfo]]:
        """Get entity from cache
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of entity ('data' or 'public')
            
        Returns:
            Entity information or None if not found
        """
        cache_key = self._build_cache_key("entity", entity_name, type=entity_type)
        
        # L1: Memory cache
        if self._memory_cache is not None:
            with self._lock:
                cached = self._memory_cache.get(cache_key)
                if cached is not None:
                    return cached
        
        # L2: Disk cache
        if self._disk_cache is not None:
            cached = self._disk_cache.get(cache_key)
            if cached is not None:
                if self._memory_cache is not None:
                    with self._lock:
                        self._memory_cache[cache_key] = cached
                return cached
        
        # L3: Database
        entity = await self._get_entity_from_db(entity_name, entity_type)
        if entity is not None:
            # Cache in upper layers
            if self._disk_cache is not None:
                self._disk_cache.set(cache_key, entity, expire=self.cache_ttl)
            if self._memory_cache is not None:
                with self._lock:
                    self._memory_cache[cache_key] = entity
        
        return entity
    
    async def _get_entity_from_db(self, entity_name: str, entity_type: str) -> Optional[Union[DataEntityInfo, PublicEntityInfo]]:
        """Get entity from database with full details"""
        if entity_type == "data":
            return await self._get_data_entity_from_db(entity_name)
        elif entity_type == "public":
            return await self._get_public_entity_from_db(entity_name)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    async def _get_data_entity_from_db(self, entity_name: str) -> Optional[DataEntityInfo]:
        """Get data entity from database"""
        async with aiosqlite.connect(self._database.db_path) as db:
            cursor = await db.execute(
                """SELECT name, public_entity_name, public_collection_name, label_id,
                          entity_category, data_service_enabled, data_management_enabled,
                          is_read_only
                   FROM data_entities de
                   JOIN metadata_versions mv ON de.version_id = mv.id
                   WHERE de.name = ? AND mv.environment_id = ? AND mv.is_active = 1""",
                (entity_name, self._environment_id)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return DataEntityInfo(
                name=row[0],
                public_entity_name=row[1] or "",
                public_collection_name=row[2] or "",
                label_id=row[3],
                entity_category=row[4],
                data_service_enabled=bool(row[5]),
                data_management_enabled=bool(row[6]),
                is_read_only=bool(row[7])
            )
    
    async def _get_public_entity_from_db(self, entity_name: str) -> Optional[PublicEntityInfo]:
        """Get public entity from database with full details"""
        async with aiosqlite.connect(self._database.db_path) as db:
            # Get entity base info
            cursor = await db.execute(
                """SELECT pe.id, pe.name, pe.entity_set_name, pe.label_id,
                          pe.is_read_only, pe.configuration_enabled
                   FROM public_entities pe
                   JOIN metadata_versions mv ON pe.version_id = mv.id
                   WHERE pe.name = ? AND mv.environment_id = ? AND mv.is_active = 1""",
                (entity_name, self._environment_id)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            entity_id, name, entity_set_name, label_id, is_read_only, configuration_enabled = row
            
            # Create entity info
            entity = PublicEntityInfo(
                name=name,
                entity_set_name=entity_set_name,
                label_id=label_id,
                is_read_only=bool(is_read_only),
                configuration_enabled=bool(configuration_enabled)
            )
            
            # Get properties
            entity.properties = await self._get_entity_properties(db, entity_id)
            
            # Get navigation properties
            entity.navigation_properties = await self._get_navigation_properties(db, entity_id)
            
            # Get property groups
            entity.property_groups = await self._get_property_groups(db, entity_id)
            
            # Get actions
            entity.actions = await self._get_entity_actions(db, entity_id)
            
            return entity
    
    async def _get_entity_properties(self, db: Any, entity_id: int) -> List[PublicEntityPropertyInfo]:
        """Get entity properties from database"""
        cursor = await db.execute(
            """SELECT name, type_name, data_type, odata_xpp_type, label_id,
                      is_key, is_mandatory, configuration_enabled, allow_edit,
                      allow_edit_on_create, is_dimension, dimension_relation,
                      is_dynamic_dimension, dimension_legal_entity_property,
                      dimension_type_property, property_order
               FROM entity_properties
               WHERE entity_id = ?
               ORDER BY property_order, name""",
            (entity_id,)
        )
        
        properties = []
        async for row in cursor:
            prop = PublicEntityPropertyInfo(
                name=row[0],
                type_name=row[1],
                data_type=row[2],
                odata_xpp_type=row[3],
                label_id=row[4],
                is_key=bool(row[5]),
                is_mandatory=bool(row[6]),
                configuration_enabled=bool(row[7]),
                allow_edit=bool(row[8]),
                allow_edit_on_create=bool(row[9]),
                is_dimension=bool(row[10]),
                dimension_relation=row[11],
                is_dynamic_dimension=bool(row[12]),
                dimension_legal_entity_property=row[13],
                dimension_type_property=row[14],
                property_order=row[15]
            )
            properties.append(prop)
        
        return properties
    
    async def _get_navigation_properties(self, db: Any, entity_id: int) -> List[NavigationPropertyInfo]:
        """Get navigation properties with constraints"""
        cursor = await db.execute(
            """SELECT np.id, np.name, np.related_entity, np.related_relation_name, np.cardinality
               FROM navigation_properties np
               WHERE np.entity_id = ?
               ORDER BY np.name""",
            (entity_id,)
        )
        
        nav_props = []
        async for row in cursor:
            nav_id, name, related_entity, related_relation_name, cardinality = row
            
            # Get constraints for this navigation property
            constraints = await self._get_relation_constraints(db, nav_id)
            
            nav_prop = NavigationPropertyInfo(
                name=name,
                related_entity=related_entity,
                related_relation_name=related_relation_name,
                cardinality=cardinality,
                constraints=constraints
            )
            nav_props.append(nav_prop)
        
        return nav_props
    
    async def _get_relation_constraints(self, db: Any, nav_prop_id: int) -> List[RelationConstraintInfo]:
        """Get relation constraints for navigation property"""
        cursor = await db.execute(
            """SELECT constraint_type, property_name, referenced_property,
                      fixed_value, fixed_value_str, related_property
               FROM relation_constraints
               WHERE navigation_property_id = ?""",
            (nav_prop_id,)
        )
        
        constraints = []
        async for row in cursor:
            constraint_type, prop_name, ref_prop, fixed_val, fixed_val_str, related_prop = row
            
            if constraint_type == "Referential":
                constraint = ReferentialConstraintInfo(
                    constraint_type="Referential",
                    property=prop_name,
                    referenced_property=ref_prop
                )
            elif constraint_type == "Fixed":
                constraint = FixedConstraintInfo(
                    constraint_type="Fixed",
                    property=prop_name,
                    value=fixed_val,
                    value_str=fixed_val_str
                )
            elif constraint_type == "RelatedFixed":
                constraint = RelatedFixedConstraintInfo(
                    constraint_type="RelatedFixed",
                    related_property=related_prop,
                    value=fixed_val,
                    value_str=fixed_val_str
                )
            else:
                # Base constraint type
                constraint = RelationConstraintInfo(constraint_type=constraint_type)
            
            constraints.append(constraint)
        
        return constraints
    
    async def _get_property_groups(self, db: Any, entity_id: int) -> List[PropertyGroupInfo]:
        """Get property groups for entity"""
        cursor = await db.execute(
            """SELECT pg.name, GROUP_CONCAT(pgm.property_name ORDER BY pgm.member_order) as properties
               FROM property_groups pg
               LEFT JOIN property_group_members pgm ON pg.id = pgm.group_id
               WHERE pg.entity_id = ?
               GROUP BY pg.id, pg.name
               ORDER BY pg.group_order, pg.name""",
            (entity_id,)
        )
        
        groups = []
        async for row in cursor:
            name, properties_str = row
            properties = properties_str.split(',') if properties_str else []
            
            group = PropertyGroupInfo(
                name=name,
                properties=properties
            )
            groups.append(group)
        
        return groups
    
    async def _get_entity_actions(self, db: Any, entity_id: int) -> List[ActionInfo]:
        """Get actions for entity"""
        # First get entity information
        entity_cursor = await db.execute(
            """SELECT pe.name, pe.entity_set_name
               FROM public_entities pe
               WHERE pe.id = ?""",
            (entity_id,)
        )
        entity_row = await entity_cursor.fetchone()
        entity_name = entity_row[0] if entity_row else None
        entity_set_name = entity_row[1] if entity_row else None
        
        cursor = await db.execute(
            """SELECT ea.id, ea.name, ea.binding_kind, ea.field_lookup,
                      ea.return_type_name, ea.return_is_collection, ea.return_odata_xpp_type
               FROM entity_actions ea
               WHERE ea.entity_id = ? OR ea.entity_id IS NULL
               ORDER BY ea.name""",
            (entity_id,)
        )
        
        actions = []
        async for row in cursor:
            action_id, name, binding_kind, field_lookup, return_type_name, return_is_collection, return_odata_xpp_type = row
            
            # Get action parameters
            parameters = await self._get_action_parameters(db, action_id)
            
            # Create return type if specified
            return_type = None
            if return_type_name:
                return_type = ActionTypeInfo(
                    type_name=return_type_name,
                    is_collection=bool(return_is_collection),
                    odata_xpp_type=return_odata_xpp_type
                )
            
            action = ActionInfo(
                name=name,
                binding_kind=binding_kind or "Unbound",
                entity_name=entity_name,
                entity_set_name=entity_set_name,
                parameters=parameters,
                return_type=return_type,
                field_lookup=field_lookup
            )
            actions.append(action)
        
        return actions
    
    async def _get_action_parameters(self, db: Any, action_id: int) -> List[ActionParameterInfo]:
        """Get parameters for action"""
        cursor = await db.execute(
            """SELECT name, type_name, is_collection, odata_xpp_type, parameter_order
               FROM action_parameters
               WHERE action_id = ?
               ORDER BY parameter_order, name""",
            (action_id,)
        )
        
        parameters = []
        async for row in cursor:
            name, type_name, is_collection, odata_xpp_type, parameter_order = row
            
            param_type = ActionTypeInfo(
                type_name=type_name,
                is_collection=bool(is_collection),
                odata_xpp_type=odata_xpp_type
            )
            
            param = ActionParameterInfo(
                name=name,
                type=param_type,
                parameter_order=parameter_order
            )
            parameters.append(param)
        
        return parameters
    
    async def get_label(self, label_id: str, language: str = "en-US") -> Optional[str]:
        """Get label text from cache
        
        Args:
            label_id: Label identifier
            language: Language code
            
        Returns:
            Label text or None if not found
        """
        if self._environment_id is None:
            await self.initialize()
        
        cache_key = self._build_cache_key("label", label_id, language=language)
        
        # L1: Memory cache
        if self._memory_cache:
            with self._lock:
                cached_value = self._memory_cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Label cache hit (memory): {label_id} ({language})")
                    return cached_value
        
        # L2: Disk cache (optional)
        if self._disk_cache:
            try:
                with self._lock:
                    cached_value = self._disk_cache.get(cache_key)
                    if cached_value is not None:
                        logger.debug(f"Label cache hit (disk): {label_id} ({language})")
                        # Store in memory cache
                        if self._memory_cache:
                            self._memory_cache[cache_key] = cached_value
                        return cached_value
            except Exception as e:
                logger.warning(f"Disk cache error for label {label_id}: {e}")
        
        # L3: Database
        label_info = await self._database.get_label(label_id, language)
        if label_info:
            logger.debug(f"Label cache hit (database): {label_id} ({language})")
            # Store in upper cache levels
            with self._lock:
                if self._memory_cache:
                    self._memory_cache[cache_key] = label_info.value
                if self._disk_cache:
                    try:
                        self._disk_cache[cache_key] = label_info.value
                    except Exception as e:
                        logger.warning(f"Failed to store label in disk cache: {e}")
            return label_info.value
        
        logger.debug(f"Label cache miss: {label_id} ({language})")
        return None
    
    async def set_label(self, label: LabelInfo, ttl_hours: int = 24):
        """Set label in cache
        
        Args:
            label: LabelInfo object to store
            ttl_hours: Time to live in hours
        """
        if self._environment_id is None:
            await self.initialize()
        
        cache_key = self._build_cache_key("label", label.id, language=label.language)
        
        # Store in all cache levels
        with self._lock:
            # L1: Memory cache
            if self._memory_cache:
                self._memory_cache[cache_key] = label.value
            
            # L2: Disk cache
            if self._disk_cache:
                try:
                    self._disk_cache[cache_key] = label.value
                except Exception as e:
                    logger.warning(f"Failed to store label in disk cache: {e}")
        
        # L3: Database
        await self._database.set_label(label, ttl_hours)
        
        logger.debug(f"Label cached: {label.id} ({label.language})")
    
    async def set_labels_batch(self, labels: List[LabelInfo], ttl_hours: int = 24):
        """Set multiple labels in cache
        
        Args:
            labels: List of LabelInfo objects to store
            ttl_hours: Time to live in hours
        """
        if not labels:
            return
            
        if self._environment_id is None:
            await self.initialize()
        
        # Store in all cache levels
        with self._lock:
            for label in labels:
                cache_key = self._build_cache_key("label", label.id, language=label.language)
                
                # L1: Memory cache
                if self._memory_cache:
                    self._memory_cache[cache_key] = label.value
                
                # L2: Disk cache
                if self._disk_cache:
                    try:
                        self._disk_cache[cache_key] = label.value
                    except Exception as e:
                        logger.warning(f"Failed to store label in disk cache: {e}")
        
        # L3: Database (batch operation)
        await self._database.set_labels_batch(labels, ttl_hours)
        
        logger.debug(f"Batch cached {len(labels)} labels")
    
    async def clear_expired_labels(self):
        """Clear expired labels from all cache levels"""
        if self._environment_id is None:
            await self.initialize()
        
        # Clear from database
        await self._database.clear_expired_labels()
        
        # For memory and disk cache, we rely on their built-in TTL mechanisms
        # Memory cache (TTLCache) automatically removes expired items
        # Disk cache (diskcache) also has TTL support
        
        logger.debug("Expired labels cleared")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get metadata cache statistics
        
        Returns:
            Dictionary with cache statistics and database information
        """
        if self._environment_id is None:
            await self.initialize()
        
        return await self._database.get_statistics(self._environment_id)
    
    # Data Entity Methods
    
    async def search_data_entities(self, pattern: str = "", entity_category: Optional[str] = None,
                                  data_service_enabled: Optional[bool] = None,
                                  data_management_enabled: Optional[bool] = None,
                                  is_read_only: Optional[bool] = None) -> List[DataEntityInfo]:
        """Search data entities with filtering and caching
        
        Args:
            pattern: Search pattern for entity name (regex supported)
            entity_category: Filter by entity category (e.g., 'Master', 'Transaction')
            data_service_enabled: Filter by data service enabled status
            data_management_enabled: Filter by data management enabled status
            is_read_only: Filter by read-only status
            
        Returns:
            List of matching data entities
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Build cache key for search
        key_parts = ["data_entities_search", pattern or ""]
        if entity_category is not None:
            key_parts.append(f"category:{entity_category}")
        if data_service_enabled is not None:
            key_parts.append(f"ds_enabled:{data_service_enabled}")
        if data_management_enabled is not None:
            key_parts.append(f"dm_enabled:{data_management_enabled}")
        if is_read_only is not None:
            key_parts.append(f"readonly:{is_read_only}")
        
        cache_key = "|".join(key_parts)
        
        # L1: Memory cache (if available)
        if self._memory_cache:
            entities = self._memory_cache.get(cache_key)
            if entities is not None:
                logger.debug(f"Memory cache hit for data entities search: {pattern}")
                return entities
        
        # L2: Disk cache (if available)
        if self._disk_cache:
            try:
                entities = self._disk_cache.get(cache_key)
                if entities is not None:
                    logger.debug(f"Disk cache hit for data entities search: {pattern}")
                    # Store in memory cache
                    if self._memory_cache:
                        self._memory_cache[cache_key] = entities
                    return entities
            except Exception as e:
                logger.warning(f"Disk cache error for data entities search: {e}")
        
        # L3: Database
        entities = await self._search_data_entities_from_db(
            pattern, entity_category, data_service_enabled,
            data_management_enabled, is_read_only
        )
        
        # Cache results
        if self._memory_cache:
            self._memory_cache[cache_key] = entities
        if self._disk_cache:
            try:
                self._disk_cache.set(cache_key, entities, expire=3600)  # 1 hour TTL
            except Exception as e:
                logger.warning(f"Failed to cache data entities search to disk: {e}")
        
        logger.debug(f"Database lookup for data entities search: {pattern}, found {len(entities)} entities")
        
        return entities
    
    async def _search_data_entities_from_db(self, pattern: str = "", entity_category: Optional[str] = None,
                                           data_service_enabled: Optional[bool] = None,
                                           data_management_enabled: Optional[bool] = None,
                                           is_read_only: Optional[bool] = None) -> List[DataEntityInfo]:
        """Search data entities from database with filtering"""
        if aiosqlite is None:
            return []
        
        # Build WHERE clause
        where_conditions = ["mv.environment_id = ?", "mv.is_active = 1"]
        params = [self._environment_id]
        
        if pattern:
            # Use LIKE for simple pattern matching
            where_conditions.append("LOWER(de.name) LIKE LOWER(?)")
            params.append(f"%{pattern}%")
        
        if entity_category is not None:
            where_conditions.append("de.entity_category = ?")
            params.append(entity_category)
        
        if data_service_enabled is not None:
            where_conditions.append("de.data_service_enabled = ?")
            params.append(1 if data_service_enabled else 0)
        
        if data_management_enabled is not None:
            where_conditions.append("de.data_management_enabled = ?")
            params.append(1 if data_management_enabled else 0)
        
        if is_read_only is not None:
            where_conditions.append("de.is_read_only = ?")
            params.append(1 if is_read_only else 0)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT de.name, de.public_entity_name, de.public_collection_name, 
                   de.label_id, de.entity_category, de.data_service_enabled,
                   de.data_management_enabled, de.is_read_only
            FROM data_entities de
            JOIN metadata_versions mv ON de.version_id = mv.id
            WHERE {where_clause}
            ORDER BY de.name
        """
        
        async with aiosqlite.connect(self._database.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
        
        entities = []
        for row in rows:
            
            entity = DataEntityInfo(
                name=row[0],
                public_entity_name=row[1] or "",
                public_collection_name=row[2] or "",
                label_id=row[3],

                entity_category=row[4],
                data_service_enabled=bool(row[5]),
                data_management_enabled=bool(row[6]),
                is_read_only=bool(row[7])
            )
            
            entities.append(entity)
        
        # Apply regex pattern if provided and contains regex characters
        if pattern and re.search(r'[.*+?^${}()|[\]\\]', pattern):
            try:
                flags = re.IGNORECASE
                entities = [e for e in entities if re.search(pattern, e.name, flags)]
            except re.error:
                # If regex is invalid, fall back to simple substring matching
                logger.warning(f"Invalid regex pattern '{pattern}', using substring matching")
        
        return entities
    
    async def get_data_entity_info(self, entity_name: str, resolve_labels: bool = True,
                                  language: str = "en-US") -> Optional[DataEntityInfo]:
        """Get detailed data entity information with label resolution
        
        Args:
            entity_name: Name of the data entity
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            
        Returns:
            DataEntityInfo object or None if not found
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Get entity from cache/database
        entity = await self.get_entity(entity_name, "data")
        if not entity or not isinstance(entity, DataEntityInfo):
            return None
        
        # Resolve labels if requested
        if resolve_labels and entity.label_id:
            label_text = await self.get_label(entity.label_id, language)
            if label_text:
                entity.label_text = label_text
        
        return entity

    # Public Entity Methods
    
    async def search_public_entities(self, pattern: str = "", is_read_only: Optional[bool] = None,
                                   configuration_enabled: Optional[bool] = None) -> List[PublicEntityInfo]:
        """Search public entities with filtering and caching
        
        Args:
            pattern: Search pattern for entity name (regex supported)
            is_read_only: Filter by read-only status
            configuration_enabled: Filter by configuration enabled status
            
        Returns:
            List of matching public entities
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Build cache key for search
        key_parts = ["public_entities_search", pattern or ""]
        if is_read_only is not None:
            key_parts.append(f"readonly:{is_read_only}")
        if configuration_enabled is not None:
            key_parts.append(f"config_enabled:{configuration_enabled}")
        
        cache_key = "|".join(key_parts)
        
        # L1: Memory cache (if available)
        if self._memory_cache:
            entities = self._memory_cache.get(cache_key)
            if entities is not None:
                logger.debug(f"Memory cache hit for public entities search: {pattern}")
                return entities
        
        # L2: Disk cache (if available)
        if self._disk_cache:
            try:
                entities = self._disk_cache.get(cache_key)
                if entities is not None:
                    logger.debug(f"Disk cache hit for public entities search: {pattern}")
                    # Store in memory cache
                    if self._memory_cache:
                        self._memory_cache[cache_key] = entities
                    return entities
            except Exception as e:
                logger.warning(f"Disk cache error for public entities search: {e}")
        
        # L3: Database
        entities = await self._search_public_entities_from_db(
            pattern, is_read_only, configuration_enabled
        )
        
        # Cache results
        if self._memory_cache:
            self._memory_cache[cache_key] = entities
        if self._disk_cache:
            try:
                self._disk_cache.set(cache_key, entities, expire=3600)  # 1 hour TTL
            except Exception as e:
                logger.warning(f"Failed to cache public entities search to disk: {e}")
        
        logger.debug(f"Database lookup for public entities search: {pattern}, found {len(entities)} entities")
        return entities
    
    async def _search_public_entities_from_db(self, pattern: str = "", is_read_only: Optional[bool] = None,
                                            configuration_enabled: Optional[bool] = None) -> List[PublicEntityInfo]:
        """Search public entities from database with filtering"""
        if aiosqlite is None:
            return []
        
        # Build WHERE clause
        where_conditions = ["mv.environment_id = ?", "mv.is_active = 1"]
        params = [self._environment_id]
        
        if pattern:
            # Use LIKE for simple pattern matching
            where_conditions.append("LOWER(pe.name) LIKE LOWER(?)")
            params.append(f"%{pattern}%")
        
        if is_read_only is not None:
            where_conditions.append("pe.is_read_only = ?")
            params.append(1 if is_read_only else 0)
        
        if configuration_enabled is not None:
            where_conditions.append("pe.configuration_enabled = ?")
            params.append(1 if configuration_enabled else 0)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT pe.name, pe.entity_set_name, pe.label_id, 
                   pe.is_read_only, pe.configuration_enabled
            FROM public_entities pe
            JOIN metadata_versions mv ON pe.version_id = mv.id
            WHERE {where_clause}
            ORDER BY pe.name
        """
        
        async with aiosqlite.connect(self._database.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
        
        entities = []
        for row in rows:
            entity = PublicEntityInfo(
                name=row[0],
                entity_set_name=row[1] or "",
                label_id=row[2],
                is_read_only=bool(row[3]),
                configuration_enabled=bool(row[4])
            )
            entities.append(entity)
        
        # Apply regex pattern if provided and contains regex characters
        if pattern and re.search(r'[.*+?^${}()|[\]\\]', pattern):
            try:
                flags = re.IGNORECASE
                entities = [e for e in entities if re.search(pattern, e.name, flags)]
            except re.error:
                # If regex is invalid, fall back to simple substring matching
                logger.warning(f"Invalid regex pattern '{pattern}', using substring matching")
        
        return entities
    
    async def get_public_entity_info(self, entity_name: str, resolve_labels: bool = True,
                                   language: str = "en-US") -> Optional[PublicEntityInfo]:
        """Get detailed public entity information with label resolution
        
        Args:
            entity_name: Name of the public entity
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            
        Returns:
            PublicEntityInfo object or None if not found
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Get entity from cache/database (this already includes full details)
        entity = await self.get_entity(entity_name, "public")
        if not entity or not isinstance(entity, PublicEntityInfo):
            return None
        
        # Resolve labels if requested
        if resolve_labels:
            await self._resolve_public_entity_labels(entity, language)
        
        return entity
    
    async def _resolve_public_entity_labels(self, entity: PublicEntityInfo, language: str) -> None:
        """Resolve labels for a public entity and its properties"""
        # Collect all label IDs
        label_ids = []
        
        if entity.label_id:
            label_ids.append(entity.label_id)
        
        for prop in entity.properties:
            if prop.label_id:
                label_ids.append(prop.label_id)
        
        # Resolve labels in batch if any label IDs found
        if label_ids:
            # Remove duplicates while preserving order
            unique_label_ids = list(dict.fromkeys(label_ids))
            
            # Get labels from cache
            label_texts = {}
            for label_id in unique_label_ids:
                label_text = await self.get_label(label_id, language)
                if label_text:
                    label_texts[label_id] = label_text
            
            # Apply resolved labels
            if entity.label_id and entity.label_id in label_texts:
                entity.label_text = label_texts[entity.label_id]
            
            for prop in entity.properties:
                if prop.label_id and prop.label_id in label_texts:
                    prop.label_text = label_texts[prop.label_id]

    # Enumeration Methods
    
    async def search_public_enumerations(self, pattern: str = "") -> List[EnumerationInfo]:
        """Search public enumerations with filtering and caching
        
        Args:
            pattern: Search pattern for enumeration name (regex supported)
            
        Returns:
            List of matching enumerations
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Build cache key for search
        cache_key = f"public_enumerations_search|{pattern or ''}"
        
        # L1: Memory cache (if available)
        if self._memory_cache:
            enumerations = self._memory_cache.get(cache_key)
            if enumerations is not None:
                logger.debug(f"Memory cache hit for public enumerations search: {pattern}")
                return enumerations
        
        # L2: Disk cache (if available)
        if self._disk_cache:
            try:
                enumerations = self._disk_cache.get(cache_key)
                if enumerations is not None:
                    logger.debug(f"Disk cache hit for public enumerations search: {pattern}")
                    # Store in memory cache
                    if self._memory_cache:
                        self._memory_cache[cache_key] = enumerations
                    return enumerations
            except Exception as e:
                logger.warning(f"Disk cache error for public enumerations search: {e}")
        
        # L3: Database
        enumerations = await self._search_public_enumerations_from_db(pattern)
        
        # Cache results
        if self._memory_cache:
            self._memory_cache[cache_key] = enumerations
        if self._disk_cache:
            try:
                self._disk_cache.set(cache_key, enumerations, expire=3600)  # 1 hour TTL
            except Exception as e:
                logger.warning(f"Failed to cache public enumerations search to disk: {e}")
        
        logger.debug(f"Database lookup for public enumerations search: {pattern}, found {len(enumerations)} enumerations")
        return enumerations
    
    async def _search_public_enumerations_from_db(self, pattern: str = "") -> List[EnumerationInfo]:
        """Search public enumerations from database with filtering"""
        if aiosqlite is None:
            return []
        
        # Build WHERE clause
        where_conditions = ["mv.environment_id = ?", "mv.is_active = 1"]
        params = [self._environment_id]
        
        if pattern:
            # Use LIKE for simple pattern matching
            where_conditions.append("LOWER(e.name) LIKE LOWER(?)")
            params.append(f"%{pattern}%")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT e.name, e.label_id
            FROM enumerations e
            JOIN metadata_versions mv ON e.version_id = mv.id
            WHERE {where_clause}
            ORDER BY e.name
        """
        
        async with aiosqlite.connect(self._database.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
        
        enumerations = []
        for row in rows:
            enum = EnumerationInfo(
                name=row[0],
                label_id=row[1]
            )
            enumerations.append(enum)
        
        # Apply regex pattern if provided and contains regex characters
        if pattern and re.search(r'[.*+?^${}()|[\]\\]', pattern):
            try:
                flags = re.IGNORECASE
                enumerations = [e for e in enumerations if re.search(pattern, e.name, flags)]
            except re.error:
                # If regex is invalid, fall back to simple substring matching
                logger.warning(f"Invalid regex pattern '{pattern}', using substring matching")
        
        return enumerations
    
    async def get_public_enumeration_info(self, enumeration_name: str, resolve_labels: bool = True,
                                        language: str = "en-US") -> Optional[EnumerationInfo]:
        """Get detailed enumeration information with label resolution
        
        Args:
            enumeration_name: Name of the enumeration
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution
            
        Returns:
            EnumerationInfo object or None if not found
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Get enumeration from database with full details including members
        enum = await self._get_enumeration_from_db(enumeration_name)
        if not enum:
            return None
        
        # Resolve labels if requested
        if resolve_labels:
            await self._resolve_enumeration_labels(enum, language)
        
        return enum
    
    async def _get_enumeration_from_db(self, enumeration_name: str) -> Optional[EnumerationInfo]:
        """Get enumeration from database with full details"""
        if aiosqlite is None:
            return None
        
        async with aiosqlite.connect(self._database.db_path) as db:
            # Get enumeration base info
            cursor = await db.execute(
                """SELECT e.id, e.name, e.label_id
                   FROM enumerations e
                   JOIN metadata_versions mv ON e.version_id = mv.id
                   WHERE e.name = ? AND mv.environment_id = ? AND mv.is_active = 1""",
                (enumeration_name, self._environment_id)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            enum_id, name, label_id = row
            
            # Create enumeration info
            enum = EnumerationInfo(
                name=name,
                label_id=label_id
            )
            
            # Get enumeration members
            cursor = await db.execute(
                """SELECT name, value, label_id, configuration_enabled
                   FROM enumeration_members
                   WHERE enumeration_id = ?
                   ORDER BY member_order, name""",
                (enum_id,)
            )
            member_rows = await cursor.fetchall()
            
            for member_row in member_rows:
                member = EnumerationMemberInfo(
                    name=member_row[0],
                    value=member_row[1],
                    label_id=member_row[2],
                    configuration_enabled=bool(member_row[3])
                )
                enum.members.append(member)
            
            return enum
    
    async def _resolve_enumeration_labels(self, enum: EnumerationInfo, language: str) -> None:
        """Resolve labels for an enumeration and its members"""
        # Collect all label IDs
        label_ids = []
        
        if enum.label_id:
            label_ids.append(enum.label_id)
        
        for member in enum.members:
            if member.label_id:
                label_ids.append(member.label_id)
        
        # Resolve labels in batch if any label IDs found
        if label_ids:
            # Remove duplicates while preserving order
            unique_label_ids = list(dict.fromkeys(label_ids))
            
            # Get labels from cache
            label_texts = {}
            for label_id in unique_label_ids:
                label_text = await self.get_label(label_id, language)
                if label_text:
                    label_texts[label_id] = label_text
            
            # Apply resolved labels
            if enum.label_id and enum.label_id in label_texts:
                enum.label_text = label_texts[enum.label_id]
            
            for member in enum.members:
                if member.label_id and member.label_id in label_texts:
                    member.label_text = label_texts[member.label_id]

    # Action Methods
    
    async def search_actions(self, pattern: str = "", entity_name: Optional[str] = None,
                           binding_kind: Optional[str] = None, is_function: Optional[bool] = None) -> List[ActionInfo]:
        """Search actions with filtering and caching
        
        Args:
            pattern: Search pattern for action name (regex supported)
            entity_name: Filter actions that are bound to a specific entity
            binding_kind: Filter by binding type (Unbound, BoundToEntitySet, BoundToEntityInstance)
            is_function: Filter by function type (if supported in future)
            
        Returns:
            List of matching actions with full details
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Build cache key for search
        key_parts = ["actions_search", pattern or ""]
        if entity_name:
            key_parts.append(f"entity:{entity_name}")
        if binding_kind:
            key_parts.append(f"binding:{binding_kind}")
        if is_function is not None:
            key_parts.append(f"function:{is_function}")
        
        cache_key = "|".join(key_parts)
        
        # L1: Memory cache (if available)
        if self._memory_cache:
            actions = self._memory_cache.get(cache_key)
            if actions is not None:
                logger.debug(f"Memory cache hit for actions search: {pattern}")
                return actions
        
        # L2: Disk cache (if available)
        if self._disk_cache:
            try:
                actions = self._disk_cache.get(cache_key, default=None)
                if actions is not None:
                    logger.debug(f"Disk cache hit for actions search: {pattern}")
                    # Store in memory cache for faster access
                    if self._memory_cache:
                        self._memory_cache[cache_key] = actions
                    return actions
            except Exception as e:
                logger.warning(f"Disk cache error for actions search: {e}")
        
        # L3: Database
        actions = await self._search_actions_from_db(pattern, entity_name, binding_kind, is_function)
        
        # Cache results
        if self._memory_cache:
            self._memory_cache[cache_key] = actions
        if self._disk_cache:
            try:
                self._disk_cache.set(cache_key, actions, expire=self._cache_ttl_seconds)
            except Exception as e:
                logger.warning(f"Failed to cache actions search results: {e}")
        
        logger.debug(f"Database lookup for actions search: {pattern}, found {len(actions)} actions")
        return actions
    
    async def _search_actions_from_db(self, pattern: str = "", entity_name: Optional[str] = None,
                                    binding_kind: Optional[str] = None, is_function: Optional[bool] = None) -> List[ActionInfo]:
        """Search actions from database with filtering"""
        if aiosqlite is None:
            raise MetadataError("aiosqlite not available for database operations")
        
        # Build WHERE clause - start with conditions that apply to all actions
        where_conditions = []
        params = []
        
        # For bound actions, check the version info through public entities
        # For unbound actions (entity_id IS NULL), we need a different approach
        bound_where_conditions = ["mv.environment_id = ?", "mv.is_active = 1"]
        bound_params = [self._environment_id]
        
        if pattern:
            bound_where_conditions.append("ea.name LIKE ?")
            bound_params.append(f"%{pattern}%")
        
        if entity_name:
            bound_where_conditions.append("pe.name = ?")
            bound_params.append(entity_name)
        
        if binding_kind:
            bound_where_conditions.append("ea.binding_kind = ?")
            bound_params.append(binding_kind)
        
        bound_where_clause = " AND ".join(bound_where_conditions)
        
        # Query for bound actions (have entity_id)
        bound_query = f"""
            SELECT ea.id, ea.name, ea.binding_kind, ea.field_lookup,
                   ea.return_type_name, ea.return_is_collection, ea.return_odata_xpp_type,
                   pe.name as entity_name, pe.entity_set_name
            FROM entity_actions ea
            LEFT JOIN public_entities pe ON ea.entity_id = pe.id   
            LEFT JOIN metadata_versions mv ON pe.version_id = mv.id
            WHERE ea.entity_id IS NOT NULL AND {bound_where_clause}
        """
        
        # Query for unbound actions (entity_id IS NULL)
        unbound_where_conditions = []
        unbound_params = []
        
        if pattern:
            unbound_where_conditions.append("ea.name LIKE ?")
            unbound_params.append(f"%{pattern}%")
        
        if binding_kind:
            unbound_where_conditions.append("ea.binding_kind = ?")
            unbound_params.append(binding_kind)
        
        # For unbound actions, we only include them if entity_name is not specified
        # (since unbound actions are not tied to specific entities)
        if not entity_name:
            unbound_where_clause = " AND ".join(unbound_where_conditions) if unbound_where_conditions else "1=1"
            unbound_query = f"""
                SELECT ea.id, ea.name, ea.binding_kind, ea.field_lookup,
                       ea.return_type_name, ea.return_is_collection, ea.return_odata_xpp_type,
                       NULL as entity_name, NULL as entity_set_name
                FROM entity_actions ea
                WHERE ea.entity_id IS NULL AND {unbound_where_clause}
            """
            
            # Combine both queries
            query = f"""
                {bound_query}
                UNION ALL
                {unbound_query}
                ORDER BY name
            """
            params = bound_params + unbound_params
        else:
            # If entity_name is specified, only search bound actions
            query = f"{bound_query} ORDER BY ea.name"
            params = bound_params
        
        async with aiosqlite.connect(self._database.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            actions = []
            for row in rows:
                action_id, name, binding_kind_val, field_lookup, return_type_name, return_is_collection, return_odata_xpp_type, entity_name_val, entity_set_name = row
                
                # Get action parameters
                parameters = await self._get_action_parameters_for_search(db, action_id)
                
                # Create return type if specified
                return_type = None
                if return_type_name:
                    return_type = ActionTypeInfo(
                        type_name=return_type_name,
                        is_collection=bool(return_is_collection),
                        odata_xpp_type=return_odata_xpp_type
                    )
                
                action = ActionInfo(
                    name=name,
                    binding_kind=binding_kind_val or "Unbound",
                    entity_name=entity_name_val,
                    entity_set_name=entity_set_name,
                    parameters=parameters,
                    return_type=return_type,
                    field_lookup=field_lookup
                )
                actions.append(action)
        
        # Apply regex pattern if provided and contains regex characters
        if pattern and re.search(r'[.*+?^${}()|[\]\\]', pattern):
            try:
                regex_pattern = re.compile(pattern, re.IGNORECASE)
                actions = [action for action in actions if regex_pattern.search(action.name)]
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
        
        return actions
    
    async def _get_action_parameters_for_search(self, db: Any, action_id: int) -> List[ActionParameterInfo]:
        """Get parameters for action during search (optimized for batch operations)"""
        cursor = await db.execute(
            """SELECT name, type_name, is_collection, odata_xpp_type, parameter_order
               FROM action_parameters
               WHERE action_id = ?
               ORDER BY parameter_order, name""",
            (action_id,)
        )
        
        parameters = []
        async for row in cursor:
            name, type_name, is_collection, odata_xpp_type, parameter_order = row
            
            # Create action type
            action_type = ActionTypeInfo(
                type_name=type_name,
                is_collection=bool(is_collection),
                odata_xpp_type=odata_xpp_type
            )
            
            parameter = ActionParameterInfo(
                name=name,
                type=action_type,
                parameter_order=parameter_order
            )
            parameters.append(parameter)
        
        return parameters
    
    async def get_action_info(self, action_name: str, entity_name: Optional[str] = None) -> Optional[ActionInfo]:
        """Get detailed action information
        
        Args:
            action_name: Name of the action
            entity_name: Optional entity name for bound actions
            
        Returns:
            ActionInfo object or None if not found
        """
        if self._environment_id is None:
            await self.initialize()
        
        # Build cache key
        cache_key = f"action_info|{action_name}"
        if entity_name:
            cache_key += f"|{entity_name}"
        
        # L1: Memory cache (if available)
        if self._memory_cache:
            action = self._memory_cache.get(cache_key)
            if action is not None:
                return action
        
        # L2: Disk cache (if available)
        if self._disk_cache:
            try:
                action = self._disk_cache.get(cache_key, default=None)
                if action is not None:
                    if self._memory_cache:
                        self._memory_cache[cache_key] = action
                    return action
            except Exception as e:
                logger.warning(f"Disk cache error for action info: {e}")
        
        # L3: Database
        action = await self._get_action_from_db(action_name, entity_name)
        
        # Cache result
        if self._memory_cache:
            self._memory_cache[cache_key] = action
        if self._disk_cache and action:
            try:
                self._disk_cache.set(cache_key, action, expire=self._cache_ttl_seconds)
            except Exception as e:
                logger.warning(f"Failed to cache action info: {e}")
        
        return action
    
    async def _get_action_from_db(self, action_name: str, entity_name: Optional[str] = None) -> Optional[ActionInfo]:
        """Get action from database"""
        if aiosqlite is None:
            raise MetadataError("aiosqlite not available for database operations")
        
        # Try bound actions first (actions with entity_id)
        bound_where_conditions = ["mv.environment_id = ?", "mv.is_active = 1", "ea.name = ?"]
        bound_params = [self._environment_id, action_name]
        
        if entity_name:
            bound_where_conditions.append("pe.name = ?")
            bound_params.append(entity_name)
        
        bound_where_clause = " AND ".join(bound_where_conditions)
        
        bound_query = f"""
            SELECT ea.id, ea.name, ea.binding_kind, ea.field_lookup,
                   ea.return_type_name, ea.return_is_collection, ea.return_odata_xpp_type,
                   pe.name as entity_name, pe.entity_set_name
            FROM entity_actions ea
            LEFT JOIN public_entities pe ON ea.entity_id = pe.id   
            LEFT JOIN metadata_versions mv ON pe.version_id = mv.id
            WHERE ea.entity_id IS NOT NULL AND {bound_where_clause}
            LIMIT 1
        """
        
        async with aiosqlite.connect(self._database.db_path) as db:
            cursor = await db.execute(bound_query, bound_params)
            row = await cursor.fetchone()
            
            # If no bound action found and no specific entity requested, try unbound actions
            if not row and not entity_name:
                unbound_query = """
                    SELECT ea.id, ea.name, ea.binding_kind, ea.field_lookup,
                           ea.return_type_name, ea.return_is_collection, ea.return_odata_xpp_type,
                           NULL as entity_name, NULL as entity_set_name
                    FROM entity_actions ea
                    WHERE ea.entity_id IS NULL AND ea.name = ?
                    LIMIT 1
                """
                cursor = await db.execute(unbound_query, [action_name])
                row = await cursor.fetchone()
            
            if not row:
                return None
            
            action_id, name, binding_kind_val, field_lookup, return_type_name, return_is_collection, return_odata_xpp_type, entity_name_val, entity_set_name = row
            
            # Get action parameters
            parameters = await self._get_action_parameters_for_search(db, action_id)
            
            # Create return type if specified
            return_type = None
            if return_type_name:
                return_type = ActionTypeInfo(
                    type_name=return_type_name,
                    is_collection=bool(return_is_collection),
                    odata_xpp_type=return_odata_xpp_type
                )
            
            return ActionInfo(
                name=name,
                binding_kind=binding_kind_val or "Unbound",
                entity_name=entity_name_val,
                entity_set_name=entity_set_name,
                parameters=parameters,
                return_type=return_type,
                field_lookup=field_lookup
            )


class MetadataSearchEngine:
    """Advanced metadata search with SQLite FTS5"""
    
    def __init__(self, metadata_cache: MetadataCache):
        """Initialize search engine
        
        Args:
            metadata_cache: Metadata cache instance
        """
        self.cache = metadata_cache
        self._search_cache = {}
        self._search_cache_lock = threading.RLock()
    
    async def rebuild_search_index(self):
        """Rebuild the FTS5 search index from current metadata"""
        if self.cache._environment_id is None:
            await self.cache.initialize()
        
        # Delegate to database layer
        await self.cache._database.rebuild_fts_index(self.cache._environment_id)
    
    async def search(self, query: SearchQuery) -> SearchResults:
        """Execute metadata search
        
        Args:
            query: Search query parameters
            
        Returns:
            Search results
        """
        start_time = time.time()
        
        # Build cache key
        cache_key = self._build_search_cache_key(query)
        
        # Check cache
        with self._search_cache_lock:
            cached = self._search_cache.get(cache_key)
            if cached and time.time() - cached['timestamp'] < 300:  # 5 minute cache
                cached['results'].cache_hit = True
                cached['results'].query_time_ms = (time.time() - start_time) * 1000
                return cached['results']
        
        # Execute search
        if query.use_fulltext and self.cache.enable_fts:
            results = await self._fts_search(query)
        else:
            results = await self._pattern_search(query)
        
        # Calculate timing
        results.query_time_ms = (time.time() - start_time) * 1000
        results.cache_hit = False
        
        # Cache results
        with self._search_cache_lock:
            self._search_cache[cache_key] = {
                'results': results,
                'timestamp': time.time()
            }
            
            # Limit cache size
            if len(self._search_cache) > 100:
                oldest_key = min(self._search_cache.keys(), 
                               key=lambda k: self._search_cache[k]['timestamp'])
                del self._search_cache[oldest_key]
        
        return results
    
    def _build_search_cache_key(self, query: SearchQuery) -> str:
        """Build cache key for search query"""
        key_parts = [
            query.text,
            "|".join(query.entity_types or []),
            str(query.limit),
            str(query.offset),
            str(query.use_fulltext),
            str(query.include_properties),
            str(query.include_actions)
        ]
        
        if query.filters:
            for k, v in sorted(query.filters.items()):
                key_parts.append(f"{k}:{v}")
        
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    async def _fts_search(self, query: SearchQuery) -> SearchResults:
        """Full-text search using FTS5"""
        search_query = self._build_fts_query(query.text)
        
        async with aiosqlite.connect(self.cache._database.db_path) as db:
            sql = """
                SELECT entity_name, entity_type, entity_set_name, description,
                       bm25(metadata_search) as relevance,
                       snippet(metadata_search, 0, '<mark>', '</mark>', '...', 32) as snippet
                FROM metadata_search 
                WHERE metadata_search MATCH ?
            """
            
            params = [search_query]
            
            # Add entity type filter
            if query.entity_types:
                placeholders = ",".join("?" * len(query.entity_types))
                sql += f" AND entity_type IN ({placeholders})"
                params.extend(query.entity_types)
            
            sql += " ORDER BY bm25(metadata_search) LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])
            
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = SearchResult(
                    name=row[0],
                    entity_type=row[1],
                    entity_set_name=row[2],
                    description=row[3],
                    relevance=row[4],
                    snippet=row[5]
                )
                results.append(result)
            
            # Get total count
            count_cursor = await db.execute(
                "SELECT COUNT(*) FROM metadata_search WHERE metadata_search MATCH ?",
                (search_query,)
            )
            total_count = (await count_cursor.fetchone())[0]
            
            return SearchResults(
                results=results,
                total_count=total_count
            )
    
    async def _pattern_search(self, query: SearchQuery) -> SearchResults:
        """Pattern-based search for simple queries"""
        pattern = f"%{query.text.lower()}%"
        
        async with aiosqlite.connect(self.cache._database.db_path) as db:
            # Search across multiple entity types
            union_queries = []
            params = []
            
            if not query.entity_types or "data_entity" in query.entity_types:
                union_queries.append("""
                    SELECT de.name as entity_name, 'data_entity' as entity_type,
                           de.public_collection_name as entity_set_name,
                           de.label_id as description, 0.5 as relevance,
                           de.name as snippet
                    FROM data_entities de
                    JOIN metadata_versions mv ON de.version_id = mv.id
                    WHERE LOWER(de.name) LIKE ? AND mv.environment_id = ? AND mv.is_active = 1
                """)
                params.extend([pattern, self.cache._environment_id])
            
            if not query.entity_types or "public_entity" in query.entity_types:
                union_queries.append("""
                    SELECT pe.name as entity_name, 'public_entity' as entity_type,
                           pe.entity_set_name, pe.label_id as description, 0.5 as relevance,
                           pe.name as snippet
                    FROM public_entities pe
                    JOIN metadata_versions mv ON pe.version_id = mv.id
                    WHERE LOWER(pe.name) LIKE ? AND mv.environment_id = ? AND mv.is_active = 1
                """)
                params.extend([pattern, self.cache._environment_id])
            
            if not query.entity_types or "enumeration" in query.entity_types:
                union_queries.append("""
                    SELECT e.name as entity_name, 'enumeration' as entity_type,
                           e.name as entity_set_name, e.label_id as description, 0.5 as relevance,
                           e.name as snippet
                    FROM enumerations e
                    JOIN metadata_versions mv ON e.version_id = mv.id
                    WHERE LOWER(e.name) LIKE ? AND mv.environment_id = ? AND mv.is_active = 1
                """)
                params.extend([pattern, self.cache._environment_id])
            
            if not union_queries:
                return SearchResults(results=[], total_count=0)
            
            sql = " UNION ALL ".join(union_queries)
            sql += " ORDER BY relevance DESC, entity_name LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])
            
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = SearchResult(
                    name=row[0],
                    entity_type=row[1],
                    entity_set_name=row[2],
                    description=row[3],
                    relevance=row[4],
                    snippet=row[5]
                )
                results.append(result)
            
            return SearchResults(
                results=results,
                total_count=len(results)  # Simplified count for pattern search
            )
    
    def _build_fts_query(self, text: str) -> str:
        """Build FTS5 query from user input"""
        # Simple FTS query building - can be enhanced with more sophisticated parsing
        # Handle basic operators and quoted phrases
        
        # If already quoted or contains operators, use as-is
        if '"' in text or any(op in text for op in ['AND', 'OR', 'NOT', '*']):
            return text
        
        # For simple terms, create a phrase query with prefix matching
        terms = text.strip().split()
        if len(terms) == 1:
            return f'"{terms[0]}"*'
        else:
            return f'"{" ".join(terms)}"'


# Export classes for public API
__all__ = [
    'MetadataDatabase',
    'MetadataCache', 
    'MetadataSearchEngine'
]