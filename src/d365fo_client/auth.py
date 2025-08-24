"""Authentication utilities for D365 F&O client."""

from datetime import datetime
from typing import Optional

from azure.identity import ClientSecretCredential, DefaultAzureCredential

from .models import FOClientConfig


class AuthenticationManager:
    """Manages authentication for F&O client"""

    def __init__(self, config: FOClientConfig):
        """Initialize authentication manager

        Args:
            config: F&O client configuration
        """
        self.config = config
        self._token = None
        self._token_expires = None
        self.credential = self._setup_credentials()

    def _setup_credentials(self):
        """Setup authentication credentials"""
        if self.config.use_default_credentials:
            return DefaultAzureCredential()
        elif (
            self.config.client_id
            and self.config.client_secret
            and self.config.tenant_id
        ):
            return ClientSecretCredential(
                tenant_id=self.config.tenant_id,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
            )
        else:
            raise ValueError(
                "Must provide either use_default_credentials=True or client credentials"
            )

    async def get_token(self) -> str:
        """Get authentication token

        Returns:
            Bearer token string
        """
        # Skip authentication for localhost/mock server
        if self._is_localhost():
            return "mock-token-for-localhost"

        if (
            self._token
            and self._token_expires
            and datetime.now().timestamp() < self._token_expires
        ):
            return self._token

        # Try different scopes
        scopes_to_try = [
            f"{self.config.base_url}/.default",
            f"{self.config.client_id}/.default" if self.config.client_id else None,
        ]

        for scope in scopes_to_try:
            if not scope:
                continue
            try:
                token = self.credential.get_token(scope)
                self._token = token.token
                self._token_expires = token.expires_on
                return self._token
            except Exception as e:
                print(f"Failed to get token with scope {scope}: {e}")
                continue

        raise Exception("Failed to get authentication token")

    def _is_localhost(self) -> bool:
        """Check if the base URL is localhost (for mock testing)

        Returns:
            True if base URL is localhost/127.0.0.1
        """
        base_url = self.config.base_url.lower()
        return any(host in base_url for host in ["localhost", "127.0.0.1", "::1"])

    def invalidate_token(self):
        """Invalidate cached token to force refresh"""
        self._token = None
        self._token_expires = None
