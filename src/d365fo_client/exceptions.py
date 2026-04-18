"""Exception classes for D365 F&O client."""

from typing import Optional


class FOClientError(Exception):
    """Base exception for F&O client errors.

    Attributes:
        activity_id: The ``ms-dyn-aid`` response header value returned by D365FO.
            Include this in support tickets to allow Microsoft to trace the request
            through service telemetry.
        request_id: The ``x-ms-client-request-id`` value sent in the request header.
            Also required for support ticket tracing.
    """

    def __init__(
        self,
        message: str,
        activity_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.activity_id: Optional[str] = activity_id
        self.request_id: Optional[str] = request_id

    def to_dict(self) -> dict:
        """Return a structured representation suitable for AI agent consumption."""
        result: dict = {"error": str(self)}
        if self.activity_id:
            result["ms_dyn_aid"] = self.activity_id
        if self.request_id:
            result["x_ms_client_request_id"] = self.request_id
        return result


class AuthenticationError(FOClientError):
    """Authentication related errors"""

    pass


class MetadataError(FOClientError):
    """Metadata operation errors"""

    pass


class EntityError(FOClientError):
    """Entity operation errors"""

    pass


class ActionError(FOClientError):
    """Action execution errors"""

    pass


class LabelError(FOClientError):
    """Label operation errors"""

    pass


class ConfigurationError(FOClientError):
    """Configuration related errors"""

    pass


class NetworkError(FOClientError):
    """Network and HTTP related errors"""

    pass
