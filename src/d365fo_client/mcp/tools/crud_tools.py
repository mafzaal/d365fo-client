"""CRUD operation tools for MCP server."""

import json
import logging
import time
from typing import List

from mcp import Tool
from mcp.types import TextContent

from ...models import QueryOptions
from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class CrudTools:
    """CRUD operation tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize CRUD tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    def get_tools(self) -> List[Tool]:
        """Get list of CRUD tools.

        Returns:
            List of Tool definitions
        """
        return [
            self._get_query_entities_tool(),
            self._get_entity_record_tool(),
            self._get_create_record_tool(),
            self._get_update_record_tool(),
            self._get_delete_record_tool(),
            self._get_call_action_tool(),
        ]

    def _get_query_entities_tool(self) -> Tool:
        """Get query entities tool definition."""
        return Tool(
            name="d365fo_query_entities",
            description="Query and retrieve multiple records from D365 Finance & Operations data entities using OData standards. Supports advanced filtering, sorting, field selection, and pagination. Use this tool to search for specific records, generate reports, or perform bulk data analysis. Returns structured JSON data with optional metadata like record counts and pagination links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "The name of the D365FO data entity to query. This should be the public collection name or the entity set name (e.g., 'CustomersV3', 'SalesOrderHeadersV2', 'ItemsV2'). Use metadata discovery tools first to find the correct entity name if unsure.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile name containing connection details and authentication settings. Use 'default' if not specified or when working with a single environment.",
                        "default": "default",
                    },
                    "select": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of field names to include in the response (OData $select). Only specified fields will be returned, improving performance and reducing payload size. Example: ['CustomerAccount', 'Name', 'PrimaryContactEmail']. If omitted, all fields are returned.",
                    },
                    "filter": {
                        "type": "string",
                        "description": 'OData filter expression to restrict which records are returned (OData $filter). Supports standard OData operators: eq (equals), ne (not equals), gt (greater than), ge (greater or equal), lt (less than), le (less or equal), and (), or, not. Examples: "CustomerAccount eq \'CUST001\'", "CreditLimit gt 10000", "Name contains \'Corp\'".',
                    },
                    "expand": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of navigation property names to expand and include related entity data (OData $expand). This fetches related records in a single request. Example: ['PrimaryAddress', 'SalesOrders']. Use sparingly as it increases response size and processing time.",
                    },
                    "orderBy": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of field names for sorting results (OData $orderby). Add 'desc' suffix for descending order. Examples: ['Name'], ['CreditLimit desc'], ['CustomerAccount', 'Name desc']. Default order is ascending.",
                    },
                    "top": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000,
                        "description": "Maximum number of records to return (OData $top). Use for pagination and performance optimization. D365FO has built-in limits, typically 1000 records maximum per request. Combine with 'skip' for pagination.",
                    },
                    "skip": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Number of records to skip before returning results (OData $skip). Used for pagination - skip N records to get the next page. Example: skip=100 with top=50 gets records 101-150.",
                    },
                    "count": {
                        "type": "boolean",
                        "description": "Whether to include the total count of matching records in the response (OData $count). Useful for pagination UI and progress indicators. May impact performance on large datasets as it requires counting all matching records.",
                    },
                },
                "required": ["entityName"],
            },
        )

    def _get_entity_record_tool(self) -> Tool:
        """Get entity record tool definition."""
        return Tool(
            name="d365fo_get_entity_record",
            description="Retrieve a single specific record from a D365 Finance & Operations data entity using its primary key. This is the most efficient way to fetch a known record when you have its unique identifier. Supports field selection and expanding related data. Use this when you need details for one specific record rather than searching through multiple records.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "The name of the D365FO data entity containing the record. This should be the public entity name (e.g., 'CustomersV3', 'SalesOrderHeadersV2'). Use metadata discovery tools to find the correct entity name and identify key fields.",
                    },
                    "key": {
                        "oneOf": [
                            {
                                "type": "string",
                                "description": "Single string key value for entities with simple primary keys",
                            },
                            {
                                "type": "object",
                                "description": "Composite key object for entities with multiple key fields",
                                "additionalProperties": {"type": "string"},
                            },
                        ],
                        "description": "Primary key value(s) that uniquely identify the record. For single-key entities, provide a string value (e.g., 'CUST001'). For composite-key entities, provide an object with key field names and values (e.g., {'DataArea': 'USMF', 'CustomerAccount': 'CUST001'}). Use entity schema discovery to identify key fields.",
                    },
                    "select": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of specific field names to include in the response (OData $select). Only specified fields will be returned, improving performance and reducing response size. Example: ['CustomerAccount', 'Name', 'PrimaryContactEmail']. If omitted, all fields are returned.",
                    },
                    "expand": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of navigation property names to expand and include related entity data in the response (OData $expand). This allows fetching related records in a single request. Example: ['PrimaryAddress', 'ContactDetails']. Use entity schema discovery to identify available navigation properties.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["entityName", "key"],
            },
        )

    def _get_create_record_tool(self) -> Tool:
        """Get create record tool definition."""
        return Tool(
            name="d365fo_create_entity_record",
            description="Create a new record in a D365 Finance & Operations data entity. This operation performs data validation and may trigger business logic, workflows, and number sequences. The entity must support write operations (not read-only). Use entity schema discovery to identify required fields, data types, and validation rules before creating records.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "The name of the D365FO data entity where the new record will be created. This should be the public collection name or the entity set name (e.g., 'CustomersV3', 'SalesOrderHeadersV2'). Verify the entity supports create operations by checking it's not read-only using metadata discovery tools.",
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data object containing field names and values for the new record. Must include all mandatory fields as defined in the entity schema. Field names are case-sensitive and must match the entity's property names exactly. Example: {'CustomerAccount': 'CUST001', 'Name': 'Example Corp', 'CustomerGroupId': 'DEFAULT'}. Use entity schema discovery to identify required fields and their data types.",
                    },
                    "returnRecord": {
                        "type": "boolean",
                        "description": "Whether to return the complete created record in the response. Set to true to get the full record with system-generated values (like IDs, timestamps, calculated fields). Set to false for better performance when you only need confirmation of creation success.",
                        "default": False,
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["entityName", "data"],
            },
        )

    def _get_update_record_tool(self) -> Tool:
        """Get update record tool definition."""
        return Tool(
            name="d365fo_update_entity_record",
            description="Update an existing record in a D365 Finance & Operations data entity. This operation modifies specific fields while preserving others, performs validation, and may trigger business logic and workflows. The entity must support write operations. Use partial updates by including only the fields you want to change - omitted fields remain unchanged.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "The name of the D365FO data entity containing the record to update. This should be the public entity name (e.g., 'CustomersV3', 'SalesOrderHeadersV2'). Verify the entity supports update operations by checking it's not read-only using metadata discovery tools.",
                    },
                    "key": {
                        "oneOf": [
                            {
                                "type": "string",
                                "description": "Single string key value for entities with simple primary keys",
                            },
                            {
                                "type": "object",
                                "description": "Composite key object for entities with multiple key fields",
                                "properties": {},
                            },
                        ],
                        "description": "Primary key value(s) that uniquely identify the record to update. For single-key entities, provide a string value (e.g., 'CUST001'). For composite-key entities, provide an object with key field names and values (e.g., {'DataArea': 'USMF', 'CustomerAccount': 'CUST001'}). The record must exist or the operation will fail.",
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data object containing only the fields and values to update. This is a partial update - only include fields you want to change. Field names are case-sensitive and must match the entity's property names exactly. Example: {'Name': 'Updated Corp Name', 'CreditLimit': 50000}. Key fields typically cannot be updated.",
                    },
                    "returnRecord": {
                        "type": "boolean",
                        "description": "Whether to return the complete updated record in the response. Set to true to get the full record with all current values after the update. Set to false for better performance when you only need confirmation of update success.",
                        "default": False,
                    },
                    "ifMatch": {
                        "type": "string",
                        "description": "ETag value for optimistic concurrency control (optional). If provided, the update will only succeed if the record hasn't been modified by another process since the ETag was obtained. This prevents conflicting updates in multi-user scenarios. Get the ETag from a previous read operation.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["entityName", "key", "data"],
            },
        )

    def _get_delete_record_tool(self) -> Tool:
        """Get delete record tool definition."""
        return Tool(
            name="d365fo_delete_entity_record",
            description="Permanently delete a record from a D365 Finance & Operations data entity. This operation removes the record completely and may trigger cascading deletes, business logic, and workflows. The entity must support delete operations. Use with caution as this action cannot be undone. Verify business rules allow deletion before proceeding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "The name of the D365FO data entity containing the record to delete. This should be the public entity name (e.g., 'CustomersV3', 'SalesOrderHeadersV2'). Verify the entity supports delete operations and check for any business constraints that might prevent deletion.",
                    },
                    "key": {
                        "oneOf": [
                            {
                                "type": "string",
                                "description": "Single string key value for entities with simple primary keys",
                            },
                            {
                                "type": "object",
                                "description": "Composite key object for entities with multiple key fields",
                                "properties": {},
                            },
                        ],
                        "description": "Primary key value(s) that uniquely identify the record to delete. For single-key entities, provide a string value (e.g., 'CUST001'). For composite-key entities, provide an object with key field names and values (e.g., {'DataArea': 'USMF', 'CustomerAccount': 'CUST001'}). The record must exist or the operation will fail.",
                    },
                    "ifMatch": {
                        "type": "string",
                        "description": "ETag value for optimistic concurrency control (optional). If provided, the delete will only succeed if the record hasn't been modified by another process since the ETag was obtained. This prevents accidental deletion of records that have been updated by other users. Get the ETag from a previous read operation.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["entityName", "key"],
            },
        )

    def _get_call_action_tool(self) -> Tool:
        """Get call action tool definition."""
        return Tool(
            name="d365fo_call_action",
            description="Execute/invoke a D365 Finance & Operations OData action method. Actions are server-side operations that perform business logic, calculations, or complex operations beyond standard CRUD. Actions can be unbound (standalone), bound to entity collections, or bound to specific entity instances. Use action discovery tools to find available actions and their parameters before calling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "actionName": {
                        "type": "string",
                        "description": "The full name of the OData action to invoke. This is typically in the format 'Microsoft.Dynamics.DataEntities.ActionName' for system actions, or a simple name for custom actions. Examples: 'Microsoft.Dynamics.DataEntities.GetKeys', 'Microsoft.Dynamics.DataEntities.GetApplicationVersion'. Use action search tools to discover available actions and their exact names.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile name containing connection details and authentication settings for the D365FO environment. Use 'default' if not specified or when working with a single environment. Different profiles allow connecting to multiple D365FO environments (dev, test, prod).",
                        "default": "default",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Action parameters as key-value pairs (optional). Parameter names and types must match the action definition exactly. Use action discovery tools to identify required and optional parameters. Examples: {'entityName': 'CustomersV3'}, {'startDate': '2024-01-01', 'endDate': '2024-12-31'}. Leave empty {} for actions that require no parameters.",
                    },
                    "entityName": {
                        "type": "string",
                        "description": "The name of the data entity for entity-bound actions (optional). Required for actions with bindingKind 'BoundToEntitySet' or 'BoundToEntity'. This should be the public entity name or collection name. Use metadata discovery to identify the correct entity name for bound actions.",
                    },
                    "entityKey": {
                        "oneOf": [
                            {
                                "type": "string",
                                "description": "Single string key value for simple primary keys",
                            },
                            {
                                "type": "object",
                                "description": "Composite key object for multiple key fields",
                                "properties": {},
                            },
                        ],
                        "description": "Primary key value(s) identifying a specific entity instance for 'BoundToEntity' actions (optional). For single-key entities, provide a string. For composite keys, provide an object with key field names and values. Only required when bindingKind is 'BoundToEntity'.",
                    },
                    "bindingKind": {
                        "type": "string",
                        "description": "Explicitly specify the action's binding type if known (optional). Helps the system determine how to invoke the action. 'Unbound' actions are called directly. 'BoundToEntitySet' actions operate on entity collections. 'BoundToEntity' actions operate on specific entity instances. If not provided, the system will attempt to determine the binding automatically.",
                        "enum": ["Unbound", "BoundToEntitySet", "BoundToEntity"],
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 300,
                        "default": 30,
                        "description": "Request timeout in seconds. Actions may take longer than normal CRUD operations, especially complex business calculations or batch operations. Increase timeout for long-running actions. Default is 30 seconds, maximum is 300 seconds (5 minutes).",
                    },
                },
                "required": ["actionName"],
            },
        )

    async def execute_query_entities(self, arguments: dict) -> List[TextContent]:
        """Execute query entities tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            # Build query options
            options = QueryOptions(
                select=arguments.get("select"),
                filter=arguments.get("filter"),
                expand=arguments.get("expand"),
                orderby=arguments.get("orderBy"),
                top=arguments.get("top", None),
                skip=arguments.get("skip"),
                count=arguments.get("count", False),
            )

            # Execute query
            start_time = time.time()
            result = await client.get_entities(arguments["entityName"], options=options)
            query_time = time.time() - start_time

            # Format response
            response = {
                "data": result.get("value", []),
                "count": result.get("@odata.count"),
                "nextLink": result.get("@odata.nextLink"),
                "queryTime": round(query_time, 3),
                "totalRecords": len(result.get("value", [])),
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Query entities failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_query_entities",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute get entity record tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            start_time = time.time()
            record = await client.get_entity_by_key(
                arguments["entityName"],
                arguments["key"],
                select=arguments.get("select"),
                expand=arguments.get("expand"),
            )
            retrieval_time = time.time() - start_time

            response = {
                "record": record,
                "found": record is not None,
                "retrievalTime": round(retrieval_time, 3),
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Get entity record failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_entity_record",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_create_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute create entity record tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            result = await client.create_entity(
                arguments["entityName"], arguments["data"]
            )

            response = {
                "success": True,
                "recordId": result.get("id") if result else None,
                "createdRecord": (
                    result if arguments.get("returnRecord", False) else None
                ),
                "validationErrors": None,
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Create entity record failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_create_entity_record",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_update_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute update entity record tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            result = await client.update_entity(
                arguments["entityName"], arguments["key"], arguments["data"]
            )

            response = {
                "success": True,
                "updatedRecord": (
                    result if arguments.get("returnRecord", False) else None
                ),
                "validationErrors": None,
                "conflictDetected": False,
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Update entity record failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_update_entity_record",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_delete_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute delete entity record tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            await client.delete_entity(arguments["entityName"], arguments["key"])

            response = {"success": True, "conflictDetected": False, "error": None}

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Delete entity record failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_delete_entity_record",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_call_action(self, arguments: dict) -> List[TextContent]:
        """Execute call action tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            action_name = arguments["actionName"]
            parameters = arguments.get("parameters", {})
            entity_name = arguments.get("entityName")
            entity_key = arguments.get("entityKey")
            binding_kind = arguments.get("bindingKind")

            # Log the action call attempt
            logger.info(f"Calling action: {action_name}")
            if entity_name:
                logger.info(f"  Entity: {entity_name}")
            if entity_key:
                logger.info(f"  Key: {entity_key}")
            if binding_kind:
                logger.info(f"  Binding: {binding_kind}")

            start_time = time.time()

            # Call the action using the client's call_action method
            result = await client.call_action(
                action_name=action_name,
                parameters=parameters,
                entity_name=entity_name,
                entity_key=entity_key,
            )

            execution_time = time.time() - start_time

            # Format response
            response = {
                "success": True,
                "actionName": action_name,
                "result": result,
                "executionTime": round(execution_time, 3),
                "parameters": parameters,
                "binding": (
                    {
                        "entityName": entity_name,
                        "entityKey": entity_key,
                        "bindingKind": binding_kind,
                    }
                    if entity_name or entity_key
                    else None
                ),
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Call action failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_call_action",
                "actionName": arguments.get("actionName"),
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
