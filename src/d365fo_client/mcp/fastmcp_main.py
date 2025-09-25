#!/usr/bin/env python3
"""Entry point for the FastMCP-based D365FO MCP Server."""

import argparse
import asyncio
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Literal
from mcp.server.fastmcp import FastMCP

from d365fo_client import __version__
from d365fo_client.mcp import FastD365FOMCPServer
from d365fo_client.mcp.fastmcp_utils import create_default_profile_if_needed, load_default_config
from d365fo_client.profile_manager import ProfileManager
from d365fo_client.utils import get_default_cache_directory



def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration with 24-hour log rotation.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get log file path from environment variable or use default
    log_file_path = os.getenv("D365FO_LOG_FILE")
    
    if log_file_path:
        # Use custom log file path from environment variable
        log_file = Path(log_file_path)
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Use default log file path
        log_dir = Path.home() / ".d365fo-mcp" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "fastmcp-server.log"

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
  MCP_HTTP_HOST             Default HTTP host (default: 127.0.0.1)
  MCP_HTTP_PORT             Default HTTP port (default: 8000)
  MCP_HTTP_STATELESS        Enable stateless mode (true/false)
  MCP_HTTP_JSON             Enable JSON response mode (true/false)
  MCP_MAX_CONCURRENT_REQUESTS  Max concurrent requests (default: 10)
  MCP_REQUEST_TIMEOUT       Request timeout in seconds (default: 30)
  D365FO_LOG_LEVEL          Logging level (DEBUG, INFO, WARNING, ERROR)
  D365FO_LOG_FILE           Custom log file path (default: ~/.d365fo-mcp/logs/fastmcp-server.log)
  D365FO_META_CACHE_DIR   Metadata cache directory (default: ~/.d365fo-mcp/cache)

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


# Parse arguments first to check transport
args = parse_arguments()
arg_transport =  args.transport


# Set up logging and load configuration
if arg_transport == "http":
    arg_transport = "streamable-http"

transport:Literal["stdio", "sse", "streamable-http"] = arg_transport

setup_logging(args.log_level or os.getenv("D365FO_LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

logger.info(f"Starting FastD365FOMCPServer v{__version__} with transport: {transport}")

# Use load_default_config with args instead of separate load_config function
config = load_default_config(args)

default_fo = config.get("default_environment", {})

config_path = default_fo.get("metadata_cache_dir", get_default_cache_directory())

logger.info(f"Using config path: {config_path}")

# Create profile manager with config path
profile_manager = ProfileManager(str(Path(config_path) / "config.yaml"))

if not create_default_profile_if_needed(profile_manager, config):
    # TODO: Migrate legacy profiles if needed
    logger.warning("Migrate legacy profiles if needed.")

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

server = FastD365FOMCPServer(mcp,config,profile_manager=profile_manager)


def main() -> None:
    """Main entry point for the FastMCP server."""

    # Handle Windows event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
