"""JSON service tools for MCP server."""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class JsonServiceTools:
    """JSON service tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize JSON service tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    def get_tools(self) -> List[Tool]:
        """Get list of JSON service tools.

        Returns:
            List of Tool definitions
        """
        return [
            self._get_call_json_service_tool(),
            self._get_call_sql_diagnostic_service_tool(),
        ]

    def _get_call_json_service_tool(self) -> Tool:
        """Get generic JSON service call tool definition."""
        return Tool(
            name="d365fo_call_json_service",
            description="Call a D365 F&O JSON service endpoint using the /api/services pattern. This provides a generic way to invoke any JSON service operation in D365 F&O.",
            inputSchema={
                "type": "object",
                "properties": {
                    "serviceGroup": {
                        "type": "string",
                        "description": "Service group name (e.g., 'SysSqlDiagnosticService')",
                    },
                    "serviceName": {
                        "type": "string", 
                        "description": "Service name (e.g., 'SysSqlDiagnosticServiceOperations')",
                    },
                    "operationName": {
                        "type": "string",
                        "description": "Operation name (e.g., 'GetAxSqlExecuting')",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Optional parameters to send in the POST body",
                        "additionalProperties": True,
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["serviceGroup", "serviceName", "operationName"],
            },
        )

    def _get_call_sql_diagnostic_service_tool(self) -> Tool:
        """Get SQL diagnostic service tool definition with predefined operations."""
        return Tool(
            name="d365fo_call_sql_diagnostic_service",
            description="Call SQL diagnostic service operations for D365 F&O performance monitoring. Provides convenient access to common SQL diagnostic operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "GetAxSqlExecuting",
                            "GetAxSqlResourceStats", 
                            "GetAxSqlBlocking",
                            "GetAxSqlLockInfo",
                            "GetAxSqlDisabledIndexes",
                        ],
                        "description": "SQL diagnostic operation to execute",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Operation-specific parameters",
                        "properties": {
                            "start": {
                                "type": "string",
                                "description": "Start date/time (ISO format) for GetAxSqlResourceStats",
                            },
                            "end": {
                                "type": "string", 
                                "description": "End date/time (ISO format) for GetAxSqlResourceStats",
                            },
                            "sinceLastMinutes": {
                                "type": "integer",
                                "description": "Alternative to start/end - get stats for last N minutes",
                                "minimum": 1,
                                "maximum": 1440,
                            },
                        },
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["operation"],
            },
        )

    async def execute_call_json_service(self, arguments: dict) -> List[TextContent]:
        """Execute generic JSON service call tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            start_time = time.time()
            profile = arguments.get("profile", "default")
            
            service_group = arguments["serviceGroup"]
            service_name = arguments["serviceName"]
            operation_name = arguments["operationName"]
            parameters = arguments.get("parameters")

            # Get client and call service
            client = await self.client_manager.get_client(profile)
            response = await client.post_json_service(
                service_group=service_group,
                service_name=service_name,
                operation_name=operation_name,
                parameters=parameters,
            )

            execution_time = time.time() - start_time

            # Format response
            result = {
                "success": response.success,
                "statusCode": response.status_code,
                "data": response.data,
                "executionTimeMs": round(execution_time * 1000, 2),
                "serviceGroup": service_group,
                "serviceName": service_name,
                "operationName": operation_name,
            }

            if response.error_message:
                result["errorMessage"] = response.error_message

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str),
                )
            ]

        except Exception as e:
            logger.error(f"Error calling JSON service: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "serviceGroup": arguments.get("serviceGroup"),
                "serviceName": arguments.get("serviceName"),
                "operationName": arguments.get("operationName"),
            }
            return [
                TextContent(
                    type="text",
                    text=json.dumps(error_result, indent=2),
                )
            ]

    async def execute_call_sql_diagnostic_service(self, arguments: dict) -> List[TextContent]:
        """Execute SQL diagnostic service call tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            start_time = time.time()
            profile = arguments.get("profile", "default")
            operation = arguments["operation"]
            parameters = arguments.get("parameters", {})

            # Prepare service call parameters
            service_group = "SysSqlDiagnosticService"
            service_name = "SysSqlDiagnosticServiceOperations"

            # Handle special parameter processing for GetAxSqlResourceStats
            service_parameters = None
            if operation == "GetAxSqlResourceStats":
                service_parameters = self._prepare_resource_stats_parameters(parameters)
            elif parameters:
                service_parameters = parameters

            # Get client and call service
            client = await self.client_manager.get_client(profile)
            response = await client.post_json_service(
                service_group=service_group,
                service_name=service_name,
                operation_name=operation,
                parameters=service_parameters,
            )

            execution_time = time.time() - start_time

            # Format response
            result = {
                "success": response.success,
                "statusCode": response.status_code,
                "data": response.data,
                "executionTimeMs": round(execution_time * 1000, 2),
                "operation": operation,
                "parameters": service_parameters,
            }

            if response.error_message:
                result["errorMessage"] = response.error_message

            # Add operation-specific formatting
            if response.success and response.data:
                result["summary"] = self._format_operation_summary(operation, response.data)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str),
                )
            ]

        except Exception as e:
            logger.error(f"Error calling SQL diagnostic service: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "operation": arguments.get("operation"),
            }
            return [
                TextContent(
                    type="text",
                    text=json.dumps(error_result, indent=2),
                )
            ]

    def _prepare_resource_stats_parameters(self, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare parameters for GetAxSqlResourceStats operation.

        Args:
            parameters: Input parameters

        Returns:
            Formatted parameters for the service call
        """
        from datetime import datetime, timezone, timedelta

        if "sinceLastMinutes" in parameters:
            # Convert sinceLastMinutes to start/end dates
            minutes = parameters["sinceLastMinutes"]
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=minutes)
            
            return {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            }
        elif "start" in parameters and "end" in parameters:
            # Use provided start/end dates
            return {
                "start": parameters["start"],
                "end": parameters["end"],
            }
        else:
            # Default to last 10 minutes
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=10)
            
            return {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            }

    def _format_operation_summary(self, operation: str, data: Any) -> Dict[str, Any]:
        """Format operation-specific summary information.

        Args:
            operation: Operation name
            data: Response data

        Returns:
            Summary information
        """
        summary = {"operation": operation}

        if isinstance(data, list):
            summary["recordCount"] = str(len(data))
            
            if operation == "GetAxSqlExecuting":
                summary["description"] = f"Found {len(data)} currently executing SQL statements"
            elif operation == "GetAxSqlResourceStats":
                summary["description"] = f"Retrieved {len(data)} SQL resource statistics records"
            elif operation == "GetAxSqlBlocking":
                summary["description"] = f"Found {len(data)} SQL blocking situations"
            elif operation == "GetAxSqlLockInfo":
                summary["description"] = f"Retrieved {len(data)} SQL lock information records"
            elif operation == "GetAxSqlDisabledIndexes":
                summary["description"] = f"Found {len(data)} disabled indexes"
        else:
            summary["description"] = f"Operation {operation} completed successfully"

        return summary