"""FastMCP-based D365FO MCP Server implementation.

This module provides a FastMCP-based implementation of the D365FO MCP server
with support for multiple transports (stdio, SSE, streamable-HTTP) and
improved performance, scalability, and deployment flexibility.
"""

import asyncio
import json
import logging
import os
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

        logger.info("Registered core D365FO tools with FastMCP")

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

        logger.info("Registered core D365FO resources with FastMCP")

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

    async def run(self, transport: Literal["stdio", "sse", "streamable-http"] = "stdio"):
        """Run the FastMCP server with specified transport.
        
        Args:
            transport: Transport protocol to use
        """
        try:
            logger.info(f"Starting FastD365FOMCPServer v{__version__} with {transport} transport...")

            # Perform startup initialization
            await self._startup_initialization()

            # Run server with specified transport
            self.mcp.run(transport=transport)

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