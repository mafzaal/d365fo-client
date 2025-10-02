"""API Key authentication provider for FastMCP.

This provider implements simple API key authentication using the Authorization header.
Suitable for service-to-service authentication and simpler deployment scenarios.

IMPORTANT: FastMCP uses BearerAuthBackend which extracts tokens from the Authorization header
and calls token_verifier.verify_token(). Clients must send the API key as:
    Authorization: Bearer <your-api-key>

The token_verifier.verify_token() method performs constant-time comparison of the API key.
"""

from __future__ import annotations

import secrets

from pydantic import SecretStr

from ..auth import AccessToken, TokenVerifier
from d365fo_client.mcp.utilities.logging import get_logger

logger = get_logger(__name__)


class APIKeyVerifier(TokenVerifier):
    """API Key token verifier for FastMCP.

    This is a TokenVerifier that validates API keys sent as Bearer tokens.
    FastMCP's BearerAuthBackend extracts the token from "Authorization: Bearer <token>"
    and passes it to this verifier's verify_token() method.

    This is a simpler alternative to OAuth for scenarios where:
    - Service-to-service authentication is needed
    - Simplified deployment without OAuth infrastructure
    - Single-user or trusted client scenarios

    Security features:
    - Constant-time comparison to prevent timing attacks
    - SecretStr storage to prevent accidental logging
    - No token expiration (suitable for long-lived API keys)
    """

    def __init__(
        self,
        api_key: SecretStr,
        base_url: str | None = None,
        required_scopes: list[str] | None = None,
    ):
        """Initialize API key provider.

        Args:
            api_key: The secret API key value
            base_url: Base URL of the server
            required_scopes: Required scopes (for compatibility, not enforced for API keys)
        """
        super().__init__(base_url=base_url, required_scopes=required_scopes)
        self.api_key = api_key

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify API key token.

        This method is called by FastMCP's BearerAuthBackend after extracting
        the token from "Authorization: Bearer <token>" header.

        Args:
            token: The API key extracted from the Authorization header

        Returns:
            AccessToken if valid, None otherwise
        """
        # Constant-time comparison to prevent timing attacks
        if secrets.compare_digest(token, self.api_key.get_secret_value()):
            logger.debug("API key authentication successful")
            return AccessToken(
                token=token,
                scopes=self.required_scopes or [],
                client_id="api_key_client",  # Fixed client_id for API key auth
                expires_at=None,  # API keys don't expire
                resource=None,
            )

        logger.warning("Invalid API key provided")
        return None
