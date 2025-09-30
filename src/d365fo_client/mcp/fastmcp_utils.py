"""Utility functions for FastMCP server configuration and setup."""
import argparse
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from d365fo_client import __version__
from d365fo_client.credential_sources import EnvironmentCredentialSource
from d365fo_client.profile_manager import ProfileManager
from d365fo_client.settings import get_settings
from d365fo_client.utils import get_default_cache_directory

logger = logging.getLogger(__name__)

def load_default_config(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """Load configuration for FastMCP server from arguments and environment.

    Args:
        args: Optional parsed command line arguments. If not provided, 
              defaults will be used for all argument-based configuration.

    Returns:
        Configuration dictionary
    """
    # Get settings instance
    settings = get_settings()
    
    # Extract values from args with settings fallbacks
    if args is not None:
        transport = args.transport
        host = args.host if hasattr(args, 'host') else settings.http_host
        port = args.port if hasattr(args, 'port') else settings.http_port
        stateless = getattr(args, 'stateless', False) or settings.http_stateless
        json_response = getattr(args, 'json_response', False) or settings.http_json
        debug = getattr(args, 'debug', False) or settings.debug
    else:
        transport = settings.mcp_transport.value
        host = settings.http_host
        port = settings.http_port
        stateless = settings.http_stateless
        json_response = settings.http_json
        debug = settings.debug

    # Get startup mode from settings
    startup_mode = settings.get_startup_mode()

    # Build default environment from settings
    default_environment = {
        "use_default_credentials": True,
        "use_cache_first": settings.use_cache_first,
        "timeout": settings.timeout,
        "verify_ssl": settings.verify_ssl,
        "use_label_cache": settings.use_label_cache,
        "label_cache_expiry_minutes": settings.label_cache_expiry_minutes,
        "metadata_cache_dir": settings.cache_dir,
        "base_url": settings.base_url,
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "tenant_id": settings.tenant_id,
    }



    return {
        "startup_mode": startup_mode,
        "server": {
            "name": "d365fo-fastmcp-server",
            "version": __version__,
            "debug": debug or os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
            "transport": {
                "default": transport,
                "stdio": {
                    "enabled": True
                },
                "sse": {
                    "enabled": True,
                    "host": host,
                    "port": port,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST"],
                        "headers": ["*"]
                    }
                },
                "http": {
                    "enabled": True,
                    "host": host,
                    "port": port,
                    "stateless": stateless,
                    "json_response": json_response,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST", "DELETE"],
                        "headers": ["*"]
                    }
                },
            }
        },
        "default_environment": default_environment,
        "performance": {
            "max_concurrent_requests": settings.max_concurrent_requests,
            "connection_pool_size": int(os.getenv("MCP_CONNECTION_POOL_SIZE", "5")),
            "request_timeout": settings.request_timeout,
            "batch_size": int(os.getenv("MCP_BATCH_SIZE", "100")),
            "enable_performance_monitoring": os.getenv(
                "MCP_PERFORMANCE_MONITORING", "true"
            ).lower()
            in ("true", "1", "yes"),
            "session_cleanup_interval": int(
                os.getenv("MCP_SESSION_CLEANUP_INTERVAL", "300")
            ),
            "max_request_history": int(
                os.getenv("MCP_MAX_REQUEST_HISTORY", "1000")
            ),
        },
        "security": {
            "encrypt_cached_tokens": True,
            "token_expiry_buffer_minutes": 5,
            "max_retry_attempts": 3,
        },
    }

def create_default_profile_if_needed(profile_manager:"ProfileManager", config:Dict) -> Optional[bool]:
    """Create a default profile from environment variables if needed."""
    try:
        # Check if default profile already exists
        existing_default = profile_manager.get_default_profile()
        if existing_default:
            logger.info(f"Default profile already exists: {existing_default.name}")
            return False

        # Get default environment configuration
        default_environment = config.get("default_environment", {})
        
        # Get settings for direct access
        settings = get_settings()
        
        # Get base URL from environment or config
        base_url = default_environment.get("base_url") or settings.base_url

        if not base_url:
            logger.warning("Cannot create default profile - D365FO_BASE_URL not set")
            return False

        # Determine authentication mode based on startup mode
        startup_mode = config.get("startup_mode", "profile_only")
        
        # Check for legacy credentials in environment
        client_id = default_environment.get("client_id") or settings.client_id
        client_secret = default_environment.get("client_secret") or settings.client_secret
        tenant_id = default_environment.get("tenant_id") or settings.tenant_id
        
        if startup_mode == "client_credentials":
            auth_mode = "client_credentials"
            if not all([client_id, client_secret, tenant_id]):
                logger.error("Client credentials mode requires D365FO_CLIENT_ID, D365FO_CLIENT_SECRET, and D365FO_TENANT_ID")
                return
        else:
            auth_mode = "default"
            # Clear client credentials for default auth mode
            client_id = None
            client_secret = None
            tenant_id = None

        # Create default profile with unique name
        profile_name = "default-from-env"
        
        # Check if profile with this name already exists
        existing_profile = profile_manager.get_profile(profile_name)
        if existing_profile:
            logger.info(f"Profile '{profile_name}' already exists, setting as default")
            profile_manager.set_default_profile(profile_name)
            return

        credential_source = None
        if startup_mode == "client_credentials":
            credential_source = EnvironmentCredentialSource()

        # Use configuration values with proper defaults
        use_label_cache = default_environment.get("use_label_cache", True)
        timeout = default_environment.get("timeout", 60)
        verify_ssl = default_environment.get("verify_ssl", True)

        success = profile_manager.create_profile(
            name=profile_name,
            base_url=base_url,
            auth_mode=auth_mode,
            client_id=None,  # use from env var
            client_secret=None,  # use from env var
            tenant_id=None,  # use from env var
            description=f"Auto-created from environment variables at startup (mode: {startup_mode})",
            use_label_cache=use_label_cache,
            timeout=timeout,
            verify_ssl=verify_ssl,
            credential_source=credential_source
        )

        if success:
            # Set as default profile
            profile_manager.set_default_profile(profile_name)
            logger.info(f"Created and set default profile: {profile_name}")
            logger.info(f"Profile configured for: {base_url}")
            logger.info(f"Authentication mode: {auth_mode}")
            logger.info(f"Use label cache: {use_label_cache}")
            logger.info(f"Timeout: {timeout}s")
            logger.info(f"Verify SSL: {verify_ssl}")
            
            if auth_mode == "client_credentials":
                logger.info(f"Client ID: {client_id}")
                logger.info(f"Tenant ID: {tenant_id}")
                
        else:
            logger.warning(f"Failed to create default profile: {profile_name}")
        
        return success

    except Exception as e:
        logger.error(f"Error creating default profile: {e}")


def migrate_legacy_config(profile_manager: "ProfileManager") -> bool:
    """Migrate legacy configuration file to new format if needed.
    
    This function detects legacy config files and migrates them to the new format
    that supports modern credential_source structures and proper field names.
    
    Args:
        profile_manager: ProfileManager instance to use for migration
        
    Returns:
        True if migration was performed, False if no migration needed
    """
    try:
        config_path = Path(profile_manager.config_manager.config_path)
        
        if not config_path.exists():
            logger.debug("No config file found - no migration needed")
            return False
            
        # Load raw config data to check for legacy format
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
            
        if not config_data.get('profiles'):
            logger.debug("No profiles found in config - no migration needed")
            return False
            
        # Check if migration is needed by examining profile structures
        needs_migration = _is_legacy_config_format(config_data)
        
        if not needs_migration:
            logger.debug("Config is already in new format - no migration needed")
            return False
            
        logger.info("Legacy config format detected - starting migration...")
        
        # Create backup of original config
        backup_path = config_path.with_suffix('.yaml.backup')
        config_path.rename(backup_path)
        logger.info(f"Created backup of original config: {backup_path}")
        
        # Migrate each profile
        migration_results = {}
        migrated_profiles = {}
        
        for profile_name, profile_data in config_data.get('profiles', {}).items():
            try:
                # Apply legacy field migrations
                migrated_data = _migrate_legacy_profile_data(profile_data.copy())
                
                # Create profile using the migration-aware method
                from d365fo_client.profiles import Profile
                profile = Profile.create_from_dict(profile_name, migrated_data)
                
                # Store migrated profile
                migrated_profiles[profile_name] = profile
                migration_results[profile_name] = True
                logger.info(f"Successfully migrated profile: {profile_name}")
                
            except Exception as e:
                logger.error(f"Failed to migrate profile {profile_name}: {e}")
                migration_results[profile_name] = False
                
        # Save all migrated profiles
        successful_migrations = 0
        for profile_name, profile in migrated_profiles.items():
            try:
                profile_manager.config_manager.save_profile(profile)
                successful_migrations += 1
            except Exception as e:
                logger.error(f"Failed to save migrated profile {profile_name}: {e}")
                
        # Migrate global settings (default_profile)
        if 'default_profile' in config_data:
            try:
                default_profile_name = config_data['default_profile']
                if default_profile_name in migrated_profiles:
                    profile_manager.set_default_profile(default_profile_name)
                    logger.info(f"Migrated default profile setting: {default_profile_name}")
            except Exception as e:
                logger.error(f"Failed to migrate default profile setting: {e}")
                
        # Log migration summary
        total_profiles = len(config_data.get('profiles', {}))
        logger.info(f"Migration completed: {successful_migrations}/{total_profiles} profiles migrated successfully")
        
        if successful_migrations > 0:
            logger.info(f"Original config backed up to: {backup_path}")
            logger.info("You can remove the backup file once you've verified the migration worked correctly")
            return True
        else:
            # Restore backup if no profiles were migrated successfully
            logger.error("Migration failed - restoring original config")
            backup_path.rename(config_path)
            return False
            
    except Exception as e:
        logger.error(f"Error during config migration: {e}")
        return False


def _is_legacy_config_format(config_data: Dict[str, Any]) -> bool:
    """Check if config data is in legacy format that needs migration.
    
    Args:
        config_data: Raw config data loaded from YAML
        
    Returns:
        True if migration is needed, False otherwise
    """
    profiles = config_data.get('profiles', {})
    
    if not profiles:
        return False
        
    # Check for legacy format indicators
    for profile_name, profile_data in profiles.items():
        # Legacy format indicators:
        # 1. Missing verify_ssl field (was added later)
        # 2. Has auth_mode field but missing use_default_credentials field
        # 3. credential_source field structure differences
        # 4. cache_dir instead of metadata_cache_dir
        
        # Check for missing verify_ssl (common in legacy configs)
        if 'verify_ssl' not in profile_data:
            logger.debug(f"Legacy format detected: profile {profile_name} missing verify_ssl")
            return True
            
        # Check for auth_mode without use_default_credentials (legacy pattern)
        if 'auth_mode' in profile_data and 'use_default_credentials' not in profile_data:
            logger.debug(f"Legacy format detected: profile {profile_name} has auth_mode but missing use_default_credentials")
            return True
            
        # Check for cache_dir instead of metadata_cache_dir
        if 'cache_dir' in profile_data and 'metadata_cache_dir' not in profile_data:
            logger.debug(f"Legacy format detected: profile {profile_name} uses cache_dir instead of metadata_cache_dir")
            return True
            
        # Check credential_source format - legacy might have different structure or be missing
        credential_source = profile_data.get('credential_source')
        if credential_source is not None and isinstance(credential_source, dict):
            # Legacy credential_source might be missing required fields
            required_fields = ['source_type']
            if not all(field in credential_source for field in required_fields):
                logger.debug(f"Legacy format detected: profile {profile_name} has incomplete credential_source")
                return True
                
    return False


def _migrate_legacy_profile_data(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy profile data to new format.
    
    Args:
        profile_data: Legacy profile data
        
    Returns:
        Migrated profile data
    """
    migrated_data = profile_data.copy()
    
    # Add missing verify_ssl field with default value
    if 'verify_ssl' not in migrated_data:
        migrated_data['verify_ssl'] = True
        logger.debug("Added missing verify_ssl field with default value True")
        
    # Migrate cache_dir to metadata_cache_dir
    if 'cache_dir' in migrated_data and 'metadata_cache_dir' not in migrated_data:
        migrated_data['metadata_cache_dir'] = migrated_data.pop('cache_dir')
        logger.debug("Migrated cache_dir to metadata_cache_dir")
        
    # Handle auth_mode migration to use_default_credentials
    auth_mode = migrated_data.get('auth_mode')
    if auth_mode and 'use_default_credentials' not in migrated_data:
        if auth_mode == 'default':
            migrated_data['use_default_credentials'] = True
            logger.debug("Migrated auth_mode='default' to use_default_credentials=True")
        elif auth_mode == 'client_credentials':
            migrated_data['use_default_credentials'] = False  
            logger.debug("Migrated auth_mode='client_credentials' to use_default_credentials=False")
        else:
            # Unknown auth_mode, default to True for safety
            migrated_data['use_default_credentials'] = True
            logger.warning(f"Unknown auth_mode '{auth_mode}', defaulting to use_default_credentials=True")
            
    # Clean up auth_mode field as it's no longer needed
    migrated_data.pop('auth_mode', None)
    
    # Ensure credential_source is properly structured if present
    credential_source = migrated_data.get('credential_source')
    if credential_source is not None and isinstance(credential_source, dict):
        # Ensure source_type is present (environment is the most common)
        if 'source_type' not in credential_source:
            # Try to infer source_type from the structure
            if any(key.endswith('_var') for key in credential_source.keys()):
                credential_source['source_type'] = 'environment'
                logger.debug("Inferred credential_source.source_type as 'environment'")
            else:
                # Remove invalid credential_source
                migrated_data['credential_source'] = None
                logger.warning("Removed invalid credential_source structure")
                
    # Remove fields that are no longer needed or handled differently
    obsolete_fields = ['auth_mode']  # Already handled above
    for field in obsolete_fields:
        migrated_data.pop(field, None)
        
    return migrated_data