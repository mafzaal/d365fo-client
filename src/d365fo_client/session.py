"""HTTP session management for D365 F&O client."""

import logging
import uuid
from pathlib import Path
from typing import Dict, Optional

import aiohttp

from .auth import AuthenticationManager
from .models import FOClientConfig

logger = logging.getLogger(__name__)

# File in ~/.d365fo-client/ that persists the stable trace client ID
_TRACE_CLIENT_ID_FILE = Path.home() / ".d365fo-client" / "trace_client_id"


def _load_or_create_trace_client_id(override: Optional[str]) -> str:
    """Return the trace client ID, honouring this resolution order:

    1. Explicitly configured ``trace_client_id`` value.
    2. Value persisted in ``~/.d365fo-client/trace_client_id``.
    3. Freshly generated UUID4 that is then persisted for future runs.
    """
    if override:
        return override

    try:
        if _TRACE_CLIENT_ID_FILE.exists():
            stored = _TRACE_CLIENT_ID_FILE.read_text(encoding="utf-8").strip()
            if stored:
                return stored
    except Exception:
        pass

    new_id = str(uuid.uuid4())
    try:
        _TRACE_CLIENT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TRACE_CLIENT_ID_FILE.write_text(new_id, encoding="utf-8")
    except Exception:
        pass  # Non-fatal; we still have an in-memory ID for this run

    return new_id


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

        # Stable ID representing this d365fo-client application instance.
        # Sent as ``x-ms-client-session-id`` on every request.
        if config.enable_request_tracing:
            self._trace_client_id: str = _load_or_create_trace_client_id(
                config.trace_client_id
            )
            logger.debug("Request tracing enabled. trace_client_id=%s", self._trace_client_id)
        else:
            self._trace_client_id = ""

    @property
    def trace_client_id(self) -> str:
        """Stable GUID that identifies this d365fo-client instance."""
        return self._trace_client_id

    def get_tracing_headers(self) -> Dict[str, str]:
        """Return per-request tracing headers.

        Generates a fresh ``x-ms-client-request-id`` UUID on every call as
        required by the D365FO service-request-tracing specification.  Returns
        an empty dict when tracing is disabled.
        """
        if not self.config.enable_request_tracing:
            return {}
        return {"x-ms-client-request-id": str(uuid.uuid4())}

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
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Stable session-level tracing header (same for every request in this session)
        if self.config.enable_request_tracing and self._trace_client_id:
            headers["x-ms-client-session-id"] = self._trace_client_id

        self._session.headers.update(headers)

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
