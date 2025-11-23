"""Sync tools mixin for FastMCP server."""

import logging
from typing import Optional

from ...sync_models import SyncStatus, SyncStrategy
from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class SyncToolsMixin(BaseToolsMixin):
    """Metadata synchronization tools for FastMCP server."""

    def register_sync_tools(self):
        """Register all sync tools with FastMCP."""

        @self.mcp.tool()
        async def d365fo_start_sync(
            strategy: str = "full_without_labels",
            global_version_id: Optional[int] = None,
            profile: str = "default",
        ) -> dict:
            """Start a metadata synchronization session and return a session ID for tracking progress.

            This downloads and caches metadata from D365 F&O including entities, schemas, enumerations, and labels.

            Args:
                strategy: Sync strategy to use. 'full' downloads all metadata, 'entities_only' downloads just entities for quick refresh,
                         'labels_only' downloads only labels, 'full_without_labels' downloads all metadata except labels,
                         'sharing_mode' copies from compatible versions, 'incremental' updates only changes (fallback to full).
                global_version_id: Specific global version ID to sync. If not provided, will detect current version automatically.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                Dictionary with sync session details
            """
            try:
                client = await self._get_client(profile)

                # Initialize metadata first to ensure all components are available
                await client.initialize_metadata()

                if not hasattr(client, "sync_session_manager"):
                    error_response = {
                        "success": False,
                        "error": "Sync session management not available in this client version",
                        "message": "Upgrade to session-based sync manager to access sync functionality",
                    }
                    return error_response

                strategy_enum = SyncStrategy(strategy)
                sync_needed = True
                session_id = None

                # Auto-detect version if not provided
                if global_version_id is None:
                    if (
                        not hasattr(client, "metadata_cache")
                        or client.metadata_cache is None
                    ):
                        error_response = {
                            "success": False,
                            "error": "Metadata cache not available in this client version",
                            "message": "Cannot auto-detect version without metadata cache",
                        }
                        return error_response

                    sync_needed, detected_version_id = (
                        await client.metadata_cache.check_version_and_sync()
                    )
                    if detected_version_id is None:
                        raise ValueError("Could not detect global version ID")
                    global_version_id = detected_version_id

                if sync_needed or strategy_enum == SyncStrategy.LABELS_ONLY:
                    # Start sync session
                    session_id = await client.sync_session_manager.start_sync_session(
                        global_version_id=global_version_id,
                        strategy=strategy_enum,
                        initiated_by="mcp",
                    )

                response = {
                    "success": True,
                    "session_id": (
                        session_id
                        if sync_needed or strategy_enum == SyncStrategy.LABELS_ONLY
                        else None
                    ),
                    "global_version_id": global_version_id,
                    "strategy": strategy,
                    "message": (
                        f"Sync session {session_id} started successfully"
                        if sync_needed or strategy_enum == SyncStrategy.LABELS_ONLY
                        else f"Metadata already up to date at version {global_version_id}, no sync needed"
                    ),
                    "instructions": (
                        f"Use d365fo_get_sync_progress with session_id '{session_id}' to monitor progress"
                        if sync_needed or strategy_enum == SyncStrategy.LABELS_ONLY
                        else None
                    ),
                }

                return response

            except Exception as e:
                logger.error(f"Start sync failed: {e}")
                error_response = {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_start_sync",
                    "arguments": {
                        "strategy": strategy,
                        "global_version_id": global_version_id,
                        "profile": profile,
                    },
                }
                return error_response

        @self.mcp.tool()
        async def d365fo_get_sync_progress(
            session_id: str, profile: str = "default"
        ) -> dict:
            """Get detailed progress information for a specific sync session including current phase, completion percentage, items processed, and estimated time remaining.

            Args:
                session_id: Session ID of the sync operation to check progress for
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                Dictionary with sync progress
            """
            try:
                client = await self._get_client(profile)

                # Initialize metadata to ensure sync session manager is available
                await client.initialize_metadata()

                if not hasattr(client, "sync_session_manager"):
                    error_response = {
                        "success": False,
                        "error": "Sync session management not available in this client version",
                        "session_id": session_id,
                    }
                    return error_response

                # Get session details
                session = client.sync_session_manager.get_sync_session(session_id)

                if not session:
                    error_response = {
                        "success": False,
                        "error": f"Session {session_id} not found",
                        "session_id": session_id,
                    }
                    return error_response

                # Convert session to detailed progress response
                response = {
                    "success": True,
                    "session": session.to_dict(),
                    "summary": {
                        "status": session.status,
                        "progress_percent": round(session.progress_percent, 1),
                        "current_phase": session.current_phase,
                        "current_activity": session.current_activity,
                        "estimated_remaining_seconds": session.estimate_remaining_time(),
                        "is_running": session.status == SyncStatus.RUNNING,
                        "can_cancel": session.can_cancel,
                    },
                }

                return response

            except Exception as e:
                logger.error(f"Get sync progress failed: {e}")
                error_response = {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_get_sync_progress",
                    "arguments": {"session_id": session_id, "profile": profile},
                }
                return error_response

        @self.mcp.tool()
        async def d365fo_cancel_sync(session_id: str, profile: str = "default") -> dict:
            """Cancel a running sync session. Only sessions that are currently running and marked as cancellable can be cancelled.

            Args:
                session_id: Session ID of the sync operation to cancel
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                Dictionary with cancellation result
            """
            try:
                client = await self._get_client(profile)

                # Initialize metadata to ensure sync session manager is available
                await client.initialize_metadata()

                if not hasattr(client, "sync_session_manager"):
                    error_response = {
                        "success": False,
                        "error": "Sync session management not available in this client version",
                        "session_id": session_id,
                    }
                    return error_response

                # Cancel session
                cancelled = await client.sync_session_manager.cancel_sync_session(
                    session_id
                )

                response = {
                    "success": cancelled,
                    "session_id": session_id,
                    "message": f"Session {session_id} {'cancelled' if cancelled else 'could not be cancelled'}",
                    "details": "Session may not be cancellable if already completed or failed",
                }

                return response

            except Exception as e:
                logger.error(f"Cancel sync failed: {e}")
                error_response = {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_cancel_sync",
                    "arguments": {"session_id": session_id, "profile": profile},
                }
                return error_response

        @self.mcp.tool()
        async def d365fo_list_sync_sessions(profile: str = "default") -> dict:
            """Get a list of all currently active sync sessions with their status, progress, and details.

            Args:
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                Dictionary with active sync sessions
            """
            try:
                client = await self._get_client(profile)

                # Initialize metadata to ensure sync session manager is available
                await client.initialize_metadata()

                if not hasattr(client, "sync_session_manager"):
                    error_response = {
                        "success": False,
                        "error": "Sync session management not available in this client version",
                        "message": "Upgrade to session-based sync manager to access session listing",
                    }
                    return error_response

                # Get active sessions
                active_sessions = client.sync_session_manager.get_active_sessions()

                response = {
                    "success": True,
                    "active_sessions": [
                        session.to_dict() for session in active_sessions
                    ],
                    "total_count": len(active_sessions),
                    "running_count": len(
                        [s for s in active_sessions if s.status == SyncStatus.RUNNING]
                    ),
                    "summary": {
                        "has_running_sessions": any(
                            s.status == SyncStatus.RUNNING for s in active_sessions
                        ),
                        "latest_session": (
                            active_sessions[-1].to_dict() if active_sessions else None
                        ),
                    },
                }

                return response

            except Exception as e:
                logger.error(f"List sync sessions failed: {e}")
                error_response = {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_list_sync_sessions",
                    "arguments": {"profile": profile},
                }
                return error_response

        @self.mcp.tool()
        async def d365fo_get_sync_history(
            limit: int = 20, profile: str = "default"
        ) -> dict:
            """Get the history of completed sync sessions including success/failure status, duration, and statistics.

            Args:
                limit: Maximum number of historical sessions to return (default: 20, max: 100)
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                Dictionary with sync history
            """
            try:
                # Validate limit parameter
                limit = max(1, min(limit, 100))  # Clamp between 1 and 100

                client = await self._get_client(profile)

                # Initialize metadata to ensure sync session manager is available
                await client.initialize_metadata()

                if not hasattr(client, "sync_session_manager"):
                    error_response = {
                        "success": False,
                        "error": "Sync session management not available in this client version",
                        "message": "Upgrade to session-based sync manager to access history",
                    }
                    return error_response

                # Get session history
                history = client.sync_session_manager.get_session_history(limit)

                response = {
                    "success": True,
                    "history": [session.to_dict() for session in history],
                    "total_count": len(history),
                    "summary": {
                        "successful_syncs": len(
                            [s for s in history if s.status == SyncStatus.COMPLETED]
                        ),
                        "failed_syncs": len(
                            [s for s in history if s.status == SyncStatus.FAILED]
                        ),
                        "cancelled_syncs": len(
                            [s for s in history if s.status == SyncStatus.CANCELLED]
                        ),
                        "average_duration": (
                            sum(
                                s.duration_seconds
                                for s in history
                                if s.duration_seconds
                            )
                            / len([s for s in history if s.duration_seconds])
                            if history
                            else 0
                        ),
                    },
                }

                return response

            except Exception as e:
                logger.error(f"Get sync history failed: {e}")
                error_response = {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_get_sync_history",
                    "arguments": {"limit": limit, "profile": profile},
                }
                return error_response
