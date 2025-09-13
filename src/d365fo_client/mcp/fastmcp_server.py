"""FastMCP-based D365FO MCP Server implementation.

This module provides a FastMCP-based implementation of the D365FO MCP server
with support for multiple transports (stdio, SSE, streamable-HTTP) and
improved performance, scalability, and deployment flexibility.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .. import __version__
from ..profile_manager import ProfileManager
from .client_manager import D365FOClientManager
from .models import MCPServerConfig

logger = logging.getLogger(__name__)


class FastD365FOMCPServer:
    """FastMCP-based D365FO MCP Server with multi-transport support."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the FastMCP D365FO server.

        Args:
            config: Configuration dictionary with server and transport settings
        """
        self.config = config or self._load_default_config()
        self.profile_manager = ProfileManager()
        self.client_manager = D365FOClientManager(self.config, self.profile_manager)

        # Extract server configuration
        server_config = self.config.get("server", {})
        transport_config = server_config.get("transport", {})

        # Initialize FastMCP server with configuration
        self.mcp = FastMCP(
            name=server_config.get("name", "d365fo-mcp-server"),
            instructions=server_config.get(
                "instructions", 
                "Microsoft Dynamics 365 Finance & Operations MCP Server providing comprehensive access to D365FO data, metadata, and operations"
            ),
            host=transport_config.get("http", {}).get("host", "127.0.0.1"),
            port=transport_config.get("http", {}).get("port", 8000),
            debug=server_config.get("debug", False),
            json_response=transport_config.get("http", {}).get("json_response", False),
            stateless_http=transport_config.get("http", {}).get("stateless", False),
        )

        # Store reference for dependency injection in tools
        self._setup_dependency_injection()

        # Register all tools, resources, and prompts
        self._register_tools()
        self._register_resources()
        self._register_prompts()

        logger.info(f"FastD365FOMCPServer v{__version__} initialized")

    def _setup_dependency_injection(self):
        """Set up dependency injection for tools to access client manager."""
        # Store client manager reference for use in tool functions
        self.mcp._client_manager = self.client_manager
        
    def _register_tools(self):
        """Register all D365FO tools using FastMCP decorators."""
        
        # Connection Tools
        @self.mcp.tool()
        async def d365fo_test_connection(profile: str = None) -> str:
            """Test connection to D365FO environment.
            
            Args:
                profile: Optional profile name to test (uses default if not specified)
                
            Returns:
                JSON string with connection test results
            """
            try:
                result = await self.client_manager.test_connection(profile)
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "profile": profile
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_environment_info(profile: str = None) -> str:
            """Get D365FO environment information and version details.
            
            Args:
                profile: Optional profile name (uses default if not specified)
                
            Returns:
                JSON string with environment information
            """
            try:
                result = await self.client_manager.get_environment_info(profile)
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Failed to get environment info: {e}")
                return json.dumps({
                    "error": str(e),
                    "profile": profile
                }, indent=2)

        # Basic CRUD Tools
        @self.mcp.tool()
        async def d365fo_query_entities(
            entityName: str,
            select: List[str] = None,
            filter: str = None,
            orderBy: List[str] = None,
            top: int = 100,
            skip: int = None,
            count: bool = False,
            expand: List[str] = None,
            profile: str = None
        ) -> str:
            """Query D365FO data entities with OData parameters.
            
            Args:
                entityName: Name of the D365FO data entity to query
                select: List of fields to include in response
                filter: OData filter expression
                orderBy: List of fields to sort by
                top: Maximum number of records to return
                skip: Number of records to skip
                count: Whether to include total count
                expand: List of navigation properties to expand
                profile: Optional profile name
                
            Returns:
                JSON string with query results
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Build query options
                from ..models import QueryOptions
                options = QueryOptions(
                    select=select,
                    filter=filter,
                    orderby=orderBy,
                    top=top,
                    skip=skip,
                    count=count,
                    expand=expand
                )
                
                # Execute query
                result = await client.get_entities(entityName, options=options)
                
                return json.dumps({
                    "entityName": entityName,
                    "data": result.get("value", []),
                    "count": result.get("@odata.count"),
                    "nextLink": result.get("@odata.nextLink"),
                    "totalRecords": len(result.get("value", []))
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Query entities failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "entityName": entityName,
                    "parameters": {
                        "select": select,
                        "filter": filter,
                        "top": top
                    }
                }, indent=2)

        @self.mcp.tool() 
        async def d365fo_get_entity_record(
            entityName: str,
            key: str,
            select: List[str] = None,
            expand: List[str] = None,
            profile: str = None
        ) -> str:
            """Get a specific record from a D365FO data entity.
            
            Args:
                entityName: Name of the D365FO data entity
                key: Primary key value or composite key object
                select: List of fields to include in response
                expand: List of navigation properties to expand
                profile: Optional profile name
                
            Returns:
                JSON string with the entity record
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Build query options
                from ..models import QueryOptions
                options = QueryOptions(
                    select=select,
                    expand=expand
                ) if select or expand else None
                
                # Get entity record
                result = await client.get_entity_record(entityName, key, options)
                
                return json.dumps({
                    "entityName": entityName,
                    "key": key,
                    "data": result
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get entity record failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "entityName": entityName,
                    "key": key
                }, indent=2)

        # Basic Metadata Tools
        @self.mcp.tool()
        async def d365fo_search_entities(
            pattern: str,
            limit: int = 100,
            data_service_enabled: bool = None,
            data_management_enabled: bool = None,
            entity_category: str = None,
            is_read_only: bool = None,
            profile: str = None
        ) -> str:
            """Search for D365FO data entities using filters.
            
            Args:
                pattern: Search pattern for entity names
                limit: Maximum number of entities to return
                data_service_enabled: Filter by OData API availability
                data_management_enabled: Filter by DMF support
                entity_category: Filter by entity category
                is_read_only: Filter by read-only status
                profile: Optional profile name
                
            Returns:
                JSON string with matching entities
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Search entities
                entities = await client.search_data_entities(
                    pattern=pattern,
                    limit=limit,
                    data_service_enabled=data_service_enabled,
                    data_management_enabled=data_management_enabled,
                    entity_category=entity_category,
                    is_read_only=is_read_only
                )
                
                return json.dumps({
                    "searchPattern": pattern,
                    "totalFound": len(entities),
                    "entities": entities
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Search entities failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "searchPattern": pattern
                }, indent=2)

        # Additional CRUD Tools
        @self.mcp.tool()
        async def d365fo_create_entity_record(
            entityName: str,
            data: dict,
            returnRecord: bool = False,
            profile: str = None
        ) -> str:
            """Create a new record in a D365 Finance & Operations data entity.
            
            Args:
                entityName: Name of the D365FO data entity
                data: Record data containing field names and values
                returnRecord: Whether to return the complete created record
                profile: Optional profile name
                
            Returns:
                JSON string with creation result
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Create entity record
                result = await client.create_entity_record(
                    entityName, data, returnRecord
                )
                
                return json.dumps({
                    "entityName": entityName,
                    "created": True,
                    "data": result if returnRecord else data
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Create entity record failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "entityName": entityName,
                    "created": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_update_entity_record(
            entityName: str,
            key: str,
            data: dict,
            returnRecord: bool = False,
            ifMatch: str = None,
            profile: str = None
        ) -> str:
            """Update an existing record in a D365 Finance & Operations data entity.
            
            Args:
                entityName: Name of the D365FO data entity
                key: Primary key value or composite key object
                data: Record data containing fields to update
                returnRecord: Whether to return the complete updated record
                ifMatch: ETag value for optimistic concurrency control
                profile: Optional profile name
                
            Returns:
                JSON string with update result
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Update entity record
                result = await client.update_entity_record(
                    entityName, key, data, returnRecord, ifMatch
                )
                
                return json.dumps({
                    "entityName": entityName,
                    "key": key,
                    "updated": True,
                    "data": result if returnRecord else data
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Update entity record failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "entityName": entityName,
                    "key": key,
                    "updated": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_delete_entity_record(
            entityName: str,
            key: str,
            ifMatch: str = None,
            profile: str = None
        ) -> str:
            """Delete a record from a D365 Finance & Operations data entity.
            
            Args:
                entityName: Name of the D365FO data entity
                key: Primary key value or composite key object
                ifMatch: ETag value for optimistic concurrency control
                profile: Optional profile name
                
            Returns:
                JSON string with deletion result
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Delete entity record
                await client.delete_entity_record(entityName, key, ifMatch)
                
                return json.dumps({
                    "entityName": entityName,
                    "key": key,
                    "deleted": True
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Delete entity record failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "entityName": entityName,
                    "key": key,
                    "deleted": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_call_action(
            actionName: str,
            parameters: dict = None,
            entityName: str = None,
            entityKey: str = None,
            bindingKind: str = None,
            timeout: int = 30,
            profile: str = None
        ) -> str:
            """Execute an OData action method in D365 Finance & Operations.
            
            Args:
                actionName: Full name of the OData action to invoke
                parameters: Action parameters as key-value pairs
                entityName: Entity name for bound actions
                entityKey: Primary key for entity-bound actions
                bindingKind: Action binding type (Unbound, BoundToEntitySet, BoundToEntity)
                timeout: Request timeout in seconds
                profile: Optional profile name
                
            Returns:
                JSON string with action result
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Call action
                result = await client.call_action(
                    actionName=actionName,
                    parameters=parameters or {},
                    entity_name=entityName,
                    entity_key=entityKey,
                    binding_kind=bindingKind,
                    timeout=timeout
                )
                
                return json.dumps({
                    "actionName": actionName,
                    "success": True,
                    "result": result
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Call action failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "actionName": actionName,
                    "success": False
                }, indent=2)

        # Additional Metadata Tools
        @self.mcp.tool()
        async def d365fo_get_entity_schema(
            entityName: str,
            include_properties: bool = True,
            resolve_labels: bool = True,
            language: str = "en-US",
            profile: str = None
        ) -> str:
            """Get detailed schema for a specific D365 F&O data entity.
            
            Args:
                entityName: Public name of the entity
                include_properties: Include detailed property information
                resolve_labels: Resolve and include human-readable labels
                language: Language for label resolution
                profile: Optional profile name
                
            Returns:
                JSON string with entity schema
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get entity schema
                schema = await client.get_entity_schema(
                    entity_name=entityName,
                    include_properties=include_properties,
                    resolve_labels=resolve_labels,
                    language=language
                )
                
                return json.dumps({
                    "entityName": entityName,
                    "schema": schema
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get entity schema failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "entityName": entityName
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_search_actions(
            pattern: str,
            limit: int = 100,
            bindingKind: str = None,
            entityName: str = None,
            isFunction: bool = None,
            profile: str = None
        ) -> str:
            """Search for available OData actions in D365 F&O.
            
            Args:
                pattern: Simple keyword to search for in action names
                limit: Maximum number of actions to return
                bindingKind: Filter by binding type
                entityName: Filter actions bound to specific entity
                isFunction: Filter by function vs action type
                profile: Optional profile name
                
            Returns:
                JSON string with matching actions
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Search actions
                actions = await client.search_actions(
                    pattern=pattern,
                    limit=limit,
                    binding_kind=bindingKind,
                    entity_name=entityName,
                    is_function=isFunction
                )
                
                return json.dumps({
                    "searchPattern": pattern,
                    "totalFound": len(actions),
                    "actions": actions
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Search actions failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "searchPattern": pattern
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_search_enumerations(
            pattern: str,
            limit: int = 100,
            profile: str = None
        ) -> str:
            """Search for enumerations in D365 F&O.
            
            Args:
                pattern: Simple keyword to search for in enumeration names
                limit: Maximum number of enumerations to return
                profile: Optional profile name
                
            Returns:
                JSON string with matching enumerations
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Search enumerations
                enums = await client.search_enumerations(
                    pattern=pattern,
                    limit=limit
                )
                
                return json.dumps({
                    "searchPattern": pattern,
                    "totalFound": len(enums),
                    "enumerations": enums
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Search enumerations failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "searchPattern": pattern
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_enumeration_fields(
            enumeration_name: str,
            resolve_labels: bool = True,
            language: str = "en-US",
            profile: str = None
        ) -> str:
            """Get detailed members for a specific D365 F&O enumeration.
            
            Args:
                enumeration_name: Exact name of the enumeration
                resolve_labels: Resolve and include human-readable labels
                language: Language for label resolution
                profile: Optional profile name
                
            Returns:
                JSON string with enumeration details
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get enumeration fields
                enum_info = await client.get_enumeration_fields(
                    enumeration_name=enumeration_name,
                    resolve_labels=resolve_labels,
                    language=language
                )
                
                return json.dumps({
                    "enumerationName": enumeration_name,
                    "enumeration": enum_info
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get enumeration fields failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "enumerationName": enumeration_name
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_installed_modules(
            profile: str = None
        ) -> str:
            """Get list of installed modules in D365 F&O environment.
            
            Args:
                profile: Optional profile name
                
            Returns:
                JSON string with installed modules
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get installed modules
                modules = await client.get_installed_modules()
                
                return json.dumps({
                    "totalModules": len(modules),
                    "modules": modules
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get installed modules failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        # Label Tools
        @self.mcp.tool()
        async def d365fo_get_label(
            labelId: str,
            language: str = "en-US",
            fallbackToEnglish: bool = True,
            profile: str = None
        ) -> str:
            """Get label text by label ID.
            
            Args:
                labelId: Label ID (e.g., @SYS1234)
                language: Language code for label text
                fallbackToEnglish: Fallback to English if translation not found
                profile: Optional profile name
                
            Returns:
                JSON string with label text
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get label
                label_text = await client.get_label(
                    label_id=labelId,
                    language=language,
                    fallback_to_english=fallbackToEnglish
                )
                
                return json.dumps({
                    "labelId": labelId,
                    "language": language,
                    "labelText": label_text
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get label failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "labelId": labelId
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_labels_batch(
            labelIds: List[str],
            language: str = "en-US",
            fallbackToEnglish: bool = True,
            profile: str = None
        ) -> str:
            """Get multiple labels in a single request.
            
            Args:
                labelIds: List of label IDs to retrieve
                language: Language code for label texts
                fallbackToEnglish: Fallback to English if translation not found
                profile: Optional profile name
                
            Returns:
                JSON string with label texts
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get labels batch
                labels = await client.get_labels_batch(
                    label_ids=labelIds,
                    language=language,
                    fallback_to_english=fallbackToEnglish
                )
                
                return json.dumps({
                    "language": language,
                    "totalRequested": len(labelIds),
                    "labels": labels
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get labels batch failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "labelIds": labelIds
                }, indent=2)

        # Profile Management Tools
        @self.mcp.tool()
        async def d365fo_list_profiles() -> str:
            """Get list of all available D365FO environment profiles.
            
            Returns:
                JSON string with list of profiles
            """
            try:
                profiles = self.profile_manager.list_profiles()
                
                return json.dumps({
                    "totalProfiles": len(profiles),
                    "profiles": [profile.to_dict() for profile in profiles]
                }, indent=2)
                
            except Exception as e:
                logger.error(f"List profiles failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_profile(
            profileName: str
        ) -> str:
            """Get details of a specific D365FO environment profile.
            
            Args:
                profileName: Name of the profile to retrieve
                
            Returns:
                JSON string with profile details
            """
            try:
                profile = self.profile_manager.get_profile(profileName)
                
                if profile:
                    return json.dumps({
                        "profileName": profileName,
                        "profile": profile.to_dict()
                    }, indent=2)
                else:
                    return json.dumps({
                        "error": f"Profile '{profileName}' not found",
                        "profileName": profileName
                    }, indent=2)
                
            except Exception as e:
                logger.error(f"Get profile failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": profileName
                }, indent=2)

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
            **kwargs
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
                    **kwargs
                )
                
                return json.dumps({
                    "profileName": name,
                    "created": success,
                    "setAsDefault": setAsDefault
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Create profile failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": name,
                    "created": False
                }, indent=2)

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
            **kwargs
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
                    **kwargs
                )
                
                return json.dumps({
                    "profileName": name,
                    "updated": success
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Update profile failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": name,
                    "updated": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_delete_profile(
            profileName: str
        ) -> str:
            """Delete a D365FO environment profile.
            
            Args:
                profileName: Name of the profile to delete
                
            Returns:
                JSON string with deletion result
            """
            try:
                success = self.profile_manager.delete_profile(profileName)
                
                return json.dumps({
                    "profileName": profileName,
                    "deleted": success
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Delete profile failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": profileName,
                    "deleted": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_set_default_profile(
            profileName: str
        ) -> str:
            """Set the default D365FO environment profile.
            
            Args:
                profileName: Name of the profile to set as default
                
            Returns:
                JSON string with result
            """
            try:
                success = self.profile_manager.set_default_profile(profileName)
                
                return json.dumps({
                    "profileName": profileName,
                    "setAsDefault": success
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Set default profile failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": profileName,
                    "setAsDefault": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_default_profile() -> str:
            """Get the current default D365FO environment profile.
            
            Returns:
                JSON string with default profile
            """
            try:
                profile = self.profile_manager.get_default_profile()
                
                if profile:
                    return json.dumps({
                        "defaultProfile": profile.to_dict()
                    }, indent=2)
                else:
                    return json.dumps({
                        "error": "No default profile set"
                    }, indent=2)
                
            except Exception as e:
                logger.error(f"Get default profile failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_validate_profile(
            profileName: str
        ) -> str:
            """Validate a D365FO environment profile configuration.
            
            Args:
                profileName: Name of the profile to validate
                
            Returns:
                JSON string with validation result
            """
            try:
                is_valid, errors = self.profile_manager.validate_profile(profileName)
                
                return json.dumps({
                    "profileName": profileName,
                    "isValid": is_valid,
                    "errors": errors
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Validate profile failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": profileName,
                    "isValid": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_test_profile_connection(
            profileName: str
        ) -> str:
            """Test connection for a specific D365FO environment profile.
            
            Args:
                profileName: Name of the profile to test
                
            Returns:
                JSON string with connection test result
            """
            try:
                client = await self.client_manager.get_client(profileName)
                result = await client.test_connection()
                
                return json.dumps({
                    "profileName": profileName,
                    "connectionTest": result
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Test profile connection failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "profileName": profileName,
                    "connectionSuccessful": False
                }, indent=2)

        # Database Tools
        @self.mcp.tool()
        async def d365fo_execute_sql_query(
            query: str,
            format: str = "table",
            limit: int = 100,
            profile: str = None
        ) -> str:
            """Execute a SELECT query against the D365FO metadata database.
            
            Args:
                query: SQL SELECT query to execute
                format: Output format (table, json, csv)
                limit: Maximum number of rows to return
                profile: Optional profile name
                
            Returns:
                JSON string with query results
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Execute SQL query
                result = await client.execute_sql_query(
                    query=query,
                    format=format,
                    limit=limit
                )
                
                return json.dumps({
                    "query": query,
                    "format": format,
                    "limit": limit,
                    "result": result
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Execute SQL query failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "query": query
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_database_schema(
            table_name: str = None,
            include_indexes: bool = True,
            include_relationships: bool = True,
            include_statistics: bool = True,
            profile: str = None
        ) -> str:
            """Get comprehensive schema information for D365FO metadata database.
            
            Args:
                table_name: Optional specific table name
                include_indexes: Include index information
                include_relationships: Include foreign key relationships
                include_statistics: Include table statistics
                profile: Optional profile name
                
            Returns:
                JSON string with database schema
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get database schema
                schema = await client.get_database_schema(
                    table_name=table_name,
                    include_indexes=include_indexes,
                    include_relationships=include_relationships,
                    include_statistics=include_statistics
                )
                
                return json.dumps({
                    "tableName": table_name,
                    "schema": schema
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get database schema failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "tableName": table_name
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_table_info(
            table_name: str,
            include_relationships: bool = True,
            include_sample_data: bool = False,
            profile: str = None
        ) -> str:
            """Get detailed information about a specific database table.
            
            Args:
                table_name: Name of the table to get information about
                include_relationships: Include relationships to other tables
                include_sample_data: Include sample data from the table
                profile: Optional profile name
                
            Returns:
                JSON string with table information
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get table info
                table_info = await client.get_table_info(
                    table_name=table_name,
                    include_relationships=include_relationships,
                    include_sample_data=include_sample_data
                )
                
                return json.dumps({
                    "tableName": table_name,
                    "tableInfo": table_info
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get table info failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "tableName": table_name
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_database_statistics(
            include_table_stats: bool = True,
            include_version_stats: bool = True,
            include_performance_stats: bool = True,
            profile: str = None
        ) -> str:
            """Get comprehensive database statistics and analytics.
            
            Args:
                include_table_stats: Include per-table statistics
                include_version_stats: Include version statistics
                include_performance_stats: Include performance metrics
                profile: Optional profile name
                
            Returns:
                JSON string with database statistics
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get database statistics
                stats = await client.get_database_statistics(
                    include_table_stats=include_table_stats,
                    include_version_stats=include_version_stats,
                    include_performance_stats=include_performance_stats
                )
                
                return json.dumps({
                    "databaseStatistics": stats
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get database statistics failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        # Sync Tools
        @self.mcp.tool()
        async def d365fo_start_sync(
            strategy: str = "full_without_labels",
            global_version_id: int = None,
            profile: str = None
        ) -> str:
            """Start a metadata synchronization session.
            
            Args:
                strategy: Sync strategy to use
                global_version_id: Specific global version ID to sync
                profile: Optional profile name
                
            Returns:
                JSON string with sync session details
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Start sync
                session_id = await client.start_sync(
                    strategy=strategy,
                    global_version_id=global_version_id
                )
                
                return json.dumps({
                    "sessionId": session_id,
                    "strategy": strategy,
                    "started": True
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Start sync failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "strategy": strategy,
                    "started": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_sync_progress(
            session_id: str,
            profile: str = None
        ) -> str:
            """Get detailed progress information for a sync session.
            
            Args:
                session_id: Session ID of the sync operation
                profile: Optional profile name
                
            Returns:
                JSON string with sync progress
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get sync progress
                progress = await client.get_sync_progress(session_id)
                
                return json.dumps({
                    "sessionId": session_id,
                    "progress": progress
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get sync progress failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "sessionId": session_id
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_cancel_sync(
            session_id: str,
            profile: str = None
        ) -> str:
            """Cancel a running sync session.
            
            Args:
                session_id: Session ID of the sync operation to cancel
                profile: Optional profile name
                
            Returns:
                JSON string with cancellation result
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Cancel sync
                result = await client.cancel_sync(session_id)
                
                return json.dumps({
                    "sessionId": session_id,
                    "cancelled": result.get("cancelled", False),
                    "message": result.get("message", "")
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Cancel sync failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "sessionId": session_id,
                    "cancelled": False
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_list_sync_sessions(
            profile: str = None
        ) -> str:
            """Get list of all currently active sync sessions.
            
            Args:
                profile: Optional profile name
                
            Returns:
                JSON string with active sync sessions
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # List sync sessions
                sessions = await client.list_sync_sessions()
                
                return json.dumps({
                    "totalSessions": len(sessions),
                    "sessions": sessions
                }, indent=2)
                
            except Exception as e:
                logger.error(f"List sync sessions failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.tool()
        async def d365fo_get_sync_history(
            limit: int = 20,
            profile: str = None
        ) -> str:
            """Get history of completed sync sessions.
            
            Args:
                limit: Maximum number of sessions to return
                profile: Optional profile name
                
            Returns:
                JSON string with sync history
            """
            try:
                client = await self.client_manager.get_client(profile)
                
                # Get sync history
                history = await client.get_sync_history(limit=limit)
                
                return json.dumps({
                    "limit": limit,
                    "totalReturned": len(history),
                    "history": history
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Get sync history failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "limit": limit
                }, indent=2)

        logger.info("Registered all D365FO tools with FastMCP")

    def _register_resources(self):
        """Register D365FO resources using FastMCP decorators."""
        
        @self.mcp.resource("d365fo://entities/{entity_name}")
        async def entity_resource(entity_name: str) -> str:
            """Get entity metadata and sample data.
            
            Args:
                entity_name: Name of the D365FO entity
                
            Returns:
                JSON containing entity schema and sample records
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get entity schema
                schema = await client.get_entity_schema(entity_name)
                
                # Get sample data (limit to 5 records)
                from ..models import QueryOptions
                sample_data = await client.get_entities(
                    entity_name, 
                    options=QueryOptions(top=5)
                )
                
                return json.dumps({
                    "entity_name": entity_name,
                    "schema": schema,
                    "sample_data": sample_data.get("value", []),
                    "sample_count": len(sample_data.get("value", []))
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Entity resource failed for {entity_name}: {e}")
                return json.dumps({
                    "error": str(e),
                    "entity_name": entity_name
                }, indent=2)

        @self.mcp.resource("d365fo://environment/status")
        async def environment_status_resource() -> str:
            """Get D365FO environment status and health information.
            
            Returns:
                JSON containing environment status and health metrics
            """
            try:
                # Test connection
                connection_result = await self.client_manager.test_connection()
                
                # Get environment info
                env_info = await self.client_manager.get_environment_info()
                
                return json.dumps({
                    "connection_status": connection_result,
                    "environment_info": env_info,
                    "server_version": __version__
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Environment status resource failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "server_version": __version__
                }, indent=2)

        @self.mcp.resource("d365fo://environment/version")
        async def environment_version_resource() -> str:
            """Get D365FO environment version information.
            
            Returns:
                JSON containing environment version details
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get version information
                version_info = await client.get_application_version()
                
                return json.dumps({
                    "environment_version": version_info,
                    "server_version": __version__
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Environment version resource failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "server_version": __version__
                }, indent=2)

        @self.mcp.resource("d365fo://environment/cache")
        async def environment_cache_resource() -> str:
            """Get D365FO environment cache information.
            
            Returns:
                JSON containing cache statistics and health
            """
            try:
                # Get cache information from client manager
                cache_info = {
                    "cache_enabled": True,
                    "cache_directory": self.config.get("cache", {}).get("metadata_cache_dir", ""),
                    "label_cache_enabled": self.config.get("cache", {}).get("use_label_cache", True),
                    "label_cache_expiry": self.config.get("cache", {}).get("label_cache_expiry_minutes", 120)
                }
                
                return json.dumps({
                    "cache_info": cache_info,
                    "server_version": __version__
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Environment cache resource failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "server_version": __version__
                }, indent=2)

        # Metadata Resources
        @self.mcp.resource("d365fo://metadata/entities")
        async def metadata_entities_resource() -> str:
            """Get comprehensive list of D365FO data entities.
            
            Returns:
                JSON containing all available data entities
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get all entities (limit to prevent huge responses)
                entities = await client.search_data_entities(
                    pattern="",
                    limit=1000
                )
                
                return json.dumps({
                    "total_entities": len(entities),
                    "entities": entities,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Metadata entities resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://metadata/actions")
        async def metadata_actions_resource() -> str:
            """Get comprehensive list of D365FO OData actions.
            
            Returns:
                JSON containing all available OData actions
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get all actions (limit to prevent huge responses)
                actions = await client.search_actions(
                    pattern="",
                    limit=1000
                )
                
                return json.dumps({
                    "total_actions": len(actions),
                    "actions": actions,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Metadata actions resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://metadata/enumerations")
        async def metadata_enumerations_resource() -> str:
            """Get comprehensive list of D365FO enumerations.
            
            Returns:
                JSON containing all available enumerations
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get all enumerations (limit to prevent huge responses)
                enums = await client.search_enumerations(
                    pattern="",
                    limit=1000
                )
                
                return json.dumps({
                    "total_enumerations": len(enums),
                    "enumerations": enums,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Metadata enumerations resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://metadata/labels")
        async def metadata_labels_resource() -> str:
            """Get D365FO label system information.
            
            Returns:
                JSON containing label system status and statistics
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get label system information (example labels)
                sample_labels = ["@SYS1", "@SYS23776", "@DMF123"]
                label_info = []
                
                for label_id in sample_labels:
                    try:
                        label_text = await client.get_label(label_id, language="en-US")
                        label_info.append({
                            "label_id": label_id,
                            "label_text": label_text,
                            "resolved": True
                        })
                    except:
                        label_info.append({
                            "label_id": label_id,
                            "label_text": None,
                            "resolved": False
                        })
                
                return json.dumps({
                    "label_system_active": True,
                    "sample_labels": label_info,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Metadata labels resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        # Database Resources
        @self.mcp.resource("d365fo://database/schema")
        async def database_schema_resource() -> str:
            """Get D365FO metadata database schema information.
            
            Returns:
                JSON containing database schema details
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get database schema
                schema = await client.get_database_schema(
                    include_indexes=True,
                    include_relationships=True,
                    include_statistics=True
                )
                
                return json.dumps({
                    "database_schema": schema,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Database schema resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://database/statistics")
        async def database_statistics_resource() -> str:
            """Get D365FO metadata database statistics.
            
            Returns:
                JSON containing database statistics and analytics
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get database statistics
                stats = await client.get_database_statistics(
                    include_table_stats=True,
                    include_version_stats=True,
                    include_performance_stats=True
                )
                
                return json.dumps({
                    "database_statistics": stats,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Database statistics resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://database/tables")
        async def database_tables_resource() -> str:
            """Get D365FO metadata database table information.
            
            Returns:
                JSON containing list of database tables and their properties
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get table list via SQL query
                result = await client.execute_sql_query(
                    query="SELECT name, type FROM sqlite_master WHERE type='table' ORDER BY name",
                    format="json",
                    limit=100
                )
                
                return json.dumps({
                    "database_tables": result,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Database tables resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://database/indexes")
        async def database_indexes_resource() -> str:
            """Get D365FO metadata database index information.
            
            Returns:
                JSON containing database index details
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get index information via SQL query
                result = await client.execute_sql_query(
                    query="SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY name",
                    format="json",
                    limit=100
                )
                
                return json.dumps({
                    "database_indexes": result,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Database indexes resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        @self.mcp.resource("d365fo://database/relationships")
        async def database_relationships_resource() -> str:
            """Get D365FO metadata database relationship information.
            
            Returns:
                JSON containing foreign key relationships between tables
            """
            try:
                client = await self.client_manager.get_client()
                
                # Get foreign key information 
                result = await client.execute_sql_query(
                    query="""
                    SELECT 
                        m1.name as table_name,
                        m2.name as referenced_table
                    FROM sqlite_master m1
                    JOIN sqlite_master m2 
                    WHERE m1.type='table' AND m2.type='table'
                    ORDER BY m1.name
                    """,
                    format="json",
                    limit=100
                )
                
                return json.dumps({
                    "database_relationships": result,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Database relationships resource failed: {e}")
                return json.dumps({
                    "error": str(e)
                }, indent=2)

        logger.info("Registered all D365FO resources with FastMCP")

    def _register_prompts(self):
        """Register D365FO prompts using FastMCP decorators."""
        
        @self.mcp.prompt()
        async def d365fo_sequence_analysis(
            analysis_type: str = "comprehensive",
            scope: str = "company", 
            entity_filter: str = None
        ) -> str:
            """Comprehensive analysis of D365 Finance & Operations sequence numbers.
            
            Args:
                analysis_type: Type of analysis (manual_sequences, entity_references, configuration_review, usage_patterns, comprehensive)
                scope: Analysis scope (company, legal_entity, operating_unit, global, all)
                entity_filter: Optional filter for specific entities
                
            Returns:
                Detailed analysis prompt for D365FO sequence number investigation
            """
            template = f"""
# D365 Finance & Operations Sequence Number Analysis

Please perform a **{analysis_type}** analysis of sequence numbers with scope: **{scope}**

## Analysis Configuration
- **Analysis Type**: {analysis_type}
- **Scope**: {scope}
- **Entity Filter**: {entity_filter or "all entities"}

## Analysis Framework

### 1. Sequence Number Discovery
- Identify all sequence number configurations in the system
- Map sequence numbers to business processes and entities
- Document number sequence scopes and hierarchies

### 2. Configuration Review
- Analyze sequence number setup and parameters
- Review number sequence allocation methods
- Validate continuous vs. non-continuous configurations

### 3. Usage Pattern Analysis
- Monitor sequence number consumption rates
- Identify gaps or issues in number allocation
- Analyze performance impact of sequence number generation

### 4. Risk Assessment
- Evaluate sequence number exhaustion risks
- Identify manual vs. automatic sequence assignments
- Review security and audit trail implications

## Recommended Analysis Steps

1. **Query sequence number configurations** using d365fo_query_entities with entity "NumberSequences"
2. **Analyze entity relationships** to understand sequence number dependencies
3. **Review configuration parameters** for optimal performance
4. **Generate recommendations** for improvements and risk mitigation

## Expected Deliverables
- Comprehensive sequence number inventory
- Risk assessment with priority rankings
- Performance optimization recommendations
- Configuration best practices validation

Please use the available D365FO MCP tools to gather data and provide detailed insights.
"""
            return template.strip()

        @self.mcp.prompt()
        async def d365fo_action_execution(
            action_name: str,
            entity_name: str = None,
            action_type: str = "discovery"
        ) -> str:
            """Guide for executing D365FO OData actions with proper validation and error handling.
            
            Args:
                action_name: Name of the D365FO action to execute
                entity_name: Optional entity name for bound actions
                action_type: Type of action operation (discovery, validation, execution)
                
            Returns:
                Detailed guidance for D365FO action execution
            """
            template = f"""
# D365 Finance & Operations Action Execution Guide

Executing action: **{action_name}**
Entity context: **{entity_name or "Global/Unbound"}**
Operation type: **{action_type}**

## Action Execution Framework

### 1. Action Discovery
```
1. Search for the action using: d365fo_search_actions with pattern "{action_name}"
2. Verify action availability and binding requirements
3. Review action parameters and return types
```

### 2. Action Validation
```
1. Confirm action binding type (Unbound, BoundToEntitySet, BoundToEntity)
2. Validate required parameters and data types
3. Check authentication and authorization requirements
```

### 3. Parameter Preparation
```
1. Gather required parameter values
2. Validate parameter formats and constraints
3. Prepare entity keys for bound actions (if applicable)
```

### 4. Action Execution
```
1. Use d365fo_call_action tool with proper parameters
2. Handle binding context appropriately:
   - Unbound: Direct action call
   - BoundToEntitySet: Requires entity collection context
   - BoundToEntity: Requires specific entity instance key
```

### 5. Result Processing
```
1. Parse action response and return values
2. Handle any errors or exceptions
3. Validate business logic results
```

## Execution Template

For action **{action_name}**:

1. **Discovery Phase**:
   - Use d365fo_search_actions to find action details
   - Review binding kind and parameters

2. **Preparation Phase**:
   - Gather parameter values: [list required parameters]
   - Prepare entity context if bound action

3. **Execution Phase**:
   - Call d365fo_call_action with validated parameters
   - Monitor execution status and results

4. **Validation Phase**:
   - Verify action completed successfully
   - Validate business impact and side effects

## Error Handling
- Network timeouts: Retry with exponential backoff
- Authentication errors: Verify credentials and permissions
- Parameter validation: Check data types and required fields
- Business logic errors: Review action constraints and prerequisites

Please follow this systematic approach for reliable action execution.
"""
            return template.strip()

        logger.info("Registered core D365FO prompts with FastMCP")

    def run(self, transport: Literal["stdio", "sse", "streamable-http"] = "stdio"):
        """Run the FastMCP server with specified transport.
        
        Args:
            transport: Transport protocol to use
        """
        async def _run_async():
            try:
                logger.info(f"Starting FastD365FOMCPServer v{__version__} with {transport} transport...")

                # Perform startup initialization
                await self._startup_initialization()

                # Run server with specified transport using appropriate async method
                if transport == "stdio":
                    await self.mcp.run_stdio_async()
                elif transport == "sse":
                    await self.mcp.run_sse_async()
                elif transport in ["http", "streamable-http"]:
                    await self.mcp.run_streamable_http_async()
                else:
                    raise ValueError(f"Unsupported transport: {transport}")

            except Exception as e:
                logger.error(f"Error running FastMCP server: {e}")
                raise
            finally:
                await self.cleanup()

        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we reach here, we're in an async context
            raise RuntimeError("run() should not be called from async context. Use run_async() instead.")
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            asyncio.run(_run_async())

    async def run_async(self, transport: Literal["stdio", "sse", "streamable-http"] = "stdio"):
        """Run the FastMCP server with specified transport (async version).
        
        Args:
            transport: Transport protocol to use
        """
        try:
            logger.info(f"Starting FastD365FOMCPServer v{__version__} with {transport} transport...")

            # Perform startup initialization
            await self._startup_initialization()

            # Run server with specified transport using appropriate async method
            if transport == "stdio":
                await self.mcp.run_stdio_async()
            elif transport == "sse":
                await self.mcp.run_sse_async()
            elif transport in ["http", "streamable-http"]:
                await self.mcp.run_streamable_http_async()
            else:
                raise ValueError(f"Unsupported transport: {transport}")

        except Exception as e:
            logger.error(f"Error running FastMCP server: {e}")
            raise
        finally:
            await self.cleanup()

    async def _startup_initialization(self):
        """Perform startup initialization based on configuration."""
        try:
            startup_mode = self.config.get("startup_mode", "profile_only")
            
            if startup_mode == "profile_only":
                logger.info("Server started in profile-only mode")
                logger.info("No environment variables configured - use profile management tools to configure D365FO connections")
                
            elif startup_mode in ["default_auth", "client_credentials"]:
                logger.info(f"Server started with {startup_mode} mode")
                
                # Perform health checks and create default profile
                await self._startup_health_checks()
                await self._create_default_profile_if_needed()
                
            else:
                logger.warning(f"Unknown startup mode: {startup_mode}")

        except Exception as e:
            logger.error(f"Startup initialization failed: {e}")
            # Don't fail startup on initialization failures

    async def _startup_health_checks(self):
        """Perform startup health checks."""
        try:
            logger.info("Performing startup health checks...")

            # Test default connection
            connection_ok = await self.client_manager.test_connection()
            if not connection_ok:
                logger.warning("Default connection test failed during startup")
            else:
                logger.info("Default connection test passed")

            # Get environment info to verify functionality
            try:
                env_info = await self.client_manager.get_environment_info()
                logger.info(f"Connected to D365FO environment: {env_info['base_url']}")
                logger.info(f"Application version: {env_info['versions']['application']}")
            except Exception as e:
                logger.warning(f"Could not retrieve environment info: {e}")

        except Exception as e:
            logger.error(f"Startup health checks failed: {e}")

    async def _create_default_profile_if_needed(self):
        """Create a default profile from environment variables if needed."""
        try:
            # Check if default profile already exists
            existing_default = self.profile_manager.get_default_profile()
            if existing_default:
                logger.info(f"Default profile already exists: {existing_default.name}")
                return

            # Get environment variables
            base_url = os.getenv("D365FO_BASE_URL")
            if not base_url:
                logger.warning("Cannot create default profile - D365FO_BASE_URL not set")
                return

            # Determine authentication mode
            startup_mode = self.config.get("startup_mode", "profile_only")
            client_id = os.getenv("D365FO_CLIENT_ID")
            client_secret = os.getenv("D365FO_CLIENT_SECRET")
            tenant_id = os.getenv("D365FO_TENANT_ID")

            if startup_mode == "client_credentials":
                auth_mode = "client_credentials"
                if not all([client_id, client_secret, tenant_id]):
                    logger.error("Client credentials mode requires D365FO_CLIENT_ID, D365FO_CLIENT_SECRET, and D365FO_TENANT_ID")
                    return
            else:
                auth_mode = "default"

            # Create default profile
            profile_name = "default-from-env"
            existing_profile = self.profile_manager.get_profile(profile_name)
            if existing_profile:
                logger.info(f"Profile '{profile_name}' already exists, setting as default")
                self.profile_manager.set_default_profile(profile_name)
                return

            credential_source = None
            if startup_mode == "client_credentials":
                from ..credential_sources import EnvironmentCredentialSource
                credential_source = EnvironmentCredentialSource()

            success = self.profile_manager.create_profile(
                name=profile_name,
                base_url=base_url,
                auth_mode=auth_mode,
                client_id=None,  # Use from env var
                client_secret=None,  # Use from env var  
                tenant_id=None,  # Use from env var
                description=f"Auto-created from environment variables at startup (mode: {startup_mode})",
                use_label_cache=True,
                timeout=60,
                verify_ssl=True,
                credential_source=credential_source
            )

            if success:
                self.profile_manager.set_default_profile(profile_name)
                logger.info(f"Created and set default profile: {profile_name}")
                logger.info(f"Profile configured for: {base_url}")
                logger.info(f"Authentication mode: {auth_mode}")
            else:
                logger.warning(f"Failed to create default profile: {profile_name}")

        except Exception as e:
            logger.error(f"Error creating default profile: {e}")

    async def cleanup(self):
        """Clean up resources."""
        try:
            logger.info("Cleaning up FastD365FOMCPServer...")
            await self.client_manager.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration for FastMCP server.

        Returns:
            Default configuration dictionary
        """
        base_url = os.getenv("D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com")
        
        # Determine startup mode based on environment variables
        startup_mode = "profile_only"
        if base_url and base_url != "https://usnconeboxax1aos.cloud.onebox.dynamics.com":
            if all([os.getenv("D365FO_CLIENT_ID"), os.getenv("D365FO_CLIENT_SECRET"), os.getenv("D365FO_TENANT_ID")]):
                startup_mode = "client_credentials"
            else:
                startup_mode = "default_auth"

        return {
            "startup_mode": startup_mode,
            "server": {
                "name": "d365fo-mcp-server", 
                "version": __version__,
                "debug": os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
                "transport": {
                    "default": "stdio",
                    "stdio": {
                        "enabled": True
                    },
                    "sse": {
                        "enabled": True,
                        "host": "127.0.0.1",
                        "port": int(os.getenv("MCP_SSE_PORT", "8000")),
                        "cors": {
                            "enabled": True,
                            "origins": ["*"],
                            "methods": ["GET", "POST"],
                            "headers": ["*"]
                        }
                    },
                    "http": {
                        "enabled": True,
                        "host": os.getenv("MCP_HTTP_HOST", "127.0.0.1"),
                        "port": int(os.getenv("MCP_HTTP_PORT", "8000")),
                        "stateless": os.getenv("MCP_HTTP_STATELESS", "").lower() in ("true", "1", "yes"),
                        "json_response": os.getenv("MCP_HTTP_JSON", "").lower() in ("true", "1", "yes"),
                        "cors": {
                            "enabled": True,
                            "origins": ["*"],
                            "methods": ["GET", "POST", "DELETE"],
                            "headers": ["*"]
                        }
                    }
                }
            },
            "default_environment": {
                "base_url": base_url,
                "use_default_credentials": True,
                "use_cache_first": True,
                "timeout": 60,
                "verify_ssl": True,
                "use_label_cache": True,
            },
            "cache": {
                "metadata_cache_dir": os.path.expanduser("~/.d365fo-mcp/cache"),
                "label_cache_expiry_minutes": 120,
                "use_label_cache": True,
                "cache_size_limit_mb": 100,
            },
            "performance": {
                "max_concurrent_requests": 10,
                "connection_pool_size": 5,
                "request_timeout": 30,
                "batch_size": 100,
            },
            "security": {
                "encrypt_cached_tokens": True,
                "token_expiry_buffer_minutes": 5,
                "max_retry_attempts": 3,
            },
        }