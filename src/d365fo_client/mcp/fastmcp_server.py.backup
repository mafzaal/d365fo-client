"""FastMCP-based D365FO MCP Server implementation.

This module provides a FastMCP-based implementation of the D365FO MCP server
with support for multiple transports (stdio, SSE, streamable-HTTP) and
improved performance, scalability, and deployment flexibility.
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple
from weakref import WeakValueDictionary

import aiosqlite
from mcp.server.fastmcp import FastMCP


class SessionContext:
    """Simple session context that can be weakly referenced."""

    def __init__(self, session_id: str, stateless: bool = True):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.stateless = stateless
        self.request_count = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for API compatibility."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "stateless": self.stateless,
            "request_count": self.request_count,
        }

    def __getitem__(self, key):
        """Support dict-like access for backward compatibility."""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Support dict-like access for backward compatibility."""
        setattr(self, key, value)


class DatabaseQuerySafetyError(Exception):
    """Raised when a database query is deemed unsafe or invalid."""
    pass


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
                "Microsoft Dynamics 365 Finance & Operations MCP Server providing comprehensive access to D365FO data, metadata, and operations",
            ),
            host=transport_config.get("http", {}).get("host", "127.0.0.1"),
            port=transport_config.get("http", {}).get("port", 8000),
            debug=server_config.get("debug", False),
            json_response=transport_config.get("http", {}).get("json_response", False),
            stateless_http=transport_config.get("http", {}).get("stateless", False),
        )

        # Store reference for dependency injection in tools
        self._setup_dependency_injection()

        # Initialize performance monitoring and session management
        self._setup_production_features()

        # Register all tools, resources, and prompts
        self._register_tools()
        self._register_resources()
        self._register_prompts()

        logger.info(
            f"FastD365FOMCPServer v{__version__} initialized with production features"
        )

    def _setup_dependency_injection(self):
        """Set up dependency injection for tools to access client manager."""
        # Store client manager reference for use in tool functions
        self.mcp._client_manager = self.client_manager

    def _setup_production_features(self):
        """Set up production features including performance monitoring and session management."""
        # Performance monitoring
        self._request_stats = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_response_time": 0.0,
            "last_reset": datetime.now(),
        }
        self._request_times = []
        self._max_request_history = 1000

        # Connection pool monitoring
        self._connection_pool_stats = {
            "active_connections": 0,
            "peak_connections": 0,
            "connection_errors": 0,
            "pool_hits": 0,
            "pool_misses": 0,
        }

        # Stateless session management (for HTTP transport)
        transport_config = self.config.get("server", {}).get("transport", {})
        self._stateless_mode = transport_config.get("http", {}).get("stateless", False)
        self._json_response_mode = transport_config.get("http", {}).get(
            "json_response", False
        )

        if self._stateless_mode:
            logger.info("Stateless HTTP mode enabled - sessions will not be persisted")
            # Use weak references for stateless sessions to allow garbage collection
            self._stateless_sessions = WeakValueDictionary()
        else:
            # Standard session management for stateful mode
            self._active_sessions = {}

        if self._json_response_mode:
            logger.info("JSON response mode enabled - responses will be in JSON format")

        # Performance optimization settings
        perf_config = self.config.get("performance", {})
        self._max_concurrent_requests = perf_config.get("max_concurrent_requests", 10)
        self._request_timeout = perf_config.get("request_timeout", 30)
        self._batch_size = perf_config.get("batch_size", 100)

        # Connection pooling semaphore
        self._request_semaphore = asyncio.Semaphore(self._max_concurrent_requests)

        logger.info(f"Production features configured:")
        logger.info(f"  - Stateless mode: {self._stateless_mode}")
        logger.info(f"  - JSON response mode: {self._json_response_mode}")
        logger.info(f"  - Max concurrent requests: {self._max_concurrent_requests}")
        logger.info(f"  - Request timeout: {self._request_timeout}s")

        # Database tools configuration
        self._setup_database_tools()

    def _setup_database_tools(self):
        """Set up database tools configuration."""
        # Query safety configuration
        self.max_results = 1000
        self.query_timeout_seconds = 30
        self.allowed_operations = {'SELECT'}
        self.blocked_tables = {'labels_cache'}  # Tables with potentially sensitive data
        
        # SQL injection protection patterns
        self.dangerous_patterns = [
            r';\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)',
            r'UNION\s+SELECT',
            r'--\s*[^\r\n]*',
            r'/\*.*?\*/',
            r'exec\s*\(',
            r'sp_\w+',
            r'xp_\w+',
        ]

    def _validate_query_safety(self, query: str) -> None:
        """Validate that a query is safe to execute.
        
        Args:
            query: SQL query to validate
            
        Raises:
            DatabaseQuerySafetyError: If query is deemed unsafe
        """
        # Normalize query for analysis
        normalized_query = query.strip().upper()
        
        # Check if query starts with SELECT
        if not normalized_query.startswith('SELECT'):
            raise DatabaseQuerySafetyError("Only SELECT queries are allowed")
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, normalized_query, re.IGNORECASE | re.MULTILINE):
                raise DatabaseQuerySafetyError(f"Query contains potentially dangerous pattern: {pattern}")
        
        # Check for blocked operations
        for operation in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']:
            if operation in normalized_query:
                raise DatabaseQuerySafetyError(f"Operation {operation} is not allowed")
        
        # Check for access to blocked tables
        for blocked_table in self.blocked_tables:
            if blocked_table.upper() in normalized_query:
                raise DatabaseQuerySafetyError(f"Access to table {blocked_table} is restricted")

    async def _get_database_path(self, profile: str = "default") -> str:
        """Get the path to the metadata database.
        
        Args:
            profile: Configuration profile to use
            
        Returns:
            Path to the database file
        """
        client = await self.client_manager.get_client(profile)
        if hasattr(client, 'metadata_cache') and client.metadata_cache:
            return str(client.metadata_cache.db_path)
        else:
            raise DatabaseQuerySafetyError("No metadata database available for this profile")

    async def _execute_safe_query(self, query: str, db_path: str, limit: int = 100) -> Tuple[List[str], List[Tuple]]:
        """Execute a safe SQL query and return results.
        
        Args:
            query: SQL query to execute
            db_path: Path to database file
            limit: Maximum number of rows to return
            
        Returns:
            Tuple of (column_names, rows)
        """
        # Add LIMIT clause if not present
        if limit and 'LIMIT' not in query.upper():
            query += f' LIMIT {limit}'
        
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to tuples for easier processing
            row_tuples = [tuple(row) for row in rows]
            
            return column_names, row_tuples

    def _format_query_results(self, columns: List[str], rows: List[Tuple], format_type: str = "table") -> str:
        """Format query results in the specified format.
        
        Args:
            columns: Column names
            rows: Row data
            format_type: Output format (table, json, csv)
            
        Returns:
            Formatted results string
        """
        if format_type == "json":
            # Convert to list of dictionaries
            result_dicts = []
            for row in rows:
                row_dict = {col: value for col, value in zip(columns, row)}
                result_dicts.append(row_dict)
            return json.dumps({"columns": columns, "data": result_dicts, "row_count": len(rows)}, indent=2)
        
        elif format_type == "csv":
            # CSV format
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            return output.getvalue()
        
        else:  # table format
            if not rows:
                return "No results found."
            
            # Calculate column widths
            col_widths = []
            for i, col in enumerate(columns):
                max_width = len(str(col))
                for row in rows:
                    if i < len(row):
                        max_width = max(max_width, len(str(row[i])))
                col_widths.append(min(max_width, 50))  # Cap at 50 chars
            
            # Create table
            lines = []
            
            # Header
            header = " | ".join(str(col).ljust(width) for col, width in zip(columns, col_widths))
            lines.append(header)
            lines.append("-" * len(header))
            
            # Rows
            for row in rows:
                row_str = " | ".join(
                    str(value).ljust(width)[:width] for value, width in zip(row, col_widths)
                )
                lines.append(row_str)
            
            lines.append(f"\nTotal rows: {len(rows)}")
            return "\n".join(lines)

    async def _get_schema_info(
        self, 
        db_path: str, 
        table_name: Optional[str] = None,
        include_statistics: bool = True,
        include_indexes: bool = True,
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive database schema information."""
        async with aiosqlite.connect(db_path) as db:
            schema_info = {
                "database_path": db_path,
                "generated_at": time.time(),
                "tables": {}
            }
            
            # Get list of tables
            if table_name:
                tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                cursor = await db.execute(tables_query, (table_name,))
            else:
                tables_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                cursor = await db.execute(tables_query)
            
            table_names = [row[0] for row in await cursor.fetchall()]
            
            # Get detailed info for each table
            for name in table_names:
                table_info = {"name": name}
                
                # Get column information
                cursor = await db.execute(f"PRAGMA table_info({name})")
                columns = await cursor.fetchall()
                table_info["columns"] = [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
                
                if include_statistics:
                    # Get row count
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {name}")
                    table_info["row_count"] = (await cursor.fetchone())[0]
                
                if include_indexes:
                    # Get indexes
                    cursor = await db.execute(f"PRAGMA index_list({name})")
                    indexes = await cursor.fetchall()
                    table_info["indexes"] = [
                        {
                            "name": idx[1],
                            "unique": bool(idx[2]),
                            "origin": idx[3]
                        }
                        for idx in indexes
                    ]
                
                if include_relationships:
                    # Get foreign keys
                    cursor = await db.execute(f"PRAGMA foreign_key_list({name})")
                    foreign_keys = await cursor.fetchall()
                    table_info["foreign_keys"] = [
                        {
                            "column": fk[3],
                            "references_table": fk[2],
                            "references_column": fk[4]
                        }
                        for fk in foreign_keys
                    ]
                
                schema_info["tables"][name] = table_info
            
            return schema_info

    async def _get_detailed_table_info(
        self,
        db_path: str,
        table_name: str,
        include_sample_data: bool = False,
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        async with aiosqlite.connect(db_path) as db:
            table_info = {
                "table_name": table_name,
                "generated_at": time.time()
            }
            
            # Verify table exists
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not await cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist")
            
            # Get column information with detailed types
            cursor = await db.execute(f"PRAGMA table_info({table_name})")
            columns = await cursor.fetchall()
            table_info["columns"] = [
                {
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
            
            # Get table statistics
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
            table_info["row_count"] = (await cursor.fetchone())[0]
            
            # Get indexes
            cursor = await db.execute(f"PRAGMA index_list({table_name})")
            indexes = await cursor.fetchall()
            table_info["indexes"] = []
            for idx in indexes:
                index_info = {
                    "name": idx[1],
                    "unique": bool(idx[2]),
                    "origin": idx[3]
                }
                # Get index columns
                cursor = await db.execute(f"PRAGMA index_info({idx[1]})")
                index_columns = await cursor.fetchall()
                index_info["columns"] = [col[2] for col in index_columns]
                table_info["indexes"].append(index_info)
            
            if include_relationships:
                # Get foreign keys
                cursor = await db.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = await cursor.fetchall()
                table_info["foreign_keys"] = [
                    {
                        "id": fk[0],
                        "seq": fk[1],
                        "table": fk[2],
                        "from": fk[3],
                        "to": fk[4],
                        "on_update": fk[5],
                        "on_delete": fk[6],
                        "match": fk[7]
                    }
                    for fk in foreign_keys
                ]
                
                # Find tables that reference this table
                cursor = await db.execute(
                    """SELECT name FROM sqlite_master WHERE type='table'"""
                )
                all_tables = [row[0] for row in await cursor.fetchall()]
                
                referencing_tables = []
                for other_table in all_tables:
                    cursor = await db.execute(f"PRAGMA foreign_key_list({other_table})")
                    fks = await cursor.fetchall()
                    for fk in fks:
                        if fk[2] == table_name:  # references our table
                            referencing_tables.append({
                                "table": other_table,
                                "column": fk[3],
                                "references_column": fk[4]
                            })
                
                table_info["referenced_by"] = referencing_tables
            
            if include_sample_data and table_info["row_count"] > 0:
                # Get sample data (first 5 rows)
                cursor = await db.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_rows = await cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                
                table_info["sample_data"] = {
                    "columns": column_names,
                    "rows": [list(row) for row in sample_rows]
                }
            
            return table_info

    async def _get_enhanced_statistics(
        self,
        db_path: str,
        include_table_stats: bool = True,
        include_version_stats: bool = True,
        include_performance_stats: bool = True
    ) -> Dict[str, Any]:
        """Get enhanced database statistics."""
        stats = {}
        
        async with aiosqlite.connect(db_path) as db:
            if include_table_stats:
                # Get detailed table statistics
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                table_names = [row[0] for row in await cursor.fetchall()]
                
                table_stats = {}
                for table_name in table_names:
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = (await cursor.fetchone())[0]
                    table_stats[table_name] = {"row_count": row_count}
                
                stats["detailed_table_statistics"] = table_stats
            
            if include_version_stats:
                # Enhanced version statistics
                cursor = await db.execute(
                    """SELECT 
                         COUNT(DISTINCT gv.id) as unique_versions,
                         COUNT(DISTINCT ev.environment_id) as environments_with_versions,
                         AVG(gv.reference_count) as avg_reference_count,
                         MAX(gv.last_used_at) as most_recent_use
                       FROM global_versions gv 
                       LEFT JOIN environment_versions ev ON gv.id = ev.global_version_id"""
                )
                version_stats = await cursor.fetchone()
                stats["enhanced_version_statistics"] = {
                    "unique_versions": version_stats[0],
                    "environments_with_versions": version_stats[1],
                    "average_reference_count": round(version_stats[2] or 0, 2),
                    "most_recent_use": version_stats[3]
                }
            
            if include_performance_stats:
                # Database performance statistics
                cursor = await db.execute("PRAGMA page_count")
                page_count = (await cursor.fetchone())[0]
                
                cursor = await db.execute("PRAGMA page_size")
                page_size = (await cursor.fetchone())[0]
                
                cursor = await db.execute("PRAGMA freelist_count")
                freelist_count = (await cursor.fetchone())[0]
                
                stats["performance_statistics"] = {
                    "total_pages": page_count,
                    "page_size_bytes": page_size,
                    "database_size_bytes": page_count * page_size,
                    "free_pages": freelist_count,
                    "utilized_pages": page_count - freelist_count,
                    "space_utilization_percent": round(
                        ((page_count - freelist_count) / page_count * 100) if page_count > 0 else 0, 2
                    )
                }
        
        return stats

    def _register_tools(self):
        """Register all D365FO tools using FastMCP decorators."""

        # Connection Tools
        @self.mcp.tool()
        async def d365fo_test_connection(profile: str = "default") -> str:
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
                return json.dumps(
                    {"status": "error", "error": str(e), "profile": profile}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_get_environment_info(profile: str = "default") -> str:
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
                return json.dumps({"error": str(e), "profile": profile}, indent=2)

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
                client = await self.client_manager.get_client(profile)

                # Build query options
                from ..models import QueryOptions

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

        # Basic Metadata Tools
        @self.mcp.tool()
        async def d365fo_search_entities(
            pattern: str,
            entity_category: str = None,
            data_service_enabled: bool = None,
            data_management_enabled: bool = None,
            is_read_only: bool = None,
            limit: int = 100,
            profile: str = "default",
        ) -> str:
            """Search for D365 F&O data entities using simple keyword-based search. 

            IMPORTANT: When a user asks for something like "Get data management entities" or "Find customer group entities", break the request into individual keywords and perform MULTIPLE searches, then analyze all results:

            1. Extract individual keywords from the request (e.g. "data management entities" → "data", "management", "entities")
            2. Perform separate searches for each significant keyword using simple text matching
            3. Combine and analyze results from all searches
            4. Look for entities that match the combination of concepts

            SEARCH STRATEGY EXAMPLES:
            - "data management entities" → Search for "data", then "management", then find entities matching both concepts
            - "customer groups" → Search for "customer", then "group", then find intersection
            - "sales orders" → Search for "sales", then "order", then combine results

            Use simple keywords, not complex patterns. The search will find entities containing those keywords.

            Args:
                pattern: Simple keyword or text to search for in entity names. Use plain text keywords, not regex patterns. For multi-word requests like 'data management entities': 1) Break into keywords: 'data', 'management' 2) Search for each keyword separately: 'data' then 'management' 3) Run separate searches for each keyword 4) Analyze combined results. Examples: use 'customer' to find customer entities, 'group' to find group entities.
                entity_category: Filter entities by their functional category (e.g., Master, Transaction).
                data_service_enabled: Filter entities that are enabled for OData API access (e.g., for querying).
                data_management_enabled: Filter entities that can be used with the Data Management Framework (DMF).
                is_read_only: Filter entities based on whether they are read-only or support write operations.
                limit: Maximum number of matching entities to return. Use smaller values (10-50) for initial exploration, larger values (100-500) for comprehensive searches.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with matching entities
            """
            try:
                client = await self.client_manager.get_client(profile)

                start_time = time.time()

                # Use search_data_entities to support all the filtering options
                entities = await client.search_data_entities(
                    pattern=pattern,
                    entity_category=entity_category,
                    data_service_enabled=data_service_enabled,
                    data_management_enabled=data_management_enabled,
                    is_read_only=is_read_only,
                )

                # Convert DataEntityInfo objects to dictionaries for JSON serialization
                entity_dicts = []
                for entity in entities:
                    entity_dict = entity.to_dict()
                    entity_dicts.append(entity_dict)

                # Apply limit
                filtered_entities = entity_dicts
                if limit is not None:
                    filtered_entities = entity_dicts[:limit]

                # If no results and pattern seems specific, try a broader search for suggestions
                broader_suggestions = []
                fts_suggestions = []
                if len(filtered_entities) == 0:
                    try:
                        # Try FTS5 search if metadata cache is available
                        if hasattr(client, 'metadata_cache') and client.metadata_cache:
                            fts_suggestions = await self._try_fts_search(client, pattern)
                    except Exception:
                        pass  # Ignore errors in suggestion search

                search_time = time.time() - start_time

                # Add helpful guidance when no results found
                suggestions = []
                if len(filtered_entities) == 0:
                    suggestions = [
                        "Try broader or simpler keywords to increase matches.",
                        "Consider using category filters such as entity_category.",
                        "Use data_service_enabled=True to find API-accessible entities.",
                    ]

                    # Add FTS-specific suggestions if FTS results were found
                    if fts_suggestions:
                        suggestions.insert(
                            0,
                            f"Found {len(fts_suggestions)} entities using full-text search (see ftsMatches below)",
                        )
                    elif client.metadata_cache:
                        suggestions.append(
                            "Full-text search attempted but found no matches - try simpler terms"
                        )

                response = {
                    "entities": filtered_entities,
                    "totalCount": len(entities),
                    "returnedCount": len(filtered_entities),
                    "searchTime": round(search_time, 3),
                    "pattern": pattern,
                    "limit": limit,
                    "filters": {
                        "entity_Category": entity_category,
                        "data_Service_Enabled": data_service_enabled,
                        "data_Management_Enabled": data_management_enabled,
                        "is_Read_Only": is_read_only,
                    },
                    "suggestions": suggestions if suggestions else None,
                    "broaderMatches": broader_suggestions if broader_suggestions else None,
                    "ftsMatches": fts_suggestions if fts_suggestions else None,
                }

                return json.dumps(response, indent=2)

            except Exception as e:
                logger.error(f"Search entities failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_search_entities",
                    "arguments": {
                        "pattern": pattern,
                        "entity_category": entity_category,
                        "data_service_enabled": data_service_enabled,
                        "data_management_enabled": data_management_enabled,
                        "is_read_only": is_read_only,
                        "limit": limit,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        # Additional CRUD Tools
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
                client = await self.client_manager.get_client(profile)

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
                client = await self.client_manager.get_client(profile)

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
                client = await self.client_manager.get_client(profile)

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
                client = await self.client_manager.get_client(profile)

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

        # Additional Metadata Tools
        @self.mcp.tool()
        async def d365fo_get_entity_schema(
            entityName: str,
            include_properties: bool = True,
            resolve_labels: bool = True,
            language: str = "en-US",
            profile: str = "default",
        ) -> str:
            """Get the detailed schema for a specific D365 F&O data entity, including properties, keys, and available actions.

            Args:
                entityName: The public name of the entity (e.g., 'CustomersV3').
                include_properties: Set to true to include detailed information about each property (field) in the entity.
                resolve_labels: Set to true to resolve and include human-readable labels for the entity and its properties.
                language: The language to use for resolving labels (e.g., 'en-US', 'fr-FR').
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with entity schema
            """
            try:
                client = await self.client_manager.get_client(profile)

                entity_info = await client.get_public_entity_info(entityName)

                if not entity_info:
                    raise ValueError(f"Entity not found: {entityName}")

                logger.info(f"Retrieved entity info for {entity_info}")
                entity_info_dict = entity_info.to_dict()

                return json.dumps(entity_info_dict, indent=2)

            except Exception as e:
                logger.error(f"Get entity schema failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_get_entity_schema",
                    "arguments": {
                        "entityName": entityName,
                        "include_properties": include_properties,
                        "resolve_labels": resolve_labels,
                        "language": language,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_search_actions(
            pattern: str,
            entityName: str = None,
            bindingKind: str = None,
            isFunction: bool = None,
            limit: int = 100,
            profile: str = "default",
        ) -> str:
            """Search for available OData actions in D365 F&O using simple keyword-based search.

            IMPORTANT: When searching for actions, break down user requests into individual keywords and perform MULTIPLE searches:

            1. Extract keywords from requests (e.g., \"posting actions\" → \"post\", \"posting\")
            2. Perform separate searches for each keyword using simple text matching
            3. Combine and analyze results from all searches
            4. Look for actions that match the combination of concepts

            SEARCH STRATEGY EXAMPLES:
            - \"posting actions\" → Search for \"post\", then look for posting-related actions
            - \"validation functions\" → Search for \"valid\" and \"check\", then find validation actions
            - \"workflow actions\" → Search for \"workflow\" and \"approve\", then combine results

            Use simple keywords, not complex patterns. Actions are operations that can be performed on entities or globally.

            Args:
                pattern: Simple keyword or text to search for in action names. Use plain text keywords, not regex patterns. For requests like 'posting actions': 1) Extract keywords: 'post', 'posting' 2) Search for each keyword: 'post' 3) Perform multiple searches for related terms 4) Analyze combined results. Use simple text matching.
                entityName: Optional. Filter actions that are bound to a specific data entity (e.g., 'CustomersV3').
                bindingKind: Optional. Filter by binding type: 'Unbound' (can call directly), 'BoundToEntitySet' (operates on entity collections), 'BoundToEntityInstance' (requires specific entity key).
                isFunction: Optional. Filter by type: 'true' for functions (read-only), 'false' for actions (may have side-effects). Note: This filter may not be fully supported yet.
                limit: Maximum number of matching actions to return.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with matching actions
            """
            try:
                client = await self.client_manager.get_client(profile)

                start_time = time.time()

                # Extract search parameters
                entity_name = entityName
                binding_kind = bindingKind

                # Search actions with full details
                actions = await client.search_actions(
                    pattern=pattern, entity_name=entity_name, binding_kind=binding_kind
                )

                # Apply limit
                filtered_actions = actions[:limit] if limit is not None else actions

                # Convert ActionInfo objects to dictionaries for JSON serialization
                detailed_actions = []
                for action in filtered_actions:
                    action_dict = action.to_dict()

                    # Add additional metadata for better usability
                    action_dict.update(
                        {
                            "parameter_count": len(action.parameters),
                            "has_return_value": action.return_type is not None,
                            "return_type_name": (
                                action.return_type.type_name if action.return_type else None
                            ),
                            "is_bound": action.binding_kind != "Unbound",
                            "can_call_directly": action.binding_kind == "Unbound",
                            "requires_entity_key": action.binding_kind
                            == "BoundToEntityInstance",
                        }
                    )

                    detailed_actions.append(action_dict)

                search_time = time.time() - start_time

                response = {
                    "actions": detailed_actions,
                    "total_count": len(actions),
                    "returned_count": len(filtered_actions),
                    "search_time": round(search_time, 3),
                    "search_parameters": {
                        "pattern": pattern,
                        "entity_name": entity_name,
                        "binding_kind": binding_kind,
                        "limit": limit,
                    },
                    "summary": {
                        "unbound_actions": len(
                            [a for a in filtered_actions if a.binding_kind == "Unbound"]
                        ),
                        "entity_set_bound": len(
                            [
                                a
                                for a in filtered_actions
                                if a.binding_kind == "BoundToEntitySet"
                            ]
                        ),
                        "entity_instance_bound": len(
                            [
                                a
                                for a in filtered_actions
                                if a.binding_kind == "BoundToEntityInstance"
                            ]
                        ),
                        "unique_entities": len(
                            set(a.entity_name for a in filtered_actions if a.entity_name)
                        ),
                    },
                }

                return json.dumps(response, indent=2)

            except Exception as e:
                logger.error(f"Search actions failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_search_actions",
                    "arguments": {
                        "pattern": pattern,
                        "entityName": entityName,
                        "bindingKind": bindingKind,
                        "isFunction": isFunction,
                        "limit": limit,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_search_enumerations(
            pattern: str, limit: int = 100, profile: str = "default"
        ) -> str:
            """Search for enumerations (enums) in D365 F&O using simple keyword-based search.

            IMPORTANT: When searching for enumerations, break down user requests into individual keywords and perform MULTIPLE searches:

            1. Extract keywords from requests (e.g., \"customer status enums\" → \"customer\", \"status\")  
            2. Perform separate searches for each keyword using simple text matching
            3. Combine and analyze results from all searches
            4. Look for enums that match the combination of concepts

            SEARCH STRATEGY EXAMPLES:
            - \"customer status enums\" → Search for \"customer\", then \"status\", then find status-related customer enums
            - \"blocking reasons\" → Search for \"block\" and \"reason\", then combine results
            - \"approval states\" → Search for \"approval\" and \"state\", then find approval-related enums

            Use simple keywords, not complex patterns. Enums represent lists of named constants (e.g., NoYes, CustVendorBlocked).

            Args:
                pattern: Simple keyword or text to search for in enumeration names. Use plain text keywords, not regex patterns. For requests like 'customer blocking enums': 1) Extract keywords: 'customer', 'blocking' 2) Search for each keyword: 'customer' then 'blocking' 3) Perform multiple searches 4) Analyze combined results. Use simple text matching.
                limit: Maximum number of matching enumerations to return.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with matching enumerations
            """
            try:
                client = await self.client_manager.get_client(profile)

                start_time = time.time()

                # Search for enumerations using the pattern
                enumerations = await client.search_public_enumerations(
                    pattern=pattern
                )

                # Convert EnumerationInfo objects to dictionaries for JSON serialization
                enum_dicts = []
                for enum in enumerations:
                    enum_dict = enum.to_dict()
                    enum_dicts.append(enum_dict)

                # Apply limit
                filtered_enums = enum_dicts if limit is None else enum_dicts[:limit]
                search_time = time.time() - start_time

                response = {
                    "enumerations": filtered_enums,
                    "totalCount": len(enumerations),
                    "searchTime": round(search_time, 3),
                    "pattern": pattern,
                    "limit": limit,
                }

                return json.dumps(response, indent=2)

            except Exception as e:
                logger.error(f"Search enumerations failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_search_enumerations",
                    "arguments": {
                        "pattern": pattern,
                        "limit": limit,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_get_enumeration_fields(
            enumeration_name: str,
            resolve_labels: bool = True,
            language: str = "en-US",
            profile: str = "default",
        ) -> str:
            """Get the detailed members (fields) and their values for a specific D365 F&O enumeration.

            Args:
                enumeration_name: The exact name of the enumeration (e.g., 'NoYes', 'CustVendorBlocked').
                resolve_labels: Set to true to resolve and include human-readable labels for the enumeration and its members.
                language: The language to use for resolving labels (e.g., 'en-US', 'fr-FR').
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with enumeration details
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Get detailed enumeration information
                enum_info = await client.get_public_enumeration_info(
                    enumeration_name=enumeration_name,
                    resolve_labels=resolve_labels,
                    language=language,
                )

                if not enum_info:
                    raise ValueError(f"Enumeration not found: {enumeration_name}")

                # Convert to dictionary for JSON serialization
                enum_dict = enum_info.to_dict()

                # Add additional metadata
                response = {
                    "enumeration": enum_dict,
                    "memberCount": len(enum_info.members),
                    "hasLabels": bool(enum_info.label_text),
                    "language": language if resolve_labels else None,
                }

                return json.dumps(response, indent=2)

            except Exception as e:
                logger.error(f"Get enumeration fields failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_get_enumeration_fields",
                    "arguments": {
                        "enumeration_name": enumeration_name,
                        "resolve_labels": resolve_labels,
                        "language": language,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_get_installed_modules(profile: str = "default") -> str:
            """Get the list of installed modules in the D365 F&O environment with their details including name, version, module ID, publisher, and display name.

            Args:
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with installed modules
            """
            try:
                client = await self.client_manager.get_client(profile)
                logger.info("Getting installed modules from D365 F&O environment")

                # Get the list of installed modules
                modules = await client.get_installed_modules()

                # Convert to more structured format for better readability
                response = {
                    "modules": modules,
                    "moduleCount": len(modules),
                    "retrievedAt": f"{datetime.now().isoformat()}Z",
                }

                return json.dumps(response, indent=2)

            except Exception as e:
                logger.error(f"Get installed modules failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_get_installed_modules",
                    "arguments": {
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        # Label Tools
        @self.mcp.tool()
        async def d365fo_get_label(
            labelId: str,
            language: str = "en-US",
            fallbackToEnglish: bool = True,
            profile: str = "default",
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
                    fallback_to_english=fallbackToEnglish,
                )

                return json.dumps(
                    {"labelId": labelId, "language": language, "labelText": label_text},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get label failed: {e}")
                return json.dumps({"error": str(e), "labelId": labelId}, indent=2)

        @self.mcp.tool()
        async def d365fo_get_labels_batch(
            labelIds: List[str],
            language: str = "en-US",
            fallbackToEnglish: bool = True,
            profile: str = "default",
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
                    fallback_to_english=fallbackToEnglish,
                )

                return json.dumps(
                    {
                        "language": language,
                        "totalRequested": len(labelIds),
                        "labels": labels,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get labels batch failed: {e}")
                return json.dumps({"error": str(e), "labelIds": labelIds}, indent=2)

        # Profile Management Tools
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

        # Database Tools
        @self.mcp.tool()
        async def d365fo_execute_sql_query(
            query: str,
            limit: int = 100,
            format: str = "table",
            profile: str = "default",
        ) -> str:
            """Execute a SELECT query against the D365FO metadata database to get insights from cached metadata.

            IMPORTANT SAFETY NOTES:
            - Only SELECT queries are allowed (no INSERT, UPDATE, DELETE, DROP, etc.)
            - Query results are limited to 1000 rows maximum
            - Queries timeout after 30 seconds
            - Some sensitive tables may be restricted

            AVAILABLE TABLES AND THEIR PURPOSE:
            - metadata_environments: D365FO environments and their details
            - global_versions: Global version registry with hash and reference counts
            - environment_versions: Links between environments and global versions
            - data_entities: D365FO data entities metadata
            - public_entities: Public entity schemas and configurations
            - entity_properties: Detailed property information for entities
            - entity_actions: Available OData actions for entities
            - enumerations: System enumerations and their metadata
            - enumeration_members: Individual enumeration values and labels
            - metadata_search_v2: FTS5 search index for metadata

            EXAMPLE QUERIES:
            1. Get most used entities by category:
               SELECT entity_category, COUNT(*) as count FROM data_entities GROUP BY entity_category ORDER BY count DESC

            2. Find entities with most properties:
               SELECT pe.name, COUNT(ep.id) as property_count FROM public_entities pe LEFT JOIN entity_properties ep ON pe.id = ep.entity_id GROUP BY pe.id ORDER BY property_count DESC LIMIT 10

            3. Analyze environment versions:
               SELECT me.environment_name, gv.version_hash, ev.detected_at FROM metadata_environments me JOIN environment_versions ev ON me.id = ev.environment_id JOIN global_versions gv ON ev.global_version_id = gv.id

            Use this tool to analyze metadata patterns, generate reports, and gain insights into D365FO structure.

            Args:
                query: SQL SELECT query to execute. Must be a SELECT statement only. Query will be validated for safety before execution.
                limit: Maximum number of rows to return. Default is 100, maximum is 1000.
                format: Output format for results. 'table' for human-readable format, 'json' for structured data, 'csv' for spreadsheet-compatible format.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with query results
            """
            try:
                start_time = time.time()
                
                # Validate query safety
                self._validate_query_safety(query)
                
                # Get database path
                db_path = await self._get_database_path(profile)
                
                # Execute query
                columns, rows = await self._execute_safe_query(query, db_path, limit)
                
                # Format results
                formatted_results = self._format_query_results(columns, rows, format)
                
                execution_time = time.time() - start_time
                
                # Add metadata
                metadata = {
                    "query": query,
                    "execution_time_seconds": round(execution_time, 3),
                    "row_count": len(rows),
                    "column_count": len(columns),
                    "format": format,
                    "limited_results": limit < 1000 and len(rows) == limit,
                }
                
                if format == "table":
                    response = f"Query Results:\n{formatted_results}\n\nExecution Metadata:\n{json.dumps(metadata, indent=2)}"
                else:
                    # For JSON/CSV, include metadata in structured format
                    if format == "json":
                        parsed_results = json.loads(formatted_results)
                        parsed_results["metadata"] = metadata
                        response = json.dumps(parsed_results, indent=2)
                    else:
                        response = formatted_results + f"\n\n# Metadata: {json.dumps(metadata)}"
                
                return response

            except Exception as e:
                logger.error(f"SQL query execution failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_execute_sql_query",
                    "arguments": {
                        "query": query,
                        "limit": limit,
                        "format": format,
                        "profile": profile
                    },
                    "error_type": type(e).__name__,
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_get_database_schema(
            table_name: str = None,
            include_statistics: bool = True,
            include_indexes: bool = True,
            include_relationships: bool = True,
            profile: str = "default",
        ) -> str:
            """Get comprehensive schema information for the D365FO metadata database.

            This tool provides detailed information about:
            - All database tables and their structures
            - Column definitions with types and constraints
            - Indexes and their purposes
            - Foreign key relationships
            - Table statistics (row counts, sizes)
            - FTS5 virtual table information

            Use this tool to understand the database structure before writing SQL queries.

            Args:
                table_name: Optional. Get schema for a specific table only. If omitted, returns schema for all tables.
                include_statistics: Include table statistics like row counts and sizes.
                include_indexes: Include index information for tables.
                include_relationships: Include foreign key relationships between tables.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with database schema
            """
            try:
                db_path = await self._get_database_path(profile)
                
                schema_info = await self._get_schema_info(
                    db_path, table_name, include_statistics, include_indexes, include_relationships
                )
                
                return json.dumps(schema_info, indent=2)

            except Exception as e:
                logger.error(f"Get database schema failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_get_database_schema",
                    "arguments": {
                        "table_name": table_name,
                        "include_statistics": include_statistics,
                        "include_indexes": include_indexes,
                        "include_relationships": include_relationships,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_get_table_info(
            table_name: str,
            include_sample_data: bool = False,
            include_relationships: bool = True,
            profile: str = "default",
        ) -> str:
            """Get detailed information about a specific database table including:
            - Column definitions with types, nullability, and defaults
            - Primary and foreign key constraints
            - Indexes and their characteristics
            - Table statistics (row count, size, last updated)
            - Sample data (first few rows)
            - Relationships to other tables

            This tool is useful for exploring specific tables before writing queries.

            Args:
                table_name: Name of the table to get information about (e.g., 'data_entities', 'public_entities', 'entity_properties').
                include_sample_data: Include sample data from the table (first 5 rows).
                include_relationships: Include information about relationships to other tables.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with table information
            """
            try:
                db_path = await self._get_database_path(profile)
                
                table_info = await self._get_detailed_table_info(
                    db_path, table_name, include_sample_data, include_relationships
                )
                
                return json.dumps(table_info, indent=2)

            except Exception as e:
                logger.error(f"Get table info failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_get_table_info",
                    "arguments": {
                        "table_name": table_name,
                        "include_sample_data": include_sample_data,
                        "include_relationships": include_relationships,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        @self.mcp.tool()
        async def d365fo_get_database_statistics(
            include_table_stats: bool = True,
            include_version_stats: bool = True,
            include_performance_stats: bool = True,
            profile: str = "default",
        ) -> str:
            """Get comprehensive database statistics and analytics including:
            - Overall database size and table counts
            - Record counts by table
            - Global version statistics
            - Environment statistics
            - Cache hit rates and performance metrics
            - Storage utilization analysis
            - Data distribution insights

            Use this tool to understand the overall state and health of the metadata database.

            Args:
                include_table_stats: Include per-table statistics (row counts, sizes).
                include_version_stats: Include global version and environment statistics.
                include_performance_stats: Include cache performance and query statistics.
                profile: Configuration profile to use (optional - uses default profile if not specified)

            Returns:
                JSON string with database statistics
            """
            try:
                # Get database statistics using existing method
                client = await self.client_manager.get_client(profile)
                if hasattr(client, 'metadata_cache') and hasattr(client.metadata_cache, 'database'):
                    stats = await client.metadata_cache.database.get_database_statistics()
                else:
                    raise ValueError("Database statistics not available for this profile")
                
                # Enhance with additional statistics if requested
                if include_table_stats or include_version_stats:
                    db_path = await self._get_database_path(profile)
                    additional_stats = await self._get_enhanced_statistics(
                        db_path, include_table_stats, include_version_stats, include_performance_stats
                    )
                    stats.update(additional_stats)
                
                return json.dumps(stats, indent=2)

            except Exception as e:
                logger.error(f"Get database statistics failed: {e}")
                error_response = {
                    "error": str(e),
                    "tool": "d365fo_get_database_statistics",
                    "arguments": {
                        "include_table_stats": include_table_stats,
                        "include_version_stats": include_version_stats,
                        "include_performance_stats": include_performance_stats,
                        "profile": profile
                    },
                }
                return json.dumps(error_response, indent=2)

        # Sync Tools
        @self.mcp.tool()
        async def d365fo_start_sync(
            strategy: str = "full_without_labels",
            global_version_id: int = None,
            profile: str = "default",
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
                    strategy=strategy, global_version_id=global_version_id
                )

                return json.dumps(
                    {"sessionId": session_id, "strategy": strategy, "started": True},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Start sync failed: {e}")
                return json.dumps(
                    {"error": str(e), "strategy": strategy, "started": False}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_get_sync_progress(
            session_id: str, profile: str = "default"
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

                return json.dumps(
                    {"sessionId": session_id, "progress": progress}, indent=2
                )

            except Exception as e:
                logger.error(f"Get sync progress failed: {e}")
                return json.dumps({"error": str(e), "sessionId": session_id}, indent=2)

        @self.mcp.tool()
        async def d365fo_cancel_sync(session_id: str, profile: str = "default") -> str:
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

                return json.dumps(
                    {
                        "sessionId": session_id,
                        "cancelled": result.get("cancelled", False),
                        "message": result.get("message", ""),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Cancel sync failed: {e}")
                return json.dumps(
                    {"error": str(e), "sessionId": session_id, "cancelled": False},
                    indent=2,
                )

        @self.mcp.tool()
        async def d365fo_list_sync_sessions(profile: str = "default") -> str:
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

                return json.dumps(
                    {"totalSessions": len(sessions), "sessions": sessions}, indent=2
                )

            except Exception as e:
                logger.error(f"List sync sessions failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.tool()
        async def d365fo_get_sync_history(
            limit: int = 20, profile: str = "default"
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

                return json.dumps(
                    {"limit": limit, "totalReturned": len(history), "history": history},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get sync history failed: {e}")
                return json.dumps({"error": str(e), "limit": limit}, indent=2)

        # Performance and Health Monitoring Tools
        @self.mcp.tool()
        async def d365fo_get_server_performance() -> str:
            """Get FastMCP server performance statistics and health metrics.

            Returns:
                JSON string with server performance data
            """
            try:
                performance_stats = self.get_performance_stats()

                # Add client manager health stats
                client_health = await self.client_manager.health_check()

                return json.dumps(
                    {
                        "server_performance": performance_stats,
                        "client_health": client_health,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get server performance failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.tool()
        async def d365fo_reset_performance_stats() -> str:
            """Reset server performance statistics.

            Returns:
                JSON string with reset confirmation
            """
            try:
                # Reset performance stats
                self._request_stats = {
                    "total_requests": 0,
                    "total_errors": 0,
                    "avg_response_time": 0.0,
                    "last_reset": datetime.now(),
                }
                self._request_times = []
                self._connection_pool_stats = {
                    "active_connections": 0,
                    "peak_connections": 0,
                    "connection_errors": 0,
                    "pool_hits": 0,
                    "pool_misses": 0,
                }

                # Clean up expired sessions
                self._cleanup_expired_sessions()

                return json.dumps(
                    {
                        "performance_stats_reset": True,
                        "reset_timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Reset performance stats failed: {e}")
                return json.dumps(
                    {"error": str(e), "reset_successful": False}, indent=2
                )

        @self.mcp.tool()
        async def d365fo_get_server_config() -> str:
            """Get current FastMCP server configuration and feature status.

            Returns:
                JSON string with server configuration
            """
            try:
                config_info = {
                    "server_version": __version__,
                    "stateless_mode": self._stateless_mode,
                    "json_response_mode": self._json_response_mode,
                    "max_concurrent_requests": self._max_concurrent_requests,
                    "request_timeout": self._request_timeout,
                    "batch_size": self._batch_size,
                    "transport_config": self.config.get("server", {}).get(
                        "transport", {}
                    ),
                    "performance_config": self.config.get("performance", {}),
                    "cache_config": self.config.get("cache", {}),
                    "security_config": self.config.get("security", {}),
                }

                return json.dumps(
                    {
                        "server_config": config_info,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get server config failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        logger.info(
            "Registered all D365FO tools with FastMCP (including performance monitoring)"
        )

    def _performance_monitor(self, func):
        """Decorator to monitor performance of tool executions."""

        async def wrapper(*args, **kwargs):
            start_time = time.time()

            # Increment request counter
            self._request_stats["total_requests"] += 1

            # Apply request limiting
            async with self._request_semaphore:
                try:
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=self._request_timeout
                    )

                    # Record successful execution time
                    execution_time = time.time() - start_time
                    self._record_request_time(execution_time)

                    return result

                except asyncio.TimeoutError:
                    self._request_stats["total_errors"] += 1
                    logger.error(
                        f"Tool execution timeout after {self._request_timeout}s: {func.__name__}"
                    )
                    return json.dumps(
                        {
                            "error": f"Request timeout after {self._request_timeout} seconds",
                            "tool": func.__name__,
                            "timeout": self._request_timeout,
                        },
                        indent=2,
                    )

                except Exception as e:
                    self._request_stats["total_errors"] += 1
                    execution_time = time.time() - start_time
                    self._record_request_time(execution_time)
                    logger.error(f"Tool execution error in {func.__name__}: {e}")
                    raise

        return wrapper

    def _record_request_time(self, execution_time: float):
        """Record request execution time for performance monitoring."""
        self._request_times.append(execution_time)

        # Keep only recent request times to prevent memory bloat
        if len(self._request_times) > self._max_request_history:
            self._request_times = self._request_times[-self._max_request_history :]

        # Update average response time
        if self._request_times:
            self._request_stats["avg_response_time"] = sum(self._request_times) / len(
                self._request_times
            )

    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        uptime = datetime.now() - self._request_stats["last_reset"]

        stats = {
            "server_uptime_seconds": uptime.total_seconds(),
            "total_requests": self._request_stats["total_requests"],
            "total_errors": self._request_stats["total_errors"],
            "error_rate": (
                self._request_stats["total_errors"]
                / max(1, self._request_stats["total_requests"])
            )
            * 100,
            "avg_response_time_ms": self._request_stats["avg_response_time"] * 1000,
            "current_active_requests": self._max_concurrent_requests
            - self._request_semaphore._value,
            "max_concurrent_requests": self._max_concurrent_requests,
            "connection_pool_stats": self._connection_pool_stats.copy(),
            "stateless_mode": self._stateless_mode,
            "json_response_mode": self._json_response_mode,
        }

        if self._request_times:
            stats.update(
                {
                    "min_response_time_ms": min(self._request_times) * 1000,
                    "max_response_time_ms": max(self._request_times) * 1000,
                    "p95_response_time_ms": self._calculate_percentile(
                        self._request_times, 95
                    )
                    * 1000,
                    "recent_request_count": len(self._request_times),
                }
            )

        return stats

    def _calculate_percentile(self, values: list, percentile: float) -> float:
        """Calculate percentile for a list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c

    async def _try_fts_search(self, client, pattern: str) -> List[dict]:
        """Try FTS5 full-text search when regex search fails

        Args:
            client: FOClient instance with metadata cache
            pattern: Original search pattern

        Returns:
            List of entity dictionaries from FTS search
        """
        try:
            # Import here to avoid circular imports
            from ...metadata_v2 import VersionAwareSearchEngine
            from ...models import SearchQuery

            # Create search engine if metadata cache is available (V2)
            if not hasattr(client, "metadata_cache") or not client.metadata_cache:
                return []

            # Always use V2 search engine (legacy has been removed)
            if hasattr(client.metadata_cache, "create_search_engine"):
                # V2 cache - use the convenient factory method
                search_engine = client.metadata_cache.create_search_engine()
            else:
                # Fallback - create directly (in case factory method isn't available)
                search_engine = VersionAwareSearchEngine(client.metadata_cache)

            # Extract search terms from regex pattern
            search_text = self._extract_search_terms(pattern)
            if not search_text:
                return []

            # Create search query for data entities
            query = SearchQuery(
                text=search_text,
                entity_types=["data_entity"],
                limit=5,  # Limit FTS suggestions
                use_fulltext=True,
            )

            # Execute FTS search
            fts_results = await search_engine.search(query)

            # Convert search results to entity info
            fts_entities = []
            for result in fts_results.results:
                try:
                    # Get full entity info for each FTS result
                    entity_info = await client.get_data_entity_info(result.name)
                    if entity_info:
                        entity_dict = entity_info.to_dict()
                        # Add FTS metadata
                        entity_dict["fts_relevance"] = result.relevance
                        entity_dict["fts_snippet"] = result.snippet
                        fts_entities.append(entity_dict)
                except Exception:
                    # If entity info retrieval fails, skip this result
                    continue

            return fts_entities

        except Exception as e:
            logger.debug(f"FTS search failed: {e}")
            return []

    def _extract_search_terms(self, pattern: str) -> str:
        """Extract meaningful search terms from regex pattern

        Args:
            pattern: Regex pattern to extract terms from

        Returns:
            Space-separated search terms
        """
        import re

        # Remove regex operators and extract word-like terms
        # First, handle character classes like [Cc] -> C, [Gg] -> G
        cleaned = re.sub(
            r"\[([A-Za-z])\1\]",
            r"\1",
            pattern.replace("[Cc]", "C").replace("[Gg]", "G"),
        )

        # Remove other regex characters
        cleaned = re.sub(r"[.*\\{}()|^$+?]", " ", cleaned)

        # Extract words (sequences of letters, minimum 3 chars)
        words = re.findall(r"[A-Za-z]{3,}", cleaned)

        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen and len(word) >= 3:
                seen.add(word_lower)
                unique_words.append(word)

        return " ".join(unique_words[:3])  # Limit to first 3 unique terms

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
                    entity_name, options=QueryOptions(top=5)
                )

                return json.dumps(
                    {
                        "entity_name": entity_name,
                        "schema": schema,
                        "sample_data": sample_data.get("value", []),
                        "sample_count": len(sample_data.get("value", [])),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Entity resource failed for {entity_name}: {e}")
                return json.dumps(
                    {"error": str(e), "entity_name": entity_name}, indent=2
                )

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

                return json.dumps(
                    {
                        "connection_status": connection_result,
                        "environment_info": env_info,
                        "server_version": __version__,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Environment status resource failed: {e}")
                return json.dumps(
                    {"error": str(e), "server_version": __version__}, indent=2
                )

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

                return json.dumps(
                    {
                        "environment_version": version_info,
                        "server_version": __version__,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Environment version resource failed: {e}")
                return json.dumps(
                    {"error": str(e), "server_version": __version__}, indent=2
                )

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
                    "cache_directory": self.config.get("cache", {}).get(
                        "metadata_cache_dir", ""
                    ),
                    "label_cache_enabled": self.config.get("cache", {}).get(
                        "use_label_cache", True
                    ),
                    "label_cache_expiry": self.config.get("cache", {}).get(
                        "label_cache_expiry_minutes", 120
                    ),
                }

                return json.dumps(
                    {"cache_info": cache_info, "server_version": __version__}, indent=2
                )

            except Exception as e:
                logger.error(f"Environment cache resource failed: {e}")
                return json.dumps(
                    {"error": str(e), "server_version": __version__}, indent=2
                )

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
                entities = await client.search_data_entities(pattern="")
                entities = entities[:1000]  # Limit to prevent huge responses

                return json.dumps(
                    {
                        "total_entities": len(entities),
                        "entities": entities,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Metadata entities resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.resource("d365fo://metadata/actions")
        async def metadata_actions_resource() -> str:
            """Get comprehensive list of D365FO OData actions.

            Returns:
                JSON containing all available OData actions
            """
            try:
                client = await self.client_manager.get_client()

                # Get all actions (limit to prevent huge responses)
                actions = await client.search_actions(pattern="", limit=1000)

                return json.dumps(
                    {
                        "total_actions": len(actions),
                        "actions": actions,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Metadata actions resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        @self.mcp.resource("d365fo://metadata/enumerations")
        async def metadata_enumerations_resource() -> str:
            """Get comprehensive list of D365FO enumerations.

            Returns:
                JSON containing all available enumerations
            """
            try:
                client = await self.client_manager.get_client()

                # Get all enumerations (limit to prevent huge responses)
                enums = await client.search_enumerations(pattern="", limit=1000)

                return json.dumps(
                    {
                        "total_enumerations": len(enums),
                        "enumerations": enums,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Metadata enumerations resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

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
                        label_info.append(
                            {
                                "label_id": label_id,
                                "label_text": label_text,
                                "resolved": True,
                            }
                        )
                    except:
                        label_info.append(
                            {
                                "label_id": label_id,
                                "label_text": None,
                                "resolved": False,
                            }
                        )

                return json.dumps(
                    {
                        "label_system_active": True,
                        "sample_labels": label_info,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Metadata labels resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

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
                    include_statistics=True,
                )

                return json.dumps(
                    {
                        "database_schema": schema,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Database schema resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

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
                    include_performance_stats=True,
                )

                return json.dumps(
                    {
                        "database_statistics": stats,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Database statistics resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

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
                    limit=100,
                )

                return json.dumps(
                    {
                        "database_tables": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Database tables resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

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
                    limit=100,
                )

                return json.dumps(
                    {
                        "database_indexes": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Database indexes resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

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
                    limit=100,
                )

                return json.dumps(
                    {
                        "database_relationships": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Database relationships resource failed: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        logger.info("Registered all D365FO resources with FastMCP")

    def _register_prompts(self):
        """Register D365FO prompts using FastMCP decorators."""

        @self.mcp.prompt()
        async def d365fo_sequence_analysis(
            analysis_type: str = "comprehensive",
            scope: str = "company",
            entity_filter: str = None,
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
            action_name: str, entity_name: str = None, action_type: str = "discovery"
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

    def _get_session_context(self, session_id: str = None) -> dict:
        """Get or create session context for stateless operations."""
        if not self._stateless_mode:
            # In stateful mode, return shared context
            return {"shared": True, "created_at": datetime.now()}

        # In stateless mode, each request should be independent
        if session_id and session_id in self._stateless_sessions:
            session = self._stateless_sessions[session_id]
            session.last_accessed = datetime.now()
            return session.to_dict()
        else:
            # Create new session context
            if not session_id:
                session_id = f"stateless_{int(time.time())}_{os.getpid()}"

            session_context = SessionContext(session_id)

            if session_id:
                self._stateless_sessions[session_id] = session_context

            return session_context.to_dict()

    def _cleanup_expired_sessions(self):
        """Clean up expired stateless sessions."""
        if not self._stateless_mode:
            return

        current_time = datetime.now()
        session_timeout = timedelta(minutes=30)  # 30 minute session timeout

        expired_sessions = []
        for session_id, session in self._stateless_sessions.items():
            if current_time - session.last_accessed > session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            try:
                del self._stateless_sessions[session_id]
                logger.debug(f"Cleaned up expired session: {session_id}")
            except KeyError:
                pass  # Session already removed

        if expired_sessions:
            logger.info(
                f"Cleaned up {len(expired_sessions)} expired stateless sessions"
            )

    def run(self, transport: Literal["stdio", "sse", "streamable-http"] = "stdio"):
        """Run the FastMCP server with specified transport.

        Args:
            transport: Transport protocol to use
        """

        async def _run_async():
            try:
                logger.info(
                    f"Starting FastD365FOMCPServer v{__version__} with {transport} transport..."
                )

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
            raise RuntimeError(
                "run() should not be called from async context. Use run_async() instead."
            )
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            asyncio.run(_run_async())

    async def run_async(
        self, transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    ):
        """Run the FastMCP server with specified transport (async version).

        Args:
            transport: Transport protocol to use
        """
        try:
            logger.info(
                f"Starting FastD365FOMCPServer v{__version__} with {transport} transport..."
            )

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
                logger.info(
                    "No environment variables configured - use profile management tools to configure D365FO connections"
                )

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

        # Start background tasks for production features
        if self._stateless_mode:
            # Schedule periodic cleanup of expired sessions
            asyncio.create_task(self._periodic_session_cleanup())

    async def _periodic_session_cleanup(self):
        """Periodic cleanup task for stateless sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")

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
                logger.info(
                    f"Application version: {env_info['versions']['application']}"
                )
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
                logger.warning(
                    "Cannot create default profile - D365FO_BASE_URL not set"
                )
                return

            # Determine authentication mode
            startup_mode = self.config.get("startup_mode", "profile_only")
            client_id = os.getenv("D365FO_CLIENT_ID")
            client_secret = os.getenv("D365FO_CLIENT_SECRET")
            tenant_id = os.getenv("D365FO_TENANT_ID")

            if startup_mode == "client_credentials":
                auth_mode = "client_credentials"
                if not all([client_id, client_secret, tenant_id]):
                    logger.error(
                        "Client credentials mode requires D365FO_CLIENT_ID, D365FO_CLIENT_SECRET, and D365FO_TENANT_ID"
                    )
                    return
            else:
                auth_mode = "default"

            # Create default profile
            profile_name = "default-from-env"
            existing_profile = self.profile_manager.get_profile(profile_name)
            if existing_profile:
                logger.info(
                    f"Profile '{profile_name}' already exists, setting as default"
                )
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
                credential_source=credential_source,
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

            # Clean up client manager
            await self.client_manager.cleanup()

            # Clean up stateless sessions
            if hasattr(self, "_stateless_sessions"):
                self._stateless_sessions.clear()

            # Log final performance stats
            if hasattr(self, "_request_stats"):
                final_stats = self.get_performance_stats()
                logger.info(
                    f"Final server stats: {final_stats['total_requests']} requests, "
                    f"{final_stats['total_errors']} errors, "
                    f"{final_stats['avg_response_time_ms']:.2f}ms avg response time"
                )

            logger.info("FastD365FOMCPServer cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration for FastMCP server.

        Returns:
            Default configuration dictionary
        """
        base_url = os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        )

        # Determine startup mode based on environment variables
        startup_mode = "profile_only"
        if (
            base_url
            and base_url != "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        ):
            if all(
                [
                    os.getenv("D365FO_CLIENT_ID"),
                    os.getenv("D365FO_CLIENT_SECRET"),
                    os.getenv("D365FO_TENANT_ID"),
                ]
            ):
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
                    "stdio": {"enabled": True},
                    "sse": {
                        "enabled": True,
                        "host": "127.0.0.1",
                        "port": int(os.getenv("MCP_SSE_PORT", "8000")),
                        "cors": {
                            "enabled": True,
                            "origins": ["*"],
                            "methods": ["GET", "POST"],
                            "headers": ["*"],
                        },
                    },
                    "http": {
                        "enabled": True,
                        "host": os.getenv("MCP_HTTP_HOST", "127.0.0.1"),
                        "port": int(os.getenv("MCP_HTTP_PORT", "8000")),
                        "stateless": os.getenv("MCP_HTTP_STATELESS", "").lower()
                        in ("true", "1", "yes"),
                        "json_response": os.getenv("MCP_HTTP_JSON", "").lower()
                        in ("true", "1", "yes"),
                        "cors": {
                            "enabled": True,
                            "origins": ["*"],
                            "methods": ["GET", "POST", "DELETE"],
                            "headers": ["*"],
                        },
                    },
                },
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
                "max_concurrent_requests": int(
                    os.getenv("MCP_MAX_CONCURRENT_REQUESTS", "10")
                ),
                "connection_pool_size": int(os.getenv("MCP_CONNECTION_POOL_SIZE", "5")),
                "request_timeout": int(os.getenv("MCP_REQUEST_TIMEOUT", "30")),
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
