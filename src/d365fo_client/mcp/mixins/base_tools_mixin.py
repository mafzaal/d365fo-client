"""Base mixin class for FastMCP tool categories."""

import logging

from d365fo_client.client import FOClient
from d365fo_client.profile_manager import ProfileManager
from ..client_manager import D365FOClientManager
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class BaseToolsMixin:
    """Base mixin for FastMCP tool categories.

    Provides common functionality and client access patterns
    for all tool category mixins.
    """

    # These will be injected by the main server class
    client_manager: D365FOClientManager
    mcp: FastMCP
    profile_manager: ProfileManager

    async def _get_client(self, profile: str = "default") -> FOClient:
        """Get D365FO client for specified profile.

        Args:
            profile: Profile name to use

        Returns:
            Configured D365FO client instance
        """
        if not hasattr(self, "client_manager") or not self.client_manager:
            raise RuntimeError("Client manager not initialized")
        return await self.client_manager.get_client(profile)

    def _create_error_response(
        self, error: Exception, tool_name: str, arguments: dict
    ) -> dict:
        """Create standardized error response.

        Args:
            error: Exception that occurred
            tool_name: Name of the tool that failed
            arguments: Arguments passed to the tool

        Returns:
            Dictionary with error details
        """
        return {
            "error": str(error),
            "tool": tool_name,
            "arguments": arguments,
            "error_type": type(error).__name__,
        }
