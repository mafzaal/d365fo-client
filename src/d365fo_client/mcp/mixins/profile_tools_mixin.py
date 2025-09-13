"""Profile tools mixin for FastMCP server."""

import json
import logging

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class ProfileToolsMixin(BaseToolsMixin):
    """Profile management tools for FastMCP server."""
    
    def register_profile_tools(self):
        """Register all profile tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_list_profiles() -> str:
            """Get list of all available D365FO environment profiles.

            Returns:
                JSON string with list of profiles
            """
            try:
                profiles = self.profile_manager.list_profiles()

                return json.dumps(
                    {
                        "totalProfiles": len(profiles),
                        "profiles": [profile.to_dict() for profile in profiles],
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
            description: str = None,
            authMode: str = "default",
            clientId: str = None,
            clientSecret: str = None,
            tenantId: str = None,
            timeout: int = 60,
            setAsDefault: bool = False,
            credentialSource: dict = None,
            **kwargs,
        ) -> str:
            """Create a new D365FO environment profile.

            Args:
                name: Profile name
                baseUrl: D365FO base URL
                description: Profile description
                authMode: Authentication mode
                clientId: Azure client ID
                clientSecret: Azure client secret
                tenantId: Azure tenant ID
                timeout: Request timeout in seconds
                setAsDefault: Set as default profile
                credentialSource: Credential source configuration
                **kwargs: Additional profile parameters

            Returns:
                JSON string with creation result
            """
            try:
                success = self.profile_manager.create_profile(
                    name=name,
                    base_url=baseUrl,
                    description=description,
                    auth_mode=authMode,
                    client_id=clientId,
                    client_secret=clientSecret,
                    tenant_id=tenantId,
                    timeout=timeout,
                    set_as_default=setAsDefault,
                    credential_source=credentialSource,
                    **kwargs,
                )

                return json.dumps(
                    {
                        "profileName": name,
                        "created": success,
                        "setAsDefault": setAsDefault,
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
            baseUrl: str = None,
            description: str = None,
            authMode: str = None,
            clientId: str = None,
            clientSecret: str = None,
            tenantId: str = None,
            timeout: int = None,
            credentialSource: dict = None,
            **kwargs,
        ) -> str:
            """Update an existing D365FO environment profile.

            Args:
                name: Profile name
                baseUrl: D365FO base URL
                description: Profile description
                authMode: Authentication mode
                clientId: Azure client ID
                clientSecret: Azure client secret
                tenantId: Azure tenant ID
                timeout: Request timeout in seconds
                credentialSource: Credential source configuration
                **kwargs: Additional profile parameters

            Returns:
                JSON string with update result
            """
            try:
                success = self.profile_manager.update_profile(
                    name=name,
                    base_url=baseUrl,
                    description=description,
                    auth_mode=authMode,
                    client_id=clientId,
                    client_secret=clientSecret,
                    tenant_id=tenantId,
                    timeout=timeout,
                    credential_source=credentialSource,
                    **kwargs,
                )

                return json.dumps({"profileName": name, "updated": success}, indent=2)

            except Exception as e:
                logger.error(f"Update profile failed: {e}")
                return json.dumps(
                    {"error": str(e), "profileName": name, "updated": False}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_delete_profile(profileName: str) -> str:
            """Delete a D365FO environment profile.

            Args:
                profileName: Name of the profile to delete

            Returns:
                JSON string with deletion result
            """
            try:
                success = self.profile_manager.delete_profile(profileName)

                return json.dumps(
                    {"profileName": profileName, "deleted": success}, indent=2
                )

            except Exception as e:
                logger.error(f"Delete profile failed: {e}")
                return json.dumps(
                    {"error": str(e), "profileName": profileName, "deleted": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_set_default_profile(profileName: str) -> str:
            """Set the default D365FO environment profile.

            Args:
                profileName: Name of the profile to set as default

            Returns:
                JSON string with result
            """
            try:
                success = self.profile_manager.set_default_profile(profileName)

                return json.dumps(
                    {"profileName": profileName, "setAsDefault": success}, indent=2
                )

            except Exception as e:
                logger.error(f"Set default profile failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "profileName": profileName,
                        "setAsDefault": False,
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
                is_valid, errors = self.profile_manager.validate_profile(profileName)

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