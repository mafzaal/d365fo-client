"""Microsoft Dynamics 365 Finance & Operations client package.

A comprehensive Python client for connecting to D365 F&O and performing:
- Metadata download, storage, and search
- OData action method calls
- CRUD operations on data entities
- OData query parameters support
- Label text retrieval and caching
- Multilingual label support
- Entity metadata with resolved labels

Basic Usage:
    from d365fo_client import FOClient, FOClientConfig

    config = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        use_default_credentials=True
    )

    async with FOClient(config) as client:
        # Download metadata
        await client.download_metadata()

        # Search entities
        entities = client.search_entities("customer")

        # Get entities
        customers = await client.get_entities("Customers", top=10)

        # Get labels
        label_text = await client.get_label_text("@SYS13342")

Quick Start:
    from d365fo_client import create_client

    client = create_client("https://your-fo-environment.dynamics.com")
"""

import sys
from pathlib import Path


# Dynamic version, author, and email retrieval
def _get_package_metadata():
    """Get package metadata from installed package or pyproject.toml."""
    package_name = "d365fo-client"

    # Try to get from installed package metadata first (works after pip install)
    try:
        from importlib.metadata import metadata

        pkg_metadata = metadata(package_name)

        version = pkg_metadata["Version"]
        authors = pkg_metadata.get("Author-email", "").split(", ")

        # Parse author and email from "Name <email>" format
        if authors and authors[0]:
            author_email = authors[0]
            if "<" in author_email and ">" in author_email:
                author = author_email.split("<")[0].strip()
                email = author_email.split("<")[1].split(">")[0].strip()
            else:
                # Fallback if format is different
                author = pkg_metadata.get("Author", "Muhammad Afzaal")
                email = author_email if "@" in author_email else "mo@thedataguy.pro"
        else:
            author = pkg_metadata.get("Author", "Muhammad Afzaal")
            email = "mo@thedataguy.pro"

        return version, author, email

    except ImportError:
        # importlib.metadata not available (Python < 3.8)
        pass
    except Exception:
        # Package not installed or other error
        pass

    # Fallback: try to read from pyproject.toml (development mode)
    try:
        # Try to find pyproject.toml in package directory or parent directories
        current_file = Path(__file__)
        for parent in [
            current_file.parent,
            current_file.parent.parent,
            current_file.parent.parent.parent,
        ]:
            pyproject_path = parent / "pyproject.toml"
            if pyproject_path.exists():
                # Try to use tomllib for Python 3.11+
                tomllib = None
                if sys.version_info >= (3, 11):
                    try:
                        import tomllib
                    except ImportError:
                        tomllib = None

                if tomllib:
                    with open(pyproject_path, "rb") as f:
                        data = tomllib.load(f)

                    # Use tomllib parsed data
                    project = data.get("project", {})
                    version = project.get("version", "0.1.0")

                    authors = project.get("authors", [])
                    if authors and len(authors) > 0:
                        author = authors[0].get("name", "Muhammad Afzaal")
                        email = authors[0].get("email", "mo@thedataguy.pro")
                    else:
                        author = "Muhammad Afzaal"
                        email = "mo@thedataguy.pro"

                    return version, author, email
                else:
                    # Fallback for Python < 3.11: simple parsing
                    import re

                    with open(pyproject_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    version_match = re.search(
                        r'version\s*=\s*["\']([^"\']+)["\']', content
                    )
                    author_match = re.search(
                        r'name\s*=\s*["\']([^"\']+)["\'].*?email\s*=\s*["\']([^"\']+)["\']',
                        content,
                        re.DOTALL,
                    )

                    if version_match:
                        version = version_match.group(1)
                    else:
                        version = "0.1.0"

                    if author_match:
                        author = author_match.group(1)
                        email = author_match.group(2)
                    else:
                        author = "Muhammad Afzaal"
                        email = "mo@thedataguy.pro"

                    return version, author, email

    except Exception:
        # If all else fails, use fallback values
        pass

    # Ultimate fallback
    return "0.1.0", "Muhammad Afzaal", "mo@thedataguy.pro"


__version__, __author__, __email__ = _get_package_metadata()

from .cli import CLIManager

# Import main classes and functions for public API
from .client import FOClient, create_client
from .config import ConfigManager
from .exceptions import (
    ActionError,
    AuthenticationError,
    ConfigurationError,
    EntityError,
    FOClientError,
    LabelError,
    MetadataError,
    NetworkError,
)
from .labels import resolve_labels_generic, resolve_labels_generic_with_cache
from .main import main

# MCP Server
from .mcp import D365FOClientManager, D365FOMCPServer

# Legacy Metadata Cache (deprecated - use metadata_v2)
# REMOVED: Legacy classes have been replaced with V2 implementations
# from .metadata_cache import MetadataCache, MetadataSearchEngine

# V2 Metadata Cache (recommended - now the only implementation)
from .metadata_v2 import MetadataCacheV2, VersionAwareSearchEngine

# Provide backward compatibility with immediate import errors
import warnings

class _DeprecatedMetadataCache:
    """Deprecated placeholder for MetadataCache - raises error on any access"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "MetadataCache is deprecated and has been removed. "
            "Use MetadataCacheV2 from d365fo_client.metadata_v2 instead.",
            DeprecationWarning,
            stacklevel=2
        )
        raise ImportError(
            "MetadataCache has been removed. Use MetadataCacheV2 from d365fo_client.metadata_v2 instead."
        )
    
    def __getattr__(self, name):
        raise ImportError(
            "MetadataCache has been removed. Use MetadataCacheV2 from d365fo_client.metadata_v2 instead."
        )

class _DeprecatedMetadataSearchEngine:
    """Deprecated placeholder for MetadataSearchEngine - raises error on any access"""
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "MetadataSearchEngine is deprecated and has been removed. "
            "Use VersionAwareSearchEngine from d365fo_client.metadata_v2 instead.",
            DeprecationWarning,
            stacklevel=2
        )
        raise ImportError(
            "MetadataSearchEngine has been removed. Use VersionAwareSearchEngine from d365fo_client.metadata_v2 instead."
        )
    
    def __getattr__(self, name):
        raise ImportError(
            "MetadataSearchEngine has been removed. Use VersionAwareSearchEngine from d365fo_client.metadata_v2 instead."
        )

# Create deprecated placeholder classes
MetadataCache = _DeprecatedMetadataCache
MetadataSearchEngine = _DeprecatedMetadataSearchEngine
from .models import (
    ActionInfo,
    DataEntityInfo,
    EnumerationInfo,
    EnumerationMemberInfo,
    FOClientConfig,
    LabelInfo,
    PublicEntityInfo,
    PublicEntityPropertyInfo,
    QueryOptions,
)
from .output import OutputFormatter
from .profile_manager import ProfileManager
from .profiles import Profile
from .utils import (
    ensure_directory_exists,
    extract_domain_from_url,
    get_default_cache_directory,
    get_environment_cache_dir,
    get_environment_cache_directory,
    get_user_cache_dir,
)

# Legacy aliases for backward compatibility
CLIProfile = Profile
EnvironmentProfile = Profile

# Public API
__all__ = [
    # Main client
    "FOClient",
    "create_client",
    # Legacy caching (deprecated placeholders - raise errors when used)
    "MetadataCache", 
    "MetadataSearchEngine",
    # V2 caching (now the primary implementation)
    "MetadataCacheV2", 
    "VersionAwareSearchEngine",
    "resolve_labels_generic",
    # Configuration and models
    "FOClientConfig",
    "QueryOptions",
    "LabelInfo",
    "ActionInfo",
    "DataEntityInfo",
    "PublicEntityInfo",
    "EnumerationInfo",
    "PublicEntityPropertyInfo",
    "EnumerationMemberInfo",
    # Exceptions
    "FOClientError",
    "AuthenticationError",
    "MetadataError",
    "EntityError",
    "ActionError",
    "LabelError",
    "ConfigurationError",
    "NetworkError",
    # Utilities
    "get_user_cache_dir",
    "get_default_cache_directory",
    "ensure_directory_exists",
    "extract_domain_from_url",
    "get_environment_cache_dir",
    "get_environment_cache_directory",
    # CLI components
    "OutputFormatter",
    "ConfigManager",
    "Profile",
    "ProfileManager",
    "CLIManager",
    # Legacy aliases
    "CLIProfile",
    "EnvironmentProfile",
    # MCP Server
    "D365FOMCPServer",
    "D365FOClientManager",
    # Entry point
    "main",
]
