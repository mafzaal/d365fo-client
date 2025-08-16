"""Utility functions for D365 F&O client."""

import os
import platform
from pathlib import Path
from typing import Union


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