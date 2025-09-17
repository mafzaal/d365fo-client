#!/usr/bin/env python3
"""Entry point for the FastMCP-based D365FO MCP Server."""

import argparse
import asyncio
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Literal
from mcp.server.fastmcp import FastMCP

from d365fo_client import __version__
from d365fo_client.mcp import FastD365FOMCPServer
from d365fo_client.mcp.fastmcp_utils import load_default_config



def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration with 24-hour log rotation.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create logs directory
    log_dir = Path.home() / ".d365fo-mcp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers to avoid duplicate logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create rotating file handler - rotates every 24 hours (midnight)
    log_file = log_dir / "fastmcp-server.log"
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
  uvicorn     Production ASGI server with advanced features (recommended for production)

Production Examples:
  # Development (default)
  %(prog)s                                    
  
  # Web development
  %(prog)s --transport sse --port 8000 --debug       
  
  # Basic production HTTP
  %(prog)s --transport http --host 0.0.0.0 --port 8000
  
  # Production uvicorn deployment (recommended)
  %(prog)s --transport uvicorn --host 0.0.0.0 --port 8000 --workers 4
  
  # High-availability uvicorn with SSL
  %(prog)s --transport uvicorn --host 0.0.0.0 --port 443 --workers 8 \\
           --ssl-keyfile /path/to/key.pem --ssl-certfile /path/to/cert.pem --stateless
  
  # Development with uvicorn auto-reload
  %(prog)s --transport uvicorn --port 8000 --reload --debug
  
  # Load balancer friendly deployment
  %(prog)s --transport uvicorn --host 0.0.0.0 --port 8000 --workers 4 \\
           --stateless --json-response --no-access-log
  
  # Container/Kubernetes deployment
  %(prog)s --transport uvicorn --host 0.0.0.0 --port 8000 --workers 1 \\
           --stateless --max-connections 500 --keepalive 10
  
Environment Variables:
  D365FO_BASE_URL           D365FO environment URL
  D365FO_CLIENT_ID          Azure AD client ID (optional)
  D365FO_CLIENT_SECRET      Azure AD client secret (optional)  
  D365FO_TENANT_ID          Azure AD tenant ID (optional)
  MCP_HTTP_HOST             Default HTTP host (default: 127.0.0.1)
  MCP_HTTP_PORT             Default HTTP port (default: 8000)
  MCP_HTTP_STATELESS        Enable stateless mode (true/false)
  MCP_HTTP_JSON             Enable JSON response mode (true/false)
  MCP_MAX_CONCURRENT_REQUESTS  Max concurrent requests (default: 10)
  MCP_REQUEST_TIMEOUT       Request timeout in seconds (default: 30)
  D365FO_LOG_LEVEL          Logging level (DEBUG, INFO, WARNING, ERROR)
  
  # Uvicorn-specific environment variables
  UVICORN_WORKERS           Number of worker processes (default: 1)
  UVICORN_ACCESS_LOG        Enable access logging (true/false, default: true)
  UVICORN_KEEPALIVE         Keep-alive timeout in seconds (default: 5)
  UVICORN_MAX_CONNECTIONS   Maximum concurrent connections (default: 1000)
  
Production Deployment Tips:
  - Use uvicorn transport for production deployments
  - Set workers to 2x CPU cores for CPU-bound workloads
  - Enable stateless mode for horizontal scaling
  - Use SSL certificates for HTTPS in production
  - Monitor with --access-log or external tools
  - Set appropriate max-connections based on load
        """
    )
    
    parser.add_argument(
        "--version",
        action="version", 
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "http", "streamable-http", "uvicorn"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to for SSE/HTTP transports (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for SSE/HTTP transports (default: 8000)"
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
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    # Uvicorn-specific production deployment options
    uvicorn_group = parser.add_argument_group('uvicorn production options')
    
    uvicorn_group.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes for uvicorn (default: 1, production: 4-8)"
    )
    
    uvicorn_group.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (uvicorn only, not for production)"
    )
    
    uvicorn_group.add_argument(
        "--ssl-keyfile",
        type=str,
        help="Path to SSL private key file for HTTPS (uvicorn only)"
    )
    
    uvicorn_group.add_argument(
        "--ssl-certfile", 
        type=str,
        help="Path to SSL certificate file for HTTPS (uvicorn only)"
    )
    
    uvicorn_group.add_argument(
        "--access-log",
        action="store_true",
        default=True,
        help="Enable HTTP access logging (uvicorn only, default: enabled)"
    )
    
    uvicorn_group.add_argument(
        "--no-access-log",
        action="store_true",
        help="Disable HTTP access logging (uvicorn only)"
    )
    
    uvicorn_group.add_argument(
        "--keepalive",
        type=int,
        default=5,
        help="HTTP keep-alive timeout in seconds (uvicorn only, default: 5)"
    )
    
    uvicorn_group.add_argument(
        "--max-connections",
        type=int,
        default=1000,
        help="Maximum number of concurrent connections (uvicorn only, default: 1000)"
    )

    return parser.parse_args()


def load_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Load configuration from arguments and environment.

    Args:
        args: Parsed command line arguments

    Returns:
        Configuration dictionary
    """
    # Normalize transport argument
    transport = args.transport
        

    # Get environment variables
    base_url = os.getenv("D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com")
    
    # Environment variable overrides for production deployment
    uvicorn_workers = int(os.getenv("UVICORN_WORKERS", getattr(args, 'workers', 1)))
    uvicorn_access_log = os.getenv("UVICORN_ACCESS_LOG", "true").lower() in ("true", "1", "yes")
    uvicorn_keepalive = int(os.getenv("UVICORN_KEEPALIVE", getattr(args, 'keepalive', 5)))
    uvicorn_max_connections = int(os.getenv("UVICORN_MAX_CONNECTIONS", getattr(args, 'max_connections', 1000)))
    
    # Determine startup mode based on environment variables
    startup_mode = "profile_only"
    if base_url and base_url != "https://usnconeboxax1aos.cloud.onebox.dynamics.com":
        if all([os.getenv("D365FO_CLIENT_ID"), os.getenv("D365FO_CLIENT_SECRET"), os.getenv("D365FO_TENANT_ID")]):
            startup_mode = "client_credentials"
        else:
            startup_mode = "default_auth"

    config = {
        "startup_mode": startup_mode,
        "server": {
            "name": "d365fo-fastmcp-server",
            "version": __version__,
            "debug": args.debug,
            "transport": {
                "default": transport,
                "stdio": {
                    "enabled": True
                },
                "sse": {
                    "enabled": True,
                    "host": args.host,
                    "port": args.port,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST"],
                        "headers": ["*"]
                    }
                },
                "http": {
                    "enabled": True,
                    "host": args.host,
                    "port": args.port,
                    "stateless": args.stateless,
                    "json_response": args.json_response,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST", "DELETE"],
                        "headers": ["*"]
                    }
                },
                "uvicorn": {
                    "enabled": True,
                    "host": args.host,
                    "port": args.port,
                    "workers": uvicorn_workers,
                    "reload": getattr(args, 'reload', False),
                    "ssl_keyfile": getattr(args, 'ssl_keyfile', None),
                    "ssl_certfile": getattr(args, 'ssl_certfile', None),
                    "access_log": uvicorn_access_log and not getattr(args, 'no_access_log', False),
                    "keepalive_timeout": uvicorn_keepalive,
                    "limit_concurrency": uvicorn_max_connections,
                    "stateless": args.stateless,
                    "json_response": args.json_response,
                }
            }
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
            "label_cache_expiry_minutes": int(os.getenv("MCP_LABEL_CACHE_EXPIRY", "120")),
            "use_label_cache": True,
            "cache_size_limit_mb": int(os.getenv("MCP_CACHE_SIZE_LIMIT", "100")),
        },
        "performance": {
            "max_concurrent_requests": int(os.getenv("MCP_MAX_CONCURRENT_REQUESTS", "10")),
            "connection_pool_size": int(os.getenv("MCP_CONNECTION_POOL_SIZE", "5")),
            "request_timeout": int(os.getenv("MCP_REQUEST_TIMEOUT", "30")),
            "batch_size": int(os.getenv("MCP_BATCH_SIZE", "100")),
            "enable_performance_monitoring": os.getenv("MCP_PERFORMANCE_MONITORING", "true").lower() in ("true", "1", "yes"),
        },
        "security": {
            "encrypt_cached_tokens": True,
            "token_expiry_buffer_minutes": int(os.getenv("MCP_TOKEN_EXPIRY_BUFFER", "5")),
            "max_retry_attempts": int(os.getenv("MCP_MAX_RETRY_ATTEMPTS", "3")),
            "cors_enabled": os.getenv("MCP_CORS_ENABLED", "true").lower() in ("true", "1", "yes"),
        },
    }

    return config



def main() -> None:
    """Main entry point for the FastMCP server."""

    # Handle Windows event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        # Parse arguments first to check transport
        args = parse_arguments()
        transport = args.transport
        # Set up logging and load configuration
        if transport == "http":
            transport = "streamable-http"

        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        logger.info(f"Starting FastD365FOMCPServer v{__version__} with transport: {transport}")

        # Use load_config if present, else fallback to load_default_config
        try:
            config = load_config(args)
        except Exception:
            config = load_default_config()

               # Extract server configuration
        server_config = config.get("server", {})
        transport_config = server_config.get("transport", {})
        # Initialize FastMCP server with configuration
        mcp = FastMCP(
            name=server_config.get("name", "d365fo-mcp-server"),
            instructions=server_config.get(
                "instructions",
                "Microsoft Dynamics 365 Finance & Operations MCP Server providing comprehensive access to D365FO data, metadata, and operations",
            ),
            host=transport_config.get("http", {}).get("host", "127.0.0.1"),
            port=transport_config.get("http", {}).get("port", 8000),
            debug=server_config.get("debug", False),
            json_response=transport_config.get("http", {}).get("json_response", False),
            stateless_http=transport_config.get("http", {}).get("stateless", False),
        )

        server = FastD365FOMCPServer(mcp,config)
        mcp.run(transport=transport)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
