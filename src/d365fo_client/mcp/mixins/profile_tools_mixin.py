"""Profile tools mixin for FastMCP server."""

import json
import logging
from typing import Any, Dict, Optional

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class ProfileToolsMixin(BaseToolsMixin):
    """Profile management tools for FastMCP server.

    Provides 14 comprehensive profile management tools for AI assistants to manage
    D365 F&O environment connections. Supports unified credential management through
    credential sources, full configuration control, profile cloning, import/export, and intelligent search.

    AUTHENTICATION MODES:
    - Default Credentials: When credentialSource is null/omitted, uses Azure Default Credentials
    - Credential Source: When credentialSource is provided, uses specific credential source

    CREDENTIAL SOURCE EXAMPLES for AI assistants:

    1. Environment Variables (default variable names):
       {
         "sourceType": "environment"
       }

    2. Environment Variables (custom variable names):
       {
         "sourceType": "environment",
         "clientIdVar": "MY_CLIENT_ID",
         "clientSecretVar": "MY_CLIENT_SECRET",
         "tenantIdVar": "MY_TENANT_ID"
       }

    3. Azure Key Vault with Default Auth:
       {
         "sourceType": "keyvault",
         "vaultUrl": "https://myvault.vault.azure.net/",
         "clientIdSecretName": "D365FO_CLIENT_ID",
         "clientSecretSecretName": "D365FO_CLIENT_SECRET",
         "tenantIdSecretName": "D365FO_TENANT_ID"
       }

    4. Azure Key Vault with Custom Secret Names:
       {
         "sourceType": "keyvault",
         "vaultUrl": "https://myvault.vault.azure.net/",
         "clientIdSecretName": "d365-client-id",
         "clientSecretSecretName": "d365-client-secret",
         "tenantIdSecretName": "d365-tenant-id",
         "keyvaultAuthMode": "default"
       }

    AI assistants can use these patterns to help users set up secure credential management.
    Legacy credential fields (auth_mode, client_id, client_secret, tenant_id) are automatically
    migrated to appropriate credential sources for backward compatibility.
    """
    
    def register_profile_tools(self) -> None:
        """Register all profile tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_list_profiles() -> str:
            """Get list of all available D365FO environment profiles.

            Returns:
                JSON string with list of profiles
            """
            try:
                profiles = self.profile_manager.list_profiles()

                profile_list = []
                for name, profile in profiles.items():
                    profile_dict = profile.to_dict() if hasattr(profile, 'to_dict') else {"name": name, "baseUrl": getattr(profile, 'base_url', '')}
                    profile_list.append(profile_dict)

                return json.dumps(
                    {
                        "totalProfiles": len(profiles),
                        "profiles": profile_list,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"List profiles failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.tool()
        async def d365fo_get_profile(profileName: str) -> str:
            """Get details of a specific D365FO environment profile.

            Args:
                profileName: Name of the profile to retrieve

            Returns:
                JSON string with profile details
            """
            try:
                profile = self.profile_manager.get_profile(profileName)

                if profile:
                    return json.dumps(
                        {"profileName": profileName, "profile": profile.to_dict()},
                        indent=2,
                    )
                else:
                    return json.dumps(
                        {
                            "error": f"Profile '{profileName}' not found",
                            "profileName": profileName,
                        },
                        indent=2,
                    )

            except Exception as e:
                logger.error(f"Get profile failed: {e}")
                return json.dumps(
                    {"error": str(e), "profileName": profileName}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_create_profile(
            name: str,
            baseUrl: str,
            description: Optional[str] = None,
            verifySsl: bool = True,
            timeout: int = 60,
            useLabelCache: bool = True,
            labelCacheExpiryMinutes: int = 60,
            useCacheFirst: bool = True,
            language: str = "en-US",
            cacheDir: Optional[str] = None,
            outputFormat: str = "table",
            setAsDefault: bool = False,
            credentialSource: Optional[Dict[str, Any]] = None,
        ) -> str:
            """Create a new D365FO environment profile with full configuration options.

            Args:
                name: Profile name
                baseUrl: D365FO base URL
                description: Profile description
                verifySsl: Whether to verify SSL certificates (default: True)
                timeout: Request timeout in seconds (default: 60)
                useLabelCache: Whether to enable label caching (default: True)
                labelCacheExpiryMinutes: Label cache expiry in minutes (default: 60)
                useCacheFirst: Whether to use cache-first behavior (default: True)
                language: Default language code (default: "en-US")
                cacheDir: Custom cache directory path (optional)
                outputFormat: Default output format for CLI operations (default: "table")
                setAsDefault: Set as default profile (default: False)
                credentialSource: Credential source configuration. If None, uses Azure Default Credentials. Can be:
                    - Environment variables: {"sourceType": "environment", "clientIdVar": "MY_CLIENT_ID", "clientSecretVar": "MY_CLIENT_SECRET", "tenantIdVar": "MY_TENANT_ID"}
                    - Azure Key Vault: {"sourceType": "keyvault", "vaultUrl": "https://vault.vault.azure.net/", "clientIdSecretName": "D365FO_CLIENT_ID", "clientSecretSecretName": "D365FO_CLIENT_SECRET", "tenantIdSecretName": "D365FO_TENANT_ID"}

            Returns:
                JSON string with creation result
            """
            try:
                # Handle credential source conversion
                credential_source_obj = None
                if credentialSource:
                    credential_source_obj = self._convert_credential_source(credentialSource)

                success = self.profile_manager.create_profile(
                    name=name,
                    base_url=baseUrl,
                    description=description,
                    verify_ssl=verifySsl,
                    timeout=timeout,
                    use_label_cache=useLabelCache,
                    label_cache_expiry_minutes=labelCacheExpiryMinutes,
                    use_cache_first=useCacheFirst,
                    language=language,
                    cache_dir=cacheDir,
                    credential_source=credential_source_obj,
                )

                # Set as default if requested
                if success and setAsDefault:
                    self.profile_manager.set_default_profile(name)

                # Get the created profile for detailed response
                created_profile = None
                if success:
                    created_profile = self.profile_manager.get_profile(name)

                return json.dumps(
                    {
                        "profileName": name,
                        "created": success,
                        "setAsDefault": setAsDefault and success,
                        "profile": created_profile.to_dict() if created_profile else None,
                        "authType": "default_credentials" if not credentialSource else credentialSource.get("sourceType", "unknown"),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Create profile failed: {e}")
                return json.dumps(
                    {"error": str(e), "profileName": name, "created": False}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_update_profile(
            name: str,
            baseUrl: Optional[str] = None,
            description: Optional[str] = None,
            verifySsl: Optional[bool] = None,
            timeout: Optional[int] = None,
            useLabelCache: Optional[bool] = None,
            labelCacheExpiryMinutes: Optional[int] = None,
            useCacheFirst: Optional[bool] = None,
            language: Optional[str] = None,
            cacheDir: Optional[str] = None,
            outputFormat: Optional[str] = None,
            credentialSource: Optional[Dict[str, Any]] = None,
        ) -> str:
            """Update an existing D365FO environment profile with full configuration options.

            Automatically invalidates all cached client connections to ensure they pick up
            the new profile settings on next use.

            Args:
                name: Profile name
                baseUrl: D365FO base URL
                description: Profile description
                verifySsl: Whether to verify SSL certificates
                timeout: Request timeout in seconds
                useLabelCache: Whether to enable label caching
                labelCacheExpiryMinutes: Label cache expiry in minutes
                useCacheFirst: Whether to use cache-first behavior
                language: Default language code
                cacheDir: Custom cache directory path
                outputFormat: Default output format for CLI operations
                credentialSource: Credential source configuration. Set to null to use Azure Default Credentials. Can be:
                    - Environment variables: {"sourceType": "environment", "clientIdVar": "MY_CLIENT_ID", "clientSecretVar": "MY_CLIENT_SECRET", "tenantIdVar": "MY_TENANT_ID"}
                    - Azure Key Vault: {"sourceType": "keyvault", "vaultUrl": "https://vault.vault.azure.net/", "clientIdSecretName": "D365FO_CLIENT_ID", "clientSecretSecretName": "D365FO_CLIENT_SECRET", "tenantIdSecretName": "D365FO_TENANT_ID"}

            Returns:
                JSON string with update result including number of clients invalidated
            """
            try:
                # Convert parameter names and handle credential source
                update_params = {}
                if baseUrl is not None:
                    update_params['base_url'] = baseUrl
                if description is not None:
                    update_params['description'] = description
                if verifySsl is not None:
                    update_params['verify_ssl'] = verifySsl
                if timeout is not None:
                    update_params['timeout'] = timeout
                if useLabelCache is not None:
                    update_params['use_label_cache'] = useLabelCache
                if labelCacheExpiryMinutes is not None:
                    update_params['label_cache_expiry_minutes'] = labelCacheExpiryMinutes
                if useCacheFirst is not None:
                    update_params['use_cache_first'] = useCacheFirst
                if language is not None:
                    update_params['language'] = language
                if cacheDir is not None:
                    update_params['cache_dir'] = cacheDir
                if outputFormat is not None:
                    update_params['output_format'] = outputFormat
                if credentialSource is not None:
                    update_params['credential_source'] = self._convert_credential_source(credentialSource)

                success = self.profile_manager.update_profile(name, **update_params)

                # Refresh all clients to ensure they pick up the new profile settings
                clients_refreshed = success
                if success:
                    try:
                        await self.client_manager.refresh_all_profiles()
                        logger.info(f"Refreshed all clients due to profile update: {name}")
                    except Exception as client_error:
                        logger.warning(f"Failed to refresh clients after profile update: {client_error}")
                        clients_refreshed = False
                        # Continue with success response, client refresh failure is not critical

                # Get the updated profile for detailed response
                updated_profile = None
                if success:
                    updated_profile = self.profile_manager.get_profile(name)

                return json.dumps(
                    {
                        "profileName": name,
                        "updated": success,
                        "updatedFields": list(update_params.keys()) if success else [],
                        "profile": updated_profile.to_dict() if updated_profile else None,
                        "clientsRefreshed": clients_refreshed,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Update profile failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "profileName": name,
                        "updated": False,
                        "attemptedFields": [],
                        "clientsRefreshed": False,
                    },
                    indent=2
                )

        @self.mcp.tool()
        async def d365fo_delete_profile(profileName: str) -> str:
            """Delete a D365FO environment profile.

            Automatically invalidates all cached client connections since the profile
            is no longer available.

            Args:
                profileName: Name of the profile to delete

            Returns:
                JSON string with deletion result including number of clients invalidated
            """
            try:
                success = self.profile_manager.delete_profile(profileName)

                # Refresh all clients since the profile is no longer available
                clients_refreshed = success
                if success:
                    try:
                        await self.client_manager.refresh_all_profiles()
                        logger.info(f"Refreshed all clients due to profile deletion: {profileName}")
                    except Exception as client_error:
                        logger.warning(f"Failed to refresh clients after profile deletion: {client_error}")
                        clients_refreshed = False
                        # Continue with success response, client refresh failure is not critical

                return json.dumps(
                    {
                        "profileName": profileName,
                        "deleted": success,
                        "clientsRefreshed": clients_refreshed,
                    },
                    indent=2
                )

            except Exception as e:
                logger.error(f"Delete profile failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "profileName": profileName,
                        "deleted": False,
                        "clientsRefreshed": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_set_default_profile(profileName: str) -> str:
            """Set the default D365FO environment profile.

            Automatically refreshes all cached client connections since changing the default
            profile may affect client resolution for operations that use the default profile.

            Args:
                profileName: Name of the profile to set as default

            Returns:
                JSON string with result including client refresh status
            """
            try:
                success = self.profile_manager.set_default_profile(profileName)

                # Refresh all clients since the default profile change may affect connections
                clients_refreshed = success
                if success:
                    try:
                        await self.client_manager.refresh_all_profiles()
                        logger.info(f"Refreshed all clients due to default profile change: {profileName}")
                    except Exception as client_error:
                        logger.warning(f"Failed to refresh clients after default profile change: {client_error}")
                        clients_refreshed = False
                        # Continue with success response, client refresh failure is not critical

                return json.dumps(
                    {
                        "profileName": profileName,
                        "setAsDefault": success,
                        "clientsRefreshed": clients_refreshed,
                    },
                    indent=2
                )

            except Exception as e:
                logger.error(f"Set default profile failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "profileName": profileName,
                        "setAsDefault": False,
                        "clientsRefreshed": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_get_default_profile() -> str:
            """Get the current default D365FO environment profile.

            Returns:
                JSON string with default profile
            """
            try:
                profile = self.profile_manager.get_default_profile()

                if profile:
                    return json.dumps({"defaultProfile": profile.to_dict()}, indent=2)
                else:
                    return json.dumps({"error": "No default profile set"}, indent=2)

            except Exception as e:
                logger.error(f"Get default profile failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.tool()
        async def d365fo_validate_profile(profileName: str) -> str:
            """Validate a D365FO environment profile configuration.

            Args:
                profileName: Name of the profile to validate

            Returns:
                JSON string with validation result
            """
            try:
                profile = self.profile_manager.get_profile(profileName)
                if not profile:
                    return json.dumps(
                        {"error": f"Profile '{profileName}' not found", "profileName": profileName, "isValid": False},
                        indent=2,
                    )

                errors = self.profile_manager.validate_profile(profile)
                is_valid = len(errors) == 0

                return json.dumps(
                    {"profileName": profileName, "isValid": is_valid, "errors": errors},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Validate profile failed: {e}")
                return json.dumps(
                    {"error": str(e), "profileName": profileName, "isValid": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_test_profile_connection(profileName: str) -> str:
            """Test connection for a specific D365FO environment profile.

            Args:
                profileName: Name of the profile to test

            Returns:
                JSON string with connection test result
            """
            try:
                client = await self.client_manager.get_client(profileName)
                result = await client.test_connection()

                return json.dumps(
                    {"profileName": profileName, "connectionTest": result}, indent=2
                )

            except Exception as e:
                logger.error(f"Test profile connection failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "profileName": profileName,
                        "connectionSuccessful": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_clone_profile(
            sourceProfileName: str,
            newProfileName: str,
            description: Optional[str] = None,
        ) -> str:
            """Clone an existing D365FO environment profile with optional modifications.

            Args:
                sourceProfileName: Name of the profile to clone
                newProfileName: Name for the new profile
                description: Description for the new profile

            Returns:
                JSON string with cloning result
            """
            try:
                source_profile = self.profile_manager.get_profile(sourceProfileName)
                if not source_profile:
                    return json.dumps(
                        {"error": f"Source profile '{sourceProfileName}' not found", "profileName": sourceProfileName},
                        indent=2,
                    )

                # Prepare overrides
                clone_overrides = {}
                if description is not None:
                    clone_overrides['description'] = description

                # Clone the profile
                new_profile = source_profile.clone(newProfileName, **clone_overrides)

                # Save the cloned profile
                try:
                    self.profile_manager.config_manager.save_profile(new_profile)
                    self.profile_manager.config_manager._save_config()
                    success = True
                except Exception:
                    success = False

                return json.dumps(
                    {
                        "profileName": newProfileName,
                        "sourceProfile": sourceProfileName,
                        "cloned": success,
                        "description": new_profile.description,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Clone profile failed: {e}")
                return json.dumps(
                    {"error": str(e), "sourceProfile": sourceProfileName, "newProfile": newProfileName, "cloned": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_export_profiles(filePath: str) -> str:
            """Export all D365FO environment profiles to a file.

            Args:
                filePath: Path where to export the profiles

            Returns:
                JSON string with export result
            """
            try:
                success = self.profile_manager.export_profiles(filePath)
                profiles = self.profile_manager.list_profiles()

                return json.dumps(
                    {
                        "filePath": filePath,
                        "exported": success,
                        "profileCount": len(profiles),
                        "message": f"Exported {len(profiles)} profiles to {filePath}" if success else "Export failed",
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Export profiles failed: {e}")
                return json.dumps(
                    {"error": str(e), "filePath": filePath, "exported": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_import_profiles(
            filePath: str,
            overwrite: bool = False
        ) -> str:
            """Import D365FO environment profiles from a file.

            Args:
                filePath: Path to the file containing profiles to import
                overwrite: Whether to overwrite existing profiles with the same name

            Returns:
                JSON string with import results
            """
            try:
                results = self.profile_manager.import_profiles(filePath, overwrite)

                successful_imports = [name for name, success in results.items() if success]
                failed_imports = [name for name, success in results.items() if not success]

                return json.dumps(
                    {
                        "filePath": filePath,
                        "overwrite": overwrite,
                        "totalProfiles": len(results),
                        "successfulImports": len(successful_imports),
                        "failedImports": len(failed_imports),
                        "results": results,
                        "successful": successful_imports,
                        "failed": failed_imports,
                        "message": f"Imported {len(successful_imports)} profiles successfully, {len(failed_imports)} failed",
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Import profiles failed: {e}")
                return json.dumps(
                    {"error": str(e), "filePath": filePath, "imported": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_search_profiles(
            pattern: Optional[str] = None,
            hasCredentialSource: Optional[bool] = None,
            credentialSourceType: Optional[str] = None
        ) -> str:
            """Search D365FO environment profiles based on criteria.

            Args:
                pattern: Pattern to match in profile name, description, or base URL
                hasCredentialSource: Filter by presence of credential source (True=has credential source, False=uses default credentials)
                credentialSourceType: Filter by credential source type ("environment", "keyvault")

            Returns:
                JSON string with matching profiles
            """
            try:
                all_profiles = self.profile_manager.list_profiles()
                matching_profiles = []

                for name, profile in all_profiles.items():
                    # Check pattern match
                    if pattern:
                        pattern_lower = pattern.lower()
                        if not any([
                            pattern_lower in name.lower(),
                            pattern_lower in (profile.description or "").lower(),
                            pattern_lower in profile.base_url.lower()
                        ]):
                            continue

                    # Skip auth mode check as it's no longer a field in Profile
                    # Authentication is now handled through credential_source

                    # Check credential source
                    if hasCredentialSource is not None:
                        has_cred_source = profile.credential_source is not None
                        if hasCredentialSource != has_cred_source:
                            continue

                    # Check credential source type
                    if credentialSourceType is not None:
                        if profile.credential_source is None:
                            continue  # Profile uses default credentials, no source type to match
                        if profile.credential_source.source_type != credentialSourceType:
                            continue

                    # Profile matches all criteria
                    profile_info = {
                        "name": profile.name,
                        "baseUrl": profile.base_url,
                        "description": profile.description,
                        "hasCredentialSource": profile.credential_source is not None,
                        "authType": "credential_source" if profile.credential_source is not None else "default_credentials",
                    }
                    if profile.credential_source:
                        profile_info["credentialSourceType"] = profile.credential_source.source_type

                    matching_profiles.append(profile_info)

                return json.dumps(
                    {
                        "searchCriteria": {
                            "pattern": pattern,
                            "hasCredentialSource": hasCredentialSource,
                            "credentialSourceType": credentialSourceType,
                        },
                        "totalMatches": len(matching_profiles),
                        "profiles": matching_profiles,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Search profiles failed: {e}")
                return json.dumps(
                    {"error": str(e), "searchCriteria": {"pattern": pattern, "hasCredentialSource": hasCredentialSource, "credentialSourceType": credentialSourceType}},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_get_profile_names() -> str:
            """Get list of all D365FO environment profile names.

            Returns:
                JSON string with profile names
            """
            try:
                profile_names = self.profile_manager.get_profile_names()
                default_profile = self.profile_manager.get_default_profile()

                return json.dumps(
                    {
                        "profileNames": profile_names,
                        "totalCount": len(profile_names),
                        "defaultProfile": default_profile.name if default_profile else None,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get profile names failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

    def _convert_credential_source(self, cred_source_data: Dict[str, Any]) -> Any:
        """Convert credential source data from API format to internal format.

        Args:
            cred_source_data: Credential source data in API format. Examples:
                - Environment variables:
                  {
                    "sourceType": "environment",
                    "clientIdVar": "D365FO_CLIENT_ID",       # optional, defaults to D365FO_CLIENT_ID
                    "clientSecretVar": "D365FO_CLIENT_SECRET", # optional, defaults to D365FO_CLIENT_SECRET
                    "tenantIdVar": "D365FO_TENANT_ID"        # optional, defaults to D365FO_TENANT_ID
                  }
                - Azure Key Vault:
                  {
                    "sourceType": "keyvault",
                    "vaultUrl": "https://myvault.vault.azure.net/",
                    "clientIdSecretName": "client-id",       # optional, defaults to D365FO_CLIENT_ID
                    "clientSecretSecretName": "client-secret", # optional, defaults to D365FO_CLIENT_SECRET
                    "tenantIdSecretName": "tenant-id",       # optional, defaults to D365FO_TENANT_ID
                    "keyvaultAuthMode": "default",           # optional: "default" or "client_secret"
                    "keyvaultClientId": "kv-client-id",      # required if keyvaultAuthMode is "client_secret"
                    "keyvaultClientSecret": "kv-secret",     # required if keyvaultAuthMode is "client_secret"
                    "keyvaultTenantId": "kv-tenant-id"       # required if keyvaultAuthMode is "client_secret"
                  }

        Returns:
            CredentialSource instance
        """
        from d365fo_client.credential_sources import create_credential_source

        source_type = cred_source_data.get("sourceType")
        if not source_type:
            raise ValueError("Missing sourceType in credential source data")

        kwargs = {}

        if source_type == "environment":
            if "clientIdVar" in cred_source_data:
                kwargs["client_id_var"] = cred_source_data["clientIdVar"]
            if "clientSecretVar" in cred_source_data:
                kwargs["client_secret_var"] = cred_source_data["clientSecretVar"]
            if "tenantIdVar" in cred_source_data:
                kwargs["tenant_id_var"] = cred_source_data["tenantIdVar"]
        elif source_type == "keyvault":
            if "vaultUrl" not in cred_source_data:
                raise ValueError("vaultUrl is required for keyvault credential source")
            kwargs["vault_url"] = cred_source_data["vaultUrl"]

            # Optional parameters
            optional_params = {
                "clientIdSecretName": "client_id_secret_name",
                "clientSecretSecretName": "client_secret_secret_name",
                "tenantIdSecretName": "tenant_id_secret_name",
                "keyvaultAuthMode": "keyvault_auth_mode",
                "keyvaultClientId": "keyvault_client_id",
                "keyvaultClientSecret": "keyvault_client_secret",
                "keyvaultTenantId": "keyvault_tenant_id"
            }

            for api_param, internal_param in optional_params.items():
                if api_param in cred_source_data:
                    kwargs[internal_param] = cred_source_data[api_param]
        else:
            raise ValueError(f"Unsupported credential source type: {source_type}")

        return create_credential_source(source_type, **kwargs)