"""Performance tools mixin for FastMCP server."""

import json
import logging
from datetime import datetime

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class PerformanceToolsMixin(BaseToolsMixin):
    """Performance monitoring and configuration tools for FastMCP server."""
    
    def register_performance_tools(self):
        """Register all performance tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_get_server_performance() -> dict:
            """Get FastMCP server performance statistics and health metrics.

            Returns:
                Dict with server performance data
            """
            try:
                performance_stats = self.get_performance_stats()

                # Add client manager health stats
                client_health = await self.client_manager.health_check()

                return {
                    "server_performance": performance_stats,
                    "client_health": client_health,
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Get server performance failed: {e}")
                return {"error": str(e)}

        @self.mcp.tool()
        async def d365fo_reset_performance_stats() -> dict:
            """Reset server performance statistics.

            Returns:
                Dict with reset confirmation
            """
            try:
                # Reset performance stats
                self._request_stats = {
                    "total_requests": 0,
                    "total_errors": 0,
                    "avg_response_time": 0.0,
                    "last_reset": datetime.now(),
                }
                self._request_times = []
                self._connection_pool_stats = {
                    "active_connections": 0,
                    "peak_connections": 0,
                    "connection_errors": 0,
                    "pool_hits": 0,
                    "pool_misses": 0,
                }

                # Clean up expired sessions
                self._cleanup_expired_sessions()

                return {
                    "performance_stats_reset": True,
                    "reset_timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Reset performance stats failed: {e}")
                return {"error": str(e), "reset_successful": False}

        @self.mcp.tool()
        async def d365fo_get_server_config() -> dict:
            """Get current FastMCP server configuration and feature status.

            Returns:
                Dict with server configuration
            """
            try:
                from ... import __version__
                
                config_info = {
                    "server_version": __version__,
                    "stateless_mode": self._stateless_mode,
                    "json_response_mode": self._json_response_mode,
                    "max_concurrent_requests": self._max_concurrent_requests,
                    "request_timeout": self._request_timeout,
                    "batch_size": self._batch_size,
                    "transport_config": self.config.get("server", {}).get(
                        "transport", {}
                    ),
                    "performance_config": self.config.get("performance", {}),
                    "cache_config": self.config.get("cache", {}),
                    "security_config": self.config.get("security", {}),
                }

                return {
                    "server_config": config_info,
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Get server config failed: {e}")
                return {"error": str(e)}