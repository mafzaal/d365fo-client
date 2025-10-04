#!/usr/bin/env python3
"""Entry point for the FastMCP-based D365FO MCP Server."""

import argparse
import asyncio
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Literal, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl, AnyUrl

from d365fo_client import __version__
from d365fo_client.mcp.auth_server.auth.providers.azure import AzureProvider
from d365fo_client.mcp import FastD365FOMCPServer
from d365fo_client.mcp.fastmcp_utils import create_default_profile_if_needed, load_default_config, migrate_legacy_config
from d365fo_client.profile_manager import ProfileManager
from d365fo_client.settings import get_settings
from mcp.server.auth.settings import  AuthSettings,ClientRegistrationOptions
from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier



def setup_logging(level: str = "INFO", log_file_path: Optional[str] = None) -> None:
    """Set up logging configuration with 24-hour log rotation.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file_path: Custom log file path, if None uses default from settings
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get log file path from parameter or settings
    if log_file_path:
        log_file = Path(log_file_path)
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Use default log file path from settings
        settings = get_settings()
        log_file = Path(settings.log_file) #type: ignore
        # Settings already ensures directories exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers to avoid duplicate logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create rotating file handler - rotates every 24 hours (midnight)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when='midnight',        # Rotate at midnight
        interval=1,             # Every 1 day
        backupCount=30,         # Keep 30 days of logs
        encoding='utf-8',       # Use UTF-8 encoding
        utc=False              # Use local time for rotation
    )
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="FastMCP-based D365FO MCP Server with multi-transport support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Transport Options:
  stdio       Standard input/output (default, for development and CLI tools)
  sse         Server-Sent Events (for web applications and browsers)  
  http        Streamable HTTP (for production deployments and microservices)


Production Examples:
  # Development (default)
  %(prog)s                                    
  
  # Web development
  %(prog)s --transport sse --port 8000 --debug       
  
  # Basic production HTTP
  %(prog)s --transport http --host 0.0.0.0 --port 8000
  
  
Environment Variables:
  D365FO_BASE_URL           D365FO environment URL
  D365FO_CLIENT_ID          Azure AD client ID (optional)
  D365FO_CLIENT_SECRET      Azure AD client secret (optional)  
  D365FO_TENANT_ID          Azure AD tenant ID (optional)
  D365FO_MCP_TRANSPORT      Default transport protocol (stdio, sse, http, streamable-http)
  D365FO_MCP_HTTP_HOST          Default HTTP host (default: 127.0.0.1)
  D365FO_MCP_HTTP_PORT          Default HTTP port (default: 8000)
  D365FO_MCP_HTTP_STATELESS     Enable stateless mode (true/false)
  D365FO_MCP_HTTP_JSON          Enable JSON response mode (true/false)
  D365FO_MCP_MAX_CONCURRENT_REQUESTS  Max concurrent requests (default: 10)
  D365FO_MCP_REQUEST_TIMEOUT    Request timeout in seconds (default: 30)
  D365FO_MCP_AUTH_CLIENT_ID     Azure AD client ID for authentication
  D365FO_MCP_AUTH_CLIENT_SECRET Azure AD client secret for authentication
  D365FO_MCP_AUTH_TENANT_ID    Azure AD tenant ID for authentication
  D365FO_MCP_AUTH_BASE_URL     http://localhost:8000
  D365FO_MCP_AUTH_REQUIRED_SCOPES  User.Read,email,openid,profile
  D365FO_MCP_API_KEY_VALUE      API key for authentication (send as: Authorization: Bearer <key>)
  D365FO_LOG_LEVEL               Logging level (DEBUG, INFO, WARNING, ERROR)
  D365FO_LOG_FILE                Custom log file path (default: ~/.d365fo-mcp/logs/fastmcp-server.log)
  D365FO_META_CACHE_DIR          Metadata cache directory (default: ~/.d365fo-mcp/cache)

        """
    )
    
    parser.add_argument(
        "--version",
        action="version", 
        version=f"%(prog)s {__version__}"
    )
    
    # Get settings for defaults
    settings = get_settings()
    
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "http", "streamable-http"],
        default=settings.mcp_transport.value,
        help=f"Transport protocol to use (default: {settings.mcp_transport.value}, from D365FO_MCP_TRANSPORT env var)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=settings.http_host,
        help=f"Host to bind to for SSE/HTTP transports (default: {settings.http_host})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.http_port,
        help=f"Port to bind to for SSE/HTTP transports (default: {settings.http_port})"
    )
    
    parser.add_argument(
        "--stateless",
        action="store_true",
        help="Enable stateless HTTP mode for horizontal scaling and load balancing. " +
             "In stateless mode, each request is independent and sessions are not persisted."
    )
    
    parser.add_argument(
        "--json-response",
        action="store_true",
        help="Use JSON responses instead of SSE streams (HTTP transport only). " +
             "Useful for API gateways and clients that prefer standard JSON responses."
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging and detailed error information"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=settings.log_level.value,
        help=f"Set logging level (default: {settings.log_level.value}, from D365FO_LOG_LEVEL env var)"
    )
    
    

    return parser.parse_args()


# Get settings first
settings = get_settings()

# Parse arguments  
args = parse_arguments()
arg_transport = args.transport

# Set up logging and load configuration
if arg_transport == "http":
    arg_transport = "streamable-http"

transport: Literal["stdio", "sse", "streamable-http"] = arg_transport

# Use settings for logging setup
setup_logging(args.log_level or settings.log_level.value, settings.log_file)
logger = logging.getLogger(__name__)

logger.info(f"Starting FastD365FOMCPServer v{__version__} with transport: {transport}")

# Use load_default_config with args instead of separate load_config function
config = load_default_config(args)

default_fo = config.get("default_environment", {})

config_path = default_fo.get("metadata_cache_dir", settings.meta_cache_dir)


# Create profile manager with config path
profile_manager = ProfileManager(str(Path(config_path) / "config.yaml"))

# Migrate legacy configuration if needed
if migrate_legacy_config(profile_manager):
    logger.info("Legacy configuration migrated successfully")
else:
    logger.debug("No legacy configuration migration needed")

if not create_default_profile_if_needed(profile_manager, config):
    logger.debug("Default profile already exists or creation not needed")

# Extract server configuration
server_config = config.get("server", {})
transport_config = server_config.get("transport", {})

is_remote_transport = transport in ["sse", "streamable-http"]

# Log startup configuration details
logger.info("=== Server Startup Configuration ===")
logger.info(f"Transport: {transport}")
if is_remote_transport:
    logger.info(f"Host: {transport_config.get('http', {}).get('host', '127.0.0.1')}")
    logger.info(f"Port: {transport_config.get('http', {}).get('port', 8000)}")

logger.info(f"Debug mode: {server_config.get('debug', False)}")
logger.info(f"JSON response: {transport_config.get('http', {}).get('json_response', False)}")
logger.info(f"Stateless HTTP: {transport_config.get('http', {}).get('stateless', False)}")
logger.info(f"Log level: {args.log_level}")
logger.info(f"Config path: {config_path}")
logger.info(f"D365FO Base URL: {default_fo.get('base_url', settings.base_url)}")
logger.info(f"Settings Base URL: {settings.base_url}")
logger.info(f"Startup Mode: {settings.get_startup_mode()}")
logger.info(f"Client Credentials: {'Configured' if settings.has_client_credentials() else 'Not configured'}")
logger.info("====================================")

# Validate authentication for remote transports
if is_remote_transport:
    has_oauth = settings.has_mcp_auth_credentials()
    has_api_key = settings.has_mcp_api_key_auth()

    # Must have either OAuth or API key
    if not has_oauth and not has_api_key:
        logger.error(
            "Error: Remote transports (SSE/HTTP) require authentication. "
            "Please configure either:\n"
            "  OAuth: D365FO_MCP_AUTH_CLIENT_ID, D365FO_MCP_AUTH_CLIENT_SECRET, "
            "D365FO_MCP_AUTH_TENANT_ID, D365FO_MCP_AUTH_BASE_URL, D365FO_MCP_AUTH_REQUIRED_SCOPES\n"
            "  OR\n"
            "  API Key: D365FO_MCP_API_KEY_VALUE, D365FO_MCP_API_KEY_HEADER_NAME (optional)"
        )
        sys.exit(1)

    # OAuth takes precedence if both are configured
    if has_oauth and has_api_key:
        logger.warning(
            "Both OAuth and API Key authentication configured. "
            "Using OAuth (takes precedence)."
        )    

# Initialize authentication provider
auth_provider: AzureProvider | APIKeyVerifier | None = None  # type: ignore
auth: AuthSettings | None = None

if is_remote_transport:
    has_oauth = settings.has_mcp_auth_credentials()
    has_api_key = settings.has_mcp_api_key_auth()

    if has_oauth:
        # OAuth authentication setup
        logger.info("Initializing OAuth authentication with Azure AD")

        assert settings.mcp_auth_client_id is not None
        assert settings.mcp_auth_client_secret is not None
        assert settings.mcp_auth_tenant_id is not None
        assert settings.mcp_auth_base_url is not None
        assert settings.mcp_auth_required_scopes is not None
        required_scopes = settings.mcp_auth_required_scopes_list()

        # Initialize authorization settings
        auth_provider = AzureProvider(
            client_id=settings.mcp_auth_client_id,
            client_secret=settings.mcp_auth_client_secret,
            tenant_id=settings.mcp_auth_tenant_id,
            base_url=settings.mcp_auth_base_url,
            required_scopes=required_scopes or ["User.Read"],  # type: ignore
            redirect_path="/auth/callback",
            clients_storage_path=config_path or ...
        )

        auth = AuthSettings(
            issuer_url=AnyHttpUrl(settings.mcp_auth_base_url),
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=required_scopes or ["User.Read"],  # type: ignore
                default_scopes=required_scopes or ["User.Read"],  # type: ignore
            ),
            required_scopes=required_scopes or ["User.Read"],  # type: ignore
            resource_server_url=AnyHttpUrl(settings.mcp_auth_base_url),
        )

    elif has_api_key:
        # API Key authentication setup
        logger.info("Initializing API Key authentication")

        from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier

        auth_provider = APIKeyVerifier(  # type: ignore
            api_key=settings.mcp_api_key_value,  # type: ignore
            base_url=settings.mcp_auth_base_url,
        )

        # For API Key authentication
        auth = AuthSettings(
            issuer_url=AnyHttpUrl(settings.mcp_auth_base_url) if settings.mcp_auth_base_url else AnyHttpUrl("http://localhost"),
            resource_server_url=None
        )

# Initialize FastMCP server with configuration
mcp = FastMCP(
    name=server_config.get("name", "d365fo-mcp-server"),
    auth_server_provider=auth_provider if isinstance(auth_provider, AzureProvider) else None,# type: ignore
    token_verifier=auth_provider if isinstance(auth_provider, APIKeyVerifier) else None,
    auth=auth,
    instructions=server_config.get(
        "instructions",
        "Microsoft Dynamics 365 Finance & Operations MCP Server providing comprehensive access to D365FO data, metadata, and operations",
    ),
    host=transport_config.get("http", {}).get("host", "127.0.0.1"),
    port=transport_config.get("http", {}).get("port", 8000),
    debug=server_config.get("debug", False),
    json_response=transport_config.get("http", {}).get("json_response", False),
    stateless_http=transport_config.get("http", {}).get("stateless", False),
    streamable_http_path= "/" if transport == "streamable-http" else "/mcp",
    sse_path="/" if transport == "streamable-http" else "/sse",

)

# Add OAuth callback route only for Azure OAuth provider
if is_remote_transport and isinstance(auth_provider, AzureProvider):
    from starlette.requests import Request
    from starlette.responses import RedirectResponse

    @mcp.custom_route(path=auth_provider._redirect_path, methods=["GET"]) # type: ignore
    async def handle_idp_callback(request: Request) -> RedirectResponse:
        return await auth_provider._handle_idp_callback(request) # type: ignore

# Initialize FastD365FOMCPServer
server = FastD365FOMCPServer(mcp, config, profile_manager=profile_manager)

# Configure API Key authentication if enabled
if is_remote_transport:
    from d365fo_client.mcp.auth_server.auth.providers.apikey import APIKeyVerifier

    if isinstance(auth_provider, APIKeyVerifier):

        logger.info("API Key authentication configured successfully")
        logger.info("=" * 60)
        logger.info("IMPORTANT: Clients must authenticate using:")
        logger.info("  Authorization: Bearer <your-api-key>")
        logger.info("")
        logger.info("Example:")
        logger.info(f"  curl -H 'Authorization: Bearer YOUR_KEY' http://localhost:{transport_config.get('http', {}).get('port', 8000)}/")
        logger.info("=" * 60)

logger.info("FastD365FOMCPServer initialized successfully")


def main() -> None:
    """Main entry point for the FastMCP server."""

    # Handle Windows event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
