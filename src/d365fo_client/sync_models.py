"""Enhanced sync models for progress reporting and session management."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Dict, List, Optional, Set

# Removed import to avoid circular dependency - models will be defined here


class SyncStrategy(StrEnum):
    """Metadata synchronization strategies"""

    FULL = "full"
    INCREMENTAL = "incremental"
    ENTITIES_ONLY = "entities_only"
    LABELS_ONLY = "labels_only"
    SHARING_MODE = "sharing_mode"
    FULL_WITHOUT_LABELS = "full_without_labels"


class SyncStatus(StrEnum):
    """Sync operation status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class SyncPhase(StrEnum):
    """Detailed sync phases"""

    INITIALIZING = "initializing"
    VERSION_CHECK = "version_check"
    ENTITIES = "entities"
    SCHEMAS = "schemas"
    ENUMERATIONS = "enumerations"
    LABELS = "labels"
    INDEXING = "indexing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SyncResult:
    """Enhanced synchronization result with sharing metrics"""

    sync_type: str  # full|incremental|linked|skipped|failed
    entities_synced: int = 0
    actions_synced: int = 0
    enumerations_synced: int = 0
    labels_synced: int = 0
    duration_ms: float = 0.0
    success: bool = True
    errors: List[str] = field(default_factory=list)

    # Enhanced metrics for V2
    entities_shared: int = 0
    actions_shared: int = 0
    enumerations_shared: int = 0
    labels_shared: int = 0
    cache_hit_rate: float = 0.0
    sharing_efficiency: float = 0.0  # Percentage of items shared vs downloaded
    source_version_id: Optional[int] = None  # Version we shared from

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "sync_type": self.sync_type,
            "entities_synced": self.entities_synced,
            "actions_synced": self.actions_synced,
            "enumerations_synced": self.enumerations_synced,
            "labels_synced": self.labels_synced,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "errors": self.errors,
            "entities_shared": self.entities_shared,
            "actions_shared": self.actions_shared,
            "enumerations_shared": self.enumerations_shared,
            "labels_shared": self.labels_shared,
            "cache_hit_rate": self.cache_hit_rate,
            "sharing_efficiency": self.sharing_efficiency,
            "source_version_id": self.source_version_id,
        }


@dataclass
class SyncProgress:
    """Sync progress tracking"""

    global_version_id: int
    strategy: SyncStrategy
    phase: str
    total_steps: int
    completed_steps: int
    current_operation: str
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "global_version_id": self.global_version_id,
            "strategy": self.strategy,
            "phase": self.phase,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "current_operation": self.current_operation,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "error": self.error,
        }


@dataclass
class SyncActivity:
    """Individual sync activity within a phase"""

    name: str
    status: SyncStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress_percent: float = 0.0
    items_processed: int = 0
    items_total: Optional[int] = None
    current_item: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "progress_percent": self.progress_percent,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "current_item": self.current_item,
            "error": self.error,
        }


@dataclass
class SyncSession:
    """Complete sync session with detailed tracking"""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    global_version_id: int = 0
    strategy: SyncStrategy = SyncStrategy.FULL
    status: SyncStatus = SyncStatus.PENDING

    # Overall progress
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    progress_percent: float = 0.0

    # Current state
    current_phase: SyncPhase = SyncPhase.INITIALIZING
    current_activity: Optional[str] = None

    # Phase tracking
    phases: Dict[SyncPhase, SyncActivity] = field(default_factory=dict)

    # Results
    result: Optional[SyncResult] = None
    error: Optional[str] = None

    # Metadata
    initiated_by: str = "system"  # user, system, scheduled, mcp
    can_cancel: bool = True

    # Collected label IDs during sync for efficient label processing
    collected_label_ids: Set[str] = field(default_factory=set)

    def get_overall_progress(self) -> float:
        """Calculate overall progress across all phases"""
        if not self.phases:
            return 0.0

        total_weight = len(self.phases)
        completed_weight = sum(
            (
                1.0
                if activity.status == SyncStatus.COMPLETED
                else activity.progress_percent / 100.0
            )
            for activity in self.phases.values()
        )
        return min(100.0, (completed_weight / total_weight) * 100.0)

    def get_current_activity_detail(self) -> Optional[SyncActivity]:
        """Get current running activity details"""
        if self.current_phase in self.phases:
            return self.phases[self.current_phase]
        return None

    def estimate_remaining_time(self) -> Optional[int]:
        """Estimate remaining time in seconds"""
        if not self.start_time or self.progress_percent <= 0:
            return None

        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        if self.progress_percent >= 100:
            return 0

        estimated_total = elapsed / (self.progress_percent / 100.0)
        return max(0, int(estimated_total - elapsed))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "global_version_id": self.global_version_id,
            "strategy": self.strategy,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "progress_percent": self.progress_percent,
            "current_phase": self.current_phase,
            "current_activity": self.current_activity,
            "phases": {
                phase.value: activity.to_dict()
                for phase, activity in self.phases.items()
            },
            "result": (
                self.result.to_dict()
                if self.result and hasattr(self.result, "to_dict")
                else None
            ),
            "error": self.error,
            "initiated_by": self.initiated_by,
            "can_cancel": self.can_cancel,
            "estimated_remaining_seconds": self.estimate_remaining_time(),
        }


@dataclass
class SyncSessionSummary:
    """Lightweight sync session summary for listing"""

    session_id: str
    global_version_id: int
    strategy: SyncStrategy
    status: SyncStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress_percent: float = 0.0
    current_phase: SyncPhase = SyncPhase.INITIALIZING
    current_activity: Optional[str] = None
    initiated_by: str = "system"
    duration_seconds: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "global_version_id": self.global_version_id,
            "strategy": self.strategy,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "progress_percent": self.progress_percent,
            "current_phase": self.current_phase,
            "current_activity": self.current_activity,
            "initiated_by": self.initiated_by,
            "duration_seconds": self.duration_seconds,
        }
