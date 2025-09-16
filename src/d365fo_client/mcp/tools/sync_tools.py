"""Sync management tools for MCP server."""

import json
import logging
from typing import List

from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager
from ...sync_models import SyncStrategy
from ...sync_models import SyncStatus

logger = logging.getLogger(__name__)


class SyncTools:
    """Sync management tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize sync tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    def get_tools(self) -> List[Tool]:
        """Get list of sync tools.

        Returns:
            List of Tool definitions
        """
        return [
            self._get_start_sync_tool(),
            self._get_sync_progress_tool(),
            self._get_cancel_sync_tool(),
            self._get_list_sync_sessions_tool(),
            self._get_sync_history_tool(),
        ]

    def _get_start_sync_tool(self) -> Tool:
        """Get start sync tool definition."""
        return Tool(
            name="d365fo_start_sync",
            description="Start a metadata synchronization session and return a session ID for tracking progress. This downloads and caches metadata from D365 F&O including entities, schemas, enumerations, and labels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "enum": ["full", "entities_only", "labels_only", "full_without_labels", "sharing_mode", "incremental"],
                        "description": "Sync strategy to use. 'full' downloads all metadata, 'entities_only' downloads just entities for quick refresh, 'labels_only' downloads only labels, 'full_without_labels' downloads all metadata except labels, 'sharing_mode' copies from compatible versions, 'incremental' updates only changes (fallback to full).",
                        "default": "full_without_labels"
                    },
                    "global_version_id": {
                        "type": "integer", 
                        "description": "Specific global version ID to sync. If not provided, will detect current version automatically."
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)"
                    }
                },
                "additionalProperties": False,
            },
        )

    def _get_sync_progress_tool(self) -> Tool:
        """Get sync progress tool definition."""
        return Tool(
            name="d365fo_get_sync_progress",
            description="Get detailed progress information for a specific sync session including current phase, completion percentage, items processed, and estimated time remaining.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID of the sync operation to check progress for"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)"
                    }
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
        )

    def _get_cancel_sync_tool(self) -> Tool:
        """Get cancel sync tool definition."""
        return Tool(
            name="d365fo_cancel_sync",
            description="Cancel a running sync session. Only sessions that are currently running and marked as cancellable can be cancelled.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID of the sync operation to cancel"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)"
                    }
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
        )

    def _get_list_sync_sessions_tool(self) -> Tool:
        """Get list sync sessions tool definition."""
        return Tool(
            name="d365fo_list_sync_sessions",
            description="Get a list of all currently active sync sessions with their status, progress, and details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)"
                    }
                },
                "additionalProperties": False,
            },
        )

    def _get_sync_history_tool(self) -> Tool:
        """Get sync history tool definition."""
        return Tool(
            name="d365fo_get_sync_history",
            description="Get the history of completed sync sessions including success/failure status, duration, and statistics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of historical sessions to return (default: 20, max: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)"
                    }
                },
                "additionalProperties": False,
            },
        )

    async def execute_start_sync(self, arguments: dict) -> List[TextContent]:
        """Execute start sync operation."""
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            # Initialize metadata first to ensure all components are available
            await client.initialize_metadata()

            if not hasattr(client, 'sync_session_manager'):
                # Fall back to the original sync manager if session manager not available
                return await self._fallback_start_sync(client, arguments)

            strategy_str = arguments.get("strategy", "full_without_labels")
            strategy = SyncStrategy(strategy_str)
            global_version_id = arguments.get("global_version_id")
            sync_needed = True
            session_id = None

            # Auto-detect version if not provided
            if global_version_id is None:
                sync_needed, detected_version_id = await client.metadata_cache.check_version_and_sync()
                if detected_version_id is None:
                    raise ValueError("Could not detect global version ID")
                global_version_id = detected_version_id

            if sync_needed or strategy == SyncStrategy.LABELS_ONLY:
                # Start sync session
                session_id = await client.sync_session_manager.start_sync_session(
                    global_version_id=global_version_id,
                    strategy=strategy,
                    initiated_by="mcp"
                )

            response = {
                "success": True,
                "session_id": session_id if sync_needed or strategy == SyncStrategy.LABELS_ONLY else None,
                "global_version_id": global_version_id,
                "strategy": strategy_str,
                "message": f"Sync session {session_id} started successfully" if sync_needed or strategy == SyncStrategy.LABELS_ONLY else f"Metadata already up to date at version {global_version_id}, no sync needed",
                "instructions": f"Use d365fo_get_sync_progress with session_id '{session_id}' to monitor progress" if sync_needed or strategy == SyncStrategy.LABELS_ONLY else None
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Start sync failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_start_sync",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_sync_progress(self, arguments: dict) -> List[TextContent]:
        """Execute get sync progress operation."""
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            session_id = arguments["session_id"]

            # Initialize metadata to ensure sync session manager is available
            await client.initialize_metadata()

            if not hasattr(client, 'sync_session_manager'):
                # Fall back to basic progress check
                return await self._fallback_get_progress(client, session_id)

            # Get session details
            session = client.sync_session_manager.get_sync_session(session_id)
            
            if not session:
                error_response = {
                    "success": False,
                    "error": f"Session {session_id} not found",
                    "session_id": session_id
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

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
                    "can_cancel": session.can_cancel
                }
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Get sync progress failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_get_sync_progress",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_cancel_sync(self, arguments: dict) -> List[TextContent]:
        """Execute cancel sync operation."""
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            session_id = arguments["session_id"]

            # Initialize metadata to ensure sync session manager is available
            await client.initialize_metadata()

            if not hasattr(client, 'sync_session_manager'):
                error_response = {
                    "success": False,
                    "error": "Sync session management not available in this client version",
                    "session_id": session_id
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

            # Cancel session
            cancelled = await client.sync_session_manager.cancel_sync_session(session_id)

            response = {
                "success": cancelled,
                "session_id": session_id,
                "message": f"Session {session_id} {'cancelled' if cancelled else 'could not be cancelled'}",
                "details": "Session may not be cancellable if already completed or failed"
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Cancel sync failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_cancel_sync",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_list_sync_sessions(self, arguments: dict) -> List[TextContent]:
        """Execute list sync sessions operation."""
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            # Initialize metadata to ensure sync session manager is available
            await client.initialize_metadata()

            if not hasattr(client, 'sync_session_manager'):
                # Check if legacy sync manager is running
                return await self._fallback_list_sessions(client)

            # Get active sessions
            active_sessions = client.sync_session_manager.get_active_sessions()

            response = {
                "success": True,
                "active_sessions": [session.to_dict() for session in active_sessions],
                "total_count": len(active_sessions),
                "running_count": len([s for s in active_sessions if s.status == SyncStatus.RUNNING]),
                "summary": {
                    "has_running_sessions": any(s.status == SyncStatus.RUNNING for s in active_sessions),
                    "latest_session": active_sessions[-1].to_dict() if active_sessions else None
                }
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"List sync sessions failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_list_sync_sessions",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_sync_history(self, arguments: dict) -> List[TextContent]:
        """Execute get sync history operation."""
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            limit = arguments.get("limit", 20)

            # Initialize metadata to ensure sync session manager is available
            await client.initialize_metadata()

            if not hasattr(client, 'sync_session_manager'):
                error_response = {
                    "success": False,
                    "error": "Sync session management not available in this client version",
                    "message": "Upgrade to session-based sync manager to access history"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

            # Get session history
            history = client.sync_session_manager.get_session_history(limit)

            response = {
                "success": True,
                "history": [session.to_dict() for session in history],
                "total_count": len(history),
                "summary": {
                    "successful_syncs": len([s for s in history if s.status == SyncStatus.COMPLETED]),
                    "failed_syncs": len([s for s in history if s.status == SyncStatus.FAILED]),
                    "cancelled_syncs": len([s for s in history if s.status == SyncStatus.CANCELLED]),
                    "average_duration": sum(s.duration_seconds for s in history if s.duration_seconds) / len([s for s in history if s.duration_seconds]) if history else 0
                }
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Get sync history failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_get_sync_history",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def _fallback_start_sync(self, client, arguments: dict) -> List[TextContent]:
        """Fallback to original sync manager for starting sync."""
        strategy_str = arguments.get("strategy", "full")
        strategy = SyncStrategy(strategy_str)
        global_version_id = arguments.get("global_version_id")

        # Auto-detect version if not provided
        if global_version_id is None:
            sync_needed, detected_version_id = await client.metadata_cache.check_version_and_sync()
            if detected_version_id is None:
                raise ValueError("Could not detect global version ID")
            global_version_id = detected_version_id

        # Check if sync already running
        if hasattr(client, 'smart_sync_manager') and client.smart_sync_manager.is_syncing():
            error_response = {
                "success": False,
                "error": "Sync already in progress",
                "message": "Wait for current sync to complete before starting a new one"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

        # Start sync without session tracking
        import asyncio
        sync_task = asyncio.create_task(
            client.smart_sync_manager.sync_metadata(global_version_id, strategy)
        )

        response = {
            "success": True,
            "session_id": f"legacy_{global_version_id}_{strategy_str}",
            "global_version_id": global_version_id,
            "strategy": strategy_str,
            "message": "Sync started (legacy mode)",
            "instructions": "Use d365fo_get_sync_progress to monitor progress"
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    async def _fallback_get_progress(self, client, session_id: str) -> List[TextContent]:
        """Fallback progress check for original sync manager."""
        if hasattr(client, 'smart_sync_manager'):
            progress = client.smart_sync_manager.get_sync_progress()
            is_syncing = client.smart_sync_manager.is_syncing()

            if progress:
                response = {
                    "success": True,
                    "session_id": session_id,
                    "legacy_mode": True,
                    "progress": {
                        "global_version_id": progress.global_version_id,
                        "strategy": progress.strategy,
                        "phase": progress.phase,
                        "total_steps": progress.total_steps,
                        "completed_steps": progress.completed_steps,
                        "current_operation": progress.current_operation,
                        "start_time": progress.start_time.isoformat() if progress.start_time else None,
                        "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None,
                        "error": progress.error,
                        "is_running": is_syncing
                    }
                }
            else:
                response = {
                    "success": True,
                    "session_id": session_id,
                    "legacy_mode": True,
                    "message": "No sync currently running",
                    "is_running": False
                }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        error_response = {
            "success": False,
            "error": "No sync manager available",
            "session_id": session_id
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def _fallback_list_sessions(self, client) -> List[TextContent]:
        """Fallback session list for original sync manager."""
        if hasattr(client, 'smart_sync_manager'):
            is_syncing = client.smart_sync_manager.is_syncing()
            progress = client.smart_sync_manager.get_sync_progress()

            active_sessions = []
            if is_syncing and progress:
                session = {
                    "session_id": f"legacy_{progress.global_version_id}_{progress.strategy}",
                    "global_version_id": progress.global_version_id,
                    "strategy": progress.strategy,
                    "status": "running",
                    "start_time": progress.start_time.isoformat() if progress.start_time else None,
                    "progress_percent": (progress.completed_steps / progress.total_steps * 100) if progress.total_steps > 0 else 0,
                    "current_phase": progress.phase,
                    "current_activity": progress.current_operation,
                    "initiated_by": "legacy",
                    "legacy_mode": True
                }
                active_sessions.append(session)

            response = {
                "success": True,
                "active_sessions": active_sessions,
                "total_count": len(active_sessions),
                "running_count": len(active_sessions),
                "legacy_mode": True,
                "message": "Using legacy sync manager - limited session information available"
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        error_response = {
            "success": False,
            "error": "No sync manager available"
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]