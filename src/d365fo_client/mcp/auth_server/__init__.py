"""Server components for the D365FO MCP server."""

from .auth.providers.azure import AzureProvider

__all__ = ["AzureProvider"]