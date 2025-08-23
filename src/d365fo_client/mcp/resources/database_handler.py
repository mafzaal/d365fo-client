"""Database resource handler for MCP server."""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List

from mcp.types import Resource

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class DatabaseResourceHandler:
    """Handles database resources for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize the database resource handler.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    async def list_resources(self) -> List[Resource]:
        """List available database resources.

        Returns:
            List of database resources
        """
        resources = [
            Resource(
                uri="d365fo://database/schema",
                name="Database Schema",
                description="Complete database schema with tables, columns, indexes, and relationships",
                mimeType="application/json",
            ),
            Resource(
                uri="d365fo://database/statistics",
                name="Database Statistics",
                description="Database performance statistics, table sizes, and utilization metrics",
                mimeType="application/json",
            ),
            Resource(
                uri="d365fo://database/tables",
                name="Database Tables",
                description="List of all database tables with basic information",
                mimeType="application/json",
            ),
            Resource(
                uri="d365fo://database/indexes",
                name="Database Indexes",
                description="All database indexes and their characteristics",
                mimeType="application/json",
            ),
            Resource(
                uri="d365fo://database/relationships",
                name="Database Relationships",
                description="Foreign key relationships between tables",
                mimeType="application/json",
            ),
        ]

        # Add individual table resources
        try:
            # Get list of tables from database
            client = await self.client_manager.get_client()
            if hasattr(client, 'metadata_cache') and client.metadata_cache:
                table_names = await self._get_table_names(client.metadata_cache.db_path)
                
                for table_name in table_names:
                    resources.append(
                        Resource(
                            uri=f"d365fo://database/tables/{table_name}",
                            name=f"Table: {table_name}",
                            description=f"Detailed schema and information for table {table_name}",
                            mimeType="application/json",
                        )
                    )
        except Exception as e:
            logger.warning(f"Could not load table list for resources: {e}")

        logger.info(f"Listed {len(resources)} database resources")
        return resources

    async def read_resource(self, uri: str) -> str:
        """Read specific database resource.

        Args:
            uri: Resource URI

        Returns:
            JSON string with database resource content
        """
        try:
            if uri == "d365fo://database/schema":
                return await self._get_complete_schema()
            elif uri == "d365fo://database/statistics":
                return await self._get_database_statistics()
            elif uri == "d365fo://database/tables":
                return await self._get_tables_list()
            elif uri == "d365fo://database/indexes":
                return await self._get_indexes_info()
            elif uri == "d365fo://database/relationships":
                return await self._get_relationships_info()
            elif uri.startswith("d365fo://database/tables/"):
                table_name = uri.split("/")[-1]
                return await self._get_table_details(table_name)
            else:
                raise ValueError(f"Unknown database resource URI: {uri}")
        except Exception as e:
            logger.error(f"Failed to read database resource {uri}: {e}")
            error_content = {
                "error": str(e),
                "uri": uri,
                "timestamp": datetime.utcnow().isoformat(),
                "resource_type": "database"
            }
            return json.dumps(error_content, indent=2)

    async def _get_table_names(self, db_path: str) -> List[str]:
        """Get list of table names from database."""
        import aiosqlite
        
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row[0] for row in await cursor.fetchall()]

    async def _get_complete_schema(self) -> str:
        """Get complete database schema resource."""
        try:
            client = await self.client_manager.get_client()
            if not hasattr(client, 'metadata_cache') or not client.metadata_cache:
                raise ValueError("No metadata database available")

            db_path = str(client.metadata_cache.db_path)
            
            import aiosqlite
            
            async with aiosqlite.connect(db_path) as db:
                schema_info = {
                    "database_path": db_path,
                    "generated_at": datetime.utcnow().isoformat(),
                    "tables": {},
                    "summary": {
                        "total_tables": 0,
                        "total_columns": 0,
                        "total_indexes": 0,
                        "total_foreign_keys": 0
                    }
                }
                
                # Get all tables
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                table_names = [row[0] for row in await cursor.fetchall()]
                schema_info["summary"]["total_tables"] = len(table_names)
                
                # Get detailed info for each table
                for table_name in table_names:
                    table_info = await self._get_table_schema_info(db, table_name)
                    schema_info["tables"][table_name] = table_info
                    
                    # Update summary counters
                    schema_info["summary"]["total_columns"] += len(table_info["columns"])
                    schema_info["summary"]["total_indexes"] += len(table_info["indexes"])
                    schema_info["summary"]["total_foreign_keys"] += len(table_info["foreign_keys"])
                
                return json.dumps(schema_info, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            raise

    async def _get_table_schema_info(self, db, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table."""
        table_info = {"name": table_name}
        
        # Get column information
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
        
        # Get row count
        try:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
            table_info["row_count"] = (await cursor.fetchone())[0]
        except Exception:
            table_info["row_count"] = 0
        
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
            try:
                cursor = await db.execute(f"PRAGMA index_info({idx[1]})")
                index_columns = await cursor.fetchall()
                index_info["columns"] = [col[2] for col in index_columns]
            except Exception:
                index_info["columns"] = []
            table_info["indexes"].append(index_info)
        
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
        
        return table_info

    async def _get_database_statistics(self) -> str:
        """Get database statistics resource."""
        try:
            client = await self.client_manager.get_client()
            if not hasattr(client, 'metadata_cache') or not client.metadata_cache:
                raise ValueError("No metadata database available")

            # Use existing database statistics method
            if hasattr(client.metadata_cache, 'database') and hasattr(client.metadata_cache.database, 'get_database_statistics'):
                stats = await client.metadata_cache.database.get_database_statistics()
                stats["generated_at"] = datetime.utcnow().isoformat()
                stats["resource_type"] = "database_statistics"
                return json.dumps(stats, indent=2)
            else:
                # Fallback to basic statistics
                db_path = str(client.metadata_cache.db_path)
                stats = await self._get_basic_statistics(db_path)
                return json.dumps(stats, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            raise

    async def _get_basic_statistics(self, db_path: str) -> Dict[str, Any]:
        """Get basic database statistics."""
        import aiosqlite
        import os
        
        stats = {
            "generated_at": datetime.utcnow().isoformat(),
            "database_path": db_path,
            "resource_type": "database_statistics"
        }
        
        # File size
        try:
            stats["database_size_bytes"] = os.path.getsize(db_path)
            stats["database_size_mb"] = round(stats["database_size_bytes"] / (1024 * 1024), 2)
        except Exception:
            stats["database_size_bytes"] = None
            stats["database_size_mb"] = None
        
        async with aiosqlite.connect(db_path) as db:
            # Table counts
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            table_names = [row[0] for row in await cursor.fetchall()]
            stats["table_count"] = len(table_names)
            
            # Row counts by table
            table_stats = {}
            total_rows = 0
            for table_name in table_names:
                try:
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = (await cursor.fetchone())[0]
                    table_stats[table_name] = row_count
                    total_rows += row_count
                except Exception:
                    table_stats[table_name] = 0
            
            stats["table_statistics"] = table_stats
            stats["total_rows"] = total_rows
            
            # Database page information
            try:
                cursor = await db.execute("PRAGMA page_count")
                page_count = (await cursor.fetchone())[0]
                
                cursor = await db.execute("PRAGMA page_size")
                page_size = (await cursor.fetchone())[0]
                
                stats["page_statistics"] = {
                    "page_count": page_count,
                    "page_size_bytes": page_size,
                    "calculated_size_bytes": page_count * page_size
                }
            except Exception:
                stats["page_statistics"] = None
        
        return stats

    async def _get_tables_list(self) -> str:
        """Get tables list resource."""
        try:
            client = await self.client_manager.get_client()
            if not hasattr(client, 'metadata_cache') or not client.metadata_cache:
                raise ValueError("No metadata database available")

            db_path = str(client.metadata_cache.db_path)
            
            import aiosqlite
            
            async with aiosqlite.connect(db_path) as db:
                tables_info = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "resource_type": "tables_list",
                    "tables": []
                }
                
                # Get table information
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                table_names = [row[0] for row in await cursor.fetchall()]
                
                for table_name in table_names:
                    table_info = {"name": table_name}
                    
                    # Get row count
                    try:
                        cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
                        table_info["row_count"] = (await cursor.fetchone())[0]
                    except Exception:
                        table_info["row_count"] = 0
                    
                    # Get column count
                    cursor = await db.execute(f"PRAGMA table_info({table_name})")
                    columns = await cursor.fetchall()
                    table_info["column_count"] = len(columns)
                    
                    # Get primary key columns
                    pk_columns = [col[1] for col in columns if col[5]]  # col[5] is primary key flag
                    table_info["primary_key_columns"] = pk_columns
                    
                    tables_info["tables"].append(table_info)
                
                tables_info["total_tables"] = len(tables_info["tables"])
                return json.dumps(tables_info, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get tables list: {e}")
            raise

    async def _get_indexes_info(self) -> str:
        """Get indexes information resource."""
        try:
            client = await self.client_manager.get_client()
            if not hasattr(client, 'metadata_cache') or not client.metadata_cache:
                raise ValueError("No metadata database available")

            db_path = str(client.metadata_cache.db_path)
            
            import aiosqlite
            
            async with aiosqlite.connect(db_path) as db:
                indexes_info = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "resource_type": "indexes_info",
                    "indexes": []
                }
                
                # Get all tables
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                table_names = [row[0] for row in await cursor.fetchall()]
                
                for table_name in table_names:
                    # Get indexes for this table
                    cursor = await db.execute(f"PRAGMA index_list({table_name})")
                    indexes = await cursor.fetchall()
                    
                    for idx in indexes:
                        index_info = {
                            "table": table_name,
                            "name": idx[1],
                            "unique": bool(idx[2]),
                            "origin": idx[3]
                        }
                        
                        # Get index columns
                        try:
                            cursor = await db.execute(f"PRAGMA index_info({idx[1]})")
                            index_columns = await cursor.fetchall()
                            index_info["columns"] = [
                                {"seq": col[0], "column": col[2]} for col in index_columns
                            ]
                        except Exception:
                            index_info["columns"] = []
                        
                        indexes_info["indexes"].append(index_info)
                
                indexes_info["total_indexes"] = len(indexes_info["indexes"])
                return json.dumps(indexes_info, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get indexes info: {e}")
            raise

    async def _get_relationships_info(self) -> str:
        """Get relationships information resource."""
        try:
            client = await self.client_manager.get_client()
            if not hasattr(client, 'metadata_cache') or not client.metadata_cache:
                raise ValueError("No metadata database available")

            db_path = str(client.metadata_cache.db_path)
            
            import aiosqlite
            
            async with aiosqlite.connect(db_path) as db:
                relationships_info = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "resource_type": "relationships_info",
                    "foreign_keys": [],
                    "relationship_summary": {}
                }
                
                # Get all tables
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                table_names = [row[0] for row in await cursor.fetchall()]
                
                relationship_summary = {}
                
                for table_name in table_names:
                    # Get foreign keys for this table
                    cursor = await db.execute(f"PRAGMA foreign_key_list({table_name})")
                    foreign_keys = await cursor.fetchall()
                    
                    table_relationships = {
                        "references": [],  # Tables this table references
                        "referenced_by": []  # Will be filled in second pass
                    }
                    
                    for fk in foreign_keys:
                        fk_info = {
                            "from_table": table_name,
                            "from_column": fk[3],
                            "to_table": fk[2],
                            "to_column": fk[4],
                            "on_update": fk[5],
                            "on_delete": fk[6]
                        }
                        relationships_info["foreign_keys"].append(fk_info)
                        table_relationships["references"].append({
                            "table": fk[2],
                            "via_column": fk[3]
                        })
                    
                    relationship_summary[table_name] = table_relationships
                
                # Second pass to find reverse relationships
                for fk in relationships_info["foreign_keys"]:
                    to_table = fk["to_table"]
                    if to_table in relationship_summary:
                        relationship_summary[to_table]["referenced_by"].append({
                            "table": fk["from_table"],
                            "via_column": fk["to_column"]
                        })
                
                relationships_info["relationship_summary"] = relationship_summary
                relationships_info["total_foreign_keys"] = len(relationships_info["foreign_keys"])
                
                return json.dumps(relationships_info, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get relationships info: {e}")
            raise

    async def _get_table_details(self, table_name: str) -> str:
        """Get detailed information for a specific table."""
        try:
            client = await self.client_manager.get_client()
            if not hasattr(client, 'metadata_cache') or not client.metadata_cache:
                raise ValueError("No metadata database available")

            db_path = str(client.metadata_cache.db_path)
            
            import aiosqlite
            
            async with aiosqlite.connect(db_path) as db:
                # Verify table exists
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if not await cursor.fetchone():
                    raise ValueError(f"Table '{table_name}' does not exist")
                
                table_details = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "resource_type": "table_details",
                    "table_name": table_name
                }
                
                # Get complete table schema info
                table_info = await self._get_table_schema_info(db, table_name)
                table_details.update(table_info)
                
                # Add sample data (first 3 rows)
                try:
                    cursor = await db.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_rows = await cursor.fetchall()
                    if sample_rows:
                        column_names = [desc[0] for desc in cursor.description]
                        table_details["sample_data"] = {
                            "columns": column_names,
                            "rows": [list(row) for row in sample_rows],
                            "note": "Limited to first 3 rows for preview"
                        }
                except Exception as e:
                    table_details["sample_data_error"] = str(e)
                
                return json.dumps(table_details, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get table details for {table_name}: {e}")
            raise