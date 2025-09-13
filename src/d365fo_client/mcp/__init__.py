"""MCP Server for d365fo-client.

This module provides a Model Context Protocol (MCP) server that exposes the full
capabilities of the d365fo-client to AI assistants and other MCP-compatible tools.

The server enables sophisticated Microsoft Dynamics 365 Finance & Operations
integration workflows through standardized MCP protocol.
"""

from .client_manager import D365FOClientManager
from .fastmcp_server import FastD365FOMCPServer
from .server import D365FOMCPServer

__all__ = [
    "D365FOMCPServer",           # Legacy MCP server (backward compatibility)
    "FastD365FOMCPServer",       # New FastMCP server with multi-transport support
    "D365FOClientManager",
]
