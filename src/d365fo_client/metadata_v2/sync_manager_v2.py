"""Smart sync manager with intelligent metadata synchronization strategies."""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from ..metadata_api import MetadataAPIOperations

from ..models import (
    DataEntityInfo,
    EnumerationInfo,
    LabelInfo,
    MetadataVersionInfo,
    PublicEntityInfo,
    SyncProgress,
    SyncResult,
    SyncStrategy,
)
from .cache_v2 import MetadataCacheV2

logger = logging.getLogger(__name__)


class SmartSyncManagerV2:
    """Intelligent metadata synchronization with progress tracking and error handling"""

    def __init__(self, cache: MetadataCacheV2, metadata_api: "MetadataAPIOperations"):
        """Initialize smart sync manager

        Args:
            cache: Metadata cache v2 instance
            metadata_api: Metadata API operations instance
        """
        self.cache = cache
        self.metadata_api = metadata_api
        self.version_manager = cache.version_manager

        # Sync state
        self._is_syncing = False
        self._sync_progress: Optional[SyncProgress] = None
        self._progress_callbacks: List[Callable[[SyncProgress], None]] = []

    def add_progress_callback(self, callback: Callable[[SyncProgress], None]):
        """Add progress callback

        Args:
            callback: Function to call with progress updates
        """
        self._progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[SyncProgress], None]):
        """Remove progress callback

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    def _update_progress(self, progress: SyncProgress):
        """Update sync progress and notify callbacks

        Args:
            progress: Current sync progress
        """
        self._sync_progress = progress
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def sync_metadata(
        self, global_version_id: int, strategy: SyncStrategy = SyncStrategy.FULL
    ) -> SyncResult:
        """Sync metadata for global version

        Args:
            global_version_id: Global version ID to sync
            strategy: Sync strategy to use
            force_resync: Force resync even if data exists

        Returns:
            Sync result with counts and timing
        """
        if self._is_syncing:
            return SyncResult(
                success=False,
                error="Sync already in progress",
                duration_ms=0,
                entity_count=0,
                action_count=0,
                enumeration_count=0,
                label_count=0,
            )

        self._is_syncing = True
        start_time = time.time()

        try:
            # Initialize progress
            progress = SyncProgress(
                global_version_id=global_version_id,
                strategy=strategy,
                phase="initializing",
                total_steps=self._calculate_total_steps(strategy),
                completed_steps=0,
                current_operation="Starting sync",
                start_time=datetime.now(timezone.utc),
                estimated_completion=None,
            )
            self._update_progress(progress)

            # Update sync status
            await self.version_manager.update_sync_status(
                self.cache._environment_id, global_version_id, "syncing"
            )

            # Execute sync strategy
            if strategy == SyncStrategy.FULL:
                result = await self._sync_full_metadata(global_version_id, progress)
            elif strategy == SyncStrategy.INCREMENTAL:
                result = await self._sync_incremental_metadata(
                    global_version_id, progress
                )
            elif strategy == SyncStrategy.ENTITIES_ONLY:
                result = await self._sync_entities_only(global_version_id, progress)
            elif strategy == SyncStrategy.SHARING_MODE:
                result = await self._sync_sharing_mode(global_version_id, progress)
            else:
                raise ValueError(f"Unknown sync strategy: {strategy}")

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            result.duration_ms = duration_ms

            # Update sync status
            if result.success:
                await self.version_manager.update_sync_status(
                    self.cache._environment_id,
                    global_version_id,
                    "completed",
                    duration_ms,
                )

                # Mark cache sync completed
                await self.cache.mark_sync_completed(
                    global_version_id,
                    result.entity_count,
                    result.action_count,
                    result.enumeration_count,
                    result.label_count,
                )
            else:
                await self.version_manager.update_sync_status(
                    self.cache._environment_id, global_version_id, "failed"
                )

            # Final progress update
            progress.phase = "completed" if result.success else "failed"
            progress.completed_steps = progress.total_steps
            progress.current_operation = (
                "Sync completed" if result.success else f"Sync failed: {result.error}"
            )
            progress.estimated_completion = datetime.now(timezone.utc)
            self._update_progress(progress)

            logger.info(f"Sync completed in {duration_ms}ms: {result}")
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Sync failed after {duration_ms}ms: {e}")

            # Update failed status
            await self.version_manager.update_sync_status(
                self.cache._environment_id, global_version_id, "failed"
            )

            return SyncResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                entity_count=0,
                action_count=0,
                enumeration_count=0,
                label_count=0,
            )
        finally:
            self._is_syncing = False
            # MetadataAPIOperations doesn't need explicit cleanup

    def _calculate_total_steps(self, strategy: SyncStrategy) -> int:
        """Calculate total sync steps for strategy

        Args:
            strategy: Sync strategy

        Returns:
            Total number of steps
        """
        if strategy == SyncStrategy.FULL:
            return 10  # entities, schemas, enums, labels, indexing, etc.
        elif strategy == SyncStrategy.INCREMENTAL:
            return 6  # check changes, update entities, update schemas, etc.
        elif strategy == SyncStrategy.ENTITIES_ONLY:
            return 4  # entities, basic schemas, indexing
        elif strategy == SyncStrategy.SHARING_MODE:
            return 3  # copy from compatible version
        else:
            return 5  # default estimate

    async def _sync_full_metadata(
        self, global_version_id: int, progress: SyncProgress
    ) -> SyncResult:
        """Perform full metadata synchronization

        Args:
            global_version_id: Global version ID
            progress: Progress tracker

        Returns:
            Sync result
        """
        entity_count = 0
        action_count = 0
        enumeration_count = 0
        label_count = 0

        try:
            # Step 1: Sync data entities
            progress.phase = "entities"
            progress.current_operation = "Syncing data entities"
            progress.completed_steps = 1
            self._update_progress(progress)

            entities = await self._get_data_entities()
            if entities:
                await self.cache.store_data_entities(global_version_id, entities)
                entity_count = len(entities)
                logger.info(f"Synced {entity_count} data entities")

            # Step 2: Sync public entity schemas (top entities)
            progress.phase = "schemas"
            progress.current_operation = "Syncing entity schemas"
            progress.completed_steps = 2
            self._update_progress(progress)

            public_entities = await self._get_public_entities()
            for entity in public_entities:
                await self.cache.store_public_entity_schema(global_version_id, entity)
                action_count += len(entity.actions)

            schema_count = len(public_entities)

            logger.info(f"Synced {schema_count} entity schemas")

            # Step 3: Sync enumerations
            progress.phase = "enumerations"
            progress.current_operation = "Syncing enumerations"
            progress.completed_steps = 6
            self._update_progress(progress)

            try:
                enumerations = await self._get_public_enumerations()
                if enumerations:
                    await self.cache.store_enumerations(global_version_id, enumerations)
                    enumeration_count = len(enumerations)
                    logger.info(f"Synced {enumeration_count} enumerations")
            except Exception as e:
                logger.warning(f"Failed to sync enumerations: {e}")

            # Step 4: Sync frequently used labels
            progress.phase = "labels"
            progress.current_operation = "Syncing common labels"
            progress.completed_steps = 7
            self._update_progress(progress)

            try:
                label_count = await self._sync_common_labels(
                    global_version_id, entities, public_entities, enumerations
                )
                logger.info(f"Pre-cached {label_count} common labels")
            except Exception as e:
                logger.warning(f"Failed to sync common labels: {e}")

            # Step 5: Build search index
            progress.phase = "indexing"
            progress.current_operation = "Building search index"
            progress.completed_steps = 9
            self._update_progress(progress)

            # TODO: Implement search index building
            # await self._build_search_index(global_version_id)

            # Step 6: Complete
            progress.phase = "completed"
            progress.current_operation = "Finalizing sync"
            progress.completed_steps = 10
            self._update_progress(progress)

            return SyncResult(
                success=True,
                error=None,
                duration_ms=0,  # Will be set by caller
                entity_count=entity_count,
                action_count=action_count,
                enumeration_count=enumeration_count,
                label_count=label_count,
            )

        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            return SyncResult(
                success=False,
                error=str(e),
                duration_ms=0,
                entity_count=entity_count,
                action_count=action_count,
                enumeration_count=enumeration_count,
                label_count=label_count,
            )

    async def _sync_incremental_metadata(
        self, global_version_id: int, progress: SyncProgress
    ) -> SyncResult:
        """Perform incremental metadata synchronization

        Args:
            global_version_id: Global version ID
            progress: Progress tracker

        Returns:
            Sync result
        """
        # For now, fall back to full sync
        # TODO: Implement true incremental sync logic
        logger.info("Incremental sync not yet implemented, falling back to full sync")
        return await self._sync_full_metadata(global_version_id, progress)

    async def _sync_entities_only(
        self, global_version_id: int, progress: SyncProgress
    ) -> SyncResult:
        """Sync only data entities (fast mode)

        Args:
            global_version_id: Global version ID
            progress: Progress tracker

        Returns:
            Sync result
        """
        try:
            # Step 1: Sync data entities
            progress.phase = "entities"
            progress.current_operation = "Syncing data entities"
            progress.completed_steps = 1
            self._update_progress(progress)

            entities = await self._get_data_entities()
            entity_count = 0
            if entities:
                await self.cache.store_data_entities(global_version_id, entities)
                entity_count = len(entities)
                logger.info(f"Synced {entity_count} data entities (entities-only mode)")

            # Step 2: Complete
            progress.phase = "completed"
            progress.current_operation = "Entities sync completed"
            progress.completed_steps = 4
            self._update_progress(progress)

            return SyncResult(
                success=True,
                error=None,
                duration_ms=0,
                entity_count=entity_count,
                action_count=0,
                enumeration_count=0,
                label_count=0,
            )

        except Exception as e:
            logger.error(f"Entities-only sync failed: {e}")
            return SyncResult(
                success=False,
                error=str(e),
                duration_ms=0,
                entity_count=0,
                action_count=0,
                enumeration_count=0,
                label_count=0,
            )

    async def _sync_sharing_mode(
        self, global_version_id: int, progress: SyncProgress
    ) -> SyncResult:
        """Sync using cross-environment sharing

        Args:
            global_version_id: Global version ID
            progress: Progress tracker

        Returns:
            Sync result
        """
        try:
            # Step 1: Check if compatible version exists
            progress.phase = "sharing"
            progress.current_operation = "Looking for compatible version"
            progress.completed_steps = 1
            self._update_progress(progress)

            # Get version modules for compatibility check
            version_info = await self.version_manager.get_global_version_info(
                global_version_id
            )
            if not version_info:
                raise ValueError("Global version not found")

            # Find compatible versions
            compatible_versions = await self.version_manager.find_compatible_versions(
                version_info.modules, exact_match=True
            )

            # Filter out current version and find one with complete metadata
            source_version = None
            for version in compatible_versions:
                if version.global_version_id != global_version_id:
                    if await self.cache._has_complete_metadata(
                        version.global_version_id
                    ):
                        source_version = version
                        break

            if not source_version:
                # No compatible version found, fall back to full sync
                logger.info(
                    "No compatible version found for sharing, falling back to full sync"
                )
                return await self._sync_full_metadata(global_version_id, progress)

            # Step 2: Copy metadata from compatible version
            progress.phase = "copying"
            progress.current_operation = (
                f"Copying from version {source_version.global_version_id}"
            )
            progress.completed_steps = 2
            self._update_progress(progress)

            counts = await self._copy_metadata_between_versions(
                source_version.global_version_id, global_version_id
            )

            # Step 3: Complete
            progress.phase = "completed"
            progress.current_operation = "Sharing sync completed"
            progress.completed_steps = 3
            self._update_progress(progress)

            logger.info(
                f"Shared metadata from version {source_version.global_version_id}"
            )

            return SyncResult(
                success=True,
                error=None,
                duration_ms=0,
                entity_count=counts.get("entities", 0),
                action_count=counts.get("actions", 0),
                enumeration_count=counts.get("enumerations", 0),
                label_count=counts.get("labels", 0),
            )

        except Exception as e:
            logger.error(f"Sharing sync failed: {e}")
            return SyncResult(
                success=False,
                error=str(e),
                duration_ms=0,
                entity_count=0,
                action_count=0,
                enumeration_count=0,
                label_count=0,
            )

    async def _copy_metadata_between_versions(
        self, source_version_id: int, target_version_id: int
    ) -> Dict[str, int]:
        """Copy metadata between global versions

        Args:
            source_version_id: Source global version ID
            target_version_id: Target global version ID

        Returns:
            Dictionary with copy counts
        """
        import aiosqlite

        counts = {}

        async with aiosqlite.connect(self.cache.db_path) as db:
            # Copy data entities with label processing
            await db.execute(
                """INSERT INTO data_entities
                   (global_version_id, name, public_entity_name, public_collection_name,
                    label_id, label_text, entity_category, data_service_enabled,
                    data_management_enabled, is_read_only)
                   SELECT ?, name, public_entity_name, public_collection_name,
                          label_id, 
                          CASE 
                              WHEN label_text IS NOT NULL AND label_text != '' THEN label_text
                              WHEN label_id IS NOT NULL AND label_id != '' AND NOT label_id LIKE '@%' THEN label_id
                              ELSE label_text
                          END as processed_label_text,
                          entity_category, data_service_enabled,
                          data_management_enabled, is_read_only
                   FROM data_entities
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )
            counts["entities"] = db.total_changes

            # Copy enumerations with label processing
            await db.execute(
                """INSERT INTO enumerations
                   (global_version_id, name, label_id, label_text)
                   SELECT ?, name, label_id,
                          CASE 
                              WHEN label_text IS NOT NULL AND label_text != '' THEN label_text
                              WHEN label_id IS NOT NULL AND label_id != '' AND NOT label_id LIKE '@%' THEN label_id
                              ELSE label_text
                          END as processed_label_text
                   FROM enumerations
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )
            counts["enumerations"] = db.total_changes

            # Copy public entities with label processing
            await db.execute(
                """INSERT INTO public_entities
                   (global_version_id, name, entity_set_name, label_id, label_text,
                    is_read_only, configuration_enabled)
                   SELECT ?, name, entity_set_name, label_id,
                          CASE 
                              WHEN label_text IS NOT NULL AND label_text != '' THEN label_text
                              WHEN label_id IS NOT NULL AND label_id != '' AND NOT label_id LIKE '@%' THEN label_id
                              ELSE label_text
                          END as processed_label_text,
                          is_read_only, configuration_enabled
                   FROM public_entities
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            # Copy entity properties with label processing
            # Note: We need to get the new entity IDs for the relationships
            await db.execute(
                """INSERT INTO entity_properties
                   (entity_id, global_version_id, name, type_name, data_type,
                    odata_xpp_type, label_id, label_text, is_key, is_mandatory,
                    configuration_enabled, allow_edit, allow_edit_on_create,
                    is_dimension, dimension_relation, is_dynamic_dimension,
                    dimension_legal_entity_property, dimension_type_property,
                    property_order)
                   SELECT pe_new.id as entity_id, ?, ep.name, ep.type_name, ep.data_type,
                          ep.odata_xpp_type, ep.label_id,
                          CASE 
                              WHEN ep.label_text IS NOT NULL AND ep.label_text != '' THEN ep.label_text
                              WHEN ep.label_id IS NOT NULL AND ep.label_id != '' AND NOT ep.label_id LIKE '@%' THEN ep.label_id
                              ELSE ep.label_text
                          END as processed_label_text,
                          ep.is_key, ep.is_mandatory,
                          ep.configuration_enabled, ep.allow_edit, ep.allow_edit_on_create,
                          ep.is_dimension, ep.dimension_relation, ep.is_dynamic_dimension,
                          ep.dimension_legal_entity_property, ep.dimension_type_property,
                          ep.property_order
                   FROM entity_properties ep
                   JOIN public_entities pe_old ON ep.entity_id = pe_old.id
                   JOIN public_entities pe_new ON pe_new.name = pe_old.name AND pe_new.global_version_id = ?
                   WHERE ep.global_version_id = ?""",
                (target_version_id, target_version_id, source_version_id),
            )

            # Copy enumeration members with label processing  
            await db.execute(
                """INSERT INTO enumeration_members
                   (enumeration_id, global_version_id, name, value,
                    label_id, label_text, configuration_enabled, member_order)
                   SELECT e_new.id as enumeration_id, ?, em.name, em.value,
                          em.label_id,
                          CASE 
                              WHEN em.label_text IS NOT NULL AND em.label_text != '' THEN em.label_text
                              WHEN em.label_id IS NOT NULL AND em.label_id != '' AND NOT em.label_id LIKE '@%' THEN em.label_id
                              ELSE em.label_text
                          END as processed_label_text,
                          em.configuration_enabled, em.member_order
                   FROM enumeration_members em
                   JOIN enumerations e_old ON em.enumeration_id = e_old.id
                   JOIN enumerations e_new ON e_new.name = e_old.name AND e_new.global_version_id = ?
                   WHERE em.global_version_id = ?""",
                (target_version_id, target_version_id, source_version_id),
            )

            # Copy other metadata tables as needed...
            # This is a more comprehensive implementation with label processing

            await db.commit()

        return counts

    def get_sync_progress(self) -> Optional[SyncProgress]:
        """Get current sync progress

        Returns:
            Current sync progress if syncing
        """
        return self._sync_progress

    def is_syncing(self) -> bool:
        """Check if sync is in progress

        Returns:
            True if sync is in progress
        """
        return self._is_syncing

    async def recommend_sync_strategy(self, global_version_id: int) -> SyncStrategy:
        """Recommend sync strategy based on environment and cache state

        Args:
            global_version_id: Global version ID

        Returns:
            Recommended sync strategy
        """
        try:
            # Check if metadata already exists
            has_metadata = await self.cache._has_complete_metadata(global_version_id)
            if has_metadata:
                return SyncStrategy.INCREMENTAL

            # Get version info
            version_info = await self.version_manager.get_global_version_info(
                global_version_id
            )
            if not version_info:
                return SyncStrategy.FULL

            # Check for compatible versions (sharing opportunity)
            compatible_versions = await self.version_manager.find_compatible_versions(
                version_info.sample_modules, exact_match=True
            )

            for version in compatible_versions:
                if version.global_version_id != global_version_id:
                    if await self.cache._has_complete_metadata(
                        version.global_version_id
                    ):
                        return SyncStrategy.SHARING_MODE

            # Default to full sync for new versions
            return SyncStrategy.FULL

        except Exception as e:
            logger.warning(f"Failed to recommend sync strategy: {e}")
            return SyncStrategy.FULL

    # Metadata API Methods (Using MetadataAPIOperations)

    async def _get_data_entities(self) -> List[DataEntityInfo]:
        """Get data entities using MetadataAPIOperations

        Args:
            options: OData query options

        Returns:
            List of data entity information
        """
        try:
            # Use existing search method which handles the data extraction and parsing
            entities = await self.metadata_api.search_data_entities()
            return entities

        except Exception as e:
            logger.error(f"Error getting data entities: {e}")
            raise

    async def _get_public_entities(self) -> List[PublicEntityInfo]:
        """Get detailed schema for all public entities using MetadataAPIOperations

        Returns:
            List of PublicEntityInfo with full schema
        """
        try:
            return await self.metadata_api.get_all_public_entities_with_details(
                resolve_labels=False  # We'll handle labels separately if needed
            )

        except Exception as e:
            logger.error(f"Error getting public entities: {e}")
            return []

    async def _get_public_enumerations(self) -> List[EnumerationInfo]:
        """Get public enumerations using MetadataAPIOperations

        Args:
            options: OData query options

        Returns:
            List of enumeration information
        """
        try:
            # Use existing method which handles the data extraction and parsing
            enumerations = (
                await self.metadata_api.get_all_public_enumerations_with_details(
                    resolve_labels=False  # We'll handle labels separately if needed
                )
            )
            return enumerations

        except Exception as e:
            logger.error(f"Error getting public enumerations: {e}")
            raise

    async def _get_current_version(self) -> MetadataVersionInfo:
        """Get current environment version information

        Returns:
            Current version information
        """
        try:
            # Get version information from D365 F&O using MetadataAPIOperations
            application_version = await self.metadata_api.get_application_version()
            platform_version = await self.metadata_api.get_platform_build_version()
        except Exception as e:
            logger.warning(f"Failed to get version information: {e}, using fallback")
            application_version = "10.0.latest"
            platform_version = "10.0.latest"

        # Create a version hash based on the actual version information
        version_components = {
            "application_version": application_version,
            "platform_version": platform_version,
        }

        # Create version hash
        version_str = json.dumps(version_components, sort_keys=True)
        version_hash = hashlib.sha256(version_str.encode()).hexdigest()[:16]

        return MetadataVersionInfo(
            environment_id=self.cache._environment_id,
            version_hash=version_hash,
            application_version=application_version,
            platform_version=platform_version,
            package_info=[],  # Would be populated with actual package info
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )

    async def needs_sync(self, global_version_id: int) -> bool:
        """Check if metadata synchronization is needed

        Args:
            global_version_id: Global version ID to check

        Returns:
            True if sync is needed
        """
        try:
            # Check if metadata exists for this version
            return not await self.cache._has_complete_metadata(global_version_id)

        except Exception as e:
            logger.warning(f"Could not check sync status: {e}")
            # When in doubt, assume sync is needed
            return True

    async def _sync_common_labels(
        self,
        global_version_id: int,
        entities: List[DataEntityInfo],
        public_entities: List[PublicEntityInfo],
        enumerations: List[EnumerationInfo],
    ) -> int:
        """Sync commonly used labels to improve performance

        Args:
            global_version_id: Global version ID
            entities: Data entities to extract labels from
            public_entities: Public entities to extract labels from
            enumerations: Enumerations to extract labels from

        Returns:
            Number of labels cached
        """
        label_ids = set()

        # Collect label IDs from data entities
        if entities:
            for entity in entities:
                if entity.label_id and entity.label_id.startswith("@"):
                    label_ids.add(entity.label_id)

        # Collect label IDs from public entities and their properties
        if public_entities:
            for entity in public_entities:
                if entity.label_id and entity.label_id.startswith("@"):
                    label_ids.add(entity.label_id)

                # Collect from properties
                for prop in entity.properties:
                    if prop.label_id and prop.label_id.startswith("@"):
                        label_ids.add(prop.label_id)

        # Collect label IDs from enumerations and their members
        if enumerations:
            for enum in enumerations:
                if enum.label_id and enum.label_id.startswith("@"):
                    label_ids.add(enum.label_id)

                # Collect from members
                for member in enum.members:
                    if member.label_id and member.label_id.startswith("@"):
                        label_ids.add(member.label_id)

        # Remove empty/None labels
        label_ids = {
            label_id for label_id in label_ids if label_id and label_id.strip()
        }

        if not label_ids:
            logger.debug("No label IDs found to pre-cache")
            return 0

        logger.info(f"Pre-caching {len(label_ids)} common labels")

        # Fetch labels from API and cache them
        labels_to_cache = []
        cached_count = 0

        # Use the label operations from metadata API to fetch labels
        if hasattr(self.metadata_api, "label_ops") and self.metadata_api.label_ops:
            try:
                # Get labels in batch for efficiency
                label_texts = await self.metadata_api.label_ops.get_labels_batch(
                    list(label_ids)
                )

                for label_id, label_text in label_texts.items():
                    if label_text:  # Only cache labels that have actual text
                        labels_to_cache.append(
                            LabelInfo(id=label_id, language="en-US", value=label_text)
                        )
                        cached_count += 1

                # Batch cache all labels
                if labels_to_cache:
                    await self.cache.set_labels_batch(
                        labels_to_cache, global_version_id
                    )

            except Exception as e:
                logger.warning(f"Failed to batch fetch labels: {e}")
                # Fall back to individual fetching for critical labels
                for label_id in list(label_ids)[
                    :50
                ]:  # Limit to first 50 to avoid timeout
                    try:
                        label_text = await self.metadata_api.label_ops.get_label_text(
                            label_id
                        )
                        if label_text:
                            await self.cache.set_label(
                                label_id,
                                label_text,
                                global_version_id=global_version_id,
                            )
                            cached_count += 1
                    except Exception as e2:
                        logger.debug(
                            f"Failed to fetch individual label {label_id}: {e2}"
                        )

        logger.info(f"Successfully pre-cached {cached_count} labels")
        return cached_count
