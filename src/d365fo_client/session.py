"""HTTP session management for D365 F&O client."""

from typing import Optional

import aiohttp

from .auth import AuthenticationManager
from .models import FOClientConfig


class SessionManager:
    """Manages HTTP sessions with authentication"""

    def __init__(self, config: FOClientConfig, auth_manager: AuthenticationManager):
        """Initialize session manager

        Args:
            config: F&O client configuration
            auth_manager: Authentication manager instance
        """
        self.config = config
        self.auth_manager = auth_manager
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session with auth headers

        Returns:
            Configured aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self.config.verify_ssl)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        # Update headers with fresh token
        token = await self.auth_manager.get_token()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        return self._session

    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
