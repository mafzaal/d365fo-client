"""Connection tools mixin for FastMCP server."""

import json
import logging

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class ConnectionToolsMixin(BaseToolsMixin):
    """Connection and environment tools for FastMCP server."""
    
    def register_connection_tools(self):
        """Register all connection tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_test_connection(profile: str = "default") -> str:
            """Test connection to D365FO environment.

            Args:
                profile: Optional profile name to test (uses default if not specified)

            Returns:
                JSON string with connection test results
            """
            try:
                result = await self.client_manager.test_connection(profile)
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                return json.dumps(
                    {"status": "error", "error": str(e), "profile": profile}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_get_environment_info(profile: str = "default") -> str:
            """Get D365FO environment information and version details.

            Args:
                profile: Optional profile name (uses default if not specified)

            Returns:
                JSON string with environment information
            """
            try:
                result = await self.client_manager.get_environment_info(profile)
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Failed to get environment info: {e}")
                return json.dumps({"error": str(e), "profile": profile}, indent=2)