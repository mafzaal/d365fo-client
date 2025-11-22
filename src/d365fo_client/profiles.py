"""Unified profile management for d365fo-client."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .models import FOClientConfig

if TYPE_CHECKING:
    from .credential_sources import CredentialSource

logger = logging.getLogger(__name__)


@dataclass
class Profile(FOClientConfig):
    """Unified profile for CLI and MCP operations.

    Inherits from FOClientConfig and adds profile-specific functionality
    like name, description, and CLI output formatting.
    """

    # Profile-specific identification fields
    name: str = ""
    description: Optional[str] = None

    # CLI-specific settings (with defaults for MCP)
    output_format: str = "table"

    def __post_init__(self):
        """Override parent post_init to handle profile-specific validation."""
        # Call parent validation first
        super().__post_init__()

        # Additional profile-specific validation
        if not self.name:
            raise ValueError("Profile name is required")

    def to_client_config(self) -> FOClientConfig:
        """Convert profile to FOClientConfig.

        Since Profile now inherits from FOClientConfig, we can return a copy
        of self with only the FOClientConfig fields.
        """
        from dataclasses import fields

        # Get all FOClientConfig field names
        fo_client_fields = {f.name for f in fields(FOClientConfig)}

        # Create a dict with only FOClientConfig fields from this instance
        # Use getattr to preserve object types (especially credential_source)
        client_data = {}
        for field_name in fo_client_fields:
            if hasattr(self, field_name):
                client_data[field_name] = getattr(self, field_name)

        return FOClientConfig(**client_data)

    def validate(self) -> List[str]:
        """Validate profile configuration.

        Since Profile inherits from FOClientConfig, we leverage the parent's
        validation and add profile-specific checks.
        """
        errors = []

        # Profile-specific validation
        if not self.name:
            errors.append("Profile name is required")

        # Leverage parent's validation by attempting to create the config
        try:
            self._validate_config()
        except ValueError as e:
            errors.append(str(e))

        # Validate credential_source if provided
        if self.credential_source is not None:
            # Basic validation - credential source should have a valid source_type
            if (
                not hasattr(self.credential_source, "source_type")
                or not self.credential_source.source_type
            ):
                errors.append("Credential source must have a valid source_type")

        return errors

    @classmethod
    def create_from_dict(cls, name: str, data: Dict[str, Any]) -> "Profile":
        """Create Profile from dictionary data with migration support.

        This method maintains the same interface as the original from_dict but
        works with the inheritance structure.
        """

        # Handle parameter migration from legacy formats
        migrated_data = cls._migrate_legacy_parameters(data.copy())

        # Ensure name is set
        migrated_data["name"] = name

        # Add defaults for missing parameters, focusing on Profile-specific ones
        profile_defaults = {
            "name": name,
            "description": None,
            "output_format": "table",
        }

        for key, default_value in profile_defaults.items():
            if key not in migrated_data:
                migrated_data[key] = default_value

        # Use parent's from_dict for FOClientConfig fields, then add Profile fields
        try:
            # Create FOClientConfig from the data first
            fo_config = super().from_dict(migrated_data)

            # Convert back to dict and add Profile-specific fields
            fo_data = fo_config.to_dict()
            fo_data.update(
                {
                    "name": migrated_data["name"],
                    "description": migrated_data.get("description"),
                    "output_format": migrated_data.get("output_format", "table"),
                }
            )

            # Filter out any unknown parameters
            valid_params = {
                k: v for k, v in fo_data.items() if k in cls.__dataclass_fields__
            }

            # Handle credential_source deserialization if it's still a dict
            if "credential_source" in valid_params and isinstance(
                valid_params["credential_source"], dict
            ):
                from .credential_sources import CredentialSource

                try:
                    valid_params["credential_source"] = CredentialSource.from_dict(
                        valid_params["credential_source"]
                    )
                except Exception as e:
                    logger.error(f"Error deserializing credential_source: {e}")
                    valid_params["credential_source"] = None

            return cls(**valid_params)
        except Exception as e:
            logger.error(f"Error creating profile {name}: {e}")
            logger.error(f"Data: {migrated_data}")
            raise

    @classmethod
    def _migrate_legacy_parameters(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy parameter names to current format."""

        # Map old parameter names to new ones
        parameter_migrations = {
            "label_cache": "use_label_cache",
            "label_expiry": "label_cache_expiry_minutes",
            "cache_dir": "metadata_cache_dir",  # Profile's cache_dir maps to FOClientConfig's metadata_cache_dir
        }

        for old_name, new_name in parameter_migrations.items():
            if old_name in data and new_name not in data:
                data[new_name] = data.pop(old_name)
                logger.debug(f"Migrated parameter {old_name} -> {new_name}")

        # Special handling for Profile's legacy credential migration
        # If auth_mode is "client_credentials", treat it as explicit credentials
        if data.get("auth_mode") == "client_credentials":
            data["use_default_credentials"] = False
            logger.debug(
                "Setting use_default_credentials=False for client_credentials auth_mode"
            )

        # Migrate legacy credential fields to credential_source (use parent method)
        data = FOClientConfig._migrate_legacy_credentials(data)

        return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage."""
        # Use parent's to_dict method and remove profile-specific fields that shouldn't be in storage
        data = super().to_dict()

        # Add profile-specific fields
        data.update(
            {
                "description": self.description,
                "output_format": self.output_format,
            }
        )

        # Remove name from storage (it's stored as the key)
        data.pop("name", None)

        return data

    def clone(self, name: str, **overrides) -> "Profile":
        """Create a copy of this profile with a new name and optional overrides."""
        from dataclasses import replace

        # Create a copy with new name
        new_profile = replace(self, name=name)

        # Apply any overrides
        if overrides:
            new_profile = replace(new_profile, **overrides)

        return new_profile

    def __str__(self) -> str:
        """String representation of the profile."""
        cred_info = (
            "default_credentials"
            if self.credential_source is None
            else f"credential_source={self.credential_source.source_type}"
        )
        return (
            f"Profile(name='{self.name}', base_url='{self.base_url}', auth={cred_info})"
        )

    def __repr__(self) -> str:
        """Detailed string representation of the profile."""
        cred_info = (
            "default_credentials"
            if self.credential_source is None
            else f"credential_source={self.credential_source.source_type}"
        )
        return (
            f"Profile(name='{self.name}', base_url='{self.base_url}', "
            f"auth={cred_info}, description='{self.description}')"
        )
