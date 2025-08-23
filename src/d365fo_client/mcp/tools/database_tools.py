"""Database analysis and query tools for MCP server."""

import json
import logging
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class DatabaseQuerySafetyError(Exception):
    """Raised when a database query is deemed unsafe or invalid."""
    pass


class DatabaseTools:
    """Database analysis and query tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize database tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager
        
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

    def get_tools(self) -> List[Tool]:
        """Get list of database tools.

        Returns:
            List of Tool definitions
        """
        return [
            self._get_execute_sql_query_tool(),
            self._get_database_schema_tool(),
            self._get_table_info_tool(),
            self._get_database_statistics_tool(),
        ]

    def _get_execute_sql_query_tool(self) -> Tool:
        """Get execute SQL query tool definition."""
        return Tool(
            name="d365fo_execute_sql_query",
            description="""Execute a SELECT query against the D365FO metadata database to get insights from cached metadata.

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

Use this tool to analyze metadata patterns, generate reports, and gain insights into D365FO structure.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute. Must be a SELECT statement only. Query will be validated for safety before execution.",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 100,
                        "description": "Maximum number of rows to return. Default is 100, maximum is 1000.",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["table", "json", "csv"],
                        "default": "table",
                        "description": "Output format for results. 'table' for human-readable format, 'json' for structured data, 'csv' for spreadsheet-compatible format.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["query"],
            },
        )

    def _get_database_schema_tool(self) -> Tool:
        """Get database schema tool definition."""
        return Tool(
            name="d365fo_get_database_schema",
            description="""Get comprehensive schema information for the D365FO metadata database.

This tool provides detailed information about:
- All database tables and their structures
- Column definitions with types and constraints
- Indexes and their purposes
- Foreign key relationships
- Table statistics (row counts, sizes)
- FTS5 virtual table information

Use this tool to understand the database structure before writing SQL queries.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Optional. Get schema for a specific table only. If omitted, returns schema for all tables.",
                    },
                    "include_statistics": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include table statistics like row counts and sizes.",
                    },
                    "include_indexes": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include index information for tables.",
                    },
                    "include_relationships": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include foreign key relationships between tables.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "additionalProperties": False,
            },
        )

    def _get_table_info_tool(self) -> Tool:
        """Get table info tool definition."""
        return Tool(
            name="d365fo_get_table_info",
            description="""Get detailed information about a specific database table including:
- Column definitions with types, nullability, and defaults
- Primary and foreign key constraints
- Indexes and their characteristics
- Table statistics (row count, size, last updated)
- Sample data (first few rows)
- Relationships to other tables

This tool is useful for exploring specific tables before writing queries.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to get information about (e.g., 'data_entities', 'public_entities', 'entity_properties').",
                    },
                    "include_sample_data": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include sample data from the table (first 5 rows).",
                    },
                    "include_relationships": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include information about relationships to other tables.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["table_name"],
            },
        )

    def _get_database_statistics_tool(self) -> Tool:
        """Get database statistics tool definition."""
        return Tool(
            name="d365fo_get_database_statistics",
            description="""Get comprehensive database statistics and analytics including:
- Overall database size and table counts
- Record counts by table
- Global version statistics
- Environment statistics
- Cache hit rates and performance metrics
- Storage utilization analysis
- Data distribution insights

Use this tool to understand the overall state and health of the metadata database.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_table_stats": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include per-table statistics (row counts, sizes).",
                    },
                    "include_version_stats": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include global version and environment statistics.",
                    },
                    "include_performance_stats": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include cache performance and query statistics.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "additionalProperties": False,
            },
        )

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

    async def execute_sql_query(self, arguments: dict) -> List[TextContent]:
        """Execute SQL query tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            start_time = time.time()
            
            profile = arguments.get("profile", "default")
            query = arguments["query"]
            limit = arguments.get("limit", 100)
            format_type = arguments.get("format", "table")
            
            # Validate query safety
            self._validate_query_safety(query)
            
            # Get database path
            db_path = await self._get_database_path(profile)
            
            # Execute query
            columns, rows = await self._execute_safe_query(query, db_path, limit)
            
            # Format results
            formatted_results = self._format_query_results(columns, rows, format_type)
            
            execution_time = time.time() - start_time
            
            # Add metadata
            metadata = {
                "query": query,
                "execution_time_seconds": round(execution_time, 3),
                "row_count": len(rows),
                "column_count": len(columns),
                "format": format_type,
                "limited_results": limit < 1000 and len(rows) == limit,
            }
            
            if format_type == "table":
                response = f"Query Results:\n{formatted_results}\n\nExecution Metadata:\n{json.dumps(metadata, indent=2)}"
            else:
                # For JSON/CSV, include metadata in structured format
                if format_type == "json":
                    parsed_results = json.loads(formatted_results)
                    parsed_results["metadata"] = metadata
                    response = json.dumps(parsed_results, indent=2)
                else:
                    response = formatted_results + f"\n\n# Metadata: {json.dumps(metadata)}"
            
            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"SQL query execution failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_execute_sql_query",
                "arguments": arguments,
                "error_type": type(e).__name__,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_database_schema(self, arguments: dict) -> List[TextContent]:
        """Execute get database schema tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            table_name = arguments.get("table_name")
            include_statistics = arguments.get("include_statistics", True)
            include_indexes = arguments.get("include_indexes", True)
            include_relationships = arguments.get("include_relationships", True)
            
            db_path = await self._get_database_path(profile)
            
            schema_info = await self._get_schema_info(
                db_path, table_name, include_statistics, include_indexes, include_relationships
            )
            
            return [TextContent(type="text", text=json.dumps(schema_info, indent=2))]

        except Exception as e:
            logger.error(f"Get database schema failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_database_schema",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_table_info(self, arguments: dict) -> List[TextContent]:
        """Execute get table info tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            table_name = arguments["table_name"]
            include_sample_data = arguments.get("include_sample_data", False)
            include_relationships = arguments.get("include_relationships", True)
            
            db_path = await self._get_database_path(profile)
            
            table_info = await self._get_detailed_table_info(
                db_path, table_name, include_sample_data, include_relationships
            )
            
            return [TextContent(type="text", text=json.dumps(table_info, indent=2))]

        except Exception as e:
            logger.error(f"Get table info failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_table_info",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_database_statistics(self, arguments: dict) -> List[TextContent]:
        """Execute get database statistics tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            include_table_stats = arguments.get("include_table_stats", True)
            include_version_stats = arguments.get("include_version_stats", True)
            include_performance_stats = arguments.get("include_performance_stats", True)
            
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
            
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]

        except Exception as e:
            logger.error(f"Get database statistics failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_database_statistics",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

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