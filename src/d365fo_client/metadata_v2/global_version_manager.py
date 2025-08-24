"""Global version manager for cross-environment metadata sharing."""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from ..models import EnvironmentVersionInfo, GlobalVersionInfo, ModuleVersionInfo

logger = logging.getLogger(__name__)


class GlobalVersionManager:
    """Manages global version registry and cross-environment sharing"""

    def __init__(self, db_path):
        """Initialize global version manager

        Args:
            db_path: Path to metadata database
        """
        self.db_path = db_path

    async def register_environment_version(
        self, environment_id: int, modules: List[ModuleVersionInfo]
    ) -> Tuple[int, bool]:
        """Register environment version and get/create global version

        Args:
            environment_id: Environment ID
            modules: List of module version information

        Returns:
            Tuple of (global_version_id, is_new_version)
        """
        # Calculate version hashes
        modules_hash = self._calculate_modules_hash(modules)
        version_hash = self._calculate_version_hash(modules)

        async with aiosqlite.connect(self.db_path) as db:
            # Check if this exact version already exists
            cursor = await db.execute(
                "SELECT id FROM global_versions WHERE modules_hash = ?", (modules_hash,)
            )

            existing_version = await cursor.fetchone()
            if existing_version:
                global_version_id = existing_version[0]
                is_new_version = False

                # Update reference count and last used
                await db.execute(
                    """UPDATE global_versions 
                       SET reference_count = reference_count + 1,
                           last_used_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (global_version_id,),
                )

                logger.info(f"Using existing global version {global_version_id}")
            else:
                # Create new global version
                cursor = await db.execute(
                    """INSERT INTO global_versions 
                       (version_hash, modules_hash, created_by_environment_id, reference_count)
                       VALUES (?, ?, ?, 1)""",
                    (version_hash, modules_hash, environment_id),
                )

                global_version_id = cursor.lastrowid
                is_new_version = True

                # Store module information
                await self._store_global_version_modules(db, global_version_id, modules)

                logger.info(f"Created new global version {global_version_id}")

            # Link environment to global version
            await self._link_environment_to_version(
                db, environment_id, global_version_id
            )

            await db.commit()

            return global_version_id, is_new_version

    def _calculate_modules_hash(self, modules: List[ModuleVersionInfo]) -> str:
        """Calculate hash of sorted modules

        Args:
            modules: List of module version information

        Returns:
            SHA-256 hash of sorted modules
        """
        # Sort modules by ID for consistent hashing
        sorted_modules = sorted(modules, key=lambda m: m.module_id)

        # Create hash string
        hash_data = []
        for module in sorted_modules:
            hash_data.append(f"{module.module_id}:{module.version}")

        hash_string = "|".join(hash_data)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _calculate_version_hash(self, modules: List[ModuleVersionInfo]) -> str:
        """Calculate comprehensive version hash including all module details

        Args:
            modules: List of module version information

        Returns:
            SHA-256 hash of all module details
        """
        # Sort modules by ID for consistent hashing
        sorted_modules = sorted(modules, key=lambda m: m.module_id)

        # Create comprehensive hash string
        hash_data = []
        for module in sorted_modules:
            module_data = [
                module.module_id,
                module.version or "",
                module.name or "",
                module.publisher or "",
                module.display_name or "",
            ]
            hash_data.append(":".join(module_data))

        hash_string = "|".join(hash_data)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    async def _store_global_version_modules(
        self,
        db: aiosqlite.Connection,
        global_version_id: int,
        modules: List[ModuleVersionInfo],
    ):
        """Store module information for global version

        Args:
            db: Database connection
            global_version_id: Global version ID
            modules: List of module version information
        """
        # Sort modules for consistent ordering
        sorted_modules = sorted(modules, key=lambda m: (m.module_id, m.name or ""))

        for i, module in enumerate(sorted_modules):
            await db.execute(
                """INSERT INTO global_version_modules
                   (global_version_id, module_id, module_name, version, 
                    publisher, display_name, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    global_version_id,
                    module.module_id,
                    module.name,
                    module.version,
                    module.publisher,
                    module.display_name,
                    i,
                ),
            )

    async def _link_environment_to_version(
        self, db: aiosqlite.Connection, environment_id: int, global_version_id: int
    ):
        """Link environment to global version

        Args:
            db: Database connection
            environment_id: Environment ID
            global_version_id: Global version ID
        """
        # Deactivate any existing active links for this environment
        await db.execute(
            """UPDATE environment_versions 
               SET is_active = 0 
               WHERE environment_id = ? AND is_active = 1""",
            (environment_id,),
        )

        # Create or reactivate link
        await db.execute(
            """INSERT OR REPLACE INTO environment_versions
               (environment_id, global_version_id, is_active, sync_status)
               VALUES (?, ?, 1, 'pending')""",
            (environment_id, global_version_id),
        )

    async def get_environment_version_info(
        self, environment_id: int
    ) -> Optional[Tuple[int, EnvironmentVersionInfo]]:
        """Get current version info for environment

        Args:
            environment_id: Environment ID

        Returns:
            Tuple of (global_version_id, EnvironmentVersionInfo) if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT 
                     ev.global_version_id,
                     ev.detected_at,
                     ev.sync_status,
                     gv.version_hash,
                     gv.modules_hash,
                     gv.reference_count
                   FROM environment_versions ev
                   JOIN global_versions gv ON ev.global_version_id = gv.id
                   WHERE ev.environment_id = ? AND ev.is_active = 1""",
                (environment_id,),
            )

            row = await cursor.fetchone()
            if not row:
                return None

            # Get modules for this version
            modules = await self._get_global_version_modules(db, row[0])

            version_info = EnvironmentVersionInfo(
                environment_id=environment_id,
                version_hash=row[3],
                modules_hash=row[4],
                modules=modules,
                computed_at=(
                    datetime.fromisoformat(row[1])
                    if row[1]
                    else datetime.now(timezone.utc)
                ),
                is_active=True,
            )

            return row[0], version_info  # Return (global_version_id, version_info)

    async def _get_global_version_modules(
        self, db: aiosqlite.Connection, global_version_id: int
    ) -> List[ModuleVersionInfo]:
        """Get modules for global version

        Args:
            db: Database connection
            global_version_id: Global version ID

        Returns:
            List of module version information
        """
        cursor = await db.execute(
            """SELECT module_id, module_name, version, publisher, display_name
               FROM global_version_modules
               WHERE global_version_id = ?
               ORDER BY sort_order""",
            (global_version_id,),
        )

        modules = []
        for row in await cursor.fetchall():
            modules.append(
                ModuleVersionInfo(
                    module_id=row[0],
                    name=row[1],
                    version=row[2],
                    publisher=row[3],
                    display_name=row[4],
                )
            )

        return modules

    async def get_global_version_info(
        self, global_version_id: int
    ) -> Optional[GlobalVersionInfo]:
        """Get global version information

        Args:
            global_version_id: Global version ID

        Returns:
            Global version info if found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT 
                     id, version_hash, modules_hash, first_seen_at, 
                     last_used_at, reference_count, metadata_size_bytes,
                     created_by_environment_id
                   FROM global_versions
                   WHERE id = ?""",
                (global_version_id,),
            )

            row = await cursor.fetchone()
            if not row:
                return None

            # Get modules
            modules = await self._get_global_version_modules(db, global_version_id)

            # Get linked environments
            cursor = await db.execute(
                """SELECT me.base_url, me.environment_name
                   FROM environment_versions ev
                   JOIN metadata_environments me ON ev.environment_id = me.id
                   WHERE ev.global_version_id = ? AND ev.is_active = 1""",
                (global_version_id,),
            )

            environments = []
            for env_row in await cursor.fetchall():
                environments.append(
                    {"base_url": env_row[0], "environment_name": env_row[1]}
                )

            return GlobalVersionInfo(
                id=row[0],
                version_hash=row[1],
                modules_hash=row[2],
                first_seen_at=datetime.fromisoformat(row[3]),
                last_used_at=datetime.fromisoformat(row[4]),
                reference_count=row[5],
                sample_modules=(
                    modules[:10] if modules else []
                ),  # Use first 10 modules as sample
            )

    async def find_compatible_versions(
        self, modules: List[ModuleVersionInfo], exact_match: bool = False
    ) -> List[GlobalVersionInfo]:
        """Find compatible global versions

        Args:
            modules: Target modules to find compatibility for
            exact_match: If True, require exact module match

        Returns:
            List of compatible global versions, sorted by compatibility
        """
        target_modules_hash = self._calculate_modules_hash(modules)

        async with aiosqlite.connect(self.db_path) as db:
            if exact_match:
                # Exact module match only
                cursor = await db.execute(
                    """SELECT id FROM global_versions 
                       WHERE modules_hash = ?
                       ORDER BY last_used_at DESC""",
                    (target_modules_hash,),
                )
            else:
                # Get all versions for compatibility analysis
                cursor = await db.execute(
                    """SELECT id FROM global_versions 
                       ORDER BY reference_count DESC, last_used_at DESC"""
                )

            compatible_versions = []
            for row in await cursor.fetchall():
                version_info = await self.get_global_version_info(row[0])
                if version_info:
                    if exact_match or self._is_compatible(
                        modules, version_info.modules
                    ):
                        compatible_versions.append(version_info)

            return compatible_versions

    def _is_compatible(
        self,
        target_modules: List[ModuleVersionInfo],
        candidate_modules: List[ModuleVersionInfo],
    ) -> bool:
        """Check if modules are compatible

        Args:
            target_modules: Target modules
            candidate_modules: Candidate modules to check

        Returns:
            True if modules are compatible
        """
        # Create dictionaries for easier lookup
        target_dict = {m.module_id: m for m in target_modules}
        candidate_dict = {m.module_id: m for m in candidate_modules}

        # Check core modules compatibility
        core_modules = [
            "ApplicationPlatform",
            "ApplicationFoundation",
            "ApplicationSuite",
        ]

        for core_module in core_modules:
            target_module = target_dict.get(core_module)
            candidate_module = candidate_dict.get(core_module)

            if target_module and candidate_module:
                if target_module.version != candidate_module.version:
                    return False
            elif target_module or candidate_module:
                # One has core module, other doesn't - incompatible
                return False

        # For now, require exact core module match
        # Future: implement semantic version compatibility
        return True

    async def cleanup_unused_versions(self, max_unused_days: int = 30) -> int:
        """Clean up unused global versions

        Args:
            max_unused_days: Days after which unused versions can be cleaned

        Returns:
            Number of versions cleaned up
        """
        cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.timestamp() - (max_unused_days * 86400)
        cutoff_timestamp = datetime.fromtimestamp(cutoff_date).isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            # Find unused versions
            cursor = await db.execute(
                """SELECT id FROM global_versions 
                   WHERE reference_count = 0 
                   AND last_used_at < ?""",
                (cutoff_timestamp,),
            )

            unused_versions = [row[0] for row in await cursor.fetchall()]

            if not unused_versions:
                return 0

            # Delete related data
            for global_version_id in unused_versions:
                await self._delete_global_version_data(db, global_version_id)

            await db.commit()

            logger.info(f"Cleaned up {len(unused_versions)} unused global versions")
            return len(unused_versions)

    async def _delete_global_version_data(
        self, db: aiosqlite.Connection, global_version_id: int
    ):
        """Delete all data for a global version

        Args:
            db: Database connection
            global_version_id: Global version ID to delete
        """
        # Delete in dependency order
        tables = [
            "action_parameters",
            "property_group_members",
            "relation_constraints",
            "entity_properties",
            "navigation_properties",
            "property_groups",
            "entity_actions",
            "enumeration_members",
            "data_entities",
            "public_entities",
            "enumerations",
            "labels_cache",
            "global_version_modules",
            "metadata_versions",
            "environment_versions",
            "global_versions",
        ]

        for table in tables:
            if table == "global_versions":
                # Final delete of the version record
                await db.execute(
                    f"DELETE FROM {table} WHERE id = ?", (global_version_id,)
                )
            else:
                # Delete related records
                await db.execute(
                    f"DELETE FROM {table} WHERE global_version_id = ?",
                    (global_version_id,),
                )

    async def update_sync_status(
        self,
        environment_id: int,
        global_version_id: int,
        status: str,
        duration_ms: Optional[int] = None,
    ):
        """Update sync status for environment version

        Args:
            environment_id: Environment ID
            global_version_id: Global version ID
            status: New sync status
            duration_ms: Sync duration in milliseconds
        """
        async with aiosqlite.connect(self.db_path) as db:
            if duration_ms is not None:
                await db.execute(
                    """UPDATE environment_versions
                       SET sync_status = ?, last_sync_duration_ms = ?
                       WHERE environment_id = ? AND global_version_id = ?""",
                    (status, duration_ms, environment_id, global_version_id),
                )
            else:
                await db.execute(
                    """UPDATE environment_versions
                       SET sync_status = ?
                       WHERE environment_id = ? AND global_version_id = ?""",
                    (status, environment_id, global_version_id),
                )

            await db.commit()

    async def get_version_statistics(self) -> Dict[str, Any]:
        """Get global version statistics

        Returns:
            Dictionary with version statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Basic counts
            cursor = await db.execute("SELECT COUNT(*) FROM global_versions")
            stats["total_versions"] = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(DISTINCT environment_id) FROM environment_versions"
            )
            stats["total_environments"] = (await cursor.fetchone())[0]

            # Reference statistics
            cursor = await db.execute(
                """SELECT 
                     SUM(reference_count) as total_references,
                     AVG(reference_count) as avg_references,
                     MAX(reference_count) as max_references,
                     COUNT(*) as versions_with_refs
                   FROM global_versions 
                   WHERE reference_count > 0"""
            )
            ref_stats = await cursor.fetchone()
            stats["reference_statistics"] = {
                "total_references": ref_stats[0] or 0,
                "avg_references": round(ref_stats[1] or 0, 2),
                "max_references": ref_stats[2] or 0,
                "versions_with_references": ref_stats[3] or 0,
            }

            # Version age statistics
            cursor = await db.execute(
                """SELECT 
                     COUNT(*) as recent_versions
                   FROM global_versions 
                   WHERE last_used_at >= datetime('now', '-7 days')"""
            )
            stats["recent_activity"] = {
                "versions_used_last_7_days": (await cursor.fetchone())[0]
            }

            return stats
