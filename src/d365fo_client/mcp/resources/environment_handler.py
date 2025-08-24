"""Environment resource handler for MCP server."""

import json
import logging
from datetime import datetime
from time import timezone
from typing import List

from mcp.types import Resource

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class EnvironmentResourceHandler:
    """Handles environment resources for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize the environment resource handler.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    async def list_resources(self) -> List[Resource]:
        """List available environment resources.

        Returns:
            List of environment resources
        """
        resources = [
            Resource(
                uri="d365fo://environment/status",
                name="Environment Status",
                description="Environment health and connectivity status",
                mimeType="application/json",
            ),
            Resource(
                uri="d365fo://environment/version",
                name="Version Information",
                description="D365FO application and platform version information",
                mimeType="application/json",
            ),
            Resource(
                uri="d365fo://environment/cache",
                name="Cache Status",
                description="Cache status and performance statistics",
                mimeType="application/json",
            ),
        ]

        logger.info(f"Listed {len(resources)} environment resources")
        return resources

    async def read_resource(self, uri: str) -> str:
        """Read specific environment resource.

        Args:
            uri: Resource URI

        Returns:
            JSON string with environment resource content
        """
        try:
            if uri == "d365fo://environment/status":
                return await self._get_status_resource()
            elif uri == "d365fo://environment/version":
                return await self._get_version_resource()
            elif uri == "d365fo://environment/cache":
                return await self._get_cache_resource()
            else:
                raise ValueError(f"Unknown environment resource URI: {uri}")
        except Exception as e:
            logger.error(f"Failed to read environment resource {uri}: {e}")
            error_content = {
                "error": str(e),
                "uri": uri,
                "timestamp": datetime.now(timezone.utc),
            }
            return json.dumps(error_content, indent=2)

    async def _get_status_resource(self) -> str:
        """Get environment status resource."""
        try:
            env_info = await self.client_manager.get_environment_info()
            health_check = await self.client_manager.health_check()

            status_content = {
                "baseUrl": env_info["base_url"],
                "connectivity": env_info["connectivity"],
                "healthCheck": health_check,
                "lastUpdated": datetime.now(timezone.utc),
            }

            return json.dumps(status_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get status resource: {e}")
            raise

    async def _get_version_resource(self) -> str:
        """Get version information resource."""
        try:
            env_info = await self.client_manager.get_environment_info()

            version_content = {
                "baseUrl": env_info["base_url"],
                "versions": env_info["versions"],
                "lastUpdated": datetime.now(timezone.utc),
            }

            return json.dumps(version_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get version resource: {e}")
            raise

    async def _get_cache_resource(self) -> str:
        """Get cache status resource."""
        try:
            env_info = await self.client_manager.get_environment_info()

            cache_content = {
                "baseUrl": env_info["base_url"],
                "cacheStatus": env_info["cache_status"],
                "lastUpdated": datetime.now(timezone.utc),
            }

            return json.dumps(cache_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get cache resource: {e}")
            raise
