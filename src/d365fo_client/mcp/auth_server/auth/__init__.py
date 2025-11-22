from .auth import (
    AccessToken,
    AuthProvider,
    OAuthProvider,
    RemoteAuthProvider,
    TokenVerifier,
)
from .oauth_proxy import OAuthProxy
from .providers.jwt import JWTVerifier, StaticTokenVerifier

__all__ = [
    "AuthProvider",
    "OAuthProvider",
    "TokenVerifier",
    "JWTVerifier",
    "StaticTokenVerifier",
    "RemoteAuthProvider",
    "AccessToken",
    "OAuthProxy",
]


def __getattr__(name: str):
    # Defer import because it raises a deprecation warning
    if name == "BearerAuthProvider":
        from .providers.bearer import BearerAuthProvider

        return BearerAuthProvider
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
