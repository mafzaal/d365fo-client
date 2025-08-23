"""Smart sync manager with intelligent metadata synchronization strategies."""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set, Callable
from pathlib import Path
import time

from .cache_v2 import MetadataCacheV2
from .global_version_manager import GlobalVersionManager
from ..models import (
    DataEntityInfo, PublicEntityInfo, EnumerationInfo,
    SyncProgress, SyncStrategy, SyncResult
)

logger = logging.getLogger(__name__)


class SmartSyncManagerV2:
    """Intelligent metadata synchronization with progress tracking and error handling"""
    
    def __init__(self, cache: MetadataCacheV2):
        """Initialize smart sync manager
        
        Args:
            cache: Metadata cache v2 instance
        """
        self.cache = cache
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
        self,
        fo_client,
        global_version_id: int,
        strategy: SyncStrategy = SyncStrategy.FULL,
        force_resync: bool = False
    ) -> SyncResult:
        """Sync metadata for global version
        
        Args:
            fo_client: D365 F&O client instance
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
                label_count=0
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
                estimated_completion=None
            )
            self._update_progress(progress)
            
            # Update sync status
            await self.version_manager.update_sync_status(
                self.cache._environment_id,
                global_version_id,
                "syncing"
            )
            
            # Execute sync strategy
            if strategy == SyncStrategy.FULL:
                result = await self._sync_full_metadata(fo_client, global_version_id, progress)
            elif strategy == SyncStrategy.INCREMENTAL:
                result = await self._sync_incremental_metadata(fo_client, global_version_id, progress)
            elif strategy == SyncStrategy.ENTITIES_ONLY:
                result = await self._sync_entities_only(fo_client, global_version_id, progress)
            elif strategy == SyncStrategy.SHARING_MODE:
                result = await self._sync_sharing_mode(fo_client, global_version_id, progress)
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
                    duration_ms
                )
                
                # Mark cache sync completed
                await self.cache.mark_sync_completed(
                    global_version_id,
                    result.entity_count,
                    result.action_count,
                    result.enumeration_count,
                    result.label_count
                )
            else:
                await self.version_manager.update_sync_status(
                    self.cache._environment_id,
                    global_version_id,
                    "failed"
                )
            
            # Final progress update
            progress.phase = "completed" if result.success else "failed"
            progress.completed_steps = progress.total_steps
            progress.current_operation = "Sync completed" if result.success else f"Sync failed: {result.error}"
            progress.estimated_completion = datetime.now(timezone.utc)
            self._update_progress(progress)
            
            logger.info(f"Sync completed in {duration_ms}ms: {result}")
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Sync failed after {duration_ms}ms: {e}")
            
            # Update failed status
            await self.version_manager.update_sync_status(
                self.cache._environment_id,
                global_version_id,
                "failed"
            )
            
            return SyncResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                entity_count=0,
                action_count=0,
                enumeration_count=0,
                label_count=0
            )
        finally:
            self._is_syncing = False
    
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
            return 6   # check changes, update entities, update schemas, etc.
        elif strategy == SyncStrategy.ENTITIES_ONLY:
            return 4   # entities, basic schemas, indexing
        elif strategy == SyncStrategy.SHARING_MODE:
            return 3   # copy from compatible version
        else:
            return 5   # default estimate
    
    async def _sync_full_metadata(
        self,
        fo_client,
        global_version_id: int,
        progress: SyncProgress
    ) -> SyncResult:
        """Perform full metadata synchronization
        
        Args:
            fo_client: D365 F&O client instance
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
            
            entities = await fo_client.get_data_entities()
            if entities:
                await self.cache.store_data_entities(global_version_id, entities)
                entity_count = len(entities)
                logger.info(f"Synced {entity_count} data entities")
            
            # Step 2: Sync public entity schemas (top entities)
            progress.phase = "schemas"
            progress.current_operation = "Syncing entity schemas"
            progress.completed_steps = 2
            self._update_progress(progress)
            
            # Get top public entities for schema sync
            public_entities = [e for e in entities if e.data_service_enabled and e.public_entity_name]
            top_entities = public_entities[:50]  # Limit to top 50 for performance
            
            schema_count = 0
            for i, entity in enumerate(top_entities):
                try:
                    schema = await fo_client.get_entity_schema(entity.public_entity_name)
                    if schema:
                        await self.cache.store_public_entity_schema(global_version_id, schema)
                        schema_count += 1
                        
                        # Count actions
                        action_count += len(schema.actions)
                    
                    # Update progress
                    if i % 10 == 0:
                        progress.current_operation = f"Syncing schemas ({i+1}/{len(top_entities)})"
                        self._update_progress(progress)
                        
                except Exception as e:
                    logger.warning(f"Failed to sync schema for {entity.public_entity_name}: {e}")
            
            logger.info(f"Synced {schema_count} entity schemas with {action_count} actions")
            
            # Step 3: Sync enumerations
            progress.phase = "enumerations"
            progress.current_operation = "Syncing enumerations"
            progress.completed_steps = 6
            self._update_progress(progress)
            
            try:
                enumerations = await fo_client.get_public_enumerations()
                if enumerations:
                    await self.cache.store_enumerations(global_version_id, enumerations)
                    enumeration_count = len(enumerations)
                    logger.info(f"Synced {enumeration_count} enumerations")
            except Exception as e:
                logger.warning(f"Failed to sync enumerations: {e}")
            
            # Step 4: Build search index
            progress.phase = "indexing"
            progress.current_operation = "Building search index"
            progress.completed_steps = 9
            self._update_progress(progress)
            
            # TODO: Implement search index building
            # await self._build_search_index(global_version_id)
            
            # Step 5: Complete
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
                label_count=label_count
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
                label_count=label_count
            )
    
    async def _sync_incremental_metadata(
        self,
        fo_client,
        global_version_id: int,
        progress: SyncProgress
    ) -> SyncResult:
        """Perform incremental metadata synchronization
        
        Args:
            fo_client: D365 F&O client instance
            global_version_id: Global version ID
            progress: Progress tracker
            
        Returns:
            Sync result
        """
        # For now, fall back to full sync
        # TODO: Implement true incremental sync logic
        logger.info("Incremental sync not yet implemented, falling back to full sync")
        return await self._sync_full_metadata(fo_client, global_version_id, progress)
    
    async def _sync_entities_only(
        self,
        fo_client,
        global_version_id: int,
        progress: SyncProgress
    ) -> SyncResult:
        """Sync only data entities (fast mode)
        
        Args:
            fo_client: D365 F&O client instance
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
            
            entities = await fo_client.get_data_entities()
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
                label_count=0
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
                label_count=0
            )
    
    async def _sync_sharing_mode(
        self,
        fo_client,
        global_version_id: int,
        progress: SyncProgress
    ) -> SyncResult:
        """Sync using cross-environment sharing
        
        Args:
            fo_client: D365 F&O client instance
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
            version_info = await self.version_manager.get_global_version_info(global_version_id)
            if not version_info:
                raise ValueError("Global version not found")
            
            # Find compatible versions
            compatible_versions = await self.version_manager.find_compatible_versions(
                version_info.modules,
                exact_match=True
            )
            
            # Filter out current version and find one with complete metadata
            source_version = None
            for version in compatible_versions:
                if version.global_version_id != global_version_id:
                    if await self.cache._has_complete_metadata(version.global_version_id):
                        source_version = version
                        break
            
            if not source_version:
                # No compatible version found, fall back to full sync
                logger.info("No compatible version found for sharing, falling back to full sync")
                return await self._sync_full_metadata(fo_client, global_version_id, progress)
            
            # Step 2: Copy metadata from compatible version
            progress.phase = "copying"
            progress.current_operation = f"Copying from version {source_version.global_version_id}"
            progress.completed_steps = 2
            self._update_progress(progress)
            
            counts = await self._copy_metadata_between_versions(
                source_version.global_version_id,
                global_version_id
            )
            
            # Step 3: Complete
            progress.phase = "completed"
            progress.current_operation = "Sharing sync completed"
            progress.completed_steps = 3
            self._update_progress(progress)
            
            logger.info(f"Shared metadata from version {source_version.global_version_id}")
            
            return SyncResult(
                success=True,
                error=None,
                duration_ms=0,
                entity_count=counts.get('entities', 0),
                action_count=counts.get('actions', 0),
                enumeration_count=counts.get('enumerations', 0),
                label_count=counts.get('labels', 0)
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
                label_count=0
            )
    
    async def _copy_metadata_between_versions(
        self,
        source_version_id: int,
        target_version_id: int
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
            # Copy data entities
            await db.execute(
                """INSERT INTO data_entities
                   (global_version_id, name, public_entity_name, public_collection_name,
                    label_id, label_text, entity_category, data_service_enabled,
                    data_management_enabled, is_read_only)
                   SELECT ?, name, public_entity_name, public_collection_name,
                          label_id, label_text, entity_category, data_service_enabled,
                          data_management_enabled, is_read_only
                   FROM data_entities
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id)
            )
            counts['entities'] = db.total_changes
            
            # Copy enumerations
            await db.execute(
                """INSERT INTO enumerations
                   (global_version_id, name, label_id, label_text)
                   SELECT ?, name, label_id, label_text
                   FROM enumerations
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id)
            )
            counts['enumerations'] = db.total_changes
            
            # Copy other metadata tables as needed...
            # This is a simplified implementation
            
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
    
    async def recommend_sync_strategy(
        self,
        fo_client,
        global_version_id: int
    ) -> SyncStrategy:
        """Recommend sync strategy based on environment and cache state
        
        Args:
            fo_client: D365 F&O client instance
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
            version_info = await self.version_manager.get_global_version_info(global_version_id)
            if not version_info:
                return SyncStrategy.FULL
            
            # Check for compatible versions (sharing opportunity)
            compatible_versions = await self.version_manager.find_compatible_versions(
                version_info.modules,
                exact_match=True
            )
            
            for version in compatible_versions:
                if version.global_version_id != global_version_id:
                    if await self.cache._has_complete_metadata(version.global_version_id):
                        return SyncStrategy.SHARING_MODE
            
            # Default to full sync for new versions
            return SyncStrategy.FULL
            
        except Exception as e:
            logger.warning(f"Failed to recommend sync strategy: {e}")
            return SyncStrategy.FULL