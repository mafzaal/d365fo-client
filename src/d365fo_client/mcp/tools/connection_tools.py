"""Connection tools for MCP server."""

import json
import logging
import time
from typing import List

from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class ConnectionTools:
    """Connection and testing tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize connection tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    def get_tools(self) -> List[Tool]:
        """Get list of connection tools.

        Returns:
            List of Tool definitions
        """
        return [self._get_test_connection_tool(), self._get_environment_info_tool()]

    def _get_test_connection_tool(self) -> Tool:
        """Get test connection tool definition."""
        return Tool(
            name="d365fo_test_connection",
            description="Test connectivity to D365FO environment. If no profile is specified, uses the default profile. If no default profile is set, provides guidance on setting up profiles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                    "baseUrl": {
                        "type": "string",
                        "description": "Override default base URL",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Connection timeout in seconds",
                        "minimum": 1,
                        "maximum": 300,
                    },
                },
            },
        )

    def _get_environment_info_tool(self) -> Tool:
        """Get environment info tool definition."""
        return Tool(
            name="d365fo_get_environment_info",
            description="Get comprehensive environment information. If no profile is specified, uses the default profile.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    }
                },
            },
        )

    async def execute_test_connection(self, arguments: dict) -> List[TextContent]:
        """Execute test connection tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            start_time = time.time()
            profile = arguments.get("profile", "default")

            # Test connection
            success = await self.client_manager.test_connection(profile)
            response_time = time.time() - start_time

            # Build response
            response = {
                "success": success,
                "profile": profile,
                "endpoints": {
                    "data": success,
                    "metadata": success,  # Simplification for now
                },
                "responseTime": round(response_time, 3),
                "error": None if success else "Connection failed",
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except ValueError as e:
            # Handle configuration errors with helpful messages
            logger.error(
                f"Configuration error for profile {arguments.get('profile', 'default')}: {e}"
            )
            error_response = {
                "success": False,
                "profile": arguments.get("profile", "default"),
                "endpoints": {"data": False, "metadata": False},
                "responseTime": 0.0,
                "error": str(e),
                "suggestion": "Please create a profile or set a default profile using the profile management tools.",
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
        except Exception as e:
            logger.error(f"Test connection failed: {e}")
            error_response = {
                "success": False,
                "profile": arguments.get("profile", "default"),
                "endpoints": {"data": False, "metadata": False},
                "responseTime": 0.0,
                "error": str(e),
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_environment_info(self, arguments: dict) -> List[TextContent]:
        """Execute get environment info tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            env_info = await self.client_manager.get_environment_info(profile)

            # Format response according to specification with enhanced metadata info
            response = {
                "baseUrl": env_info["base_url"],
                "versions": env_info["versions"],
                "connectivity": env_info["connectivity"],
                "metadataInfo": env_info["metadata_info"],
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except ValueError as e:
            # Handle configuration errors with helpful messages
            logger.error(
                f"Configuration error for profile {arguments.get('profile', 'default')}: {e}"
            )
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_environment_info",
                "arguments": arguments,
                "suggestion": "Please create a profile or set a default profile using the profile management tools.",
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
        except Exception as e:
            logger.error(f"Get environment info failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_environment_info",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
