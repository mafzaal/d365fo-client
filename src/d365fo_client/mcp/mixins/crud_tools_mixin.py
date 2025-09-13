"""CRUD tools mixin for FastMCP server."""

import json
import logging
from typing import List

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class CrudToolsMixin(BaseToolsMixin):
    """CRUD (Create, Read, Update, Delete) tools for FastMCP server."""
    
    def register_crud_tools(self):
        """Register all CRUD tools with FastMCP."""
        
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
            profile: str = "default",
        ) -> str:
            """Query D365FO data entities with simplified filtering capabilities.

            Args:
                entityName: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                select: List of field names to include in response
                filter: Simplified filter expression using only "eq" operation with wildcard support:
                    - Basic equality: "FieldName eq 'value'"
                    - Starts with: "FieldName eq 'value*'"
                    - Ends with: "FieldName eq '*value'"
                    - Contains: "FieldName eq '*value*'"
                    - Enum values: "StatusField eq Microsoft.Dynamics.DataEntities.EnumType'EnumValue'"
                    Example: "SalesOrderStatus eq Microsoft.Dynamics.DataEntities.SalesStatus'OpenOrder'"
                orderBy: List of field names to sort by (e.g., ["CreatedDateTime desc", "SalesId"])
                top: Maximum number of records to return (default: 100)
                skip: Number of records to skip for pagination
                count: Whether to include total count in response
                expand: List of navigation properties to expand
                profile: Profile name for connection configuration

            Returns:
                JSON string with query results including data array, count, and pagination info

            Note: This tool uses simplified OData filtering that only supports "eq" operations with wildcard patterns.
            For complex queries, retrieve data first and filter programmatically.
            """
            try:
                client = await self._get_client(profile)

                # Build query options
                from ...models import QueryOptions

                options = QueryOptions(
                    select=select,
                    filter=filter,
                    orderby=orderBy,
                    top=top,
                    skip=skip,
                    count=count,
                    expand=expand,
                )

                # Execute query
                result = await client.get_entities(entityName, options=options)

                return json.dumps(
                    {
                        "entityName": entityName,
                        "data": result.get("value", []),
                        "count": result.get("@odata.count"),
                        "nextLink": result.get("@odata.nextLink"),
                        "totalRecords": len(result.get("value", [])),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Query entities failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "entityName": entityName,
                        "parameters": {"select": select, "filter": filter, "top": top},
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_get_entity_record(
            entityName: str,
            key: str,
            select: List[str] = None,
            expand: List[str] = None,
            profile: str = "default",
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
                client = await self._get_client(profile)

                # Build query options
                from ...models import QueryOptions

                options = (
                    QueryOptions(select=select, expand=expand)
                    if select or expand
                    else None
                )

                # Get entity record
                result = await client.get_entity_by_key(entityName, key, options)

                return json.dumps(
                    {"entityName": entityName, "key": key, "data": result}, indent=2
                )

            except Exception as e:
                logger.error(f"Get entity record failed: {e}")
                return json.dumps(
                    {"error": str(e), "entityName": entityName, "key": key}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_create_entity_record(
            entityName: str,
            data: dict,
            returnRecord: bool = False,
            profile: str = "default",
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
                client = await self._get_client(profile)

                # Create entity record
                result = await client.create_entity_record(
                    entityName, data, returnRecord
                )

                return json.dumps(
                    {
                        "entityName": entityName,
                        "created": True,
                        "data": result if returnRecord else data,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Create entity record failed: {e}")
                return json.dumps(
                    {"error": str(e), "entityName": entityName, "created": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_update_entity_record(
            entityName: str,
            key: str,
            data: dict,
            returnRecord: bool = False,
            ifMatch: str = None,
            profile: str = "default",
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
                client = await self._get_client(profile)

                # Update entity record
                result = await client.update_entity_record(
                    entityName, key, data, returnRecord, ifMatch
                )

                return json.dumps(
                    {
                        "entityName": entityName,
                        "key": key,
                        "updated": True,
                        "data": result if returnRecord else data,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Update entity record failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "entityName": entityName,
                        "key": key,
                        "updated": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_delete_entity_record(
            entityName: str, key: str, ifMatch: str = None, profile: str = "default"
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
                client = await self._get_client(profile)

                # Delete entity record
                await client.delete_entity_record(entityName, key, ifMatch)

                return json.dumps(
                    {"entityName": entityName, "key": key, "deleted": True}, indent=2
                )

            except Exception as e:
                logger.error(f"Delete entity record failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "entityName": entityName,
                        "key": key,
                        "deleted": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_call_action(
            actionName: str,
            parameters: dict = None,
            entityName: str = None,
            entityKey: str = None,
            bindingKind: str = None,
            timeout: int = 30,
            profile: str = "default",
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
                client = await self._get_client(profile)

                # Call action
                result = await client.call_action(
                    actionName=actionName,
                    parameters=parameters or {},
                    entity_name=entityName,
                    entity_key=entityKey,
                    binding_kind=bindingKind,
                    timeout=timeout,
                )

                return json.dumps(
                    {"actionName": actionName, "success": True, "result": result},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Call action failed: {e}")
                return json.dumps(
                    {"error": str(e), "actionName": actionName, "success": False},
                    indent=2,
                )