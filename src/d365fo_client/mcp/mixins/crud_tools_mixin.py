"""CRUD tools mixin for FastMCP server."""

import json
import logging
from typing import List, Optional

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class CrudToolsMixin(BaseToolsMixin):
    """CRUD (Create, Read, Update, Delete) tools for FastMCP server."""
    
    def register_crud_tools(self):
        """Register all CRUD tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_query_entities(
            entityName: str,
            select: Optional[List[str]] = None,
            filter: Optional[str] = None,
            orderBy: Optional[List[str]] = None,
            top: int = 100,
            skip: Optional[int] = None,
            count: bool = False,
            expand: Optional[List[str]] = None,
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
            key_fields: List[str],
            key_values: List[str],
            select: Optional[List[str]] = None,
            expand: Optional[List[str]] = None,
            profile: str = "default",
        ) -> str:
            """Get a specific record from a D365FO data entity.

            Args:
                entityName: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: List of key field names for composite keys
                key_values: List of key values corresponding to key fields
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

                # Construct key field=value mapping
                if len(key_fields) != len(key_values):
                    raise ValueError("Key fields and values length mismatch")
                key = {k: v for k, v in zip(key_fields, key_values)} if len(key_fields) > 1 else key_values[0]

                # Get entity record
                result = await client.get_entity_by_key(entityName, key, options)# type: ignore

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
                entityName: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                data: Record data containing field names and values
                returnRecord: Whether to return the complete created record
                profile: Optional profile name

            Returns:
                JSON string with creation result
            """
            try:
                client = await self._get_client(profile)

                # Create entity record
                result = await client.create_entity(
                    entityName, data
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
            key_fields: List[str],
            key_values: List[str],
            data: dict,
            returnRecord: bool = False,
            ifMatch: Optional[str] = None,
            profile: str = "default",
        ) -> str:
            """Update an existing record in a D365 Finance & Operations data entity.

            Args:
                entityName: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: List of key field names for composite keys
                key_values: List of key values corresponding to key fields
                data: Record data containing fields to update
                returnRecord: Whether to return the complete updated record
                ifMatch: ETag value for optimistic concurrency control
                profile: Optional profile name

            Returns:
                JSON string with update result
            """
            try:
                client = await self._get_client(profile)

                # Construct key field=value mapping
                if len(key_fields) != len(key_values):
                    raise ValueError("Key fields and values length mismatch")
                key = {k: v for k, v in zip(key_fields, key_values)} if len(key_fields) > 1 else key_values[0]

                # Update entity record
                result = await client.update_entity(
                    entityName, key, data
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
                        "key": key, # type: ignore
                        "updated": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_delete_entity_record(
            entityName: str, 
            key_fields: List[str],
            key_values: List[str],
            ifMatch: Optional[str] = None, 
            profile: str = "default"
        ) -> str:
            """Delete a record from a D365 Finance & Operations data entity.

            Args:
                entityName: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: List of key field names for composite keys
                key_values: List of key values corresponding to key fields
                ifMatch: ETag value for optimistic concurrency control
                profile: Optional profile name

            Returns:
                JSON string with deletion result
            """
            try:
                client = await self._get_client(profile)

                # Construct key field=value mapping
                if len(key_fields) != len(key_values):
                    raise ValueError("Key fields and values length mismatch")
                key = {k: v for k, v in zip(key_fields, key_values)} if len(key_fields) > 1 else key_values[0]

                # Delete entity record
                await client.delete_entity(entityName, key)

                return json.dumps(
                    {"entityName": entityName, "key": key, "deleted": True}, indent=2
                )

            except Exception as e:
                logger.error(f"Delete entity record failed: {e}")
                return json.dumps(
                    {
                        "error": str(e),
                        "entityName": entityName,
                        "key": key, # type: ignore
                        "deleted": False,
                    },
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_call_action(
            actionName: str,
            parameters: dict = None,# type: ignore
            entityName: str = None,# type: ignore
            entityKey: str = None,# type: ignore
            bindingKind: str = None,# type: ignore
            timeout: int = 30,
            profile: str = "default",
        ) -> str:
            """Execute an OData action method in D365 Finance & Operations.

            Args:
                actionName: Full name of the OData action to invoke
                parameters: Action parameters as key-value pairs
                entityName: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
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
                
                result = await client.call_action(# type: ignore
                    actionName=actionName,# type: ignore
                    parameters=parameters or {},
                    entity_name=entityName,
                    entity_key=entityKey,
                    binding_kind=bindingKind,# type: ignore
                    timeout=timeout,# type: ignore
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