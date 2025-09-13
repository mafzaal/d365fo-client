#!/usr/bin/env python3
"""Entry point for the FastMCP-based D365FO MCP Server."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Literal

from d365fo_client import __version__
from d365fo_client.mcp import FastD365FOMCPServer


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure logging
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ]
    )


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

Examples:
  %(prog)s                                    # stdio transport (default)
  %(prog)s --transport sse --port 8000       # SSE transport on port 8000
  %(prog)s --transport http --host 0.0.0.0   # HTTP transport for production
  %(prog)s --transport http --stateless      # Stateless HTTP for load balancing
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
        help="Enable stateless HTTP mode (for load balancing)"
    )
    
    parser.add_argument(
        "--json-response",
        action="store_true",
        help="Use JSON responses instead of SSE streams (HTTP transport only)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
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
            "label_cache_expiry_minutes": 120,
            "use_label_cache": True,
            "cache_size_limit_mb": 100,
        },
        "performance": {
            "max_concurrent_requests": 10,
            "connection_pool_size": 5,
            "request_timeout": 30,
            "batch_size": 100,
        },
        "security": {
            "encrypt_cached_tokens": True,
            "token_expiry_buffer_minutes": 5,
            "max_retry_attempts": 3,
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
        
        logger.info(f"Starting FastD365FOMCPServer v{__version__}")
        logger.info(f"Transport: {transport}")
        
        if transport in ["sse", "http"]:
            logger.info(f"Server will bind to {args.host}:{args.port}")
            if args.stateless and transport == "http":
                logger.info("HTTP stateless mode enabled")
            if args.json_response and transport == "http":
                logger.info("JSON response mode enabled")
        
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