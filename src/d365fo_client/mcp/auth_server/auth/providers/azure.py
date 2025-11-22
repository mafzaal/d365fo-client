"""Azure (Microsoft Entra) OAuth provider for FastMCP.

This provider implements Azure/Microsoft Entra ID OAuth authentication
using the OAuth Proxy pattern for non-DCR OAuth flows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest import result

import httpx
from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from d365fo_client.mcp.utilities.auth import parse_scopes
from d365fo_client.mcp.utilities.logging import get_logger
from d365fo_client.mcp.utilities.types import NotSet, NotSetT

from ..auth import AccessToken, TokenVerifier
from ..oauth_proxy import OAuthProxy

logger = get_logger(__name__)


class AzureProviderSettings(BaseSettings):
    """Settings for Azure OAuth provider."""

    model_config = SettingsConfigDict(
        env_prefix="FASTMCP_SERVER_AUTH_AZURE_",
        env_file=".env",
        extra="ignore",
    )

    client_id: str | None = None
    client_secret: SecretStr | None = None
    tenant_id: str | None = None
    base_url: str | None = None
    redirect_path: str | None = None
    required_scopes: list[str] | None = None
    timeout_seconds: int | None = None
    allowed_client_redirect_uris: list[str] | None = None
    clients_storage_path: str | None = None

    @field_validator("required_scopes", mode="before")
    @classmethod
    def _parse_scopes(cls, v):
        return parse_scopes(v)


class AzureTokenVerifier(TokenVerifier):
    """Token verifier for Azure OAuth tokens.

    Azure tokens are JWTs, but we verify them by calling the Microsoft Graph API
    to get user information and validate the token.
    """

    def __init__(
        self,
        *,
        required_scopes: list[str] | None = None,
        timeout_seconds: int = 10,
    ):
        """Initialize the Azure token verifier.

        Args:
            required_scopes: Required OAuth scopes
            timeout_seconds: HTTP request timeout
        """
        super().__init__(required_scopes=required_scopes)
        self.timeout_seconds = timeout_seconds

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify Azure OAuth token by calling Microsoft Graph API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Use Microsoft Graph API to validate token and get user info
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": "FastMCP-Azure-OAuth",
                    },
                )

                if response.status_code != 200:
                    logger.debug(
                        "Azure token verification failed: %d - %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return None

                user_data = response.json()

                # Create AccessToken with Azure user info
                return AccessToken(
                    token=token,
                    client_id=str(user_data.get("id", "unknown")),
                    scopes=self.required_scopes or [],
                    expires_at=None,
                    claims={
                        "sub": user_data.get("id"),
                        "email": user_data.get("mail")
                        or user_data.get("userPrincipalName"),
                        "name": user_data.get("displayName"),
                        "given_name": user_data.get("givenName"),
                        "family_name": user_data.get("surname"),
                        "job_title": user_data.get("jobTitle"),
                        "office_location": user_data.get("officeLocation"),
                    },
                )

        except httpx.RequestError as e:
            logger.debug("Failed to verify Azure token: %s", e)
            return None
        except Exception as e:
            logger.debug("Azure token verification error: %s", e)
            return None


class AzureProvider(OAuthProxy):
    """Azure (Microsoft Entra) OAuth provider for FastMCP.

    This provider implements Azure/Microsoft Entra ID authentication using the
    OAuth Proxy pattern. It supports both organizational accounts and personal
    Microsoft accounts depending on the tenant configuration.

    Features:
    - Transparent OAuth proxy to Azure/Microsoft identity platform
    - Automatic token validation via Microsoft Graph API
    - User information extraction
    - Support for different tenant configurations (common, organizations, consumers)

    Setup Requirements:
    1. Register an application in Azure Portal (portal.azure.com)
    2. Configure redirect URI as: http://localhost:8000/auth/callback
    3. Note your Application (client) ID and create a client secret
    4. Optionally note your Directory (tenant) ID for single-tenant apps

    Example:
        ```python
        from fastmcp import FastMCP
        from fastmcp.server.auth.providers.azure import AzureProvider

        auth = AzureProvider(
            client_id="your-client-id",
            client_secret="your-client-secret",
            tenant_id="your-tenant-id",  # Required: your Azure tenant ID from Azure Portal
            base_url="http://localhost:8000"
        )

        mcp = FastMCP("My App", auth=auth)
        ```
    """

    def __init__(
        self,
        *,
        client_id: str | NotSetT = NotSet,
        client_secret: str | NotSetT = NotSet,
        tenant_id: str | NotSetT = NotSet,
        base_url: str | NotSetT = NotSet,
        redirect_path: str | NotSetT = NotSet,
        required_scopes: list[str] | None | NotSetT = NotSet,
        timeout_seconds: int | NotSetT = NotSet,
        allowed_client_redirect_uris: list[str] | NotSetT = NotSet,
        clients_storage_path: str | NotSetT = NotSet,  # Path to store clients data
    ):
        """Initialize Azure OAuth provider.

        Args:
            client_id: Azure application (client) ID
            client_secret: Azure client secret
            tenant_id: Azure tenant ID (your specific tenant ID, "organizations", or "consumers")
            base_url: Public URL of your FastMCP server (for OAuth callbacks)
            redirect_path: Redirect path configured in Azure (defaults to "/auth/callback")
            required_scopes: Required scopes (defaults to ["User.Read", "email", "openid", "profile"])
            timeout_seconds: HTTP request timeout for Azure API calls
            allowed_client_redirect_uris: List of allowed redirect URI patterns for MCP clients.
                If None (default), all URIs are allowed. If empty list, no URIs are allowed.
        """
        settings = AzureProviderSettings.model_validate(
            {
                k: v
                for k, v in {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "tenant_id": tenant_id,
                    "base_url": base_url,
                    "redirect_path": redirect_path,
                    "required_scopes": required_scopes,
                    "timeout_seconds": timeout_seconds,
                    "allowed_client_redirect_uris": allowed_client_redirect_uris,
                    "clients_storage_path": clients_storage_path,
                }.items()
                if v is not NotSet
            }
        )

        # Validate required settings
        if not settings.client_id:
            raise ValueError(
                "client_id is required - set via parameter or FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID"
            )
        if not settings.client_secret:
            raise ValueError(
                "client_secret is required - set via parameter or FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET"
            )

        # Validate tenant_id is provided
        if not settings.tenant_id:
            raise ValueError(
                "tenant_id is required - set via parameter or FASTMCP_SERVER_AUTH_AZURE_TENANT_ID. "
                "Use your Azure tenant ID (found in Azure Portal), 'organizations', or 'consumers'"
            )

        # Apply defaults
        tenant_id_final = settings.tenant_id

        redirect_path_final = settings.redirect_path or "/auth/callback"
        timeout_seconds_final = settings.timeout_seconds or 10
        # Default scopes for Azure - User.Read gives us access to user info via Graph API
        scopes_final = settings.required_scopes or [
            "User.Read",
            "email",
            "openid",
            "profile",
        ]
        allowed_client_redirect_uris_final = settings.allowed_client_redirect_uris

        # Extract secret string from SecretStr
        client_secret_str = (
            settings.client_secret.get_secret_value() if settings.client_secret else ""
        )

        # Create Azure token verifier
        token_verifier = AzureTokenVerifier(
            required_scopes=scopes_final,
            timeout_seconds=timeout_seconds_final,
        )

        # Build Azure OAuth endpoints with tenant
        authorization_endpoint = (
            f"https://login.microsoftonline.com/{tenant_id_final}/oauth2/v2.0/authorize"
        )
        token_endpoint = (
            f"https://login.microsoftonline.com/{tenant_id_final}/oauth2/v2.0/token"
        )

        # Initialize OAuth proxy with Azure endpoints
        super().__init__(
            upstream_authorization_endpoint=authorization_endpoint,
            upstream_token_endpoint=token_endpoint,
            upstream_client_id=settings.client_id,
            upstream_client_secret=client_secret_str,
            token_verifier=token_verifier,
            base_url=settings.base_url,  # type: ignore[arg-type]
            redirect_path=redirect_path_final,
            issuer_url=settings.base_url,
            allowed_client_redirect_uris=allowed_client_redirect_uris_final,
        )

        self.clients_storage_path = settings.clients_storage_path

        self._load_clients()

        logger.info(
            "Initialized Azure OAuth provider for client %s with tenant %s",
            settings.client_id,
            tenant_id_final,
        )

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Authorize request, removing 'resource' parameter if present."""

        if params.resource:
            params.resource = None  # Azure does not use 'resource' parameter

        return await super().authorize(client, params)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Register a new MCP client, validating redirect URIs if configured."""
        await super().register_client(client_info)
        try:
            self._save_clients()
        except Exception as e:
            logger.error(f"Failed to persist client registration: {e}")
            # Don't raise here as the client is already registered in memory

    def _save_clients(self) -> None:
        """Save client data to persistent storage.

        Raises:
            ValueError: If clients_storage_path is not configured
            OSError: If file operations fail
        """
        if not self.clients_storage_path:
            logger.warning("No clients storage path configured. Skipping client save.")
            return

        try:
            # Ensure the storage directory exists
            storage_dir = Path(self.clients_storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)

            client_json_path = storage_dir / "clients.json"

            # Convert OAuthClientInformationFull objects to dictionaries for JSON serialization
            # Use mode="json" to properly serialize complex types like AnyUrl
            clients_dict = {}
            for client_id, client in self._clients.items():
                try:
                    if hasattr(client, "model_dump"):
                        # Use json mode to ensure proper serialization of complex types (e.g., AnyUrl)
                        clients_dict[client_id] = client.model_dump(mode="json")
                    else:
                        # Fallback for non-Pydantic objects (shouldn't happen with OAuthClientInformationFull)
                        clients_dict[client_id] = client.__dict__
                except Exception as client_error:
                    logger.error(
                        f"Failed to serialize client {client_id}: {client_error}"
                    )
                    continue

            # Write to temporary file first, then rename for atomic operation
            temp_path = client_json_path.with_suffix(".tmp")
            with temp_path.open("w") as f:
                json.dump(clients_dict, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(client_json_path)

            logger.debug(
                f"Successfully saved {len(clients_dict)} clients to {client_json_path}"
            )

        except Exception as e:
            logger.error(
                f"Failed to save client data to {self.clients_storage_path}: {e}"
            )
            raise

    def _load_clients(self) -> None:
        """Load client data from persistent storage.

        Loads clients from the JSON file if it exists and is valid.
        Invalid client data is logged and skipped.
        """
        if not self.clients_storage_path:
            logger.debug("No clients storage path configured. Skipping client load.")
            return

        try:
            client_json_path = Path(self.clients_storage_path) / "clients.json"

            if not client_json_path.exists():
                logger.debug(
                    f"Client storage file {client_json_path} does not exist. Starting with empty client registry."
                )
                return

            # Read and parse the JSON file
            with client_json_path.open("r", encoding="utf-8") as f:
                clients_data = json.load(f)

            if not isinstance(clients_data, dict):
                logger.error(
                    f"Invalid client data format in {client_json_path}: expected dict, got {type(clients_data)}"
                )
                return

            loaded_count = 0
            for client_id, client_info in clients_data.items():
                try:
                    # Validate client_id is a string
                    if not isinstance(client_id, str):
                        logger.warning(
                            f"Skipping client with non-string ID: {client_id} (type: {type(client_id)})"
                        )
                        continue

                    # Validate and restore the client object
                    if not isinstance(client_info, dict):
                        logger.warning(
                            f"Skipping client {client_id}: invalid data format (expected dict, got {type(client_info)})"
                        )
                        continue

                    # Use Pydantic model_validate to restore the object with proper validation
                    client_obj = OAuthClientInformationFull.model_validate(client_info)
                    self._clients[client_id] = client_obj
                    loaded_count += 1

                except Exception as client_error:
                    logger.error(f"Failed to load client {client_id}: {client_error}")
                    continue

            logger.info(
                f"Successfully loaded {loaded_count} clients from {client_json_path}"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in client storage file {client_json_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load clients from {client_json_path}: {e}")
