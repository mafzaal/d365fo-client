#!/usr/bin/env python3
"""Entry point for the D365FO MCP Server."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from d365fo_client.mcp import D365FOMCPServer


def setup_logging(level: str = "INFO") -> None:
    """Set up logging for the MCP server.

    Args:
        level: Logging level
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create logs directory
    log_dir = Path.home() / ".d365fo-mcp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "mcp-server.log"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def load_config() -> Optional[Dict[str, Any]]:
    """Load configuration from environment and config files.

    Returns:
        Configuration dictionary or None for defaults
    """
    config = {}

    # Load from environment variables
    if base_url := os.getenv("D365FO_BASE_URL"):
        config.setdefault("default_environment", {})["base_url"] = base_url

    if client_id := os.getenv("AZURE_CLIENT_ID"):
        config.setdefault("default_environment", {})["client_id"] = client_id
        config["default_environment"]["use_default_credentials"] = False

    if client_secret := os.getenv("AZURE_CLIENT_SECRET"):
        config.setdefault("default_environment", {})["client_secret"] = client_secret

    if tenant_id := os.getenv("AZURE_TENANT_ID"):
        config.setdefault("default_environment", {})["tenant_id"] = tenant_id

    # Logging level
    log_level = os.getenv("D365FO_LOG_LEVEL", "INFO")
    setup_logging(log_level)

    return config if config else None


async def async_main() -> None:
    """Async main entry point for the MCP server."""
    try:
        # Load configuration
        config = load_config()

        # Create and run the MCP server
        server = D365FOMCPServer(config)

        logging.info("Starting D365FO MCP Server...")
        await server.run()

    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the MCP server."""
    # Ensure event loop compatibility across platforms
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass  # Graceful shutdown


if __name__ == "__main__":
    main()
