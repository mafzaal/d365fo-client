"""Configuration management for d365fo-client CLI."""

import argparse
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .models import FOClientConfig
from .profiles import Profile

logger = logging.getLogger(__name__)


# Legacy alias for backward compatibility
CLIProfile = Profile


class ConfigManager:
    """Manages configuration profiles and settings."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".d365fo-client"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            return {"profiles": {}, "default_profile": None, "global": {}}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            # Ensure required sections exist
            if "profiles" not in config:
                config["profiles"] = {}
            if "global" not in config:
                config["global"] = {}

            return config
        except Exception as e:
            # If config file is corrupted, return empty config
            print(f"Warning: Could not load config file {self.config_path}: {e}")
            return {"profiles": {}, "default_profile": None, "global": {}}

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._config_data, f, default_flow_style=False, allow_unicode=True
                )
        except Exception as e:
            print(f"Error saving config file {self.config_path}: {e}")

    def reload_config(self) -> None:
        """Reload configuration from file.

        This is useful when the config file has been modified externally
        or by another instance of the ConfigManager.
        """
        self._config_data = self._load_config()

    def get_profile(self, profile_name: str) -> Optional[Profile]:
        """Get a specific configuration profile.

        Args:
            profile_name: Name of the profile to retrieve

        Returns:
            Profile instance or None if not found
        """
        profiles = self._config_data.get("profiles", {})
        if profile_name not in profiles:
            return None

        profile_data = profiles[profile_name]
        try:
            return Profile.create_from_dict(profile_name, profile_data)
        except Exception as e:
            logger.error(f"Error loading profile {profile_name}: {e}")
            return None

    def save_profile(self, profile: Profile) -> None:
        """Save a configuration profile.

        Args:
            profile: Profile to save
        """
        if "profiles" not in self._config_data:
            self._config_data["profiles"] = {}

        # Convert profile to dict for storage
        self._config_data["profiles"][profile.name] = profile.to_dict()
        self._save_config()

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a configuration profile.

        Args:
            profile_name: Name of the profile to delete

        Returns:
            True if deleted, False if not found
        """
        profiles = self._config_data.get("profiles", {})
        if profile_name not in profiles:
            return False

        del profiles[profile_name]

        # Clear default if it was the deleted profile
        if self._config_data.get("default_profile") == profile_name:
            self._config_data["default_profile"] = None

        self._save_config()
        return True

    def list_profiles(self) -> Dict[str, Profile]:
        """List all configuration profiles.

        Returns:
            Dictionary of profile name to Profile instances
        """
        profiles = {}
        for name, data in self._config_data.get("profiles", {}).items():
            try:
                profiles[name] = Profile.create_from_dict(name, data)
            except Exception as e:
                logger.error(f"Error loading profile {name}: {e}")
                continue
        return profiles

    def set_default_profile(self, profile_name: str) -> bool:
        """Set the default profile.

        Args:
            profile_name: Name of the profile to set as default

        Returns:
            True if set, False if profile doesn't exist
        """
        profiles = self._config_data.get("profiles", {})
        if profile_name not in profiles:
            return False

        self._config_data["default_profile"] = profile_name
        self._save_config()
        return True

    def get_default_profile(self) -> Optional[Profile]:
        """Get the default configuration profile.

        Returns:
            Default Profile instance or None if not set
        """
        default_name = self._config_data.get("default_profile")
        if not default_name:
            return None

        return self.get_profile(default_name)

    def get_effective_config(self, args: argparse.Namespace) -> FOClientConfig:
        """Build effective configuration from args, environment, and profiles.

        Precedence: Command line args > Environment variables > Profile config > Defaults

        Args:
            args: Parsed command line arguments

        Returns:
            FOClientConfig instance
        """
        # Start with defaults
        config_params = {
            "base_url": None,
            "verify_ssl": True,
            "use_label_cache": True,
            "label_cache_expiry_minutes": 60,
            "use_cache_first": True,
            "timeout": 60,
            "credential_source": None,
        }

        # Temporary variables for legacy credential handling
        legacy_credentials: Dict[str, Optional[str]] = {
            "client_id": None,
            "client_secret": None,
            "tenant_id": None,
        }

        # Apply profile settings if specified
        profile = None
        profile_name = getattr(args, "profile", None)
        if profile_name:
            profile = self.get_profile(profile_name)
        elif not profile_name:
            # Try default profile
            profile = self.get_default_profile()

        if profile:
            # Convert profile to client config and extract relevant parameters
            client_config = profile.to_client_config()
            config_params.update(
                {
                    "base_url": client_config.base_url,
                    "verify_ssl": client_config.verify_ssl,
                    "use_label_cache": client_config.use_label_cache,
                    "label_cache_expiry_minutes": client_config.label_cache_expiry_minutes,
                    "use_cache_first": client_config.use_cache_first,
                    "timeout": client_config.timeout,
                    "credential_source": client_config.credential_source,
                }
            )

        # Apply environment variables
        env_mappings = {
            "D365FO_BASE_URL": "base_url",
            "D365FO_VERIFY_SSL": "verify_ssl",
            "D365FO_LABEL_CACHE": "use_label_cache",
            "D365FO_LABEL_EXPIRY": "label_cache_expiry_minutes",
            "D365FO_USE_CACHE_FIRST": "use_cache_first",
            "D365FO_TIMEOUT": "timeout",
            "D365FO_CACHE_DIR": "metadata_cache_dir",
        }

        # Environment variables for legacy credentials
        legacy_env_mappings = {
            "D365FO_CLIENT_ID": "client_id",
            "D365FO_CLIENT_SECRET": "client_secret",
            "D365FO_TENANT_ID": "tenant_id",
        }

        for env_var, param_name in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                if param_name in ["verify_ssl", "use_label_cache", "use_cache_first"]:
                    # Convert to boolean
                    config_params[param_name] = env_value.lower() in (
                        "true",
                        "1",
                        "yes",
                        "on",
                    )
                elif param_name in ["label_cache_expiry_minutes", "timeout"]:
                    # Convert to int
                    try:
                        config_params[param_name] = int(env_value)
                    except ValueError:
                        pass  # Keep default/profile value
                else:
                    config_params[param_name] = env_value

        # Handle legacy credential environment variables
        for env_var, param_name in legacy_env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                legacy_credentials[param_name] = env_value

        # Apply command line arguments (highest precedence)
        arg_mappings = {
            "base_url": "base_url",
            "verify_ssl": "verify_ssl",
            "label_cache": "use_label_cache",
            "label_expiry": "label_cache_expiry_minutes",
            "use_cache_first": "use_cache_first",
            "timeout": "timeout",
        }

        # Legacy credential CLI args
        legacy_arg_mappings = {
            "client_id": "client_id",
            "client_secret": "client_secret",
            "tenant_id": "tenant_id",
        }

        for arg_name, param_name in arg_mappings.items():
            arg_value = getattr(args, arg_name, None)
            if arg_value is not None:
                config_params[param_name] = arg_value

        # Handle legacy credential CLI arguments
        for arg_name, param_name in legacy_arg_mappings.items():
            arg_value = getattr(args, arg_name, None)
            if arg_value is not None:
                legacy_credentials[param_name] = arg_value

        # Create credential source from legacy credentials if provided
        if (
            any(legacy_credentials.values())
            and config_params["credential_source"] is None
        ):
            # Check if we have all required credentials
            if all(legacy_credentials.values()):
                from .credential_sources import EnvironmentCredentialSource

                config_params["credential_source"] = EnvironmentCredentialSource()

        return FOClientConfig(**config_params)

    def _substitute_env_variables(self, value: Any) -> Any:
        """Substitute environment variables in configuration values.

        Supports ${VAR_NAME} syntax.

        Args:
            value: Value to process

        Returns:
            Value with environment variables substituted
        """
        if not isinstance(value, str):
            return value

        # Simple environment variable substitution
        import re

        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Return original if not found

        return re.sub(r"\$\{([^}]+)\}", replace_var, value)
