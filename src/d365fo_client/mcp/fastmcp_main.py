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

from d365fo_client import __version__
from d365fo_client.mcp import FastD365FOMCPServer


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

Production Examples:
  # Development (default)
  %(prog)s                                    
  
  # Web development
  %(prog)s --transport sse --port 8000 --debug       
  
  # Production deployment
  %(prog)s --transport http --host 0.0.0.0 --port 8000
  
  # High-availability stateless deployment
  %(prog)s --transport http --host 0.0.0.0 --port 8000 --stateless
  
  # API gateway compatible
  %(prog)s --transport http --host 0.0.0.0 --port 8000 --stateless --json-response
  
  # Cloud deployment with performance monitoring
  %(prog)s --transport http --host 0.0.0.0 --port 8000 --stateless --log-level INFO
  
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
        choices=["stdio", "sse", "http", "streamable-http"],
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
    if transport == "streamable-http":
        transport = "http"

    # Get environment variables
    base_url = os.getenv("D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com")
    
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


async def async_main() -> None:
    """Async main entry point for the FastMCP server."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Set up logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        # Load configuration
        config = load_config(args)
        
        # Normalize transport
        transport = args.transport
        if transport == "streamable-http":
            transport = "http"
        
        # Print detailed startup information
        logger.info(f"Starting FastD365FOMCPServer v{__version__}")
        logger.info(f"Transport: {transport}")
        
        if transport in ["sse", "http"]:
            logger.info(f"Server will bind to {args.host}:{args.port}")
            
            # Validate host and port configuration
            if args.host == "0.0.0.0":
                logger.info("Server configured for external access (0.0.0.0)")
                logger.warning("Ensure firewall and security settings are properly configured")
            else:
                logger.info(f"Server configured for local access ({args.host})")
                
            if args.stateless and transport == "http":
                logger.info("HTTP stateless mode enabled - optimized for horizontal scaling")
                logger.info("Sessions will not be persisted between requests")
            elif transport == "http":
                logger.info("HTTP stateful mode enabled - sessions will be maintained")
                
            if args.json_response and transport == "http":
                logger.info("JSON response mode enabled - API gateway compatible")
            elif transport == "http":
                logger.info("Stream response mode enabled - optimized for real-time data")
                
        # Performance configuration logging
        max_concurrent = config.get("performance", {}).get("max_concurrent_requests", 10)
        request_timeout = config.get("performance", {}).get("request_timeout", 30)
        logger.info(f"Performance limits: {max_concurrent} concurrent requests, {request_timeout}s timeout")
        
        # Security and environment information
        startup_mode = config.get("startup_mode", "profile_only")
        logger.info(f"Authentication mode: {startup_mode}")
        
        if startup_mode == "profile_only":
            logger.info("No D365FO environment configured - use profile management tools")
        else:
            base_url = config.get("default_environment", {}).get("base_url", "")
            if base_url:
                logger.info(f"Default D365FO environment: {base_url}")
        
        # Create and run server
        server = FastD365FOMCPServer(config)
        await server.run_async(transport=transport)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the FastMCP server."""
    # Handle Windows event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()