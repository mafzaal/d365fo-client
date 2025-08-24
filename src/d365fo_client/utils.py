"""Utility functions for D365 F&O client."""

import os
import platform
import re
from pathlib import Path
from typing import Union
from urllib.parse import urlparse


def get_user_cache_dir(app_name: str = "d365fo-client") -> Path:
    r"""Get the appropriate user cache directory for the current platform.

    This function follows platform conventions for cache directories:
    - Windows: %LOCALAPPDATA%\<app_name> (e.g., C:\Users\username\AppData\Local\d365fo-client)
    - macOS: ~/Library/Caches/<app_name> (e.g., /Users/username/Library/Caches/d365fo-client)
    - Linux: ~/.cache/<app_name> (e.g., /home/username/.cache/d365fo-client)

    Args:
        app_name: Name of the application (used as directory name)

    Returns:
        Path object pointing to the cache directory

    Examples:
        >>> cache_dir = get_user_cache_dir()
        >>> print(cache_dir)  # doctest: +SKIP
        WindowsPath('C:/Users/username/AppData/Local/d365fo-client')

        >>> cache_dir = get_user_cache_dir("my-app")
        >>> "my-app" in str(cache_dir)
        True
    """
    system = platform.system()

    if system == "Windows":
        # Use LOCALAPPDATA for cache data on Windows
        # Falls back to APPDATA if LOCALAPPDATA is not available
        cache_root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if cache_root:
            return Path(cache_root) / app_name
        else:
            # Fallback: use user home directory
            return Path.home() / "AppData" / "Local" / app_name

    elif system == "Darwin":  # macOS
        # Use ~/Library/Caches on macOS
        return Path.home() / "Library" / "Caches" / app_name

    else:  # Linux and other Unix-like systems
        # Use XDG_CACHE_HOME if set, otherwise ~/.cache
        cache_root = os.environ.get("XDG_CACHE_HOME")
        if cache_root:
            return Path(cache_root) / app_name
        else:
            return Path.home() / ".cache" / app_name


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create

    Returns:
        Path object pointing to the directory

    Raises:
        OSError: If directory creation fails
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_default_cache_directory() -> str:
    r"""Get the default cache directory for d365fo-client.

    This is a convenience function that returns the appropriate cache directory
    as a string, ready to be used as the default value for metadata_cache_dir.

    Returns:
        String path to the default cache directory

    Examples:
        >>> cache_dir = get_default_cache_directory()
        >>> "d365fo-client" in cache_dir
        True
    """
    return str(get_user_cache_dir())


def extract_domain_from_url(url: str) -> str:
    """Extract and sanitize domain name from URL for use as directory name.

    Args:
        url: The base URL (e.g., "https://mycompany.sandbox.operations.dynamics.com")

    Returns:
        Sanitized domain name suitable for directory name

    Examples:
        >>> extract_domain_from_url("https://mycompany.sandbox.operations.dynamics.com")
        'mycompany.sandbox.operations.dynamics.com'

        >>> extract_domain_from_url("https://test-env.dynamics.com/")
        'test-env.dynamics.com'

        >>> extract_domain_from_url("https://localhost:8080")
        'localhost_8080'
    """
    if not url or not url.strip():
        return "unknown-domain"

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # If no netloc (malformed URL), try to extract something useful
        if not domain:
            # Try to extract domain-like pattern from the URL
            domain_match = re.search(r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", url)
            if domain_match:
                domain = domain_match.group(1).lower()
            else:
                # Fallback: create a safe name from the original URL
                safe_name = re.sub(r"[^\w\.-]", "_", url.lower())
                return safe_name[:50] or "unknown-domain"

        # Remove default ports for common schemes
        if (parsed.scheme == "https" and domain.endswith(":443")) or (
            parsed.scheme == "http" and domain.endswith(":80")
        ):
            domain = domain.rsplit(":", 1)[0]

        # Replace invalid filesystem characters with underscore
        # Windows reserved characters: < > : " | ? * \ /
        # Also replace other potentially problematic characters
        domain = re.sub(r'[<>:"|?*\\/]', "_", domain)

        # Replace remaining special characters that might cause issues
        domain = re.sub(r"[^\w\.-]", "_", domain)

        return domain or "unknown-domain"

    except Exception:
        # Fallback: create a safe name from the original URL
        safe_name = re.sub(r"[^\w\.-]", "_", url.lower())
        return safe_name[:50] or "unknown-domain"  # Limit length


def get_environment_cache_dir(base_url: str, app_name: str = "d365fo-client") -> Path:
    """Get environment-specific cache directory based on F&O base URL.

    This creates a separate cache directory for each F&O environment, allowing
    users to work with multiple environments without cache conflicts.

    Args:
        base_url: F&O environment base URL
        app_name: Application name (default: "d365fo-client")

    Returns:
        Path object pointing to the environment-specific cache directory

    Examples:
        >>> cache_dir = get_environment_cache_dir("https://usnconeboxax1aos.cloud.onebox.dynamics.com")
        >>> "usnconeboxax1aos.cloud.onebox.dynamics.com" in str(cache_dir)
        True

        >>> cache_dir = get_environment_cache_dir("https://test.dynamics.com", "my-app")
        >>> "test.dynamics.com" in str(cache_dir) and "my-app" in str(cache_dir)
        True
    """
    domain = extract_domain_from_url(base_url)
    base_cache_dir = get_user_cache_dir(app_name)
    return base_cache_dir / domain


def get_environment_cache_directory(base_url: str) -> str:
    """Get environment-specific cache directory as string.

    Convenience function that returns the environment-specific cache directory
    as a string, ready to be used for metadata_cache_dir.

    Args:
        base_url: F&O environment base URL

    Returns:
        String path to the environment-specific cache directory

    Examples:
        >>> cache_dir = get_environment_cache_directory("https://usnconeboxax1aos.cloud.onebox.dynamics.com")
        >>> isinstance(cache_dir, str) and "usnconeboxax1aos.cloud.onebox.dynamics.com" in cache_dir
        True
    """
    return str(get_environment_cache_dir(base_url))
