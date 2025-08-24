"""Version-aware metadata search engine for MetadataCacheV2."""

import hashlib
import logging
import threading
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import aiosqlite

from ..exceptions import MetadataError
from ..models import SearchQuery, SearchResult, SearchResults

if TYPE_CHECKING:
    from .cache_v2 import MetadataCacheV2

logger = logging.getLogger(__name__)


class VersionAwareSearchEngine:
    """Advanced metadata search engine with version awareness and FTS5 support.
    
    This search engine is designed to work with MetadataCacheV2 and provides:
    - Version-aware search across multiple environments
    - FTS5 full-text search capabilities
    - Pattern-based search for simple queries
    - Multi-tier caching (memory cache)
    - Cross-environment search support
    """

    def __init__(self, metadata_cache: "MetadataCacheV2"):
        """Initialize version-aware search engine.

        Args:
            metadata_cache: MetadataCacheV2 instance
        """
        self.cache = metadata_cache
        self._search_cache = {}
        self._search_cache_lock = threading.RLock()
        self._cache_ttl_seconds = 300  # 5 minutes cache TTL

    async def rebuild_search_index(self, global_version_id: Optional[int] = None):
        """Rebuild the FTS5 search index for a specific version.
        
        Args:
            global_version_id: Specific version to rebuild index for.
                             If None, rebuilds for current environment version.
        """
        if not self.cache._environment_id:
            await self.cache.initialize()

        # Get version to rebuild for
        if global_version_id is None:
            # Get current environment's active global version
            async with aiosqlite.connect(self.cache.db_path) as db:
                cursor = await db.execute(
                    """SELECT global_version_id FROM environment_versions 
                       WHERE environment_id = ? AND is_active = 1 
                       ORDER BY detected_at DESC LIMIT 1""",
                    (self.cache._environment_id,)
                )
                row = await cursor.fetchone()
                if not row:
                    logger.warning("No active version found for current environment")
                    return
                global_version_id = row[0]

        await self._rebuild_fts_index_for_version(global_version_id)

    async def _rebuild_fts_index_for_version(self, global_version_id: int):
        """Rebuild FTS5 index for specific global version."""
        async with aiosqlite.connect(self.cache.db_path) as db:
            logger.info(f"Rebuilding FTS5 search index for version {global_version_id}")
            
            # Clear existing entries for this version
            await db.execute(
                "DELETE FROM metadata_search_v2 WHERE global_version_id = ?",
                (global_version_id,)
            )

            # Index data entities
            await db.execute(
                """INSERT INTO metadata_search_v2 
                   (name, entity_type, description, properties, labels, global_version_id, entity_id)
                   SELECT 
                       de.name,
                       'data_entity',
                       COALESCE(de.label_text, de.label_id, de.name),
                       de.name || ' ' || COALESCE(de.public_entity_name, '') || ' ' || COALESCE(de.public_collection_name, ''),
                       COALESCE(de.label_text, ''),
                       de.global_version_id,
                       de.id
                   FROM data_entities de
                   WHERE de.global_version_id = ?""",
                (global_version_id,)
            )

            # Index public entities  
            await db.execute(
                """INSERT INTO metadata_search_v2 
                   (name, entity_type, description, properties, labels, global_version_id, entity_id)
                   SELECT 
                       pe.name,
                       'public_entity',
                       COALESCE(pe.label_text, pe.label_id, pe.name),
                       pe.name || ' ' || COALESCE(pe.entity_set_name, ''),
                       COALESCE(pe.label_text, ''),
                       pe.global_version_id,
                       pe.id
                   FROM public_entities pe
                   WHERE pe.global_version_id = ?""",
                (global_version_id,)
            )

            # Index enumerations
            await db.execute(
                """INSERT INTO metadata_search_v2 
                   (name, entity_type, description, properties, labels, global_version_id, entity_id)
                   SELECT 
                       e.name,
                       'enumeration',
                       COALESCE(e.label_text, e.label_id, e.name),
                       e.name,
                       COALESCE(e.label_text, ''),
                       e.global_version_id,
                       e.id
                   FROM enumerations e
                   WHERE e.global_version_id = ?""",
                (global_version_id,)
            )

            await db.commit()
            logger.info(f"FTS5 search index rebuilt for version {global_version_id}")

    async def search(self, query: SearchQuery) -> SearchResults:
        """Execute version-aware metadata search.

        Args:
            query: Search query parameters

        Returns:
            Search results with version awareness
        """
        start_time = time.time()

        # Build cache key
        cache_key = self._build_search_cache_key(query)

        # Check cache
        with self._search_cache_lock:
            cached = self._search_cache.get(cache_key)
            if cached and time.time() - cached["timestamp"] < self._cache_ttl_seconds:
                cached["results"].cache_hit = True
                cached["results"].query_time_ms = (time.time() - start_time) * 1000
                return cached["results"]

        # Execute search
        if query.use_fulltext:
            results = await self._fts_search(query)
        else:
            results = await self._pattern_search(query)

        # Calculate timing
        results.query_time_ms = (time.time() - start_time) * 1000
        results.cache_hit = False

        # Cache results
        with self._search_cache_lock:
            self._search_cache[cache_key] = {
                "results": results,
                "timestamp": time.time(),
            }

            # Limit cache size
            if len(self._search_cache) > 100:
                oldest_key = min(
                    self._search_cache.keys(),
                    key=lambda k: self._search_cache[k]["timestamp"],
                )
                del self._search_cache[oldest_key]

        return results

    def _build_search_cache_key(self, query: SearchQuery) -> str:
        """Build cache key for search query."""
        key_parts = [
            str(self.cache._environment_id or ""),
            query.text,
            "|".join(query.entity_types or []),
            str(query.limit),
            str(query.offset),
            str(query.use_fulltext),
            str(query.include_properties),
            str(query.include_actions),
        ]

        if query.filters:
            for k, v in sorted(query.filters.items()):
                key_parts.append(f"{k}:{v}")

        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    async def _fts_search(self, query: SearchQuery) -> SearchResults:
        """Full-text search using FTS5 with version awareness."""
        if not self.cache._environment_id:
            return SearchResults(results=[], total_count=0)

        search_query = self._build_fts_query(query.text)

        async with aiosqlite.connect(self.cache.db_path) as db:
            # Get current environment's active global version
            cursor = await db.execute(
                """SELECT global_version_id FROM environment_versions 
                   WHERE environment_id = ? AND is_active = 1 
                   ORDER BY detected_at DESC LIMIT 1""",
                (self.cache._environment_id,)
            )
            version_row = await cursor.fetchone()
            
            if not version_row:
                logger.warning("No active version found for FTS search")
                return SearchResults(results=[], total_count=0)
            
            global_version_id = version_row[0]

            # Execute FTS5 search
            sql = """
                SELECT name, entity_type, description, labels,
                       bm25(metadata_search_v2) as relevance,
                       snippet(metadata_search_v2, 0, '<mark>', '</mark>', '...', 32) as snippet
                FROM metadata_search_v2 
                WHERE metadata_search_v2 MATCH ? AND global_version_id = ?
            """

            params = [search_query, global_version_id]

            # Add entity type filter
            if query.entity_types:
                placeholders = ",".join("?" * len(query.entity_types))
                sql += f" AND entity_type IN ({placeholders})"
                params.extend(query.entity_types)

            sql += " ORDER BY bm25(metadata_search_v2) LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])

            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    name=row[0],
                    entity_type=row[1],
                    entity_set_name="",  # Will be populated if needed
                    description=row[2],
                    relevance=row[4],
                    snippet=row[5],
                )
                results.append(result)

            # Get total count
            count_sql = """
                SELECT COUNT(*) FROM metadata_search_v2 
                WHERE metadata_search_v2 MATCH ? AND global_version_id = ?
            """
            count_params = [search_query, global_version_id]
            
            if query.entity_types:
                placeholders = ",".join("?" * len(query.entity_types))
                count_sql += f" AND entity_type IN ({placeholders})"
                count_params.extend(query.entity_types)

            count_cursor = await db.execute(count_sql, count_params)
            total_count = (await count_cursor.fetchone())[0]

            return SearchResults(results=results, total_count=total_count)

    async def _pattern_search(self, query: SearchQuery) -> SearchResults:
        """Pattern-based search for simple queries with version awareness."""
        if not self.cache._environment_id:
            return SearchResults(results=[], total_count=0)

        pattern = f"%{query.text.lower()}%"

        async with aiosqlite.connect(self.cache.db_path) as db:
            # Get current environment's active global version
            cursor = await db.execute(
                """SELECT global_version_id FROM environment_versions 
                   WHERE environment_id = ? AND is_active = 1 
                   ORDER BY detected_at DESC LIMIT 1""",
                (self.cache._environment_id,)
            )
            version_row = await cursor.fetchone()
            
            if not version_row:
                logger.warning("No active version found for pattern search")
                return SearchResults(results=[], total_count=0)
            
            global_version_id = version_row[0]

            # Search across multiple entity types
            union_queries = []
            params = []

            if not query.entity_types or "data_entity" in query.entity_types:
                union_queries.append(
                    """
                    SELECT de.name as entity_name, 'data_entity' as entity_type,
                           de.public_collection_name as entity_set_name,
                           COALESCE(de.label_text, de.label_id) as description, 
                           0.5 as relevance,
                           de.name as snippet
                    FROM data_entities de
                    WHERE LOWER(de.name) LIKE ? AND de.global_version_id = ?
                """
                )
                params.extend([pattern, global_version_id])

            if not query.entity_types or "public_entity" in query.entity_types:
                union_queries.append(
                    """
                    SELECT pe.name as entity_name, 'public_entity' as entity_type,
                           pe.entity_set_name, 
                           COALESCE(pe.label_text, pe.label_id) as description, 
                           0.5 as relevance,
                           pe.name as snippet
                    FROM public_entities pe
                    WHERE LOWER(pe.name) LIKE ? AND pe.global_version_id = ?
                """
                )
                params.extend([pattern, global_version_id])

            if not query.entity_types or "enumeration" in query.entity_types:
                union_queries.append(
                    """
                    SELECT e.name as entity_name, 'enumeration' as entity_type,
                           e.name as entity_set_name, 
                           COALESCE(e.label_text, e.label_id) as description, 
                           0.5 as relevance,
                           e.name as snippet
                    FROM enumerations e
                    WHERE LOWER(e.name) LIKE ? AND e.global_version_id = ?
                """
                )
                params.extend([pattern, global_version_id])

            if not union_queries:
                return SearchResults(results=[], total_count=0)

            sql = " UNION ALL ".join(union_queries)
            sql += " ORDER BY relevance DESC, entity_name LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])

            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    name=row[0],
                    entity_type=row[1],
                    entity_set_name=row[2] or "",
                    description=row[3] or "",
                    relevance=row[4],
                    snippet=row[5],
                )
                results.append(result)

            return SearchResults(
                results=results,
                total_count=len(results),  # Simplified count for pattern search
            )

    def _build_fts_query(self, text: str) -> str:
        """Build FTS5 query from user input."""
        # Simple FTS query building - can be enhanced with more sophisticated parsing
        # Handle basic operators and quoted phrases

        # If already quoted or contains operators, use as-is
        if '"' in text or any(op in text for op in ["AND", "OR", "NOT", "*"]):
            return text

        # For simple terms, create a phrase query with prefix matching
        terms = text.strip().split()
        if len(terms) == 1:
            return f'"{terms[0]}"*'
        else:
            return f'"{" ".join(terms)}"'

    async def search_entities_fts(self, search_text: str, entity_types: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Simplified FTS search for entities (for MCP compatibility).
        
        Args:
            search_text: Text to search for
            entity_types: Optional list of entity types to filter by
            limit: Maximum number of results
            
        Returns:
            List of entity dictionaries
        """
        query = SearchQuery(
            text=search_text,
            entity_types=entity_types or ["data_entity"],
            limit=limit,
            use_fulltext=True
        )
        
        results = await self.search(query)
        
        # Convert to dictionary format for compatibility
        entities = []
        for result in results.results:
            entity_dict = {
                "name": result.name,
                "entity_type": result.entity_type,
                "entity_set_name": result.entity_set_name,
                "description": result.description,
                "relevance": result.relevance,
                "snippet": result.snippet
            }
            entities.append(entity_dict)
            
        return entities