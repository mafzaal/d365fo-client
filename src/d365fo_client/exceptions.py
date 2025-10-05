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


class DMFError(FOClientError):
    """Data Management Framework operation errors"""

    def __init__(
        self, message: str, execution_id: str = "", error_details: dict = None
    ):
        """Initialize DMF error.

        Args:
            message: Error message
            execution_id: DMF execution ID if available
            error_details: Additional error details
        """
        super().__init__(message)
        self.execution_id = execution_id
        self.error_details = error_details or {}


class DMFExecutionError(DMFError):
    """DMF execution specific errors"""

    pass


class DMFPackageError(DMFError):
    """DMF package operation errors"""

    pass


class DMFTimeoutError(DMFError):
    """DMF operation timeout errors"""

    pass
