"""Metadata synchronization manager for D365 F&O client."""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import logging

from .models import (
    DataEntityInfo, PublicEntityInfo, EnumerationInfo, 
    MetadataVersionInfo, SyncResult, NavigationPropertyInfo,
    PropertyGroupInfo, ActionInfo, ActionParameterInfo, ActionTypeInfo,
    RelationConstraintInfo, ReferentialConstraintInfo, FixedConstraintInfo,
    RelatedFixedConstraintInfo, PublicEntityPropertyInfo, EnumerationMemberInfo
)
from .metadata_cache import MetadataCache
from .metadata_api import MetadataAPIOperations
from .exceptions import MetadataError


logger = logging.getLogger(__name__)


class MetadataSyncManager:
    """Advanced metadata synchronization with change detection"""
    
    def __init__(self, metadata_cache: MetadataCache, metadata_api: MetadataAPIOperations):
        """Initialize sync manager
        
        Args:
            metadata_cache: Metadata cache instance
            metadata_api: Metadata API operations instance
        """
        self.cache = metadata_cache
        self.api = metadata_api
        self._sync_lock = asyncio.Lock()
    
    async def sync_metadata(self, force_full: bool = False) -> SyncResult:
        """Smart metadata synchronization with incremental updates
        
        Args:
            force_full: Force full synchronization even if not needed
            
        Returns:
            Synchronization result with statistics
        """
        async with self._sync_lock:
            start_time = time.time()
            
            try:
                # Get current environment version
                current_version = await self._get_current_version()
                
                # Get cached version
                cached_version = await self.cache._database.get_active_version(
                    self.cache._environment_id
                )
                
                # Determine sync strategy
                if force_full or not cached_version or self._needs_full_sync(current_version, cached_version):
                    result = await self._full_sync(current_version)
                else:
                    result = await self._incremental_sync(current_version, cached_version)
                
                # Update timing
                result.duration_ms = (time.time() - start_time) * 1000
                
                # Clear search cache after sync
                if hasattr(self.cache, '_search_engine'):
                    self.cache._search_engine._search_cache.clear()
                
                logger.info(f"Metadata sync completed: {result.sync_type}, "
                           f"{result.entities_synced} entities, "
                           f"{result.duration_ms:.2f}ms")
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Metadata sync failed after {duration_ms:.2f}ms: {e}")
                
                return SyncResult(
                    sync_type="failed",
                    success=False,
                    errors=[str(e)],
                    duration_ms=duration_ms
                )
    
    async def _get_current_version(self) -> MetadataVersionInfo:
        """Get current environment version information"""
        # Get version information from D365 F&O
        # This would typically include application version, platform version, and package information
        
        # For now, create a simple version hash based on available metadata
        # In a real implementation, you'd call version APIs or check timestamps
        
        version_components = {
            'timestamp': datetime.utcnow().isoformat(),
            'entities_count': 0,  # Would be populated by actual counts
            'actions_count': 0,
            'enums_count': 0
        }
        
        # Create version hash
        version_str = json.dumps(version_components, sort_keys=True)
        version_hash = hashlib.sha256(version_str.encode()).hexdigest()[:16]
        
        return MetadataVersionInfo(
            environment_id=self.cache._environment_id,
            version_hash=version_hash,
            application_version="10.0.latest",  # Would be retrieved from API
            platform_version="10.0.latest",
            package_info=[],  # Would be populated with actual package info
            created_at=datetime.utcnow(),
            is_active=True
        )
    
    def _needs_full_sync(self, current: MetadataVersionInfo, cached: MetadataVersionInfo) -> bool:
        """Determine if full sync is needed"""
        if not cached:
            return True
        
        # Compare version hashes
        if current.version_hash != cached.version_hash:
            return True
        
        # Check if cache is too old (older than 24 hours)
        if cached.created_at:
            cache_age = datetime.utcnow() - cached.created_at
            if cache_age.total_seconds() > 86400:  # 24 hours
                return True
        
        return False
    
    async def _full_sync(self, version_info: MetadataVersionInfo) -> SyncResult:
        """Perform full metadata synchronization"""
        logger.info("Starting full metadata synchronization")
        
        # Create new version in database
        version_id = await self.cache._database.create_version(
            self.cache._environment_id, version_info
        )
        
        # Sync all metadata types
        entities_count = await self._sync_data_entities(version_id)
        public_entities_count = await self._sync_public_entities(version_id)
        enums_count = await self._sync_enumerations(version_id)
        
        # Update search index
        await self._update_search_index()
        
        return SyncResult(
            sync_type="full",
            entities_synced=entities_count + public_entities_count,
            enumerations_synced=enums_count,
            success=True
        )
    
    async def _incremental_sync(self, current: MetadataVersionInfo, 
                              cached: MetadataVersionInfo) -> SyncResult:
        """Perform incremental metadata synchronization"""
        logger.info("Starting incremental metadata synchronization")
        
        # For now, incremental sync is not implemented
        # In a real implementation, you would:
        # 1. Compare timestamps or version numbers
        # 2. Identify changed entities/packages
        # 3. Sync only the changes
        
        # Fall back to full sync for now
        return await self._full_sync(current)
    
    async def _sync_data_entities(self, version_id: int) -> int:
        """Sync data entities to database"""
        logger.info("Syncing data entities")
        
        try:
            # Get all data entities from API
            entities_data = await self.api.get_data_entities()
            entities = []
            
            for item in entities_data.get('value', []):
                entity = DataEntityInfo(
                    name=item.get('Name', ''),
                    public_entity_name=item.get('PublicEntityName', ''),
                    public_collection_name=item.get('PublicCollectionName', ''),
                    label_id=item.get('LabelId'),
                    entity_category=item.get('EntityCategory'),
                    data_service_enabled=item.get('DataServiceEnabled', True),
                    data_management_enabled=item.get('DataManagementEnabled', True),
                    is_read_only=item.get('IsReadOnly', False)
                )
                entities.append(entity)
            
            # Store in database
            await self._store_data_entities(version_id, entities)
            
            logger.info(f"Synced {len(entities)} data entities")
            return len(entities)
            
        except Exception as e:
            logger.error(f"Failed to sync data entities: {e}")
            raise
    
    async def _sync_public_entities(self, version_id: int) -> int:
        """Sync public entities with full details to database (OPTIMIZED)"""
        logger.info("Syncing public entities")
        
        try:
            # Use optimized method to get all entities with full details in one API call
            entities = await self.api.get_all_public_entities_with_details(resolve_labels=False)
            
            # Store in database in batches
            batch_size = 100
            count = 0
            
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                await self._store_public_entities(version_id, batch)
                count += len(batch)
            
            logger.info(f"Synced {count} public entities")
            return count
            
        except Exception as e:
            logger.error(f"Failed to sync public entities: {e}")
            raise
    
    async def _sync_enumerations(self, version_id: int) -> int:
        """Sync enumerations to database (OPTIMIZED)"""
        logger.info("Syncing enumerations")
        
        try:
            # Use optimized method to get all enumerations with full details in one API call
            enumerations = await self.api.get_all_public_enumerations_with_details(resolve_labels=False)
            
            # Store in database
            await self._store_enumerations(version_id, enumerations)
            
            logger.info(f"Synced {len(enumerations)} enumerations")
            return len(enumerations)
            
        except Exception as e:
            logger.error(f"Failed to sync enumerations: {e}")
            raise
    
    async def _store_data_entities(self, version_id: int, entities: List[DataEntityInfo]):
        """Store data entities in database"""
        if not entities:
            return
        
        import aiosqlite
        
        async with aiosqlite.connect(self.cache._database.db_path) as db:
            await db.executemany(
                """INSERT INTO data_entities 
                   (version_id, name, public_entity_name, public_collection_name,
                    label_id, entity_category, data_service_enabled, 
                    data_management_enabled, is_read_only, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (version_id, entity.name, entity.public_entity_name,
                     entity.public_collection_name, entity.label_id, entity.entity_category,
                     entity.data_service_enabled, entity.data_management_enabled,
                     entity.is_read_only, datetime.utcnow())
                    for entity in entities
                ]
            )
            await db.commit()
    
    async def _store_public_entities(self, version_id: int, entities: List[PublicEntityInfo]):
        """Store public entities with full details in database"""
        if not entities:
            return
        
        import aiosqlite
        
        async with aiosqlite.connect(self.cache._database.db_path) as db:
            for entity in entities:
                try:
                    # Validate entity object
                    if not hasattr(entity, 'name'):
                        logger.error(f"Entity object missing 'name' attribute: {type(entity)} - {entity}")
                        continue
                        
                    # Insert entity
                    cursor = await db.execute(
                        """INSERT INTO public_entities 
                           (version_id, name, entity_set_name, label_id, 
                            is_read_only, configuration_enabled, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (version_id, entity.name, entity.entity_set_name, entity.label_id,
                         entity.is_read_only, entity.configuration_enabled, datetime.utcnow())
                    )
                    entity_id = cursor.lastrowid
                    
                    # Insert properties
                    if entity.properties:
                        await db.executemany(
                            """INSERT INTO entity_properties 
                               (entity_id, name, type_name, data_type, odata_xpp_type,
                                label_id, is_key, is_mandatory, configuration_enabled,
                                allow_edit, allow_edit_on_create, is_dimension,
                                dimension_relation, is_dynamic_dimension,
                                dimension_legal_entity_property, dimension_type_property,
                                property_order)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            [
                                (entity_id, prop.name, prop.type_name, prop.data_type,
                                 prop.odata_xpp_type, prop.label_id, prop.is_key,
                                 prop.is_mandatory, prop.configuration_enabled,
                                 prop.allow_edit, prop.allow_edit_on_create,
                                 prop.is_dimension, prop.dimension_relation,
                                 prop.is_dynamic_dimension, prop.dimension_legal_entity_property,
                                 prop.dimension_type_property, prop.property_order)
                                for prop in entity.properties
                            ]
                        )
                    
                    # Insert navigation properties and constraints
                    for nav_prop in entity.navigation_properties:
                        nav_cursor = await db.execute(
                            """INSERT INTO navigation_properties 
                               (entity_id, name, related_entity, related_relation_name,
                                cardinality, created_at)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (entity_id, nav_prop.name, nav_prop.related_entity,
                             nav_prop.related_relation_name, nav_prop.cardinality,
                             datetime.utcnow())
                        )
                        nav_prop_id = nav_cursor.lastrowid
                        
                        # Insert constraints
                        for constraint in nav_prop.constraints:
                            await self._store_relation_constraint(db, nav_prop_id, constraint)
                    
                    # Insert property groups
                    for group in entity.property_groups:
                        group_cursor = await db.execute(
                            """INSERT INTO property_groups (entity_id, name, group_order)
                               VALUES (?, ?, ?)""",
                            (entity_id, group.name, 0)
                        )
                        group_id = group_cursor.lastrowid
                        
                        # Insert group members
                        if group.properties:
                            await db.executemany(
                                """INSERT INTO property_group_members 
                                   (group_id, property_name, member_order)
                                   VALUES (?, ?, ?)""",
                                [
                                    (group_id, prop_name, idx)
                                    for idx, prop_name in enumerate(group.properties)
                                ]
                            )
                    
                    # Insert actions
                    for action in entity.actions:
                        action_cursor = await db.execute(
                            """INSERT INTO entity_actions 
                               (entity_id, name, binding_kind, field_lookup,
                                return_type_name, return_is_collection, return_odata_xpp_type,
                                created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (entity_id, action.name, action.binding_kind, action.field_lookup,
                             action.return_type.type_name if action.return_type else None,
                             action.return_type.is_collection if action.return_type else False,
                             action.return_type.odata_xpp_type if action.return_type else None,
                             datetime.utcnow())
                        )
                        action_id = action_cursor.lastrowid
                        
                        # Insert parameters
                        if action.parameters:
                            await db.executemany(
                                """INSERT INTO action_parameters 
                                   (action_id, name, type_name, is_collection,
                                    odata_xpp_type, parameter_order)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                [
                                    (action_id, param.name, param.type.type_name,
                                     param.type.is_collection, param.type.odata_xpp_type,
                                     param.parameter_order)
                                    for param in action.parameters
                                ]
                            )
                
                except Exception as e:
                    logger.error(f"Failed to store entity: {e}")
                    continue
            
            await db.commit()
    
    async def _store_relation_constraint(self, db: Any, nav_prop_id: int, 
                                       constraint: RelationConstraintInfo):
        """Store relation constraint in database"""
        if isinstance(constraint, ReferentialConstraintInfo):
            await db.execute(
                """INSERT INTO relation_constraints 
                   (navigation_property_id, constraint_type, property_name, referenced_property)
                   VALUES (?, ?, ?, ?)""",
                (nav_prop_id, constraint.constraint_type, constraint.property,
                 constraint.referenced_property)
            )
        elif isinstance(constraint, FixedConstraintInfo):
            await db.execute(
                """INSERT INTO relation_constraints 
                   (navigation_property_id, constraint_type, property_name, 
                    fixed_value, fixed_value_str)
                   VALUES (?, ?, ?, ?, ?)""",
                (nav_prop_id, constraint.constraint_type, constraint.property,
                 constraint.value, constraint.value_str)
            )
        elif isinstance(constraint, RelatedFixedConstraintInfo):
            await db.execute(
                """INSERT INTO relation_constraints 
                   (navigation_property_id, constraint_type, related_property,
                    fixed_value, fixed_value_str)
                   VALUES (?, ?, ?, ?, ?)""",
                (nav_prop_id, constraint.constraint_type, constraint.related_property,
                 constraint.value, constraint.value_str)
            )
        else:
            # Base constraint type
            await db.execute(
                """INSERT INTO relation_constraints 
                   (navigation_property_id, constraint_type)
                   VALUES (?, ?)""",
                (nav_prop_id, constraint.constraint_type)
            )
    
    async def _store_enumerations(self, version_id: int, enumerations: List[EnumerationInfo]):
        """Store enumerations in database"""
        if not enumerations:
            return
        
        import aiosqlite
        
        async with aiosqlite.connect(self.cache._database.db_path) as db:
            for enum in enumerations:
                # Insert enumeration
                cursor = await db.execute(
                    """INSERT INTO enumerations 
                       (version_id, name, label_id, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (version_id, enum.name, enum.label_id, datetime.utcnow())
                )
                enum_id = cursor.lastrowid
                
                # Insert members
                if enum.members:
                    await db.executemany(
                        """INSERT INTO enumeration_members 
                           (enumeration_id, name, value, label_id, 
                            configuration_enabled, member_order)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        [
                            (enum_id, member.name, member.value, member.label_id,
                             member.configuration_enabled, idx)
                            for idx, member in enumerate(enum.members)
                        ]
                    )
            
            await db.commit()
    
    async def _update_search_index(self):
        """Update FTS5 search index with current metadata"""
        logger.info("Updating search index")
        
        try:
            import aiosqlite
            
            async with aiosqlite.connect(self.cache._database.db_path) as db:
                # Recreate search index (FTS5 doesn't support DELETE operations)
                await db.execute("DROP TABLE IF EXISTS metadata_search")
                await db.execute("""
                    CREATE VIRTUAL TABLE metadata_search USING fts5(
                        entity_name, entity_type, entity_set_name, description, labels,
                        content=''
                    )
                """)
                
                # Index data entities
                await db.execute("""
                    INSERT INTO metadata_search 
                    (entity_name, entity_type, entity_set_name, description, labels)
                    SELECT de.name, 'data_entity', de.public_collection_name,
                           de.name || ' ' || COALESCE(de.public_entity_name, ''),
                           COALESCE(de.label_id, '')
                    FROM data_entities de
                    JOIN metadata_versions mv ON de.version_id = mv.id
                    WHERE mv.environment_id = ? AND mv.is_active = 1
                """, (self.cache._environment_id,))
                
                # Index public entities
                await db.execute("""
                    INSERT INTO metadata_search 
                    (entity_name, entity_type, entity_set_name, description, labels)
                    SELECT pe.name, 'public_entity', pe.entity_set_name,
                           pe.name || ' ' || pe.entity_set_name,
                           COALESCE(pe.label_id, '')
                    FROM public_entities pe
                    JOIN metadata_versions mv ON pe.version_id = mv.id
                    WHERE mv.environment_id = ? AND mv.is_active = 1
                """, (self.cache._environment_id,))
                
                # Index enumerations
                await db.execute("""
                    INSERT INTO metadata_search 
                    (entity_name, entity_type, entity_set_name, description, labels)
                    SELECT e.name, 'enumeration', e.name,
                           e.name,
                           COALESCE(e.label_id, '')
                    FROM enumerations e
                    JOIN metadata_versions mv ON e.version_id = mv.id
                    WHERE mv.environment_id = ? AND mv.is_active = 1
                """, (self.cache._environment_id,))
                
                await db.commit()
                
            logger.info("Search index updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update search index: {e}")
            # Don't fail the sync if search index update fails