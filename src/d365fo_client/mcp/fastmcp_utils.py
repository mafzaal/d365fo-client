"""Utility functions for FastMCP server configuration and setup."""
import os
from typing import Any, Dict
from d365fo_client import __version__

def load_default_config() -> Dict[str, Any]:
    """Load default configuration for FastMCP server.

    Returns:
        Default configuration dictionary
    """
    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )

    # Determine startup mode based on environment variables
    startup_mode = "profile_only"
    if (
        base_url
        and base_url != "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    ):
        if all(
            [
                os.getenv("D365FO_CLIENT_ID"),
                os.getenv("D365FO_CLIENT_SECRET"),
                os.getenv("D365FO_TENANT_ID"),
            ]
        ):
            startup_mode = "client_credentials"
        else:
            startup_mode = "default_auth"

    return {
        "startup_mode": startup_mode,
        "server": {
            "name": "d365fo-mcp-server",
            "version": __version__,
            "debug": os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
            "transport": {
                "default": "stdio",
                "stdio": {"enabled": True},
                "sse": {
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": int(os.getenv("MCP_SSE_PORT", "8000")),
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST"],
                        "headers": ["*"],
                    },
                },
                "http": {
                    "enabled": True,
                    "host": os.getenv("MCP_HTTP_HOST", "127.0.0.1"),
                    "port": int(os.getenv("MCP_HTTP_PORT", "8000")),
                    "stateless": os.getenv("MCP_HTTP_STATELESS", "").lower()
                    in ("true", "1", "yes"),
                    "json_response": os.getenv("MCP_HTTP_JSON", "").lower()
                    in ("true", "1", "yes"),
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST", "DELETE"],
                        "headers": ["*"],
                    },
                },
            },
        },
        "default_environment": {
            "base_url": base_url,
            "use_default_credentials": True,
            "use_cache_first": True,
            "timeout": 60,
            "verify_ssl": True,
            "use_label_cache": True,
        },
        "cache": {
            "metadata_cache_dir": os.path.expanduser("~/.d365fo-mcp/cache"),
            "label_cache_expiry_minutes": 120,
            "use_label_cache": True,
            "cache_size_limit_mb": 100,
        },
        "performance": {
            "max_concurrent_requests": int(
                os.getenv("MCP_MAX_CONCURRENT_REQUESTS", "10")
            ),
            "connection_pool_size": int(os.getenv("MCP_CONNECTION_POOL_SIZE", "5")),
            "request_timeout": int(os.getenv("MCP_REQUEST_TIMEOUT", "30")),
            "batch_size": int(os.getenv("MCP_BATCH_SIZE", "100")),
            "enable_performance_monitoring": os.getenv(
                "MCP_PERFORMANCE_MONITORING", "true"
            ).lower()
            in ("true", "1", "yes"),
            "session_cleanup_interval": int(
                os.getenv("MCP_SESSION_CLEANUP_INTERVAL", "300")
            ),
            "max_request_history": int(
                os.getenv("MCP_MAX_REQUEST_HISTORY", "1000")
            ),
        },
        "security": {
            "encrypt_cached_tokens": True,
            "token_expiry_buffer_minutes": 5,
            "max_retry_attempts": 3,
        },
    }