"""Enhanced sync manager with session-based progress tracking."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from ..metadata_api import MetadataAPIOperations

from ..models import (
    DataEntityInfo,
    EnumerationInfo,
    LabelInfo,
    PublicEntityInfo,
    SyncResult,
    SyncStrategy,
)
from ..sync_models import (
    SyncActivity,
    SyncPhase,
    SyncSession,
    SyncSessionSummary,
    SyncStatus,
)
from .cache_v2 import MetadataCacheV2

logger = logging.getLogger(__name__)


class SyncSessionManager:
    """Enhanced sync manager with session-based progress tracking."""

    def __init__(self, cache: MetadataCacheV2, metadata_api: "MetadataAPIOperations"):
        """Initialize sync session manager

        Args:
            cache: Metadata cache v2 instance
            metadata_api: Metadata API operations instance
        """
        self.cache = cache
        self.metadata_api = metadata_api
        self.version_manager = cache.version_manager

        # Session management
        self._active_sessions: Dict[str, SyncSession] = {}
        self._session_history: List[SyncSessionSummary] = []
        self._progress_callbacks: Dict[str, List[Callable[[SyncSession], None]]] = {}
        self._max_history = 100  # Keep last 100 sessions in memory

    async def start_sync_session(
        self,
        global_version_id: int,
        strategy: SyncStrategy = SyncStrategy.FULL,
        initiated_by: str = "user"
    ) -> str:
        """Start new sync session and return session ID

        Args:
            global_version_id: Global version ID to sync
            strategy: Sync strategy to use
            initiated_by: Who initiated the sync (user, system, mcp, etc.)

        Returns:
            Session ID for tracking progress

        Raises:
            ValueError: If sync already running for this version
        """
        # Check if sync already running for this version
        for session in self._active_sessions.values():
            if (session.global_version_id == global_version_id and 
                session.status == SyncStatus.RUNNING):
                raise ValueError(f"Sync already running for version {global_version_id}")

        # Create new session
        session = SyncSession(
            global_version_id=global_version_id,
            strategy=strategy,
            status=SyncStatus.PENDING,
            start_time=datetime.now(timezone.utc),
            initiated_by=initiated_by
        )

        # Initialize phases based on strategy
        session.phases = self._initialize_phases(strategy)

        # Store session
        self._active_sessions[session.session_id] = session

        # Start background sync
        asyncio.create_task(self._execute_sync_session(session.session_id))

        logger.info(f"Started sync session {session.session_id} for version {global_version_id} with strategy {strategy}")
        return session.session_id

    def _initialize_phases(self, strategy: SyncStrategy) -> Dict[SyncPhase, SyncActivity]:
        """Initialize phases based on sync strategy"""
        phases = {}

        if strategy == SyncStrategy.FULL:
            phase_list = [
                SyncPhase.INITIALIZING,
                SyncPhase.VERSION_CHECK,
                SyncPhase.ENTITIES,
                SyncPhase.SCHEMAS,
                SyncPhase.ENUMERATIONS,
                SyncPhase.LABELS,
                SyncPhase.INDEXING,
                SyncPhase.FINALIZING
            ]
        elif strategy == SyncStrategy.ENTITIES_ONLY:
            phase_list = [
                SyncPhase.INITIALIZING,
                SyncPhase.VERSION_CHECK,
                SyncPhase.ENTITIES,
                SyncPhase.FINALIZING
            ]
        elif strategy == SyncStrategy.SHARING_MODE:
            phase_list = [
                SyncPhase.INITIALIZING,
                SyncPhase.VERSION_CHECK,
                SyncPhase.FINALIZING
            ]
        else:
            phase_list = [SyncPhase.INITIALIZING, SyncPhase.FINALIZING]

        for phase in phase_list:
            phases[phase] = SyncActivity(
                name=phase.value.replace('_', ' ').title(),
                status=SyncStatus.PENDING
            )

        return phases

    async def _execute_sync_session(self, session_id: str):
        """Execute sync session with detailed progress tracking"""
        session = self._active_sessions.get(session_id)
        if not session:
            return

        try:
            session.status = SyncStatus.RUNNING
            self._notify_progress(session_id)

            # Use enhanced sync logic with detailed progress updates
            result = await self._sync_with_detailed_progress(session)

            session.result = result
            session.status = SyncStatus.COMPLETED if result.success else SyncStatus.FAILED
            session.end_time = datetime.now(timezone.utc)
            session.progress_percent = 100.0

        except Exception as e:
            logger.error(f"Sync session {session_id} failed: {e}")
            session.error = str(e)
            session.status = SyncStatus.FAILED
            session.end_time = datetime.now(timezone.utc)

        finally:
            self._notify_progress(session_id)
            self._archive_session(session_id)

    async def _sync_with_detailed_progress(self, session: SyncSession) -> SyncResult:
        """Execute sync with granular progress updates"""
        
        # Phase 1: Initializing
        await self._update_phase_progress(session, SyncPhase.INITIALIZING, SyncStatus.RUNNING)
        await asyncio.sleep(0.1)  # Simulate initialization
        await self._complete_phase(session, SyncPhase.INITIALIZING)

        # Phase 2: Version Check
        await self._update_phase_progress(session, SyncPhase.VERSION_CHECK, SyncStatus.RUNNING)
        
        # Update sync status in database
        await self.version_manager.update_sync_status(
            self.cache._environment_id, session.global_version_id, "syncing"
        )
        
        await self._complete_phase(session, SyncPhase.VERSION_CHECK)

        if session.strategy == SyncStrategy.FULL:
            # Phase 3: Entities
            await self._sync_entities_with_progress(session)

            # Phase 4: Schemas  
            await self._sync_schemas_with_progress(session)

            # Phase 5: Enumerations
            await self._sync_enumerations_with_progress(session)

            # Phase 6: Labels
            await self._sync_labels_with_progress(session)

            # Phase 7: Indexing
            await self._sync_indexing_with_progress(session)

        elif session.strategy == SyncStrategy.ENTITIES_ONLY:
            # Only sync entities
            await self._sync_entities_with_progress(session)

        elif session.strategy == SyncStrategy.SHARING_MODE:
            # Copy from compatible version
            await self._sync_sharing_with_progress(session)

        # Final phase
        await self._update_phase_progress(session, SyncPhase.FINALIZING, SyncStatus.RUNNING)
        
        # Mark cache sync completed if successful
        entity_count = session.phases.get(SyncPhase.ENTITIES, SyncActivity("", SyncStatus.PENDING)).items_processed
        action_count = session.phases.get(SyncPhase.SCHEMAS, SyncActivity("", SyncStatus.PENDING)).items_processed
        enumeration_count = session.phases.get(SyncPhase.ENUMERATIONS, SyncActivity("", SyncStatus.PENDING)).items_processed
        label_count = session.phases.get(SyncPhase.LABELS, SyncActivity("", SyncStatus.PENDING)).items_processed
        
        await self.cache.mark_sync_completed(
            session.global_version_id,
            entity_count,
            action_count,
            enumeration_count,
            label_count,
        )
        
        # Update version manager
        duration_ms = int((datetime.now(timezone.utc) - session.start_time).total_seconds() * 1000)
        await self.version_manager.update_sync_status(
            self.cache._environment_id,
            session.global_version_id,
            "completed",
            duration_ms,
        )
        
        await self._complete_phase(session, SyncPhase.FINALIZING)

        return SyncResult(
            success=True,
            error=None,
            duration_ms=duration_ms,
            entity_count=entity_count,
            action_count=action_count,
            enumeration_count=enumeration_count,
            label_count=label_count
        )

    async def _sync_entities_with_progress(self, session: SyncSession):
        """Sync entities with detailed progress reporting"""
        phase = SyncPhase.ENTITIES
        await self._update_phase_progress(session, phase, SyncStatus.RUNNING)

        activity = session.phases[phase]
        activity.current_item = "Fetching entity list..."
        self._notify_progress(session.session_id)

        try:
            # Get entities
            entities = await self._get_data_entities()
            activity.items_total = len(entities) if entities else 0

            if entities:
                for i, entity in enumerate(entities):
                    activity.current_item = f"Processing {entity.name}"
                    activity.items_processed = i + 1
                    activity.progress_percent = ((i + 1) / len(entities)) * 100

                    # Store entity
                    await self.cache.store_data_entities(session.global_version_id, [entity])

                    # Notify progress every 10 entities or at completion
                    if (i + 1) % 10 == 0 or i == len(entities) - 1:
                        self._notify_progress(session.session_id)

            await self._complete_phase(session, phase)

        except Exception as e:
            logger.error(f"Entity sync failed: {e}")
            activity.error = str(e)
            activity.status = SyncStatus.FAILED
            raise

    async def _sync_schemas_with_progress(self, session: SyncSession):
        """Sync schemas with detailed progress reporting"""
        phase = SyncPhase.SCHEMAS
        await self._update_phase_progress(session, phase, SyncStatus.RUNNING)

        activity = session.phases[phase]
        activity.current_item = "Fetching public entities..."
        self._notify_progress(session.session_id)

        try:
            public_entities = await self._get_public_entities()
            activity.items_total = len(public_entities) if public_entities else 0
            action_count = 0

            if public_entities:
                for i, entity in enumerate(public_entities):
                    activity.current_item = f"Processing schema for {entity.name}"
                    activity.items_processed = i + 1
                    activity.progress_percent = ((i + 1) / len(public_entities)) * 100

                    await self.cache.store_public_entity_schema(session.global_version_id, entity)
                    action_count += len(entity.actions)

                    # Notify progress every 5 entities
                    if (i + 1) % 5 == 0 or i == len(public_entities) - 1:
                        self._notify_progress(session.session_id)

            # Store action count for result
            activity.items_processed = action_count
            await self._complete_phase(session, phase)

        except Exception as e:
            logger.error(f"Schema sync failed: {e}")
            activity.error = str(e)
            activity.status = SyncStatus.FAILED
            raise

    async def _sync_enumerations_with_progress(self, session: SyncSession):
        """Sync enumerations with detailed progress reporting"""
        phase = SyncPhase.ENUMERATIONS
        await self._update_phase_progress(session, phase, SyncStatus.RUNNING)

        activity = session.phases[phase]
        activity.current_item = "Fetching enumerations..."
        self._notify_progress(session.session_id)

        try:
            enumerations = await self._get_public_enumerations()
            activity.items_total = len(enumerations) if enumerations else 0

            if enumerations:
                await self.cache.store_enumerations(session.global_version_id, enumerations)
                activity.items_processed = len(enumerations)
                activity.progress_percent = 100.0

            self._notify_progress(session.session_id)
            await self._complete_phase(session, phase)

        except Exception as e:
            logger.warning(f"Enumeration sync failed: {e}")
            activity.error = str(e)
            activity.status = SyncStatus.FAILED
            # Don't raise - enumerations are optional

    async def _sync_labels_with_progress(self, session: SyncSession):
        """Sync labels with detailed progress reporting"""
        phase = SyncPhase.LABELS
        await self._update_phase_progress(session, phase, SyncStatus.RUNNING)

        activity = session.phases[phase]
        activity.current_item = "Syncing common labels..."
        self._notify_progress(session.session_id)

        try:
            # Get previously synced data for label extraction
            entities_activity = session.phases.get(SyncPhase.ENTITIES)
            schemas_activity = session.phases.get(SyncPhase.SCHEMAS) 
            enums_activity = session.phases.get(SyncPhase.ENUMERATIONS)

            # For progress estimation, assume we'll cache some labels
            activity.items_total = 100  # Estimate

            # Get synced data
            entities = await self.cache.get_data_entities(session.global_version_id)
            public_entities = await self.cache.get_public_entities(session.global_version_id)
            enumerations = await self.cache.get_enumerations(session.global_version_id)

            # Sync common labels using the existing method
            label_count = await self._sync_common_labels(
                session.global_version_id,
                entities,
                public_entities,
                enumerations,
            )

            activity.items_processed = label_count
            activity.progress_percent = 100.0
            self._notify_progress(session.session_id)
            await self._complete_phase(session, phase)

        except Exception as e:
            logger.warning(f"Label sync failed: {e}")
            activity.error = str(e)
            activity.status = SyncStatus.FAILED
            # Don't raise - labels are optional

    async def _sync_indexing_with_progress(self, session: SyncSession):
        """Sync indexing with detailed progress reporting"""
        phase = SyncPhase.INDEXING
        await self._update_phase_progress(session, phase, SyncStatus.RUNNING)

        activity = session.phases[phase]
        activity.current_item = "Building search indexes..."
        self._notify_progress(session.session_id)

        try:
            # TODO: Implement search index building
            # For now, just simulate
            await asyncio.sleep(0.5)
            
            activity.progress_percent = 100.0
            self._notify_progress(session.session_id)
            await self._complete_phase(session, phase)

        except Exception as e:
            logger.warning(f"Indexing failed: {e}")
            activity.error = str(e)
            activity.status = SyncStatus.FAILED
            # Don't raise - indexing is optional

    async def _sync_sharing_with_progress(self, session: SyncSession):
        """Sync using sharing mode with detailed progress reporting"""
        phase = SyncPhase.SCHEMAS  # Reuse schemas phase for sharing
        await self._update_phase_progress(session, phase, SyncStatus.RUNNING)

        activity = session.phases[phase]
        activity.current_item = "Looking for compatible versions..."
        self._notify_progress(session.session_id)

        try:
            # Get version info
            version_info = await self.version_manager.get_global_version_info(
                session.global_version_id
            )
            if not version_info:
                raise ValueError("Global version not found")

            # Find compatible versions
            compatible_versions = await self.version_manager.find_compatible_versions(
                version_info.modules, exact_match=True
            )

            # Find source version
            source_version = None
            for version in compatible_versions:
                if version.global_version_id != session.global_version_id:
                    if await self.cache._has_complete_metadata(version.global_version_id):
                        source_version = version
                        break

            if not source_version:
                # No compatible version, fall back to full sync
                logger.info("No compatible version found for sharing, falling back to full sync")
                await self._sync_entities_with_progress(session)
                return

            activity.current_item = f"Copying from version {source_version.global_version_id}"
            self._notify_progress(session.session_id)

            # Copy metadata
            counts = await self._copy_metadata_between_versions(
                source_version.global_version_id, session.global_version_id
            )

            activity.items_processed = counts.get("entities", 0)
            activity.progress_percent = 100.0
            self._notify_progress(session.session_id)
            await self._complete_phase(session, phase)

        except Exception as e:
            logger.error(f"Sharing sync failed: {e}")
            activity.error = str(e)
            activity.status = SyncStatus.FAILED
            raise

    async def _update_phase_progress(self, session: SyncSession, phase: SyncPhase, status: SyncStatus):
        """Update phase progress"""
        if phase in session.phases:
            activity = session.phases[phase]
            activity.status = status
            if status == SyncStatus.RUNNING:
                activity.start_time = datetime.now(timezone.utc)
                session.current_phase = phase
                session.current_activity = activity.name

            session.progress_percent = session.get_overall_progress()
            self._notify_progress(session.session_id)

    async def _complete_phase(self, session: SyncSession, phase: SyncPhase):
        """Mark phase as completed"""
        if phase in session.phases:
            activity = session.phases[phase]
            activity.status = SyncStatus.COMPLETED
            activity.end_time = datetime.now(timezone.utc)
            activity.progress_percent = 100.0

            session.progress_percent = session.get_overall_progress()
            self._notify_progress(session.session_id)

    def get_sync_session(self, session_id: str) -> Optional[SyncSession]:
        """Get sync session by ID"""
        return self._active_sessions.get(session_id)

    def get_active_sessions(self) -> List[SyncSessionSummary]:
        """Get all active sync sessions"""
        return [
            SyncSessionSummary(
                session_id=session.session_id,
                global_version_id=session.global_version_id,
                strategy=session.strategy,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                progress_percent=session.progress_percent,
                current_phase=session.current_phase,
                current_activity=session.current_activity,
                initiated_by=session.initiated_by,
                duration_seconds=int((datetime.now(timezone.utc) - session.start_time).total_seconds()) if session.start_time else None
            )
            for session in self._active_sessions.values()
        ]

    def get_session_history(self, limit: int = 50) -> List[SyncSessionSummary]:
        """Get sync session history"""
        return self._session_history[-limit:]

    async def cancel_sync_session(self, session_id: str) -> bool:
        """Cancel running sync session"""
        session = self._active_sessions.get(session_id)
        if not session or not session.can_cancel:
            return False

        if session.status == SyncStatus.RUNNING:
            session.status = SyncStatus.CANCELLED
            session.end_time = datetime.now(timezone.utc)
            session.error = "Cancelled by user"
            self._notify_progress(session_id)
            self._archive_session(session_id)
            return True

        return False

    def add_progress_callback(self, session_id: str, callback: Callable[[SyncSession], None]):
        """Add progress callback for specific session"""
        if session_id not in self._progress_callbacks:
            self._progress_callbacks[session_id] = []
        self._progress_callbacks[session_id].append(callback)

    def _notify_progress(self, session_id: str):
        """Notify all callbacks for session progress"""
        session = self._active_sessions.get(session_id)
        if not session:
            return

        callbacks = self._progress_callbacks.get(session_id, [])
        for callback in callbacks:
            try:
                callback(session)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _archive_session(self, session_id: str):
        """Archive completed session"""
        session = self._active_sessions.pop(session_id, None)
        if session:
            summary = SyncSessionSummary(
                session_id=session.session_id,
                global_version_id=session.global_version_id,
                strategy=session.strategy,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                progress_percent=session.progress_percent,
                current_phase=session.current_phase,
                current_activity=session.current_activity,
                initiated_by=session.initiated_by,
                duration_seconds=int((session.end_time - session.start_time).total_seconds()) if session.start_time and session.end_time else None
            )
            
            self._session_history.append(summary)
            
            # Limit history size
            if len(self._session_history) > self._max_history:
                self._session_history = self._session_history[-self._max_history:]
            
            # Clean up callbacks
            self._progress_callbacks.pop(session_id, None)

    # Delegate to metadata API operations and cache methods
    async def _get_data_entities(self) -> List[DataEntityInfo]:
        """Get data entities using MetadataAPIOperations"""
        try:
            entities = await self.metadata_api.get_all_data_entities()
            return entities
        except Exception as e:
            logger.error(f"Error getting data entities: {e}")
            raise

    async def _get_public_entities(self) -> List[PublicEntityInfo]:
        """Get public entities with details"""
        try:
            return await self.metadata_api.get_all_public_entities_with_details(
                resolve_labels=False
            )
        except Exception as e:
            logger.error(f"Error getting public entities: {e}")
            return []

    async def _get_public_enumerations(self) -> List[EnumerationInfo]:
        """Get public enumerations with details"""
        try:
            enumerations = await self.metadata_api.get_all_public_enumerations_with_details(
                resolve_labels=False
            )
            return enumerations
        except Exception as e:
            logger.error(f"Error getting public enumerations: {e}")
            raise

    async def _sync_common_labels(
        self,
        global_version_id: int,
        entities: List[DataEntityInfo],
        public_entities: List[PublicEntityInfo],
        enumerations: List[EnumerationInfo],
    ) -> int:
        """Sync common labels from entities, schemas, and enumerations"""
        try:
            # Extract label IDs from entities, schemas, and enumerations
            label_ids = set()
            
            # From entities
            for entity in entities:
                if entity.label_id:
                    label_ids.add(entity.label_id)
            
            # From public entities (schemas)
            for entity in public_entities:
                if entity.label_id:
                    label_ids.add(entity.label_id)
                for field in entity.fields:
                    if field.label_id:
                        label_ids.add(field.label_id)
                for action in entity.actions:
                    if action.label_id:
                        label_ids.add(action.label_id)
            
            # From enumerations
            for enum in enumerations:
                if enum.label_id:
                    label_ids.add(enum.label_id)
                for member in enum.members:
                    if member.label_id:
                        label_ids.add(member.label_id)
            
            # Fetch and store labels
            label_count = 0
            if label_ids:
                labels = await self.metadata_api.get_labels(list(label_ids))
                if labels:
                    await self.cache.store_labels(global_version_id, labels)
                    label_count = len(labels)
            
            return label_count
            
        except Exception as e:
            logger.warning(f"Error syncing common labels: {e}")
            return 0

    async def _copy_metadata_between_versions(self, source_version_id: int, target_version_id: int) -> Dict[str, int]:
        """Copy metadata between global versions"""
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
                (target_version_id, source_version_id),
            )
            counts["entities"] = db.total_changes

            # Copy public entities
            await db.execute(
                """INSERT INTO public_entities
                   (global_version_id, name, public_collection_name, label_id, label_text,
                    entity_category, is_read_only, data_source_name)
                   SELECT ?, name, public_collection_name, label_id, label_text,
                          entity_category, is_read_only, data_source_name
                   FROM public_entities
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            # Copy entity fields
            await db.execute(
                """INSERT INTO entity_fields
                   (global_version_id, entity_name, field_name, odata_type, xpp_type,
                    is_key, is_nullable, max_length, scale, precision, label_id, label_text)
                   SELECT ?, entity_name, field_name, odata_type, xpp_type,
                          is_key, is_nullable, max_length, scale, precision, label_id, label_text
                   FROM entity_fields
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            # Copy entity actions
            await db.execute(
                """INSERT INTO entity_actions
                   (global_version_id, entity_name, action_name, is_function, label_id, label_text)
                   SELECT ?, entity_name, action_name, is_function, label_id, label_text
                   FROM entity_actions
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            # Copy enumerations
            await db.execute(
                """INSERT INTO enumerations
                   (global_version_id, name, label_id, label_text, is_flags)
                   SELECT ?, name, label_id, label_text, is_flags
                   FROM enumerations
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            # Copy enumeration members
            await db.execute(
                """INSERT INTO enumeration_members
                   (global_version_id, enumeration_name, member_name, member_value, label_id, label_text)
                   SELECT ?, enumeration_name, member_name, member_value, label_id, label_text
                   FROM enumeration_members
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            # Copy labels
            await db.execute(
                """INSERT INTO labels
                   (global_version_id, label_id, label_text)
                   SELECT ?, label_id, label_text
                   FROM labels
                   WHERE global_version_id = ?""",
                (target_version_id, source_version_id),
            )

            await db.commit()

        return counts