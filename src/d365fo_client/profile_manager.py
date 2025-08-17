"""Profile management for d365fo-client.

Provides centralized profile management functionality that can be used by both CLI and MCP.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import logging

from .models import FOClientConfig
from .config import CLIProfile, ConfigManager


logger = logging.getLogger(__name__)


@dataclass
class EnvironmentProfile:
    """Environment profile for MCP operations."""
    name: str
    base_url: str
    auth_mode: str = "default"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 60
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60
    language: str = "en-US"
    cache_dir: Optional[str] = None
    description: Optional[str] = None


class ProfileManager:
    """Manages environment profiles for D365FO connections."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize profile manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        # Use CLI ConfigManager as the underlying storage
        self.config_manager = ConfigManager(config_path)
        
    def list_profiles(self) -> Dict[str, EnvironmentProfile]:
        """List all available profiles.
        
        Returns:
            Dictionary of profile name to EnvironmentProfile instances
        """
        try:
            cli_profiles = self.config_manager.list_profiles()
            profiles = {}
            
            for name, cli_profile in cli_profiles.items():
                profiles[name] = self._cli_to_env_profile(cli_profile)
            
            return profiles
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return {}
    
    def get_profile(self, profile_name: str) -> Optional[EnvironmentProfile]:
        """Get a specific profile.
        
        Args:
            profile_name: Name of the profile to retrieve
            
        Returns:
            EnvironmentProfile instance or None if not found
        """
        try:
            cli_profile = self.config_manager.get_profile(profile_name)
            if cli_profile:
                return self._cli_to_env_profile(cli_profile)
            return None
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
        language: str = "en-US",
        cache_dir: Optional[str] = None,
        description: Optional[str] = None
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
            
            # Create CLI profile (without description)
            cli_profile = CLIProfile(
                name=name,
                base_url=base_url,
                auth_mode=auth_mode,
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                verify_ssl=verify_ssl,
                output_format="table",  # Default for CLI
                label_cache=use_label_cache,
                label_expiry=label_cache_expiry_minutes,
                language=language,
                cache_dir=cache_dir
            )
            
            self.config_manager.save_profile(cli_profile)
            
            # Store description separately if provided
            if description:
                self._save_profile_description(name, description)
            
            logger.info(f"Created profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating profile {name}: {e}")
            return False
    
    def update_profile(
        self,
        name: str,
        **kwargs
    ) -> bool:
        """Update an existing profile.
        
        Args:
            name: Profile name
            **kwargs: Profile attributes to update
            
        Returns:
            True if updated successfully
        """
        try:
            # Get existing profile
            cli_profile = self.config_manager.get_profile(name)
            if not cli_profile:
                logger.error(f"Profile not found: {name}")
                return False
            
            # Handle description separately
            description = kwargs.pop("description", None)
            if description is not None:
                self._save_profile_description(name, description)
            
            # Update attributes
            for key, value in kwargs.items():
                if hasattr(cli_profile, key):
                    setattr(cli_profile, key, value)
                elif key == "use_label_cache":
                    cli_profile.label_cache = value
                elif key == "label_cache_expiry_minutes":
                    cli_profile.label_expiry = value
                elif key == "timeout":
                    # CLI doesn't store timeout, but we can ignore it gracefully
                    pass
            
            self.config_manager.save_profile(cli_profile)
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
                # Also clean up description metadata
                metadata = self._load_metadata()
                if "descriptions" in metadata and profile_name in metadata["descriptions"]:
                    del metadata["descriptions"][profile_name]
                    self._save_metadata(metadata)
                
                logger.info(f"Deleted profile: {profile_name}")
            else:
                logger.error(f"Profile not found: {profile_name}")
            return success
        except Exception as e:
            logger.error(f"Error deleting profile {profile_name}: {e}")
            return False
    
    def get_default_profile(self) -> Optional[EnvironmentProfile]:
        """Get the default profile.
        
        Returns:
            Default EnvironmentProfile instance or None if not set
        """
        try:
            cli_profile = self.config_manager.get_default_profile()
            if cli_profile:
                return self._cli_to_env_profile(cli_profile)
            return None
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
    
    def profile_to_client_config(self, profile: EnvironmentProfile) -> FOClientConfig:
        """Convert an EnvironmentProfile to FOClientConfig.
        
        Args:
            profile: EnvironmentProfile instance
            
        Returns:
            FOClientConfig instance
        """
        return FOClientConfig(
            base_url=profile.base_url,
            client_id=profile.client_id,
            client_secret=profile.client_secret,
            tenant_id=profile.tenant_id,
            use_default_credentials=profile.auth_mode == "default",
            timeout=profile.timeout,
            verify_ssl=profile.verify_ssl,
            use_label_cache=profile.use_label_cache,
            label_cache_expiry_minutes=profile.label_cache_expiry_minutes,
            metadata_cache_dir=profile.cache_dir
        )
    
    def get_effective_profile(self, profile_name: Optional[str] = None) -> Optional[EnvironmentProfile]:
        """Get the effective profile to use.
        
        Args:
            profile_name: Specific profile name, or None to use default
            
        Returns:
            EnvironmentProfile instance or None if not found
        """
        if profile_name:
            return self.get_profile(profile_name)
        else:
            return self.get_default_profile()
    
    def validate_profile(self, profile: EnvironmentProfile) -> List[str]:
        """Validate a profile configuration.
        
        Args:
            profile: Profile to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not profile.name:
            errors.append("Profile name is required")
        
        if not profile.base_url:
            errors.append("Base URL is required")
        
        if not profile.base_url.startswith(("http://", "https://")):
            errors.append("Base URL must start with http:// or https://")
        
        if profile.auth_mode not in ["default", "client_credentials"]:
            errors.append("Auth mode must be 'default' or 'client_credentials'")
        
        if profile.auth_mode == "client_credentials":
            if not profile.client_id:
                errors.append("Client ID is required for client_credentials auth mode")
            if not profile.client_secret:
                errors.append("Client secret is required for client_credentials auth mode")
            if not profile.tenant_id:
                errors.append("Tenant ID is required for client_credentials auth mode")
        
        if profile.timeout <= 0:
            errors.append("Timeout must be greater than 0")
        
        if profile.label_cache_expiry_minutes <= 0:
            errors.append("Label cache expiry must be greater than 0")
        
        return errors
    
    def _cli_to_env_profile(self, cli_profile: CLIProfile) -> EnvironmentProfile:
        """Convert CLIProfile to EnvironmentProfile.
        
        Args:
            cli_profile: CLIProfile instance
            
        Returns:
            EnvironmentProfile instance
        """
        description = self._get_profile_description(cli_profile.name)
        
        return EnvironmentProfile(
            name=cli_profile.name,
            base_url=cli_profile.base_url,
            auth_mode=cli_profile.auth_mode,
            client_id=cli_profile.client_id,
            client_secret=cli_profile.client_secret,
            tenant_id=cli_profile.tenant_id,
            verify_ssl=cli_profile.verify_ssl,
            timeout=60,  # Default timeout
            use_label_cache=cli_profile.label_cache,
            label_cache_expiry_minutes=cli_profile.label_expiry,
            language=cli_profile.language,
            cache_dir=cli_profile.cache_dir,
            description=description
        )
    
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
            export_data = {
                "version": "1.0",
                "profiles": {}
            }
            
            for name, profile in profiles.items():
                export_data["profiles"][name] = asdict(profile)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Exported {len(profiles)} profiles to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting profiles to {file_path}: {e}")
            return False
    
    def import_profiles(self, file_path: str, overwrite: bool = False) -> Dict[str, bool]:
        """Import profiles from a file.
        
        Args:
            file_path: Path to import file
            overwrite: Whether to overwrite existing profiles
            
        Returns:
            Dictionary of profile name to import success status
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
                    success = self.create_profile(description=description, **profile_data)
                    results[name] = success
                    
                except Exception as e:
                    logger.error(f"Error importing profile {name}: {e}")
                    results[name] = False
            
            logger.info(f"Imported profiles from {file_path}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error importing profiles from {file_path}: {e}")
            return results
    
    def _save_profile_description(self, profile_name: str, description: str) -> None:
        """Save profile description to metadata file.
        
        Args:
            profile_name: Profile name
            description: Description text
        """
        try:
            metadata_file = self._get_metadata_file_path()
            metadata = self._load_metadata()
            
            if "descriptions" not in metadata:
                metadata["descriptions"] = {}
            
            metadata["descriptions"][profile_name] = description
            self._save_metadata(metadata)
            
        except Exception as e:
            logger.error(f"Error saving description for profile {profile_name}: {e}")
    
    def _get_profile_description(self, profile_name: str) -> Optional[str]:
        """Get profile description from metadata file.
        
        Args:
            profile_name: Profile name
            
        Returns:
            Description text or None
        """
        try:
            metadata = self._load_metadata()
            return metadata.get("descriptions", {}).get(profile_name)
        except Exception as e:
            logger.error(f"Error getting description for profile {profile_name}: {e}")
            return None
    
    def _get_metadata_file_path(self) -> str:
        """Get path to profile metadata file."""
        config_dir = Path(self.config_manager.config_path).parent
        return str(config_dir / "profile_metadata.yaml")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load profile metadata."""
        metadata_file = self._get_metadata_file_path()
        if not os.path.exists(metadata_file):
            return {}
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading metadata file {metadata_file}: {e}")
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save profile metadata."""
        try:
            metadata_file = self._get_metadata_file_path()
            os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Error saving metadata file: {e}")