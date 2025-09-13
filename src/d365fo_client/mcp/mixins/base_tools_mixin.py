"""Base mixin class for FastMCP tool categories."""

import logging
from typing import Optional
from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class BaseToolsMixin:
    """Base mixin for FastMCP tool categories.
    
    Provides common functionality and client access patterns
    for all tool category mixins.
    """
    
    # These will be injected by the main server class
    client_manager: D365FOClientManager
    mcp: 'FastMCP'  # Forward reference
    
    async def _get_client(self, profile: str = "default"):
        """Get D365FO client for specified profile.
        
        Args:
            profile: Profile name to use
            
        Returns:
            Configured D365FO client instance
        """
        if not hasattr(self, 'client_manager') or not self.client_manager:
            raise RuntimeError("Client manager not initialized")
        return await self.client_manager.get_client(profile)
    
    def _create_error_response(self, error: Exception, tool_name: str, arguments: dict) -> str:
        """Create standardized error response.
        
        Args:
            error: Exception that occurred
            tool_name: Name of the tool that failed
            arguments: Arguments passed to the tool
            
        Returns:
            JSON string with error details
        """
        import json
        return json.dumps({
            "error": str(error),
            "tool": tool_name,
            "arguments": arguments,
            "error_type": type(error).__name__,
        }, indent=2)