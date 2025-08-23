"""Enhanced database schema with global version management."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseSchemaV2:
    """Database schema manager for metadata v2"""

    @staticmethod
    async def create_schema(db: aiosqlite.Connection):
        """Create complete database schema for metadata v2"""

        # Core environment tracking (enhanced)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata_environments (
                id INTEGER PRIMARY KEY,
                base_url TEXT NOT NULL UNIQUE,
                environment_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sync_at TIMESTAMP,
                last_version_check TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """
        )

        # Global version registry (NEW)
        await db.execute(
            """
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
        """
        )

        # Environment to global version mapping (NEW)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS environment_versions (
                environment_id INTEGER REFERENCES metadata_environments(id),
                global_version_id INTEGER REFERENCES global_versions(id),
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                sync_status TEXT DEFAULT 'pending',  -- pending|syncing|completed|failed
                last_sync_duration_ms INTEGER,
                PRIMARY KEY (environment_id, global_version_id)
            )
        """
        )

        # Sample modules for global versions (NEW)
        await db.execute(
            """
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
        """
        )

        # Enhanced metadata versioning
        await db.execute(
            """
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
        """
        )

        # Version-aware metadata tables (enhanced with global_version_id)

        # Data entities
        await db.execute(
            """
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
        """
        )

        # Public entities
        await db.execute(
            """
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
        """
        )

        # Entity properties (version-aware)
        await db.execute(
            """
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
        """
        )

        # Navigation properties (version-aware)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS navigation_properties (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                related_entity TEXT,
                related_relation_name TEXT,
                cardinality TEXT DEFAULT 'Single'
            )
        """
        )

        # Relation constraints (version-aware)
        await db.execute(
            """
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
        """
        )

        # Property groups (version-aware)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS property_groups (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL REFERENCES public_entities(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL
            )
        """
        )

        # Property group members (version-aware)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS property_group_members (
                id INTEGER PRIMARY KEY,
                property_group_id INTEGER NOT NULL REFERENCES property_groups(id),
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                property_name TEXT NOT NULL,
                member_order INTEGER DEFAULT 0
            )
        """
        )

        # Entity actions (version-aware)
        await db.execute(
            """
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
        """
        )

        # Action parameters (version-aware)
        await db.execute(
            """
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
        """
        )

        # Enumerations (version-aware)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS enumerations (
                id INTEGER PRIMARY KEY,
                global_version_id INTEGER NOT NULL REFERENCES global_versions(id),
                name TEXT NOT NULL,
                label_id TEXT,
                label_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Enumeration members (version-aware)
        await db.execute(
            """
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
        """
        )

        # Labels cache (version-aware)
        await db.execute(
            """
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
        """
        )

        # FTS5 search index (version-aware)
        await db.execute(
            """
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
        """
        )

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
            # Global version modules index
            "CREATE INDEX IF NOT EXISTS idx_global_version_modules ON global_version_modules(global_version_id, module_id)",
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
        """Initialize database with path

        Args:
            db_path: Path to SQLite database file
        """
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
        """Get or create environment ID

        Args:
            base_url: Environment base URL

        Returns:
            Environment ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Try to find existing environment
            cursor = await db.execute(
                "SELECT id FROM metadata_environments WHERE base_url = ?", (base_url,)
            )

            row = await cursor.fetchone()
            if row:
                return row[0]

            # Create new environment
            environment_name = self._extract_environment_name(base_url)
            cursor = await db.execute(
                """INSERT INTO metadata_environments (base_url, environment_name)
                   VALUES (?, ?)""",
                (base_url, environment_name),
            )

            environment_id = cursor.lastrowid
            await db.commit()

            logger.info(f"Created environment {environment_id}: {environment_name}")
            return environment_id

    def _extract_environment_name(self, base_url: str) -> str:
        """Extract environment name from URL

        Args:
            base_url: Full environment URL

        Returns:
            Extracted environment name
        """
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        hostname = parsed.hostname or base_url
        return hostname.split(".")[0] if "." in hostname else hostname

    async def get_global_version_metadata_counts(
        self, global_version_id: int
    ) -> Dict[str, int]:
        """Get metadata counts for a global version

        Args:
            global_version_id: Global version ID to get counts for

        Returns:
            Dictionary with counts for each metadata type
        """
        async with aiosqlite.connect(self.db_path) as db:
            counts = {}

            tables = [
                ("data_entities", "entities"),
                ("public_entities", "public_entities"),
                ("entity_properties", "properties"),
                ("entity_actions", "actions"),
                ("enumerations", "enumerations"),
                ("labels_cache", "labels"),
            ]

            for table, key in tables:
                cursor = await db.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE global_version_id = ?",
                    (global_version_id,),
                )
                counts[key] = (await cursor.fetchone())[0]

            return counts

    async def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics

        Returns:
            Dictionary with database statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Basic table counts
            tables = [
                "metadata_environments",
                "global_versions",
                "environment_versions",
                "global_version_modules",
                "metadata_versions",
                "data_entities",
                "public_entities",
                "entity_properties",
                "navigation_properties",
                "entity_actions",
                "enumerations",
                "labels_cache",
            ]

            for table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = (await cursor.fetchone())[0]

            # Global version statistics
            cursor = await db.execute(
                """SELECT 
                     COUNT(*) as total_versions,
                     SUM(reference_count) as total_references,
                     AVG(reference_count) as avg_references,
                     MAX(reference_count) as max_references
                   FROM global_versions"""
            )
            version_stats = await cursor.fetchone()
            stats["version_statistics"] = {
                "total_versions": version_stats[0],
                "total_references": version_stats[1] or 0,
                "avg_references": round(version_stats[2] or 0, 2),
                "max_references": version_stats[3] or 0,
            }

            # Environment statistics
            cursor = await db.execute(
                """SELECT 
                     COUNT(DISTINCT me.id) as total_environments,
                     COUNT(DISTINCT ev.global_version_id) as linked_versions
                   FROM metadata_environments me
                   LEFT JOIN environment_versions ev ON me.id = ev.environment_id
                   WHERE ev.is_active = 1"""
            )
            env_stats = await cursor.fetchone()
            stats["environment_statistics"] = {
                "total_environments": env_stats[0],
                "linked_versions": env_stats[1] or 0,
            }

            # Database file size
            try:
                db_size = self.db_path.stat().st_size
                stats["database_size_bytes"] = db_size
                stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
            except Exception:
                stats["database_size_bytes"] = None
                stats["database_size_mb"] = None

            return stats

    async def vacuum_database(self) -> bool:
        """Vacuum database to reclaim space

        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("VACUUM")
                await db.commit()
            logger.info("Database vacuum completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False

    async def check_database_integrity(self) -> Dict[str, Any]:
        """Check database integrity

        Returns:
            Dictionary with integrity check results
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Run integrity check
            cursor = await db.execute("PRAGMA integrity_check")
            integrity_result = await cursor.fetchone()

            # Run foreign key check
            cursor = await db.execute("PRAGMA foreign_key_check")
            foreign_key_issues = await cursor.fetchall()

            return {
                "integrity_ok": integrity_result[0] == "ok",
                "integrity_message": integrity_result[0],
                "foreign_key_issues": len(foreign_key_issues),
                "foreign_key_details": foreign_key_issues[
                    :10
                ],  # Limit to first 10 issues
            }
