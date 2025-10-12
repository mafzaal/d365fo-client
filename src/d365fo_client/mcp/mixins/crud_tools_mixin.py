"""CRUD tools mixin for FastMCP server."""

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
            entity_name: str,
            select: Optional[List[str]] = None,
            filter: Optional[str] = None,
            order_by: Optional[List[str]] = None,
            top: int = 100,
            skip: Optional[int] = None,
            count: bool = False,
            expand: Optional[List[str]] = None,
            profile: str = "default",
        ) -> dict:
            """Query D365FO data entities with simplified filtering capabilities.

            Args:
                entity_name: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                select: List of field names to include in response
                filter: Simplified filter expression using only "eq" operation with wildcard support:
                    - Basic equality: "FieldName eq 'value'"
                    - Starts with: "FieldName eq 'value*'"
                    - Ends with: "FieldName eq '*value'"
                    - Contains: "FieldName eq '*value*'"
                    - Enum values: "StatusField eq Microsoft.Dynamics.DataEntities.EnumType'EnumValue'"
                    Example: "SalesOrderStatus eq Microsoft.Dynamics.DataEntities.SalesStatus'OpenOrder'"
                order_by: List of field names to sort by (e.g., ["CreatedDateTime desc", "SalesId"])
                top: Maximum number of records to return (default: 100)
                skip: Number of records to skip for pagination
                count: Whether to include total count in response
                expand: List of navigation properties to expand
                profile: Profile name for connection configuration

            Returns:
                Dictionary with query results including data array, count, and pagination info

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
                    orderby=order_by,
                    top=top,
                    skip=skip,
                    count=count,
                    expand=expand,
                )

                # FOClient now handles validation and schema fetching
                result = await client.get_entities(entity_name, options=options)

                return {
                    "entityName": entity_name,
                    "data": result.get("value", []),
                    "count": result.get("@odata.count"),
                    "nextLink": result.get("@odata.nextLink"),
                    "totalRecords": len(result.get("value", [])),
                }

            except Exception as e:
                logger.error(f"Query entities failed: {e}")
                return {
                    "error": str(e),
                    "entityName": entity_name,
                    "parameters": {"select": select, "filter": filter, "top": top},
                }

        @self.mcp.tool()
        async def d365fo_get_entity_record(
            entity_name: str,
            key_fields: List[str],
            key_values: List[str],
            select: Optional[List[str]] = None,
            expand: Optional[List[str]] = None,
            profile: str = "default",
        ) -> dict:
            """Get a specific record from a D365FO data entity.

            Args:
                entity_name: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: List of key field names for composite keys
                key_values: List of key values corresponding to key fields
                select: List of fields to include in response
                expand: List of navigation properties to expand
                profile: Optional profile name

            Returns:
                Dictionary with the entity record
            """
            try:
                # Validate key_fields and key_values match
                if len(key_fields) != len(key_values):
                    return {
                        "error": "Key fields and values length mismatch",
                        "entityName": entity_name,
                        "key_fields": key_fields,
                        "key_values": key_values,
                    }

                # Build key dict
                key = {k: v for k, v in zip(key_fields, key_values)}

                client = await self._get_client(profile)

                # Build query options
                from ...models import QueryOptions

                options = (
                    QueryOptions(select=select, expand=expand)
                    if select or expand
                    else None
                )

                # FOClient now handles:
                # - Schema lookup via get_public_entity_schema_by_entityset()
                # - Entity validation (raises FOClientError if not found)
                # - Schema-aware key encoding via QueryBuilder
                result = await client.get_entity(entity_name, key, options)

                return {"entityName": entity_name, "key": key, "data": result}

            except Exception as e:
                logger.error(f"Get entity record failed: {e}")
                # Build key dict for error response if possible
                try:
                    key = (
                        {k: v for k, v in zip(key_fields, key_values)}
                        if len(key_fields) == len(key_values)
                        else None
                    )
                except Exception:
                    key = None
                return {
                    "error": str(e),
                    "entityName": entity_name,
                    "key_fields": key_fields,
                    "key_values": key_values,
                    "key": key,
                }

        @self.mcp.tool()
        async def d365fo_create_entity_record(
            entity_name: str,
            data: dict,
            return_record: bool = False,
            profile: str = "default",
        ) -> dict:
            """Create a new record in a D365 Finance & Operations data entity.

            Args:
                entity_name: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                data: Record data containing field names and values
                return_record: Whether to return the complete created record
                profile: Optional profile name

            Returns:
                Dictionary with creation result
            """
            try:
                client = await self._get_client(profile)

                # FOClient now handles:
                # - Schema validation via get_public_entity_schema_by_entityset()
                # - Entity existence check (raises FOClientError if not found)
                # - Read-only validation (raises FOClientError if read-only)
                # - OData serialization via crud_ops
                result = await client.create_entity(entity_name, data)

                return {
                    "entityName": entity_name,
                    "created": True,
                    "data": result if return_record else data,
                }

            except Exception as e:
                logger.error(f"Create entity record failed: {e}")
                return {"error": str(e), "entityName": entity_name, "created": False}

        @self.mcp.tool()
        async def d365fo_update_entity_record(
            entity_name: str,
            key_fields: List[str],
            key_values: List[str],
            data: dict,
            return_record: bool = False,
            profile: str = "default",
        ) -> dict:
            """Update an existing record in a D365 Finance & Operations data entity.

            Args:
                entity_name: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: List of key field names for composite keys
                key_values: List of key values corresponding to key fields
                data: Record data containing fields to update
                return_record: Whether to return the complete updated record
                profile: Optional profile name

            Returns:
                Dictionary with update result
            """
            try:
                # Validate key_fields and key_values match
                if len(key_fields) != len(key_values):
                    return {
                        "error": "Key fields and values length mismatch",
                        "entityName": entity_name,
                        "key_fields": key_fields,
                        "key_values": key_values,
                        "updated": False,
                    }

                # Build key dict
                key = {k: v for k, v in zip(key_fields, key_values)}

                client = await self._get_client(profile)

                # FOClient now handles:
                # - Schema validation via get_public_entity_schema_by_entityset()
                # - Entity existence check (raises FOClientError if not found)
                # - Read-only validation (raises FOClientError if read-only)
                # - Schema-aware key encoding via QueryBuilder
                result = await client.update_entity(entity_name, key, data)

                return {
                    "entityName": entity_name,
                    "key": key,
                    "updated": True,
                    "data": result if return_record else data,
                }

            except Exception as e:
                logger.error(f"Update entity record failed: {e}")
                # Build key dict for error response if possible
                try:
                    key = (
                        {k: v for k, v in zip(key_fields, key_values)}
                        if len(key_fields) == len(key_values)
                        else None
                    )
                except Exception:
                    key = None
                return {
                    "error": str(e),
                    "entityName": entity_name,
                    "key": key,
                    "updated": False,
                }

        @self.mcp.tool()
        async def d365fo_delete_entity_record(
            entity_name: str,
            key_fields: List[str],
            key_values: List[str],
            profile: str = "default",
        ) -> dict:
            """Delete a record from a D365 Finance & Operations data entity.

            Args:
                entity_name: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: List of key field names for composite keys
                key_values: List of key values corresponding to key fields
                profile: Optional profile name

            Returns:
                Dictionary with deletion result
            """
            try:
                # Validate key_fields and key_values match
                if len(key_fields) != len(key_values):
                    return {
                        "error": "Key fields and values length mismatch",
                        "entityName": entity_name,
                        "key_fields": key_fields,
                        "key_values": key_values,
                        "deleted": False,
                    }

                # Build key dict
                key = {k: v for k, v in zip(key_fields, key_values)}

                client = await self._get_client(profile)

                # FOClient now handles:
                # - Schema validation via get_public_entity_schema_by_entityset()
                # - Entity existence check (raises FOClientError if not found)
                # - Read-only validation (raises FOClientError if read-only)
                # - Schema-aware key encoding via QueryBuilder
                await client.delete_entity(entity_name, key)

                return {"entityName": entity_name, "key": key, "deleted": True}

            except Exception as e:
                logger.error(f"Delete entity record failed: {e}")
                # Build key dict for error response if possible
                try:
                    key = (
                        {k: v for k, v in zip(key_fields, key_values)}
                        if len(key_fields) == len(key_values)
                        else None
                    )
                except Exception:
                    key = None
                return {
                    "error": str(e),
                    "entityName": entity_name,
                    "key": key,
                    "deleted": False,
                }

        @self.mcp.tool()
        async def d365fo_call_action(
            action_name: str,
            entity_name: str = None,  # type: ignore
            parameters: dict = None,  # type: ignore
            key_fields: List[str] = None,  # type: ignore
            key_values: List[str] = None,  # type: ignore
            profile: str = "default",
        ) -> dict:
            """Execute an OData action method in D365 Finance & Operations.

            Args:
                action_name: Full name of the OData action to invoke
                parameters: Action parameters as key-value pairs
                entity_name: The entity's public collection name or entity set name (e.g., "CustomersV3", "SalesOrders", "DataManagementEntities")
                key_fields: Primary key fields for entity-bound actions
                key_values: Primary key values for entity-bound actions
                profile: Optional profile name

            Returns:
                Dictionary with action result
            """
            try:
                client = await self._get_client(profile)

                # Call action
                # Construct key field=value mapping (only if both key_fields and key_values are provided)
                key = None
                if key_fields is not None and key_values is not None:
                    if len(key_fields) != len(key_values):
                        raise ValueError("Key fields and values length mismatch")
                    key = {k: v for k, v in zip(key_fields, key_values)}

                result = await client.call_action(
                    action_name=action_name,  # type: ignore
                    parameters=parameters or {},
                    entity_name=entity_name,
                    entity_key=key,
                )

                return {"actionName": action_name, "success": True, "result": result}

            except Exception as e:
                logger.error(f"Call action failed: {e}")
                return {"error": str(e), "actionName": action_name, "success": False}

        @self.mcp.tool()
        async def d365fo_call_json_service(
            service_group: str,
            service_name: str,
            operation_name: str,
            parameters: Optional[dict] = None,
            profile: str = "default",
        ) -> dict:
            """Call a D365 F&O JSON service endpoint using the /api/services pattern.

            This provides a generic way to invoke any JSON service operation in D365 F&O.

            Args:
                service_group: Service group name (e.g., 'SysSqlDiagnosticService')
                service_name: Service name (e.g., 'SysSqlDiagnosticServiceOperations')
                operation_name: Operation name (e.g., 'GetAxSqlExecuting')
                parameters: Optional parameters to send in the POST body
                profile: Configuration profile to use

            Returns:
                Dictionary with service response data and metadata

            Example:
                Call a service without parameters:
                {
                    "service_group": "SysSqlDiagnosticService",
                    "service_name": "SysSqlDiagnosticServiceOperations",
                    "operation_name": "GetAxSqlExecuting"
                }

                Call a service with parameters:
                {
                    "service_group": "SysSqlDiagnosticService",
                    "service_name": "SysSqlDiagnosticServiceOperations",
                    "operation_name": "GetAxSqlResourceStats",
                    "parameters": {
                        "start": "2023-01-01T00:00:00Z",
                        "end": "2023-01-02T00:00:00Z"
                    }
                }
            """
            try:
                client = await self._get_client(profile)

                # Call the JSON service
                response = await client.post_json_service(
                    service_group=service_group,
                    service_name=service_name,
                    operation_name=operation_name,
                    parameters=parameters,
                )

                # Format response
                result = {
                    "success": response.success,
                    "statusCode": response.status_code,
                    "data": response.data,
                    "serviceGroup": service_group,
                    "serviceName": service_name,
                    "operationName": operation_name,
                }

                if response.error_message:
                    result["errorMessage"] = response.error_message

                return result

            except Exception as e:
                logger.error(f"JSON service call failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "serviceGroup": service_group,
                    "serviceName": service_name,
                    "operationName": operation_name,
                }
