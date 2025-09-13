"""Sync tools mixin for FastMCP server."""

import json
import logging

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class SyncToolsMixin(BaseToolsMixin):
    """Metadata synchronization tools for FastMCP server."""
    
    def register_sync_tools(self):
        """Register all sync tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_start_sync(
            strategy: str = "full_without_labels",
            global_version_id: int = None,
            profile: str = "default",
        ) -> str:
            """Start a metadata synchronization session.

            Args:
                strategy: Sync strategy to use
                global_version_id: Specific global version ID to sync
                profile: Optional profile name

            Returns:
                JSON string with sync session details
            """
            try:
                client = await self._get_client(profile)

                # Start sync
                session_id = await client.start_sync(
                    strategy=strategy, global_version_id=global_version_id
                )

                return json.dumps(
                    {"sessionId": session_id, "strategy": strategy, "started": True},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Start sync failed: {e}")
                return json.dumps(
                    {"error": str(e), "strategy": strategy, "started": False}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_get_sync_progress(
            session_id: str, profile: str = "default"
        ) -> str:
            """Get detailed progress information for a sync session.

            Args:
                session_id: Session ID of the sync operation
                profile: Optional profile name

            Returns:
                JSON string with sync progress
            """
            try:
                client = await self._get_client(profile)

                # Get sync progress
                progress = await client.get_sync_progress(session_id)

                return json.dumps(
                    {"sessionId": session_id, "progress": progress}, indent=2
                )

            except Exception as e:
                logger.error(f"Get sync progress failed: {e}")
                return json.dumps({"error": str(e), "sessionId": session_id}, indent=2)

        @self.mcp.tool()
        async def d365fo_cancel_sync(session_id: str, profile: str = "default") -> str:
            """Cancel a running sync session.

            Args:
                session_id: Session ID of the sync operation to cancel
                profile: Optional profile name

            Returns:
                JSON string with cancellation result
            """
            try:
                client = await self._get_client(profile)

                # Cancel sync
                result = await client.cancel_sync(session_id)

                return json.dumps(
                    {
                        "sessionId": session_id,
                        "cancelled": result.get("cancelled", False),
                        "message": result.get("message", ""),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Cancel sync failed: {e}")
                return json.dumps(
                    {"error": str(e), "sessionId": session_id, "cancelled": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_list_sync_sessions(profile: str = "default") -> str:
            """Get list of all currently active sync sessions.

            Args:
                profile: Optional profile name

            Returns:
                JSON string with active sync sessions
            """
            try:
                client = await self._get_client(profile)

                # List sync sessions
                sessions = await client.list_sync_sessions()

                return json.dumps(
                    {"totalSessions": len(sessions), "sessions": sessions}, indent=2
                )

            except Exception as e:
                logger.error(f"List sync sessions failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.tool()
        async def d365fo_get_sync_history(
            limit: int = 20, profile: str = "default"
        ) -> str:
            """Get history of completed sync sessions.

            Args:
                limit: Maximum number of sessions to return
                profile: Optional profile name

            Returns:
                JSON string with sync history
            """
            try:
                client = await self._get_client(profile)

                # Get sync history
                history = await client.get_sync_history(limit=limit)

                return json.dumps(
                    {"limit": limit, "totalReturned": len(history), "history": history},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get sync history failed: {e}")
                return json.dumps({"error": str(e), "limit": limit}, indent=2)