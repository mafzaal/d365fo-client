"""Utility functions for FastMCP server configuration and setup."""
import argparse
import logging
import os
from typing import Any, Dict, Optional
from d365fo_client import __version__
from d365fo_client.credential_sources import EnvironmentCredentialSource
from d365fo_client.profile_manager import ProfileManager
from d365fo_client.utils import get_default_cache_directory

logger = logging.getLogger(__name__)

def load_default_config(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """Load configuration for FastMCP server from arguments and environment.

    Args:
        args: Optional parsed command line arguments. If not provided, 
              defaults will be used for all argument-based configuration.

    Returns:
        Configuration dictionary
    """
    # Extract values from args with environment variable fallbacks
    # For command line arguments, prefer explicit args over env vars, but fall back to env vars for defaults
    if args is not None:
        transport = args.transport
        # Use env vars if args are at their default values
        host = args.host if args.host != "127.0.0.1" else os.getenv("MCP_HTTP_HOST", "127.0.0.1")
        port = args.port if args.port != 8000 else int(os.getenv("MCP_HTTP_PORT", "8000"))
        stateless = args.stateless or os.getenv("MCP_HTTP_STATELESS", "").lower() in ("true", "1", "yes")
        json_response = args.json_response or os.getenv("MCP_HTTP_JSON", "").lower() in ("true", "1", "yes")
        debug = args.debug or os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    else:
        transport = 'stdio'
        host = os.getenv("MCP_HTTP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_HTTP_PORT", "8000"))
        stateless = os.getenv("MCP_HTTP_STATELESS", "").lower() in ("true", "1", "yes")
        json_response = os.getenv("MCP_HTTP_JSON", "").lower() in ("true", "1", "yes")
        debug = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")

    # Get environment variables
    base_url = os.getenv("D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com")
    
    # Determine startup mode based on environment variables
    startup_mode = "profile_only"
    if base_url and base_url != "https://usnconeboxax1aos.cloud.onebox.dynamics.com":
        if all([os.getenv("D365FO_CLIENT_ID"), os.getenv("D365FO_CLIENT_SECRET"), os.getenv("D365FO_TENANT_ID")]):
            startup_mode = "client_credentials"
        else:
            startup_mode = "default_auth"

    # Environment variable mappings
    env_mappings = {
        "D365FO_BASE_URL": "base_url",
        "D365FO_VERIFY_SSL": "verify_ssl",
        "D365FO_LABEL_CACHE": "use_label_cache",
        "D365FO_LABEL_EXPIRY": "label_cache_expiry_minutes",
        "D365FO_USE_CACHE_FIRST": "use_cache_first",
        "D365FO_TIMEOUT": "timeout",
        "D365FO_CACHE_DIR": "metadata_cache_dir",
        "D365FO_CLIENT_ID": "client_id",
        "D365FO_CLIENT_SECRET": "client_secret",
        "D365FO_TENANT_ID": "tenant_id",
    }



    # Build default environment from environment variables
    default_environment = {
        "use_default_credentials": True,
        "use_cache_first": True,
        "timeout": 60,
        "verify_ssl": True,
        "use_label_cache": True,
        "metadata_cache_dir": os.getenv("D365FO_CACHE_DIR", get_default_cache_directory()),
    }

    # Apply environment variable mappings
    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            # Convert boolean strings
            if config_key in ["verify_ssl", "use_label_cache", "use_cache_first"]:
                default_environment[config_key] = value.lower() in ("true", "1", "yes", "on")
            # Convert numeric strings
            elif config_key in ["timeout", "label_cache_expiry_minutes"]:
                try:
                    default_environment[config_key] = int(value)
                except ValueError:
                    pass  # Keep default value
            else:
                default_environment[config_key] = value



    return {
        "startup_mode": startup_mode,
        "server": {
            "name": "d365fo-fastmcp-server",
            "version": __version__,
            "debug": debug or os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
            "transport": {
                "default": transport,
                "stdio": {
                    "enabled": True
                },
                "sse": {
                    "enabled": True,
                    "host": host,
                    "port": port,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST"],
                        "headers": ["*"]
                    }
                },
                "http": {
                    "enabled": True,
                    "host": host,
                    "port": port,
                    "stateless": stateless,
                    "json_response": json_response,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST", "DELETE"],
                        "headers": ["*"]
                    }
                },
            }
        },
        "default_environment": default_environment,
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

def create_default_profile_if_needed(profile_manager:"ProfileManager", config:Dict) -> Optional[bool]:
    """Create a default profile from environment variables if needed."""
    try:
        # Check if default profile already exists
        existing_default = profile_manager.get_default_profile()
        if existing_default:
            logger.info(f"Default profile already exists: {existing_default.name}")
            return False

        # Get default environment configuration
        default_environment = config.get("default_environment", {})
        
        # Get base URL from environment or config
        base_url = default_environment.get("base_url") or os.getenv("D365FO_BASE_URL")

        if not base_url:
            logger.warning("Cannot create default profile - D365FO_BASE_URL not set")
            return False

        # Determine authentication mode based on startup mode
        startup_mode = config.get("startup_mode", "profile_only")
        
        # Check for legacy credentials in environment
        client_id = default_environment.get("client_id") or os.getenv("D365FO_CLIENT_ID")
        client_secret = default_environment.get("client_secret") or os.getenv("D365FO_CLIENT_SECRET")
        tenant_id = default_environment.get("tenant_id") or os.getenv("D365FO_TENANT_ID")
        
        if startup_mode == "client_credentials":
            auth_mode = "client_credentials"
            if not all([client_id, client_secret, tenant_id]):
                logger.error("Client credentials mode requires D365FO_CLIENT_ID, D365FO_CLIENT_SECRET, and D365FO_TENANT_ID")
                return
        else:
            auth_mode = "default"
            # Clear client credentials for default auth mode
            client_id = None
            client_secret = None
            tenant_id = None

        # Create default profile with unique name
        profile_name = "default-from-env"
        
        # Check if profile with this name already exists
        existing_profile = profile_manager.get_profile(profile_name)
        if existing_profile:
            logger.info(f"Profile '{profile_name}' already exists, setting as default")
            profile_manager.set_default_profile(profile_name)
            return

        credential_source = None
        if startup_mode == "client_credentials":
            credential_source = EnvironmentCredentialSource()

        # Use configuration values with proper defaults
        use_label_cache = default_environment.get("use_label_cache", True)
        timeout = default_environment.get("timeout", 60)
        verify_ssl = default_environment.get("verify_ssl", True)

        success = profile_manager.create_profile(
            name=profile_name,
            base_url=base_url,
            auth_mode=auth_mode,
            client_id=None,  # use from env var
            client_secret=None,  # use from env var
            tenant_id=None,  # use from env var
            description=f"Auto-created from environment variables at startup (mode: {startup_mode})",
            use_label_cache=use_label_cache,
            timeout=timeout,
            verify_ssl=verify_ssl,
            credential_source=credential_source
        )

        if success:
            # Set as default profile
            profile_manager.set_default_profile(profile_name)
            logger.info(f"Created and set default profile: {profile_name}")
            logger.info(f"Profile configured for: {base_url}")
            logger.info(f"Authentication mode: {auth_mode}")
            logger.info(f"Use label cache: {use_label_cache}")
            logger.info(f"Timeout: {timeout}s")
            logger.info(f"Verify SSL: {verify_ssl}")
            
            if auth_mode == "client_credentials":
                logger.info(f"Client ID: {client_id}")
                logger.info(f"Tenant ID: {tenant_id}")
                
        else:
            logger.warning(f"Failed to create default profile: {profile_name}")
        
        return success

    except Exception as e:
        logger.error(f"Error creating default profile: {e}")