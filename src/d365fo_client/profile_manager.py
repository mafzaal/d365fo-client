"""Profile management for d365fo-client.

Provides centralized profile management functionality that can be used by both CLI and MCP.
"""

import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import ConfigManager
from .models import FOClientConfig
from .profiles import Profile

logger = logging.getLogger(__name__)

# Legacy alias for backward compatibility
EnvironmentProfile = Profile


class ProfileManager:
    """Manages environment profiles for D365FO connections."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize profile manager.

        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        # Use CLI ConfigManager as the underlying storage
        self.config_manager = ConfigManager(config_path)

    def list_profiles(self) -> Dict[str, Profile]:
        """List all available profiles.

        Returns:
            Dictionary of profile name to Profile instances
        """
        try:
            return self.config_manager.list_profiles()
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return {}

    def get_profile(self, profile_name: str) -> Optional[Profile]:
        """Get a specific profile.

        Args:
            profile_name: Name of the profile to retrieve

        Returns:
            Profile instance or None if not found
        """
        try:
            return self.config_manager.get_profile(profile_name)
        except Exception as e:
            logger.error(f"Error getting profile {profile_name}: {e}")
            return None

    def create_profile(
        self,
        name: str,
        base_url: str,
        auth_mode: str = "default",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 60,
        use_label_cache: bool = True,
        label_cache_expiry_minutes: int = 60,
        use_cache_first: bool = True,
        language: str = "en-US",
        cache_dir: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Create a new profile.

        Args:
            name: Profile name
            base_url: D365FO base URL
            auth_mode: Authentication mode
            client_id: Azure client ID (optional)
            client_secret: Azure client secret (optional)
            tenant_id: Azure tenant ID (optional)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            use_label_cache: Whether to enable label caching
            label_cache_expiry_minutes: Label cache expiry in minutes
            language: Default language code
            cache_dir: Cache directory path
            description: Profile description (stored separately from CLI profile)

        Returns:
            True if created successfully
        """
        try:
            # Check if profile already exists
            if self.config_manager.get_profile(name):
                logger.error(f"Profile already exists: {name}")
                return False

            # Create unified profile
            profile = Profile(
                name=name,
                base_url=base_url,
                auth_mode=auth_mode,
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                verify_ssl=verify_ssl,
                timeout=timeout,
                use_label_cache=use_label_cache,
                label_cache_expiry_minutes=label_cache_expiry_minutes,
                use_cache_first=use_cache_first,
                language=language,
                cache_dir=cache_dir,
                description=description,
                output_format="table",  # Default for CLI compatibility
            )

            self.config_manager.save_profile(profile)

            logger.info(f"Created profile: {name}")
            return True

        except Exception as e:
            logger.error(f"Error creating profile {name}: {e}")
            return False

    def update_profile(self, name: str, **kwargs) -> bool:
        """Update an existing profile.

        Args:
            name: Profile name
            **kwargs: Profile attributes to update

        Returns:
            True if updated successfully
        """
        try:
            # Get existing profile
            profile = self.get_profile(name)
            if not profile:
                logger.error(f"Profile not found: {name}")
                return False

            # Create updated profile with new attributes
            from dataclasses import replace

            updated_profile = replace(profile, **kwargs)

            # Save updated profile
            self.config_manager.save_profile(updated_profile)

            logger.info(f"Updated profile: {name}")
            return True

        except Exception as e:
            logger.error(f"Error updating profile {name}: {e}")
            return False

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile.

        Args:
            profile_name: Name of the profile to delete

        Returns:
            True if deleted successfully
        """
        try:
            success = self.config_manager.delete_profile(profile_name)
            if success:
                logger.info(f"Deleted profile: {profile_name}")
            else:
                logger.error(f"Profile not found: {profile_name}")
            return success
        except Exception as e:
            logger.error(f"Error deleting profile {profile_name}: {e}")
            return False

    def get_default_profile(self) -> Optional[Profile]:
        """Get the default profile.

        Returns:
            Default Profile instance or None if not set
        """
        try:
            return self.config_manager.get_default_profile()
        except Exception as e:
            logger.error(f"Error getting default profile: {e}")
            return None

    def set_default_profile(self, profile_name: str) -> bool:
        """Set the default profile.

        Args:
            profile_name: Name of the profile to set as default

        Returns:
            True if set successfully
        """
        try:
            success = self.config_manager.set_default_profile(profile_name)
            if success:
                logger.info(f"Set default profile: {profile_name}")
            else:
                logger.error(f"Profile not found: {profile_name}")
            return success
        except Exception as e:
            logger.error(f"Error setting default profile {profile_name}: {e}")
            return False

    def profile_to_client_config(self, profile: Profile) -> FOClientConfig:
        """Convert a Profile to FOClientConfig.

        Args:
            profile: Profile instance

        Returns:
            FOClientConfig instance
        """
        return profile.to_client_config()

    def get_effective_profile(
        self, profile_name: Optional[str] = None
    ) -> Optional[Profile]:
        """Get the effective profile to use.

        Args:
            profile_name: Specific profile name, or None to use default

        Returns:
            Profile instance or None if not found
        """
        if profile_name:
            return self.get_profile(profile_name)
        else:
            return self.get_default_profile()

    def validate_profile(self, profile: Profile) -> List[str]:
        """Validate a profile configuration.

        Args:
            profile: Profile to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return profile.validate()

    def get_profile_names(self) -> List[str]:
        """Get list of all profile names.

        Returns:
            List of profile names
        """
        return list(self.list_profiles().keys())

    def export_profiles(self, file_path: str) -> bool:
        """Export all profiles to a file.

        Args:
            file_path: Path to export file

        Returns:
            True if exported successfully
        """
        try:
            profiles = self.list_profiles()
            export_data = {"version": "1.0", "profiles": {}}

            for name, profile in profiles.items():
                export_data["profiles"][name] = asdict(profile)

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Exported {len(profiles)} profiles to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting profiles to {file_path}: {e}")
            return False

    def import_profiles(
        self, file_path: str, overwrite: bool = False
    ) -> Dict[str, bool]:
        """Import profiles from a file.

        Args:
            file_path: Path to import file
            overwrite: Whether to overwrite existing profiles

        Returns:
            Dictionary of profile name to import success status
        """
        results = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = yaml.safe_load(f)

            if not import_data or "profiles" not in import_data:
                logger.error("Invalid import file format")
                return results

            for name, profile_data in import_data["profiles"].items():
                try:
                    # Check if profile exists
                    if self.get_profile(name) and not overwrite:
                        logger.warning(f"Profile {name} already exists, skipping")
                        results[name] = False
                        continue

                    # If overwrite is enabled, delete existing profile first
                    if overwrite and self.get_profile(name):
                        self.delete_profile(name)

                    # Extract description if present
                    description = profile_data.pop("description", None)

                    # Create profile
                    success = self.create_profile(
                        description=description, **profile_data
                    )
                    results[name] = success

                except Exception as e:
                    logger.error(f"Error importing profile {name}: {e}")
                    results[name] = False

            logger.info(f"Imported profiles from {file_path}: {results}")
            return results

        except Exception as e:
            logger.error(f"Error importing profiles from {file_path}: {e}")
            return results
