"""Exception classes for D365 F&O client."""


class FOClientError(Exception):
    """Base exception for F&O client errors"""

    pass


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
