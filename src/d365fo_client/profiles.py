"""Unified profile management for d365fo-client."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .models import FOClientConfig
    from .credential_sources import CredentialSource

logger = logging.getLogger(__name__)


@dataclass
class Profile:
    """Unified profile for CLI and MCP operations."""

    # Core identification
    name: str
    description: Optional[str] = None

    # Connection settings
    base_url: str = ""
    verify_ssl: bool = True
    timeout: int = 60
    credential_source: Optional["CredentialSource"] = None

    # Cache settings
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60
    use_cache_first: bool = True
    cache_dir: Optional[str] = None

    # Localization
    language: str = "en-US"

    # CLI-specific settings (with defaults for MCP)
    output_format: str = "table"

    def to_client_config(self) -> "FOClientConfig":
        """Convert profile to FOClientConfig."""
        from .models import FOClientConfig

        # Handle credential migration: if profile has legacy credentials, create credential_source
        credential_source = self.credential_source
        if credential_source is None and self._has_legacy_credentials():
            credential_source = self._create_credential_source_from_legacy()

        return FOClientConfig(
            base_url=self.base_url,
            timeout=self.timeout,
            verify_ssl=self.verify_ssl,
            use_label_cache=self.use_label_cache,
            label_cache_expiry_minutes=self.label_cache_expiry_minutes,
            use_cache_first=self.use_cache_first,
            metadata_cache_dir=self.cache_dir,
            credential_source=credential_source,
        )

    def _has_legacy_credentials(self) -> bool:
        """Check if profile has legacy credential fields."""
        return (
            #ignore type checking here
            
            hasattr(self, 'client_id') and self.client_id or # type: ignore
            hasattr(self, 'client_secret') and self.client_secret or # type: ignore
            hasattr(self, 'tenant_id') and self.tenant_id # type: ignore
        )

    def _create_credential_source_from_legacy(self) -> Optional["CredentialSource"]:
        """Create credential source from legacy fields."""
        # Check if we should use default credentials
        use_default = getattr(self, 'use_default_credentials', None)
        auth_mode = getattr(self, 'auth_mode', 'default')

        # If explicitly set to use default credentials or auth_mode is default, return None
        if use_default is True or (use_default is None and auth_mode == 'default'):
            return None

        # If we have explicit credentials, create environment credential source
        client_id = getattr(self, 'client_id', None)
        client_secret = getattr(self, 'client_secret', None)
        tenant_id = getattr(self, 'tenant_id', None)

        if all([client_id, client_secret, tenant_id]):
            from .credential_sources import EnvironmentCredentialSource
            return EnvironmentCredentialSource()

        return None

    def validate(self) -> List[str]:
        """Validate profile configuration."""
        errors = []

        if not self.base_url:
            errors.append("Base URL is required")

        if not self.base_url.startswith(("http://", "https://")):
            errors.append("Base URL must start with http:// or https://")

        if self.timeout <= 0:
            errors.append("Timeout must be greater than 0")

        if self.label_cache_expiry_minutes <= 0:
            errors.append("Label cache expiry must be greater than 0")

        # Validate credential_source if provided
        if self.credential_source is not None:
            # Basic validation - credential source should have a valid source_type
            if not hasattr(self.credential_source, 'source_type') or not self.credential_source.source_type:
                errors.append("Credential source must have a valid source_type")

        return errors

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "Profile":
        """Create Profile from dictionary data with migration support."""

        # Handle parameter migration from legacy formats
        migrated_data = cls._migrate_legacy_parameters(data.copy())

        # Ensure name is set
        migrated_data["name"] = name

        # Add defaults for missing parameters
        defaults = {
            "description": None,
            "base_url": "",
            "verify_ssl": True,
            "timeout": 60,
            "use_label_cache": True,
            "label_cache_expiry_minutes": 60,
            "use_cache_first": True,
            "cache_dir": None,
            "language": "en-US",
            "output_format": "table",
            "credential_source": None,
        }

        for key, default_value in defaults.items():
            if key not in migrated_data:
                migrated_data[key] = default_value

        # Filter out any unknown parameters
        valid_params = {
            k: v for k, v in migrated_data.items() if k in cls.__dataclass_fields__
        }

        # Handle credential_source deserialization
        if "credential_source" in valid_params and valid_params["credential_source"] is not None:
            from .credential_sources import CredentialSource
            credential_source_data = valid_params["credential_source"]
            try:
                valid_params["credential_source"] = CredentialSource.from_dict(credential_source_data)
            except Exception as e:
                logger.error(f"Error deserializing credential_source: {e}")
                valid_params["credential_source"] = None

        try:
            return cls(**valid_params)
        except Exception as e:
            logger.error(f"Error creating profile {name}: {e}")
            logger.error(f"Data: {valid_params}")
            raise

    @classmethod
    def _migrate_legacy_parameters(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy parameter names to current format."""

        # Map old parameter names to new ones
        parameter_migrations = {
            "label_cache": "use_label_cache",
            "label_expiry": "label_cache_expiry_minutes",
        }

        for old_name, new_name in parameter_migrations.items():
            if old_name in data and new_name not in data:
                data[new_name] = data.pop(old_name)
                logger.debug(f"Migrated parameter {old_name} -> {new_name}")

        # Migrate legacy credential fields to credential_source
        data = cls._migrate_legacy_credentials(data)

        return data

    @classmethod
    def _migrate_legacy_credentials(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy credential fields to credential_source."""
        # Check for legacy credential fields
        legacy_fields = ["client_id", "client_secret", "tenant_id", "auth_mode", "use_default_credentials"]
        has_legacy_creds = any(field in data for field in legacy_fields)

        if has_legacy_creds and "credential_source" not in data:
            # Determine if we should use default credentials
            use_default = data.get("use_default_credentials", None)
            auth_mode = data.get("auth_mode", "default")

            # Check if explicit credentials are provided
            client_id = data.get("client_id")
            client_secret = data.get("client_secret")
            tenant_id = data.get("tenant_id")

            has_explicit_creds = all([client_id, client_secret, tenant_id])

            # Only create credential source if explicitly not using default credentials AND has explicit creds
            if use_default is False and has_explicit_creds:
                from .credential_sources import EnvironmentCredentialSource
                data["credential_source"] = EnvironmentCredentialSource().to_dict()
                logger.debug("Migrated legacy credentials to environment credential source")
            elif auth_mode == "client_credentials" and has_explicit_creds:
                from .credential_sources import EnvironmentCredentialSource
                data["credential_source"] = EnvironmentCredentialSource().to_dict()
                logger.debug("Migrated client_credentials auth mode to environment credential source")
            # Otherwise, credential_source remains None (use default credentials)

        # Remove legacy fields after migration
        for field in legacy_fields:
            if field in data:
                logger.debug(f"Removing legacy credential field: {field}")
                data.pop(field)

        return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage."""
        from dataclasses import asdict

        # Convert to dict and remove name (stored as key)
        data = asdict(self)
        data.pop("name", None)

        # Handle credential_source serialization
        if self.credential_source is not None:
            data["credential_source"] = self.credential_source.to_dict()

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
        cred_info = "default_credentials" if self.credential_source is None else f"credential_source={self.credential_source.source_type}"
        return f"Profile(name='{self.name}', base_url='{self.base_url}', auth={cred_info})"

    def __repr__(self) -> str:
        """Detailed string representation of the profile."""
        cred_info = "default_credentials" if self.credential_source is None else f"credential_source={self.credential_source.source_type}"
        return (
            f"Profile(name='{self.name}', base_url='{self.base_url}', "
            f"auth={cred_info}, description='{self.description}')"
        )
