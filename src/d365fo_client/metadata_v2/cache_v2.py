"""Version-aware metadata cache implementation."""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
import aiosqlite
import json

from .database_v2 import MetadataDatabaseV2
from .global_version_manager import GlobalVersionManager
from .version_detector import ModuleVersionDetector
from ..models import (
    ModuleVersionInfo, EnvironmentVersionInfo, GlobalVersionInfo,
    DataEntityInfo, PublicEntityInfo, PublicEntityPropertyInfo, NavigationPropertyInfo,
    RelationConstraintInfo, PropertyGroupInfo, ActionInfo,
    ActionParameterInfo, EnumerationInfo, EnumerationMemberInfo
)

logger = logging.getLogger(__name__)


class MetadataCacheV2:
    """Version-aware metadata cache with intelligent invalidation"""
    
    def __init__(self, cache_dir: Path, base_url: str):
        """Initialize metadata cache v2
        
        Args:
            cache_dir: Directory for cache storage
            base_url: D365 F&O environment base URL
        """
        self.cache_dir = cache_dir
        self.base_url = base_url
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Database and managers
        self.db_path = cache_dir / "metadata_v2.db"
        self.database = MetadataDatabaseV2(self.db_path)
        self.version_manager = GlobalVersionManager(self.db_path)
        # Note: version_detector will be initialized when needed with proper api_operations
        self.version_detector = None
        
        # Cache state
        self._environment_id: Optional[int] = None
        self._current_version_info: Optional[EnvironmentVersionInfo] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize cache database and environment"""
        if self._initialized:
            return
        
        await self.database.initialize()
        self._environment_id = await self.database.get_or_create_environment(self.base_url)
        self._initialized = True
        
        logger.info(f"MetadataCacheV2 initialized for environment {self._environment_id}")
    
    async def check_version_and_sync(self, fo_client) -> Tuple[bool, Optional[int]]:
        """Check environment version and determine if sync is needed
        
        Args:
            fo_client: D365 F&O client instance
            
        Returns:
            Tuple of (sync_needed, global_version_id)
        """
        await self.initialize()
        
        # Initialize version detector if not already done
        if self.version_detector is None:
            # For now, we'll skip the actual version detection
            # In a full implementation, this would use fo_client's API operations
            logger.warning("Version detector not available - using fallback mode")
            return True, None
        
        # Detect current version
        modules = await self.version_detector.detect_version(fo_client)
        if not modules:
            logger.warning("Could not detect environment version")
            return True, None
        
        # Register/find global version
        global_version_id, is_new_version = await self.version_manager.register_environment_version(
            self._environment_id, modules
        )
        
        # Update current version info
        self._current_version_info = await self.version_manager.get_environment_version_info(
            self._environment_id
        )
        
        if is_new_version:
            logger.info(f"New version detected: {global_version_id}")
            return True, global_version_id
        
        # Check if metadata exists for this version
        if await self._has_complete_metadata(global_version_id):
            logger.info(f"Using cached metadata for version {global_version_id}")
            return False, global_version_id
        else:
            logger.info(f"Metadata incomplete for version {global_version_id}, sync needed")
            return True, global_version_id
    
    async def _has_complete_metadata(self, global_version_id: int) -> bool:
        """Check if metadata is complete for a global version
        
        Args:
            global_version_id: Global version ID to check
            
        Returns:
            True if metadata is complete
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Check metadata version record
            cursor = await db.execute(
                """SELECT sync_completed_at, entity_count, action_count, enumeration_count
                   FROM metadata_versions
                   WHERE global_version_id = ?""",
                (global_version_id,)
            )
            
            row = await cursor.fetchone()
            if not row or not row[0]:  # No completed sync
                return False
            
            # Check basic entity count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM data_entities WHERE global_version_id = ?",
                (global_version_id,)
            )
            
            entity_count = (await cursor.fetchone())[0]
            return entity_count > 0  # Has some entities
    
    async def store_data_entities(
        self, 
        global_version_id: int, 
        entities: List[DataEntityInfo]
    ):
        """Store data entities for global version
        
        Args:
            global_version_id: Global version ID
            entities: List of data entity information
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Clear existing entities for this version
            await db.execute(
                "DELETE FROM data_entities WHERE global_version_id = ?",
                (global_version_id,)
            )
            
            # Insert new entities
            for entity in entities:
                await db.execute(
                    """INSERT INTO data_entities
                       (global_version_id, name, public_entity_name, public_collection_name,
                        label_id, label_text, entity_category, data_service_enabled,
                        data_management_enabled, is_read_only)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        global_version_id, entity.name, entity.public_entity_name,
                        entity.public_collection_name, entity.label_id, entity.label_text,
                        entity.entity_category, entity.data_service_enabled,
                        entity.data_management_enabled, entity.is_read_only
                    )
                )
            
            await db.commit()
            logger.info(f"Stored {len(entities)} data entities for version {global_version_id}")
    
    async def get_data_entities(
        self, 
        global_version_id: Optional[int] = None,
        data_service_enabled: Optional[bool] = None,
        entity_category: Optional[str] = None,
        name_pattern: Optional[str] = None
    ) -> List[DataEntityInfo]:
        """Get data entities with filtering
        
        Args:
            global_version_id: Global version ID (uses current if None)
            data_service_enabled: Filter by data service enabled status
            entity_category: Filter by entity category
            name_pattern: Filter by name pattern (SQL LIKE)
            
        Returns:
            List of matching data entities
        """
        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()
            if global_version_id is None:
                return []
        
        # Build query conditions
        conditions = ["global_version_id = ?"]
        params = [global_version_id]
        
        if data_service_enabled is not None:
            conditions.append("data_service_enabled = ?")
            params.append(data_service_enabled)
        
        if entity_category is not None:
            conditions.append("entity_category = ?")
            params.append(entity_category)
        
        if name_pattern is not None:
            conditions.append("name LIKE ?")
            params.append(name_pattern)
        
        where_clause = " AND ".join(conditions)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"""SELECT name, public_entity_name, public_collection_name,
                           label_id, label_text, entity_category, data_service_enabled,
                           data_management_enabled, is_read_only
                    FROM data_entities
                    WHERE {where_clause}
                    ORDER BY name""",
                params
            )
            
            entities = []
            for row in await cursor.fetchall():
                entities.append(DataEntityInfo(
                    name=row[0],
                    public_entity_name=row[1],
                    public_collection_name=row[2],
                    label_id=row[3],
                    label_text=row[4],
                    entity_category=row[5],
                    data_service_enabled=row[6],
                    data_management_enabled=row[7],
                    is_read_only=row[8]
                ))
            
            return entities
    
    async def store_public_entity_schema(
        self,
        global_version_id: int,
        entity_schema: PublicEntityInfo
    ):
        """Store public entity schema
        
        Args:
            global_version_id: Global version ID
            entity_schema: Public entity schema information
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Insert/update entity
            cursor = await db.execute(
                """INSERT OR REPLACE INTO public_entities
                   (global_version_id, name, entity_set_name, label_id, label_text,
                    is_read_only, configuration_enabled)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    global_version_id, entity_schema.name, entity_schema.entity_set_name,
                    entity_schema.label_id, entity_schema.label_text,
                    entity_schema.is_read_only, entity_schema.configuration_enabled
                )
            )
            
            entity_id = cursor.lastrowid
            
            # Clear existing related data
            await db.execute(
                "DELETE FROM entity_properties WHERE entity_id = ?",
                (entity_id,)
            )
            await db.execute(
                "DELETE FROM navigation_properties WHERE entity_id = ?",
                (entity_id,)
            )
            await db.execute(
                "DELETE FROM entity_actions WHERE entity_id = ?",
                (entity_id,)
            )
            
            # Store properties
            for prop in entity_schema.properties:
                await db.execute(
                    """INSERT INTO entity_properties
                       (entity_id, global_version_id, name, type_name, data_type,
                        odata_xpp_type, label_id, label_text, is_key, is_mandatory,
                        configuration_enabled, allow_edit, allow_edit_on_create,
                        is_dimension, dimension_relation, is_dynamic_dimension,
                        dimension_legal_entity_property, dimension_type_property,
                        property_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entity_id, global_version_id, prop.name, prop.type_name,
                        prop.data_type, prop.odata_xpp_type, prop.label_id,
                        prop.label_text, prop.is_key, prop.is_mandatory,
                        prop.configuration_enabled, prop.allow_edit,
                        prop.allow_edit_on_create, prop.is_dimension,
                        prop.dimension_relation, prop.is_dynamic_dimension,
                        prop.dimension_legal_entity_property,
                        prop.dimension_type_property, prop.property_order
                    )
                )
            
            # Store navigation properties
            for nav_prop in entity_schema.navigation_properties:
                nav_cursor = await db.execute(
                    """INSERT INTO navigation_properties
                       (entity_id, global_version_id, name, related_entity,
                        related_relation_name, cardinality)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        entity_id, global_version_id, nav_prop.name,
                        nav_prop.related_entity, nav_prop.related_relation_name,
                        nav_prop.cardinality
                    )
                )
                
                nav_prop_id = nav_cursor.lastrowid
                
                # Store relation constraints
                for constraint in nav_prop.relation_constraints:
                    await db.execute(
                        """INSERT INTO relation_constraints
                           (navigation_property_id, global_version_id, constraint_type,
                            property_name, referenced_property, related_property,
                            fixed_value, fixed_value_str)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            nav_prop_id, global_version_id, constraint.constraint_type,
                            constraint.property_name, constraint.referenced_property,
                            constraint.related_property, constraint.fixed_value,
                            constraint.fixed_value_str
                        )
                    )
            
            # Store actions
            for action in entity_schema.actions:
                action_cursor = await db.execute(
                    """INSERT INTO entity_actions
                       (entity_id, global_version_id, name, binding_kind, entity_name,
                        entity_set_name, return_type_name, return_is_collection,
                        return_odata_xpp_type, field_lookup)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entity_id, global_version_id, action.name, action.binding_kind,
                        action.entity_name, action.entity_set_name,
                        action.return_type.type_name if action.return_type else None,
                        action.return_type.is_collection if action.return_type else False,
                        action.return_type.odata_xpp_type if action.return_type else None,
                        action.field_lookup
                    )
                )
                
                action_id = action_cursor.lastrowid
                
                # Store action parameters
                for param in action.parameters:
                    await db.execute(
                        """INSERT INTO action_parameters
                           (action_id, global_version_id, name, type_name,
                            is_collection, odata_xpp_type, parameter_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            action_id, global_version_id, param.name,
                            param.type_name, param.is_collection,
                            param.odata_xpp_type, param.parameter_order
                        )
                    )
            
            await db.commit()
            logger.info(f"Stored entity schema for {entity_schema.name}")
    
    async def get_public_entity_schema(
        self,
        entity_name: str,
        global_version_id: Optional[int] = None
    ) -> Optional[PublicEntityInfo]:
        """Get public entity schema
        
        Args:
            entity_name: Entity name to retrieve
            global_version_id: Global version ID (uses current if None)
            
        Returns:
            Public entity schema if found
        """
        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()
            if global_version_id is None:
                return None
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get entity
            cursor = await db.execute(
                """SELECT id, name, entity_set_name, label_id, label_text,
                          is_read_only, configuration_enabled
                   FROM public_entities
                   WHERE name = ? AND global_version_id = ?""",
                (entity_name, global_version_id)
            )
            
            entity_row = await cursor.fetchone()
            if not entity_row:
                return None
            
            entity_id = entity_row[0]
            
            # Get properties
            cursor = await db.execute(
                """SELECT name, type_name, data_type, odata_xpp_type, label_id,
                          label_text, is_key, is_mandatory, configuration_enabled,
                          allow_edit, allow_edit_on_create, is_dimension,
                          dimension_relation, is_dynamic_dimension,
                          dimension_legal_entity_property, dimension_type_property,
                          property_order
                   FROM entity_properties
                   WHERE entity_id = ?
                   ORDER BY property_order""",
                (entity_id,)
            )
            
            properties = []
            for prop_row in await cursor.fetchall():
                properties.append(PublicEntityPropertyInfo(
                    name=prop_row[0],
                    type_name=prop_row[1],
                    data_type=prop_row[2],
                    odata_xpp_type=prop_row[3],
                    label_id=prop_row[4],
                    label_text=prop_row[5],
                    is_key=prop_row[6],
                    is_mandatory=prop_row[7],
                    configuration_enabled=prop_row[8],
                    allow_edit=prop_row[9],
                    allow_edit_on_create=prop_row[10],
                    is_dimension=prop_row[11],
                    dimension_relation=prop_row[12],
                    is_dynamic_dimension=prop_row[13],
                    dimension_legal_entity_property=prop_row[14],
                    dimension_type_property=prop_row[15],
                    property_order=prop_row[16]
                ))
            
            # Navigation properties and actions would be loaded similarly...
            # Simplified for brevity
            
            return PublicEntityInfo(
                name=entity_row[1],
                entity_set_name=entity_row[2],
                label_id=entity_row[3],
                label_text=entity_row[4],
                is_read_only=entity_row[5],
                configuration_enabled=entity_row[6],
                properties=properties,
                navigation_properties=[],  # TODO: Load navigation properties
                property_groups=[],       # TODO: Load property groups
                actions=[]                # TODO: Load actions
            )
    
    async def store_enumerations(
        self,
        global_version_id: int,
        enumerations: List[EnumerationInfo]
    ):
        """Store enumerations
        
        Args:
            global_version_id: Global version ID
            enumerations: List of enumeration information
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Clear existing enumerations for this version
            await db.execute(
                "DELETE FROM enumerations WHERE global_version_id = ?",
                (global_version_id,)
            )
            
            for enum_info in enumerations:
                # Insert enumeration
                cursor = await db.execute(
                    """INSERT INTO enumerations
                       (global_version_id, name, label_id, label_text)
                       VALUES (?, ?, ?, ?)""",
                    (
                        global_version_id, enum_info.name,
                        enum_info.label_id, enum_info.label_text
                    )
                )
                
                enum_id = cursor.lastrowid
                
                # Insert members
                for member in enum_info.members:
                    await db.execute(
                        """INSERT INTO enumeration_members
                           (enumeration_id, global_version_id, name, value,
                            label_id, label_text, configuration_enabled, member_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            enum_id, global_version_id, member.name, member.value,
                            member.label_id, member.label_text,
                            member.configuration_enabled, member.member_order
                        )
                    )
            
            await db.commit()
            logger.info(f"Stored {len(enumerations)} enumerations for version {global_version_id}")
    
    async def get_enumeration_info(
        self,
        enum_name: str,
        global_version_id: Optional[int] = None
    ) -> Optional[EnumerationInfo]:
        """Get enumeration information
        
        Args:
            enum_name: Enumeration name
            global_version_id: Global version ID (uses current if None)
            
        Returns:
            Enumeration info if found
        """
        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()
            if global_version_id is None:
                return None
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get enumeration
            cursor = await db.execute(
                """SELECT id, name, label_id, label_text
                   FROM enumerations
                   WHERE name = ? AND global_version_id = ?""",
                (enum_name, global_version_id)
            )
            
            enum_row = await cursor.fetchone()
            if not enum_row:
                return None
            
            enum_id = enum_row[0]
            
            # Get members
            cursor = await db.execute(
                """SELECT name, value, label_id, label_text, configuration_enabled, member_order
                   FROM enumeration_members
                   WHERE enumeration_id = ?
                   ORDER BY member_order""",
                (enum_id,)
            )
            
            members = []
            for member_row in await cursor.fetchall():
                members.append(EnumerationMemberInfo(
                    name=member_row[0],
                    value=member_row[1],
                    label_id=member_row[2],
                    label_text=member_row[3],
                    configuration_enabled=member_row[4],
                    member_order=member_row[5]
                ))
            
            return EnumerationInfo(
                name=enum_row[1],
                label_id=enum_row[2],
                label_text=enum_row[3],
                members=members
            )
    
    async def mark_sync_completed(
        self,
        global_version_id: int,
        entity_count: int = 0,
        action_count: int = 0,
        enumeration_count: int = 0,
        label_count: int = 0
    ):
        """Mark sync as completed for a global version
        
        Args:
            global_version_id: Global version ID
            entity_count: Number of entities synced
            action_count: Number of actions synced
            enumeration_count: Number of enumerations synced
            label_count: Number of labels synced
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO metadata_versions
                   (global_version_id, sync_completed_at, entity_count,
                    action_count, enumeration_count, label_count)
                   VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)""",
                (global_version_id, entity_count, action_count, enumeration_count, label_count)
            )
            
            await db.commit()
            logger.info(f"Marked sync completed for version {global_version_id}")
    
    async def _get_current_global_version_id(self) -> Optional[int]:
        """Get current global version ID for environment
        
        Returns:
            Current global version ID if available
        """
        if self._current_version_info:
            return self._current_version_info.global_version_id
        
        if self._environment_id is None:
            return None
        
        version_info = await self.version_manager.get_environment_version_info(self._environment_id)
        if version_info:
            self._current_version_info = version_info
            return version_info.global_version_id
        
        return None
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {}
        
        # Database statistics
        db_stats = await self.database.get_database_statistics()
        stats.update(db_stats)
        
        # Version statistics
        version_stats = await self.version_manager.get_version_statistics()
        stats['version_manager'] = version_stats
        
        # Current version info
        current_version = await self._get_current_global_version_id()
        if current_version:
            version_info = await self.version_manager.get_global_version_info(current_version)
            if version_info:
                stats['current_version'] = {
                    'global_version_id': version_info.global_version_id,
                    'version_hash': version_info.version_hash,
                    'modules_count': len(version_info.modules),
                    'reference_count': version_info.reference_count,
                    'linked_environments': len(version_info.linked_environments)
                }
        
        return stats