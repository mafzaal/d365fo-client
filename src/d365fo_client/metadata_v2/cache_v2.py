"""Version-aware metadata cache implementation."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import aiosqlite

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from ..metadata_api import MetadataAPIOperations

from ..models import (
    ActionInfo,
    ActionParameterInfo,
    ActionParameterTypeInfo,
    ActionReturnTypeInfo,
    Cardinality,
    DataEntityInfo,
    EnumerationInfo,
    EnumerationMemberInfo,
    EnvironmentVersionInfo,
    FixedConstraintInfo,
    GlobalVersionInfo,
    LabelInfo,
    ModuleVersionInfo,
    NavigationPropertyInfo,
    ODataBindingKind,
    PropertyGroupInfo,
    PublicEntityActionInfo,
    PublicEntityInfo,
    PublicEntityPropertyInfo,
    ReferentialConstraintInfo,
    RelatedFixedConstraintInfo,
    RelationConstraintInfo,
    VersionDetectionResult,
)
from .database_v2 import MetadataDatabaseV2
from .global_version_manager import GlobalVersionManager
from .version_detector import ModuleVersionDetector

logger = logging.getLogger(__name__)


class MetadataCacheV2:
    """Version-aware metadata cache with intelligent invalidation"""

    def __init__(
        self,
        cache_dir: Path,
        base_url: str,
        metadata_api: Optional["MetadataAPIOperations"] = None,
    ):
        """Initialize metadata cache v2

        Args:
            cache_dir: Directory for cache storage
            base_url: D365 F&O environment base URL
            metadata_api: Optional MetadataAPIOperations instance for version detection
        """
        self.cache_dir = cache_dir
        self.base_url = base_url
        self.metadata_api = metadata_api
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Database and managers
        self.db_path = cache_dir / "metadata_v2.db"
        self.database = MetadataDatabaseV2(self.db_path)
        self.version_manager = GlobalVersionManager(self.db_path)

        # Version detector - initialized when metadata_api is available
        self.version_detector = None
        if self.metadata_api:
            self.version_detector = ModuleVersionDetector(self.metadata_api)

        # Cache state
        self._environment_id: Optional[int] = None
        self._current_version_info: Optional[EnvironmentVersionInfo] = None
        self._current_global_version_id: Optional[int] = None
        self._initialized = False

    async def initialize(self):
        """Initialize cache database and environment"""
        if self._initialized:
            return

        await self.database.initialize()
        self._environment_id = await self.database.get_or_create_environment(
            self.base_url
        )
        self._initialized = True

        logger.info(
            f"MetadataCacheV2 initialized for environment {self._environment_id}"
        )

    def set_metadata_api(self, metadata_api: "MetadataAPIOperations"):
        """Set metadata API operations instance and initialize version detector

        Args:
            metadata_api: MetadataAPIOperations instance
        """
        self.metadata_api = metadata_api
        self.version_detector = ModuleVersionDetector(metadata_api)
        logger.debug("Version detector initialized with metadata API")

    async def check_version_and_sync(
        self, metadata_api: Optional["MetadataAPIOperations"] = None
    ) -> Tuple[bool, Optional[int]]:
        """Check environment version and determine if sync is needed

        Args:
            metadata_api: Optional MetadataAPIOperations instance for version detection

        Returns:
            Tuple of (sync_needed, global_version_id)
        """
        await self.initialize()

        # Set up version detector if metadata_api is provided
        if metadata_api and not self.version_detector:
            self.set_metadata_api(metadata_api)

        # Check if version detector is available
        if not self.version_detector:
            logger.warning("Version detector not available - sync needed")
            return True, None

        try:
            # Detect current version
            detection_result = await self.version_detector.get_environment_version()

            if not detection_result.success or not detection_result.version_info:
                logger.warning(
                    f"Version detection failed: {detection_result.error_message}"
                )
                return True, None

            version_info = detection_result.version_info
            logger.info(
                f"Version detected: {len(version_info.modules)} modules, "
                f"hash: {version_info.version_hash}"
            )

            # Set environment ID on version info
            version_info.environment_id = self._environment_id

            # Register/find global version
            global_version_id, was_created = (
                await self.version_manager.register_environment_version(
                    self._environment_id, version_info.modules
                )
            )

            # Update current version info
            self._current_version_info = version_info
            self._current_global_version_id = global_version_id

            if was_created:
                logger.info(f"New version detected: {global_version_id}")
                return True, global_version_id

            # Check if metadata exists for this version
            if await self._has_complete_metadata(global_version_id):
                logger.info(f"Using cached metadata for version {global_version_id}")
                return False, global_version_id
            else:
                logger.info(
                    f"Metadata incomplete for version {global_version_id}, sync needed"
                )
                return True, global_version_id

        except Exception as e:
            logger.error(f"Version detection failed: {e}")
            return True, None

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
                (global_version_id,),
            )

            row = await cursor.fetchone()
            if not row or not row[0]:  # No completed sync
                return False

            # Check basic entity count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM data_entities WHERE global_version_id = ?",
                (global_version_id,),
            )

            entity_count = (await cursor.fetchone())[0]
            return entity_count > 0  # Has some entities

    async def store_data_entities(
        self, global_version_id: int, entities: List[DataEntityInfo]
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
                (global_version_id,),
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
                        global_version_id,
                        entity.name,
                        entity.public_entity_name,
                        entity.public_collection_name,
                        entity.label_id,
                        entity.label_text,
                        entity.entity_category,
                        entity.data_service_enabled,
                        entity.data_management_enabled,
                        entity.is_read_only,
                    ),
                )

            await db.commit()
            logger.info(
                f"Stored {len(entities)} data entities for version {global_version_id}"
            )

    async def get_data_entities(
        self,
        global_version_id: Optional[int] = None,
        data_service_enabled: Optional[bool] = None,
        entity_category: Optional[str] = None,
        name_pattern: Optional[str] = None,
    ) -> List[DataEntityInfo]:
        """Get data entities with filtering

        Args:
            global_version_id: Global version ID (uses current if None)
            data_service_enabled: Filter by data service enabled status
            entity_category: Filter by entity category
            name_pattern: Filter by name pattern (SQL LIKE) - searches across all text fields:
                         name, public_entity_name, public_collection_name, label_id, label_text, entity_category

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
            # Search across all text fields with OR conditions
            conditions.append(
                "(name LIKE ? OR public_entity_name LIKE ? OR public_collection_name LIKE ? OR label_id LIKE ? OR label_text LIKE ? OR entity_category LIKE ?)"
            )
            # Add the pattern 6 times for each field
            params.extend([name_pattern] * 6)

        where_clause = " AND ".join(conditions)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"""SELECT name, public_entity_name, public_collection_name,
                           label_id, label_text, entity_category, data_service_enabled,
                           data_management_enabled, is_read_only
                    FROM data_entities
                    WHERE {where_clause}
                    ORDER BY name""",
                params,
            )

            entities = []
            for row in await cursor.fetchall():
                entities.append(
                    DataEntityInfo(
                        name=row[0],
                        public_entity_name=row[1],
                        public_collection_name=row[2],
                        label_id=row[3],
                        label_text=row[4],
                        entity_category=row[5],
                        data_service_enabled=row[6],
                        data_management_enabled=row[7],
                        is_read_only=row[8],
                    )
                )

            return entities

    async def store_public_entity_schema(
        self, global_version_id: int, entity_schema: PublicEntityInfo
    ):
        """Store public entity schema

        Args:
            global_version_id: Global version ID
            entity_schema: Public entity schema information
        """
        async with aiosqlite.connect(self.db_path) as db:
            # First, get existing entity ID if it exists for this name and version
            cursor = await db.execute(
                """SELECT id FROM public_entities 
                   WHERE name = ? AND global_version_id = ?""",
                (entity_schema.name, global_version_id),
            )

            existing_entity = await cursor.fetchone()
            existing_entity_id = existing_entity[0] if existing_entity else None

            # Clear existing related data for this entity and version
            if existing_entity_id:
                logger.debug(
                    f"Clearing existing data for entity {entity_schema.name} (ID: {existing_entity_id})"
                )

                # Delete related data in correct order (respecting foreign key constraints)
                # 1. Delete relation constraints first
                await db.execute(
                    """DELETE FROM relation_constraints 
                       WHERE navigation_property_id IN (
                           SELECT id FROM navigation_properties 
                           WHERE entity_id = ? AND global_version_id = ?
                       )""",
                    (existing_entity_id, global_version_id),
                )

                # 2. Delete action parameters
                await db.execute(
                    """DELETE FROM action_parameters 
                       WHERE action_id IN (
                           SELECT id FROM entity_actions 
                           WHERE entity_id = ? AND global_version_id = ?
                       )""",
                    (existing_entity_id, global_version_id),
                )

                # 3. Delete property group members
                await db.execute(
                    """DELETE FROM property_group_members 
                       WHERE property_group_id IN (
                           SELECT id FROM property_groups 
                           WHERE entity_id = ? AND global_version_id = ?
                       )""",
                    (existing_entity_id, global_version_id),
                )

                # 4. Delete direct child records
                await db.execute(
                    "DELETE FROM entity_properties WHERE entity_id = ? AND global_version_id = ?",
                    (existing_entity_id, global_version_id),
                )
                await db.execute(
                    "DELETE FROM navigation_properties WHERE entity_id = ? AND global_version_id = ?",
                    (existing_entity_id, global_version_id),
                )
                await db.execute(
                    "DELETE FROM property_groups WHERE entity_id = ? AND global_version_id = ?",
                    (existing_entity_id, global_version_id),
                )
                await db.execute(
                    "DELETE FROM entity_actions WHERE entity_id = ? AND global_version_id = ?",
                    (existing_entity_id, global_version_id),
                )

                # 5. Finally delete the entity itself
                await db.execute(
                    "DELETE FROM public_entities WHERE id = ? AND global_version_id = ?",
                    (existing_entity_id, global_version_id),
                )

            # Insert new entity
            cursor = await db.execute(
                """INSERT INTO public_entities
                   (global_version_id, name, entity_set_name, label_id, label_text,
                    is_read_only, configuration_enabled)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    global_version_id,
                    entity_schema.name,
                    entity_schema.entity_set_name,
                    entity_schema.label_id,
                    entity_schema.label_text,
                    entity_schema.is_read_only,
                    entity_schema.configuration_enabled,
                ),
            )

            entity_id = cursor.lastrowid

            # Store properties
            prop_order = 0
            for prop in entity_schema.properties:
                prop_order += 1
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
                        entity_id,
                        global_version_id,
                        prop.name,
                        prop.type_name,
                        prop.data_type,
                        prop.data_type,
                        prop.label_id,
                        prop.label_text,
                        prop.is_key,
                        prop.is_mandatory,
                        prop.configuration_enabled,
                        prop.allow_edit,
                        prop.allow_edit_on_create,
                        prop.is_dimension,
                        prop.dimension_relation,
                        prop.is_dynamic_dimension,
                        prop.dimension_legal_entity_property,
                        prop.dimension_type_property,
                        prop_order,
                    ),
                )

            # Store navigation properties
            for nav_prop in entity_schema.navigation_properties:
                nav_cursor = await db.execute(
                    """INSERT INTO navigation_properties
                       (entity_id, global_version_id, name, related_entity,
                        related_relation_name, cardinality)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        entity_id,
                        global_version_id,
                        nav_prop.name,
                        nav_prop.related_entity,
                        nav_prop.related_relation_name,
                        nav_prop.cardinality.value,  # Convert enum to string value
                    ),
                )

                nav_prop_id = nav_cursor.lastrowid

                # Store relation constraints
                for constraint in nav_prop.constraints:
                    await db.execute(
                        """INSERT INTO relation_constraints
                           (navigation_property_id, global_version_id, constraint_type,
                            property_name, referenced_property, related_property,
                            fixed_value, fixed_value_str)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            nav_prop_id,
                            global_version_id,
                            constraint.constraint_type,
                            getattr(constraint, "property", None),
                            getattr(constraint, "referenced_property", None),
                            getattr(constraint, "related_property", None),
                            getattr(constraint, "value", None),
                            getattr(constraint, "value_str", None),
                        ),
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
                        entity_id,
                        global_version_id,
                        action.name,
                        action.binding_kind.value,  # Convert enum to string value
                        entity_schema.name,
                        entity_schema.entity_set_name,
                        action.return_type.type_name if action.return_type else None,
                        (
                            action.return_type.is_collection
                            if action.return_type
                            else False
                        ),
                        (
                            action.return_type.odata_xpp_type
                            if action.return_type
                            else None
                        ),
                        action.field_lookup,
                    ),
                )

                action_id = action_cursor.lastrowid

                # Store action parameters
                param_order = 0
                for param in action.parameters:
                    param_order += 1
                    await db.execute(
                        """INSERT INTO action_parameters
                           (action_id, global_version_id, name, type_name,
                            is_collection, odata_xpp_type, parameter_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            action_id,
                            global_version_id,
                            param.name,
                            param.type.type_name,
                            param.type.is_collection,
                            param.type.type_name,
                            param_order,
                        ),
                    )

            # Store property groups
            for group in entity_schema.property_groups:
                group_cursor = await db.execute(
                    """INSERT INTO property_groups
                       (entity_id, global_version_id, name)
                       VALUES (?, ?, ?)""",
                    (entity_id, global_version_id, group.name),
                )
                
                group_id = group_cursor.lastrowid
                
                # Store property group members
                for property_name in group.properties:
                    await db.execute(
                        """INSERT INTO property_group_members
                           (property_group_id, global_version_id, property_name)
                           VALUES (?, ?, ?)""",
                        (group_id, global_version_id, property_name),
                    )

            await db.commit()
            logger.debug(f"Stored entity schema for {entity_schema.name}")

    async def get_public_entity_schema(
        self, entity_name: str, global_version_id: Optional[int] = None
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
                (entity_name, global_version_id),
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
                (entity_id,),
            )

            properties = []
            for prop_row in await cursor.fetchall():
                properties.append(
                    PublicEntityPropertyInfo(
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
                        property_order=prop_row[16],
                    )
                )

            # Get navigation properties
            cursor = await db.execute(
                """SELECT id, name, related_entity, related_relation_name, cardinality
                   FROM navigation_properties
                   WHERE entity_id = ?
                   ORDER BY name""",
                (entity_id,),
            )

            navigation_properties = []
            for nav_row in await cursor.fetchall():
                nav_prop_id = nav_row[0]
                
                # Get constraints for this navigation property
                constraint_cursor = await db.execute(
                    """SELECT constraint_type, property_name, referenced_property,
                              related_property, fixed_value, fixed_value_str
                       FROM relation_constraints
                       WHERE navigation_property_id = ?
                       ORDER BY constraint_type""",
                    (nav_prop_id,),
                )

                constraints = []
                for constraint_row in await constraint_cursor.fetchall():
                    constraint_type = constraint_row[0]
                    
                    if constraint_type == "Referential":
                        constraints.append(
                            ReferentialConstraintInfo(
                                property=constraint_row[1],
                                referenced_property=constraint_row[2],
                            )
                        )
                    elif constraint_type == "Fixed":
                        constraints.append(
                            FixedConstraintInfo(
                                property=constraint_row[1],
                                value=constraint_row[4],
                                value_str=constraint_row[5],
                            )
                        )
                    elif constraint_type == "RelatedFixed":
                        constraints.append(
                            RelatedFixedConstraintInfo(
                                related_property=constraint_row[3],
                                value=constraint_row[4],
                                value_str=constraint_row[5],
                            )
                        )

                navigation_properties.append(
                    NavigationPropertyInfo(
                        name=nav_row[1],
                        related_entity=nav_row[2],
                        related_relation_name=nav_row[3],
                        cardinality=Cardinality(nav_row[4]) if nav_row[4] else Cardinality.SINGLE,
                        constraints=constraints,
                    )
                )

            # Get property groups
            cursor = await db.execute(
                """SELECT id, name
                   FROM property_groups
                   WHERE entity_id = ?
                   ORDER BY name""",
                (entity_id,),
            )

            property_groups = []
            for group_row in await cursor.fetchall():
                group_id = group_row[0]
                
                # Get property group members
                member_cursor = await db.execute(
                    """SELECT property_name
                       FROM property_group_members
                       WHERE property_group_id = ?
                       ORDER BY property_name""",
                    (group_id,),
                )

                property_names = [row[0] for row in await member_cursor.fetchall()]

                property_groups.append(
                    PropertyGroupInfo(
                        name=group_row[1],
                        properties=property_names,
                    )
                )

            # Get actions
            cursor = await db.execute(
                """SELECT id, name, binding_kind, return_type_name, return_is_collection,
                          return_odata_xpp_type, field_lookup
                   FROM entity_actions
                   WHERE entity_id = ?
                   ORDER BY name""",
                (entity_id,),
            )

            actions = []
            for action_row in await cursor.fetchall():
                action_id = action_row[0]
                
                # Get action parameters
                param_cursor = await db.execute(
                    """SELECT name, type_name, is_collection, odata_xpp_type, parameter_order
                       FROM action_parameters
                       WHERE action_id = ?
                       ORDER BY parameter_order""",
                    (action_id,),
                )

                parameters = []
                for param_row in await param_cursor.fetchall():
                    parameters.append(
                        ActionParameterInfo(
                            name=param_row[0],
                            type=ActionParameterTypeInfo(
                                type_name=param_row[1],
                                is_collection=param_row[2],
                                odata_xpp_type=param_row[3],
                            ),
                            parameter_order=param_row[4],
                        )
                    )

                # Create return type if present
                return_type = None
                if action_row[3]:  # return_type_name
                    return_type = ActionReturnTypeInfo(
                        type_name=action_row[3],
                        is_collection=action_row[4],
                        odata_xpp_type=action_row[5],
                    )

                actions.append(
                    PublicEntityActionInfo(
                        name=action_row[1],
                        binding_kind=ODataBindingKind(action_row[2]),
                        parameters=parameters,
                        return_type=return_type,
                        field_lookup=action_row[6],
                    )
                )

            return PublicEntityInfo(
                name=entity_row[1],
                entity_set_name=entity_row[2],
                label_id=entity_row[3],
                label_text=entity_row[4],
                is_read_only=entity_row[5],
                configuration_enabled=entity_row[6],
                properties=properties,
                navigation_properties=navigation_properties,
                property_groups=property_groups,
                actions=actions,
            )

    async def store_enumerations(
        self, global_version_id: int, enumerations: List[EnumerationInfo]
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
                (global_version_id,),
            )

            for enum_info in enumerations:
                # Insert enumeration
                cursor = await db.execute(
                    """INSERT INTO enumerations
                       (global_version_id, name, label_id, label_text)
                       VALUES (?, ?, ?, ?)""",
                    (
                        global_version_id,
                        enum_info.name,
                        enum_info.label_id,
                        enum_info.label_text,
                    ),
                )

                enum_id = cursor.lastrowid

                # Insert members
                member_order = 0
                for member in enum_info.members:
                    member_order += 1
                    await db.execute(
                        """INSERT INTO enumeration_members
                           (enumeration_id, global_version_id, name, value,
                            label_id, label_text, configuration_enabled, member_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            enum_id,
                            global_version_id,
                            member.name,
                            member.value,
                            member.label_id,
                            member.label_text,
                            member.configuration_enabled,
                            member_order,
                        ),
                    )

            await db.commit()
            logger.info(
                f"Stored {len(enumerations)} enumerations for version {global_version_id}"
            )

    async def get_enumeration_info(
        self, enum_name: str, global_version_id: Optional[int] = None
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
                (enum_name, global_version_id),
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
                (enum_id,),
            )

            members = []
            for member_row in await cursor.fetchall():
                members.append(
                    EnumerationMemberInfo(
                        name=member_row[0],
                        value=member_row[1],
                        label_id=member_row[2],
                        label_text=member_row[3],
                        configuration_enabled=member_row[4],
                        member_order=member_row[5],
                    )
                )

            return EnumerationInfo(
                name=enum_row[1],
                label_id=enum_row[2],
                label_text=enum_row[3],
                members=members,
            )

    async def mark_sync_completed(
        self,
        global_version_id: int,
        entity_count: int = 0,
        action_count: int = 0,
        enumeration_count: int = 0,
        label_count: int = 0,
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
                (
                    global_version_id,
                    entity_count,
                    action_count,
                    enumeration_count,
                    label_count,
                ),
            )

            await db.commit()
            logger.info(f"Marked sync completed for version {global_version_id}")

    async def _get_current_global_version_id(self) -> Optional[int]:
        """Get current global version ID for environment

        Returns:
            Current global version ID if available
        """
        if self._current_global_version_id is not None:
            return self._current_global_version_id

        if self._environment_id is None:
            return None

        result = await self.version_manager.get_environment_version_info(
            self._environment_id
        )
        if result:
            global_version_id, version_info = result
            self._current_version_info = version_info
            self._current_global_version_id = global_version_id
            return global_version_id

        return None

    # Label Operations

    async def get_label(
        self,
        label_id: str,
        language: str = "en-US",
        global_version_id: Optional[int] = None,
    ) -> Optional[str]:
        """Get label text from cache

        Args:
            label_id: Label identifier (e.g., "@SYS13342")
            language: Language code (e.g., "en-US")
            global_version_id: Global version ID (uses current if None, includes temporary entries)

        Returns:
            Label text or None if not found or expired
        """
        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()

        async with aiosqlite.connect(self.db_path) as db:
            if global_version_id is not None:
                # Search for specific version
                cursor = await db.execute(
                    """SELECT label_text, expires_at
                       FROM labels_cache 
                       WHERE global_version_id = ? AND label_id = ? AND language = ?
                       AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)""",
                    (global_version_id, label_id, language),
                )
            else:
                # Search across all versions (including temporary entries)
                cursor = await db.execute(
                    """SELECT label_text, expires_at
                       FROM labels_cache 
                       WHERE label_id = ? AND language = ?
                       AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                       ORDER BY global_version_id DESC
                       LIMIT 1""",  # Get the highest version (prefer actual versions over temporary)
                    (label_id, language),
                )

            row = await cursor.fetchone()
            if row:
                # Update hit count and last accessed time
                if global_version_id is not None:
                    await db.execute(
                        """UPDATE labels_cache 
                           SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP
                           WHERE global_version_id = ? AND label_id = ? AND language = ?""",
                        (global_version_id, label_id, language),
                    )
                else:
                    # Update for the found entry
                    await db.execute(
                        """UPDATE labels_cache 
                           SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP
                           WHERE label_id = ? AND language = ? AND label_text = ?""",
                        (label_id, language, row[0]),
                    )
                await db.commit()

                logger.debug(f"Label cache hit: {label_id} ({language}) -> {row[0]}")
                return row[0]

            logger.debug(f"Label cache miss: {label_id} ({language})")
            return None

    async def set_label(
        self,
        label_id: str,
        label_text: str,
        language: str = "en-US",
        global_version_id: Optional[int] = None,
        ttl_hours: int = 24,
    ):
        """Set label in cache

        Args:
            label_id: Label identifier
            label_text: Label text value
            language: Language code
            global_version_id: Global version ID (uses current if None)
            ttl_hours: Time to live in hours
        """
        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()
            if global_version_id is None:
                # Create a temporary version for immediate label caching
                logger.warning(
                    "No global version ID available, creating temporary cache entry"
                )
                global_version_id = -1  # Use -1 for temporary entries

        # Calculate expiration time
        from datetime import datetime, timedelta, timezone

        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO labels_cache
                   (global_version_id, label_id, language, label_text, expires_at, hit_count, last_accessed)
                   VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)""",
                (
                    global_version_id,
                    label_id,
                    language,
                    label_text,
                    expires_at.isoformat(),
                ),
            )
            await db.commit()

        logger.debug(f"Label cached: {label_id} ({language}) -> {label_text}")

    async def set_labels_batch(
        self,
        labels: List[LabelInfo],
        global_version_id: Optional[int] = None,
        ttl_hours: int = 24,
    ):
        """Set multiple labels in cache efficiently

        Args:
            labels: List of LabelInfo objects
            global_version_id: Global version ID (uses current if None)
            ttl_hours: Time to live in hours
        """
        if not labels:
            return

        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()
            if global_version_id is None:
                # Create a temporary version for immediate label caching
                logger.warning(
                    "No global version ID available, creating temporary cache entries"
                )
                global_version_id = -1  # Use -1 for temporary entries

        # Calculate expiration time
        from datetime import datetime, timedelta, timezone

        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

        # Prepare batch data
        label_data = []
        for label in labels:
            label_data.append(
                (
                    global_version_id,
                    label.id,
                    label.language,
                    label.value,
                    expires_at.isoformat(),
                )
            )

        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """INSERT OR REPLACE INTO labels_cache
                   (global_version_id, label_id, language, label_text, expires_at, hit_count, last_accessed)
                   VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)""",
                label_data,
            )
            await db.commit()

        logger.info(
            f"Batch cached {len(labels)} labels for version {global_version_id}"
        )

    async def get_labels_batch(
        self,
        label_ids: List[str],
        language: str = "en-US",
        global_version_id: Optional[int] = None,
    ) -> Dict[str, str]:
        """Get multiple labels from cache efficiently

        Args:
            label_ids: List of label IDs to retrieve
            language: Language code
            global_version_id: Global version ID (uses current if None, includes temporary entries)

        Returns:
            Dictionary mapping label_id to label_text for found labels
        """
        if not label_ids:
            return {}

        if global_version_id is None:
            global_version_id = await self._get_current_global_version_id()

        # Create placeholders for SQL IN clause
        placeholders = ",".join("?" for _ in label_ids)

        async with aiosqlite.connect(self.db_path) as db:
            if global_version_id is not None:
                # Search for specific version
                params = [global_version_id, language] + label_ids
                query = f"""SELECT label_id, label_text
                            FROM labels_cache 
                            WHERE global_version_id = ? AND language = ? AND label_id IN ({placeholders})
                            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)"""
            else:
                # Search across all versions (including temporary entries)
                params = [language] + label_ids
                query = f"""SELECT label_id, label_text
                            FROM labels_cache 
                            WHERE language = ? AND label_id IN ({placeholders})
                            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                            ORDER BY global_version_id DESC"""  # Prefer actual versions over temporary

            cursor = await db.execute(query, params)

            results = {}
            found_ids = []
            async for row in cursor:
                if row[0] not in results:  # Only use first match (highest version)
                    results[row[0]] = row[1]
                    found_ids.append(row[0])

            # Update hit counts for found labels
            if found_ids and global_version_id is not None:
                update_placeholders = ",".join("?" for _ in found_ids)
                await db.execute(
                    f"""UPDATE labels_cache 
                        SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP
                        WHERE global_version_id = ? AND language = ? AND label_id IN ({update_placeholders})""",
                    [global_version_id, language] + found_ids,
                )
                await db.commit()

            logger.debug(f"Label batch lookup: {len(results)}/{len(label_ids)} found")
            return results

    async def clear_expired_labels(self, global_version_id: Optional[int] = None):
        """Clear expired labels from cache

        Args:
            global_version_id: Global version ID to clear (clears all if None)
        """
        async with aiosqlite.connect(self.db_path) as db:
            if global_version_id is not None:
                cursor = await db.execute(
                    """DELETE FROM labels_cache 
                       WHERE global_version_id = ? AND expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP""",
                    (global_version_id,),
                )
            else:
                cursor = await db.execute(
                    """DELETE FROM labels_cache 
                       WHERE expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP"""
                )

            deleted_count = cursor.rowcount
            await db.commit()

        logger.info(f"Cleared {deleted_count} expired labels")

    async def get_label_cache_statistics(
        self, global_version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get label cache statistics

        Args:
            global_version_id: Global version ID to get stats for (all if None)

        Returns:
            Dictionary with label cache statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Base query conditions
            if global_version_id is not None:
                version_filter = "WHERE global_version_id = ?"
                params = [global_version_id]
            else:
                version_filter = ""
                params = []

            # Total labels
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM labels_cache {version_filter}", params
            )
            stats["total_labels"] = (await cursor.fetchone())[0]

            # Expired labels
            cursor = await db.execute(
                f"""SELECT COUNT(*) FROM labels_cache 
                    {version_filter} {'AND' if version_filter else 'WHERE'} 
                    expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP""",
                params,
            )
            stats["expired_labels"] = (await cursor.fetchone())[0]

            # Active labels
            stats["active_labels"] = stats["total_labels"] - stats["expired_labels"]

            # Languages
            cursor = await db.execute(
                f"""SELECT language, COUNT(*) FROM labels_cache 
                    {version_filter} {'AND' if version_filter else 'WHERE'} 
                    (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    GROUP BY language ORDER BY COUNT(*) DESC""",
                params,
            )
            stats["languages"] = dict(await cursor.fetchall())

            # Hit statistics
            cursor = await db.execute(
                f"""SELECT 
                      COUNT(*) as accessed_labels,
                      SUM(hit_count) as total_hits,
                      AVG(hit_count) as avg_hits_per_label,
                      MAX(hit_count) as max_hits
                    FROM labels_cache 
                    {version_filter} {'AND' if version_filter else 'WHERE'} 
                    hit_count > 0""",
                params,
            )
            hit_stats = await cursor.fetchone()
            if hit_stats[0]:  # If there are accessed labels
                stats["hit_statistics"] = {
                    "accessed_labels": hit_stats[0],
                    "total_hits": hit_stats[1] or 0,
                    "average_hits_per_label": round(hit_stats[2] or 0, 2),
                    "max_hits": hit_stats[3] or 0,
                }
            else:
                stats["hit_statistics"] = {
                    "accessed_labels": 0,
                    "total_hits": 0,
                    "average_hits_per_label": 0,
                    "max_hits": 0,
                }

            return stats

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
        stats["version_manager"] = version_stats

        # Current version info
        current_version = await self._get_current_global_version_id()
        if current_version:
            version_info = await self.version_manager.get_global_version_info(
                current_version
            )
            if version_info:
                stats["current_version"] = {
                    "global_version_id": version_info.id,
                    "version_hash": version_info.version_hash,
                    "modules_count": len(version_info.sample_modules),
                    "reference_count": version_info.reference_count,
                }

        # Label cache statistics
        label_stats = await self.get_label_cache_statistics(current_version)
        stats["label_cache"] = label_stats

        return stats

    def create_search_engine(self):
        """Create a search engine instance for this cache.
        
        Returns:
            VersionAwareSearchEngine instance
        """
        from .search_engine_v2 import VersionAwareSearchEngine
        return VersionAwareSearchEngine(self)
