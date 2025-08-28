"""Metadata API operations for D365 F&O client."""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from d365fo_client.crud import CrudOperations

from .labels import LabelOperations
from .models import (
    ActionInfo,
    ActionParameterInfo,
    ActionParameterTypeInfo,
    ActionReturnTypeInfo,
    Cardinality,
    DataEntityInfo,
    EntityCategory,
    EnumerationInfo,
    EnumerationMemberInfo,
    FixedConstraintInfo,
    NavigationPropertyInfo,
    ODataBindingKind,
    PropertyGroupInfo,
    PublicEntityActionInfo,
    PublicEntityInfo,
    PublicEntityPropertyInfo,
    QueryOptions,
    ReferentialConstraintInfo,
    RelatedFixedConstraintInfo,
)
from .query import QueryBuilder
from .session import SessionManager

logger = logging.getLogger(__name__)


class MetadataAPIOperations:
    """Operations for metadata API endpoints"""

    def __init__(
        self,
        session_manager: SessionManager,
        metadata_url: str,
        label_ops: Optional[LabelOperations] = None,
    ):
        """Initialize metadata API operations

        Args:
            session_manager: Session manager for HTTP requests
            metadata_url: Base metadata URL
            label_ops: Label operations for resolving labels
        """
        self.session_manager = session_manager
        self.metadata_url = metadata_url
        self.label_ops = label_ops
        self.crud_ops = CrudOperations(
            self.session_manager, self.session_manager.config.base_url
        )

    def _parse_public_entity_from_json(self, item: Dict[str, Any]) -> PublicEntityInfo:
        """Parse a public entity from JSON data returned by PublicEntities API

        Args:
            item: JSON object representing a single public entity

        Returns:
            PublicEntityInfo object with full details
        """
        # Create entity info
        entity = PublicEntityInfo(
            name=item.get("Name", ""),
            entity_set_name=item.get("EntitySetName", ""),
            label_id=item.get("LabelId"),
            is_read_only=item.get("IsReadOnly", False),
            configuration_enabled=item.get("ConfigurationEnabled", True),
        )

        # Process properties
        prop_order = 1
        for prop_data in item.get("Properties", []):
            prop = PublicEntityPropertyInfo(
                name=prop_data.get("Name", ""),
                type_name=prop_data.get("TypeName", ""),
                data_type=prop_data.get("DataType", ""),
                odata_xpp_type=prop_data.get("DataType", ""),
                label_id=prop_data.get("LabelId"),
                is_key=prop_data.get("IsKey", False),
                is_mandatory=prop_data.get("IsMandatory", False),
                configuration_enabled=prop_data.get("ConfigurationEnabled", True),
                allow_edit=prop_data.get("AllowEdit", True),
                allow_edit_on_create=prop_data.get("AllowEditOnCreate", True),
                is_dimension=prop_data.get("IsDimension", False),
                dimension_relation=prop_data.get("DimensionRelation"),
                is_dynamic_dimension=prop_data.get("IsDynamicDimension", False),
                dimension_legal_entity_property=prop_data.get(
                    "DimensionLegalEntityProperty"
                ),
                dimension_type_property=prop_data.get("DimensionTypeProperty"),
                property_order=prop_order,
            )
            prop_order += 1
            entity.properties.append(prop)

        # Process navigation properties
        for nav_data in item.get("NavigationProperties", []):
            # Convert cardinality string to enum
            cardinality_str = nav_data.get("Cardinality", "Single")
            try:
                if cardinality_str == "Single":
                    cardinality = Cardinality.SINGLE
                elif cardinality_str == "Multiple":
                    cardinality = Cardinality.MULTIPLE
                else:
                    cardinality = Cardinality.SINGLE  # Default
            except Exception:
                cardinality = Cardinality.SINGLE
                
            nav_prop = NavigationPropertyInfo(
                name=nav_data.get("Name", ""),
                related_entity=nav_data.get("RelatedEntity", ""),
                related_relation_name=nav_data.get("RelatedRelationName"),
                cardinality=cardinality,
            )

            # Process constraints
            for constraint_data in nav_data.get("Constraints", []):
                odata_type = constraint_data.get("@odata.type", "")
                
                if "ReferentialConstraint" in odata_type:
                    # Referential constraint (foreign key relationship)
                    constraint = ReferentialConstraintInfo(
                        property=constraint_data.get("Property", ""),
                        referenced_property=constraint_data.get(
                            "ReferencedProperty", ""
                        ),
                    )
                    nav_prop.constraints.append(constraint)
                    
                elif "RelatedFixedConstraint" in odata_type:
                    # Related fixed constraint (check this before FixedConstraint)
                    constraint = RelatedFixedConstraintInfo(
                        related_property=constraint_data.get("RelatedProperty", ""),
                        value=constraint_data.get("Value"),
                        value_str=constraint_data.get("ValueStr", constraint_data.get("StringValue")),
                    )
                    nav_prop.constraints.append(constraint)
                    
                elif "FixedConstraint" in odata_type:
                    # Fixed value constraint
                    constraint = FixedConstraintInfo(
                        property=constraint_data.get("Property", ""),
                        value=constraint_data.get("Value"),
                        value_str=constraint_data.get("ValueStr", constraint_data.get("StringValue")),
                    )
                    nav_prop.constraints.append(constraint)
                    nav_prop.constraints.append(constraint)

            entity.navigation_properties.append(nav_prop)

        # Process property groups
        for group_data in item.get("PropertyGroups", []):
            prop_group = PropertyGroupInfo(
                name=group_data.get("Name", ""),
                properties=group_data.get("Properties", []),
            )
            entity.property_groups.append(prop_group)

        # Process actions
        for action_data in item.get("Actions", []):
            # Convert binding kind string to enum
            binding_kind_str = action_data.get("BindingKind", "BoundToEntitySet")
            try:
                # Try to map the string to the enum
                if binding_kind_str == "BoundToEntityInstance":
                    binding_kind = ODataBindingKind.BOUND_TO_ENTITY_INSTANCE
                elif binding_kind_str == "BoundToEntitySet":
                    binding_kind = ODataBindingKind.BOUND_TO_ENTITY_SET
                elif binding_kind_str == "Unbound":
                    binding_kind = ODataBindingKind.UNBOUND
                else:
                    # Default to BoundToEntitySet if unknown
                    binding_kind = ODataBindingKind.BOUND_TO_ENTITY_SET
            except Exception:
                binding_kind = ODataBindingKind.BOUND_TO_ENTITY_SET
                
            action = PublicEntityActionInfo(
                name=action_data.get("Name", ""),
                binding_kind=binding_kind,
                field_lookup=action_data.get("FieldLookup"),
            )

            # Process parameters
            for param_data in action_data.get("Parameters", []):
                param_type_data = param_data.get("Type", {})
                param_type = ActionParameterTypeInfo(
                    type_name=param_type_data.get("TypeName", ""),
                    is_collection=param_type_data.get("IsCollection", False),
                )

                param = ActionParameterInfo(
                    name=param_data.get("Name", ""), type=param_type
                )
                action.parameters.append(param)

            # Process return type
            return_type_data = action_data.get("ReturnType")
            if return_type_data:
                action.return_type = ActionReturnTypeInfo(
                    type_name=return_type_data.get("TypeName", ""),
                    is_collection=return_type_data.get("IsCollection", False),
                )

            entity.actions.append(action)

        return entity

    def _parse_public_enumeration_from_json(
        self, item: Dict[str, Any]
    ) -> EnumerationInfo:
        """Parse a public enumeration from JSON data returned by PublicEnumerations API

        Args:
            item: JSON object representing a single public enumeration

        Returns:
            EnumerationInfo object with full details
        """
        # Create enumeration info
        enum = EnumerationInfo(name=item.get("Name", ""), label_id=item.get("LabelId"))

        # Process members
        for member_data in item.get("Members", []):
            member = EnumerationMemberInfo(
                name=member_data.get("Name", ""),
                value=member_data.get("Value", 0),
                label_id=member_data.get("LabelId"),
                configuration_enabled=member_data.get("ConfigurationEnabled", True),
            )
            enum.members.append(member)

        return enum

    # DataEntities endpoint operations

    async def get_data_entities(
        self, options: Optional[QueryOptions] = None
    ) -> Dict[str, Any]:
        """Get data entities from DataEntities endpoint

        Args:
            options: OData query options

        Returns:
            List of DataEntityInfo objects
        """
        session = await self.session_manager.get_session()
        url = f"{self.metadata_url}/DataEntities"

        params = QueryBuilder.build_query_params(options)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                raise Exception(
                    f"Failed to get data entities: {response.status} - {await response.text()}"
                )

    async def search_data_entities(
        self,
        pattern: str = "",
        entity_category: Optional[str] = None,
        data_service_enabled: Optional[bool] = None,
        data_management_enabled: Optional[bool] = None,
        is_read_only: Optional[bool] = None,
    ) -> List[DataEntityInfo]:
        """Search data entities with filtering

        Args:
            pattern: Search pattern for entity name (regex supported)
            entity_category: Filter by entity category (e.g., 'Master', 'Transaction')
            data_service_enabled: Filter by data service enabled status
            data_management_enabled: Filter by data management enabled status
            is_read_only: Filter by read-only status

        Returns:
            List of matching data entities
        """
        # Build OData filter
        filters = []

        if pattern:
            # Use contains for pattern matching
            filters.append(f"contains(tolower(Name), '{pattern.lower()}')")

        if entity_category is not None:
            # EntityCategory is an enum, use the correct enum syntax
            filters.append(
                f"EntityCategory eq Microsoft.Dynamics.Metadata.EntityCategory'{entity_category}'"
            )

        if data_service_enabled is not None:
            filters.append(f"DataServiceEnabled eq {str(data_service_enabled).lower()}")

        if data_management_enabled is not None:
            filters.append(
                f"DataManagementEnabled eq {str(data_management_enabled).lower()}"
            )

        if is_read_only is not None:
            filters.append(f"IsReadOnly eq {str(is_read_only).lower()}")

        options = QueryOptions()
        if filters:
            options.filter = " and ".join(filters)

        data = await self.get_data_entities(options)

        entities = []
        for item in data.get("value", []):
            # Convert entity category string to enum
            entity_category_str = item.get("EntityCategory")
            entity_category = None
            if entity_category_str:
                try:
                    # Try to map the string to the enum
                    if entity_category_str == "Master":
                        entity_category = EntityCategory.MASTER
                    elif entity_category_str == "Transaction":
                        entity_category = EntityCategory.TRANSACTION
                    elif entity_category_str == "Configuration":
                        entity_category = EntityCategory.CONFIGURATION
                    elif entity_category_str == "Reference":
                        entity_category = EntityCategory.REFERENCE
                    elif entity_category_str == "Document":
                        entity_category = EntityCategory.DOCUMENT
                    elif entity_category_str == "Parameters":
                        entity_category = EntityCategory.PARAMETERS
                    # If no match, leave as None
                except Exception:
                    entity_category = None
            
            entity = DataEntityInfo(
                name=item.get("Name", ""),
                public_entity_name=item.get("PublicEntityName", ""),
                public_collection_name=item.get("PublicCollectionName", ""),
                label_id=item.get("LabelId"),
                data_service_enabled=item.get("DataServiceEnabled", False),
                data_management_enabled=item.get("DataManagementEnabled", False),
                entity_category=entity_category,
                is_read_only=item.get("IsReadOnly", False),
            )
            entities.append(entity)

        # Apply regex pattern matching if provided
        if pattern and re.search(r"[.*+?^${}()|[\]\\]", pattern):
            flags = re.IGNORECASE
            entities = [e for e in entities if re.search(pattern, e.name, flags)]

        return entities

    async def get_data_entity_info(
        self, entity_name: str, resolve_labels: bool = True, language: str = "en-US"
    ) -> Optional[DataEntityInfo]:
        """Get detailed information about a specific data entity

        Args:
            entity_name: Name of the data entity
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            DataEntityInfo object or None if not found
        """
        try:
            session = await self.session_manager.get_session()
            url = f"{self.metadata_url}/DataEntities('{entity_name}')"

            async with session.get(url) as response:
                if response.status == 200:
                    item = await response.json()
                    
                    # Convert entity category string to enum
                    entity_category_str = item.get("EntityCategory")
                    entity_category = None
                    if entity_category_str:
                        try:
                            # Try to map the string to the enum
                            if entity_category_str == "Master":
                                entity_category = EntityCategory.MASTER
                            elif entity_category_str == "Transaction":
                                entity_category = EntityCategory.TRANSACTION
                            elif entity_category_str == "Configuration":
                                entity_category = EntityCategory.CONFIGURATION
                            elif entity_category_str == "Reference":
                                entity_category = EntityCategory.REFERENCE
                            elif entity_category_str == "Document":
                                entity_category = EntityCategory.DOCUMENT
                            elif entity_category_str == "Parameters":
                                entity_category = EntityCategory.PARAMETERS
                            # If no match, leave as None
                        except Exception:
                            entity_category = None
                    
                    entity = DataEntityInfo(
                        name=item.get("Name", ""),
                        public_entity_name=item.get("PublicEntityName", ""),
                        public_collection_name=item.get("PublicCollectionName", ""),
                        label_id=item.get("LabelId"),
                        data_service_enabled=item.get("DataServiceEnabled", False),
                        data_management_enabled=item.get(
                            "DataManagementEnabled", False
                        ),
                        entity_category=entity_category,
                        is_read_only=item.get("IsReadOnly", False),
                    )

                    # Resolve labels if requested
                    if resolve_labels and self.label_ops and entity.label_id:
                        entity.label_text = await self.label_ops.get_label_text(
                            entity.label_id, language
                        )

                    return entity
                elif response.status == 404:
                    return None
                else:
                    raise Exception(
                        f"Failed to get data entity: {response.status} - {await response.text()}"
                    )

        except Exception as e:
            raise Exception(f"Error getting data entity '{entity_name}': {e}")

    # PublicEntities endpoint operations

    async def get_public_entities(
        self, options: Optional[QueryOptions] = None
    ) -> Dict[str, Any]:
        """Get public entities from PublicEntities endpoint

        Args:
            options: OData query options

        Returns:
            Response containing public entities
        """
        session = await self.session_manager.get_session()
        url = f"{self.metadata_url}/PublicEntities"

        params = QueryBuilder.build_query_params(options)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(
                    f"Failed to get public entities: {response.status} - {await response.text()}"
                )

    async def get_all_public_entities_with_details(
        self, resolve_labels: bool = False, language: str = "en-US"
    ) -> List[PublicEntityInfo]:
        """Get all public entities with full details in a single optimized call

        This method uses the fact that PublicEntities endpoint returns complete entity data,
        avoiding the need for individual calls to PublicEntities('EntityName').

        Args:
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            List of PublicEntityInfo objects with complete details
        """
        # Get all public entities with full details
        entities_data = await self.get_public_entities()
        entities = []

        for item in entities_data.get("value", []):
            try:
                # Parse entity using utility function
                entity = self._parse_public_entity_from_json(item)

                # Resolve labels if requested
                if resolve_labels and self.label_ops:
                    await self._resolve_public_entity_labels(entity, language)

                entities.append(entity)

            except Exception as e:
                # Log error but continue processing other entities
                logger.warning(
                    f"Failed to parse entity {item.get('Name', 'unknown')}: {e}"
                )
                continue

        return entities

    async def search_public_entities(
        self,
        pattern: str = "",
        is_read_only: Optional[bool] = None,
        configuration_enabled: Optional[bool] = None,
    ) -> List[PublicEntityInfo]:
        """Search public entities with filtering

        Args:
            pattern: Search pattern for entity name (regex supported)
            is_read_only: Filter by read-only status
            configuration_enabled: Filter by configuration enabled status

        Returns:
            List of matching public entities (without detailed properties)
        """
        # Build OData filter
        filters = []

        if pattern:
            # Use contains for pattern matching
            filters.append(f"contains(tolower(Name), '{pattern.lower()}')")

        if is_read_only is not None:
            filters.append(f"IsReadOnly eq {str(is_read_only).lower()}")

        if configuration_enabled is not None:
            filters.append(
                f"ConfigurationEnabled eq {str(configuration_enabled).lower()}"
            )

        options = QueryOptions()
        if filters:
            options.filter = " and ".join(filters)

        # Only select basic fields for search to improve performance
        options.select = [
            "Name",
            "EntitySetName",
            "LabelId",
            "IsReadOnly",
            "ConfigurationEnabled",
        ]

        data = await self.get_public_entities(options)

        entities = []
        for item in data.get("value", []):
            entity = PublicEntityInfo(
                name=item.get("Name", ""),
                entity_set_name=item.get("EntitySetName", ""),
                label_id=item.get("LabelId"),
                is_read_only=item.get("IsReadOnly", False),
                configuration_enabled=item.get("ConfigurationEnabled", True),
            )
            entities.append(entity)

        # Apply regex pattern matching if provided
        if pattern and re.search(r"[.*+?^${}()|[\]\\]", pattern):
            flags = re.IGNORECASE
            entities = [e for e in entities if re.search(pattern, e.name, flags)]

        return entities

    async def get_public_entity_info(
        self, entity_name: str, resolve_labels: bool = True, language: str = "en-US"
    ) -> Optional[PublicEntityInfo]:
        """Get detailed information about a specific public entity

        Args:
            entity_name: Name of the public entity
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            PublicEntityInfo object with full details or None if not found
        """
        try:
            session = await self.session_manager.get_session()
            url = f"{self.metadata_url}/PublicEntities('{entity_name}')"

            async with session.get(url) as response:
                if response.status == 200:
                    item = await response.json()

                    # Use utility function to parse the entity
                    entity = self._parse_public_entity_from_json(item)

                    # Resolve labels if requested
                    if resolve_labels and self.label_ops:
                        await self._resolve_public_entity_labels(entity, language)

                    return entity
                elif response.status == 404:
                    return None
                else:
                    raise Exception(
                        f"Failed to get public entity: {response.status} - {await response.text()}"
                    )

        except Exception as e:
            raise Exception(f"Error getting public entity '{entity_name}': {e}")

    # PublicEnumerations endpoint operations

    async def get_public_enumerations(
        self, options: Optional[QueryOptions] = None
    ) -> Dict[str, Any]:
        """Get public enumerations from PublicEnumerations endpoint

        Args:
            options: OData query options

        Returns:
            Response containing public enumerations
        """
        session = await self.session_manager.get_session()
        url = f"{self.metadata_url}/PublicEnumerations"

        params = QueryBuilder.build_query_params(options)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(
                    f"Failed to get public enumerations: {response.status} - {await response.text()}"
                )

    async def get_all_public_enumerations_with_details(
        self, resolve_labels: bool = False, language: str = "en-US"
    ) -> List[EnumerationInfo]:
        """Get all public enumerations with full details in a single optimized call

        This method uses the fact that PublicEnumerations endpoint returns complete enumeration data,
        avoiding the need for individual calls to PublicEnumerations('EnumName').

        Args:
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            List of EnumerationInfo objects with complete details
        """
        # Get all public enumerations with full details
        enums_data = await self.get_public_enumerations()
        enumerations = []

        for item in enums_data.get("value", []):
            try:
                # Parse enumeration using utility function
                enum = self._parse_public_enumeration_from_json(item)

                # Resolve labels if requested
                if resolve_labels and self.label_ops:
                    await self._resolve_enumeration_labels(enum, language)

                enumerations.append(enum)

            except Exception as e:
                # Log error but continue processing other enumerations
                logger.warning(
                    f"Failed to parse enumeration {item.get('Name', 'unknown')}: {e}"
                )
                continue

        return enumerations

    async def search_public_enumerations(
        self, pattern: str = ""
    ) -> List[EnumerationInfo]:
        """Search public enumerations with filtering

        Args:
            pattern: Search pattern for enumeration name (regex supported)

        Returns:
            List of matching enumerations (without detailed members)
        """
        # Build OData filter
        options = QueryOptions()
        if pattern:
            options.filter = f"contains(tolower(Name), '{pattern.lower()}')"

        # Only select basic fields for search to improve performance
        options.select = ["Name", "LabelId"]

        data = await self.get_public_enumerations(options)

        enumerations = []
        for item in data.get("value", []):
            enum = EnumerationInfo(
                name=item.get("Name", ""), label_id=item.get("LabelId")
            )
            enumerations.append(enum)

        # Apply regex pattern matching if provided
        if pattern and re.search(r"[.*+?^${}()|[\]\\]", pattern):
            flags = re.IGNORECASE
            enumerations = [
                e for e in enumerations if re.search(pattern, e.name, flags)
            ]

        return enumerations

    async def get_public_enumeration_info(
        self,
        enumeration_name: str,
        resolve_labels: bool = True,
        language: str = "en-US",
    ) -> Optional[EnumerationInfo]:
        """Get detailed information about a specific public enumeration

        Args:
            enumeration_name: Name of the enumeration
            resolve_labels: Whether to resolve label IDs to text
            language: Language for label resolution

        Returns:
            EnumerationInfo object with full details or None if not found
        """
        try:
            session = await self.session_manager.get_session()
            url = f"{self.metadata_url}/PublicEnumerations('{enumeration_name}')"

            async with session.get(url) as response:
                if response.status == 200:
                    item = await response.json()

                    # Use utility function to parse the enumeration
                    enum = self._parse_public_enumeration_from_json(item)

                    # Resolve labels if requested
                    if resolve_labels and self.label_ops:
                        await self._resolve_enumeration_labels(enum, language)

                    return enum
                elif response.status == 404:
                    return None
                else:
                    raise Exception(
                        f"Failed to get public enumeration: {response.status} - {await response.text()}"
                    )

        except Exception as e:
            raise Exception(
                f"Error getting public enumeration '{enumeration_name}': {e}"
            )

    # Helper methods for label resolution

    async def _resolve_public_entity_labels(
        self, entity: PublicEntityInfo, language: str
    ) -> None:
        """Resolve labels for a public entity"""
        # Collect all label IDs
        label_ids = []

        if entity.label_id:
            label_ids.append(entity.label_id)

        for prop in entity.properties:
            if prop.label_id:
                label_ids.append(prop.label_id)

        # Resolve labels in batch
        if label_ids:
            labels = await self.label_ops.get_labels_batch(label_ids, language)

            # Apply resolved labels
            if entity.label_id:
                entity.label_text = labels.get(entity.label_id)

            for prop in entity.properties:
                if prop.label_id:
                    prop.label_text = labels.get(prop.label_id)

    async def _resolve_enumeration_labels(
        self, enum: EnumerationInfo, language: str
    ) -> None:
        """Resolve labels for an enumeration"""
        # Collect all label IDs
        label_ids = []

        if enum.label_id:
            label_ids.append(enum.label_id)

        for member in enum.members:
            if member.label_id:
                label_ids.append(member.label_id)

        # Resolve labels in batch
        if label_ids:
            labels = await self.label_ops.get_labels_batch(label_ids, language)

            # Apply resolved labels
            if enum.label_id:
                enum.label_text = labels.get(enum.label_id)

            for member in enum.members:
                if member.label_id:
                    member.label_text = labels.get(member.label_id)

    # Version Information Methods

    async def get_application_version(self) -> str:
        """Get the current application version of the D365 F&O environment

        Returns:
            str: The application version string

        Raises:
            Exception: If the action call fails
        """
        try:
            result = await self.crud_ops.call_action(
                "GetApplicationVersion", {}, "DataManagementEntities", None
            )
            # The action returns a simple string value
            if isinstance(result, str):
                return result
            elif isinstance(result, dict) and "value" in result:
                return str(result["value"])
            else:
                return str(result) if result is not None else ""

        except Exception as e:
            logger.error(f"Failed to get application version: {e}")
            raise

    async def get_platform_build_version(self) -> str:
        """Get the current platform build version of the D365 F&O environment

        Returns:
            str: The platform build version string

        Raises:
            Exception: If the action call fails
        """
        try:
            result = await self.crud_ops.call_action(
                "GetPlatformBuildVersion", {}, "DataManagementEntities", None
            )
            # The action returns a simple string value
            if isinstance(result, str):
                return result
            elif isinstance(result, dict) and "value" in result:
                return str(result["value"])
            else:
                return str(result) if result is not None else ""

        except Exception as e:
            logger.error(f"Failed to get platform build version: {e}")
            raise

    async def get_installed_modules(self) -> List[str]:
        """Get the list of installed modules in the D365 F&O environment

        Returns:
            List[str]: List of module strings in format:
                "Name: {name} | Version: {version} | Module: {module_id} | Publisher: {publisher} | DisplayName: {display_name}"

        Raises:
            Exception: If the action call fails
        """
        try:
            result = await self.crud_ops.call_action(
                "GetInstalledModules", {}, "SystemNotifications", None
            )

            # The action returns a list of module strings
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "value" in result:
                modules = result["value"]
                if isinstance(modules, list):
                    return modules
                else:
                    logger.warning(
                        f"GetInstalledModules returned unexpected value format: {type(modules)}"
                    )
                    return []
            else:
                logger.warning(
                    f"GetInstalledModules returned unexpected format: {type(result)}"
                )
                return []

        except Exception as e:
            logger.error(f"Failed to get installed modules: {e}")
            raise

    # Action Operations

    async def search_actions(
        self,
        pattern: str = "",
        entity_name: Optional[str] = None,
        binding_kind: Optional[str] = None,
    ) -> List["ActionInfo"]:
        """Search actions across all public entities

        Args:
            pattern: Search pattern for action name (regex supported)
            entity_name: Filter actions that are bound to a specific entity
            binding_kind: Filter by binding type (Unbound, BoundToEntitySet, BoundToEntityInstance)

        Returns:
            List of ActionInfo objects with full details
        """
        from .models import ActionInfo

        actions = []
        
        try:
            # Compile regex pattern if provided
            regex_pattern = None
            if pattern:
                try:
                    regex_pattern = re.compile(pattern, re.IGNORECASE)
                except re.error:
                    # If regex is invalid, treat as literal string
                    pattern_lower = pattern.lower()
                    regex_pattern = lambda x: pattern_lower in x.lower()
                else:
                    regex_pattern = regex_pattern.search

            # Get all public entities with full details
            entities = await self.get_all_public_entities_with_details(resolve_labels=False)

            for entity in entities:
                # Filter by entity name if specified
                if entity_name and entity.name != entity_name:
                    continue

                # Process all actions in this entity
                for action in entity.actions:
                    # Filter by action name pattern
                    if regex_pattern and not regex_pattern(action.name):
                        continue

                    # Filter by binding kind
                    if binding_kind and action.binding_kind != binding_kind:
                        continue

                    # Create ActionInfo with entity context
                    action_info = ActionInfo(
                        name=action.name,
                        binding_kind=action.binding_kind,
                        entity_name=entity.name,  # public entity name
                        entity_set_name=entity.entity_set_name,  # entity set name for OData URLs
                        parameters=action.parameters,
                        return_type=action.return_type,
                        field_lookup=action.field_lookup,
                    )
                    actions.append(action_info)

        except Exception as e:
            logger.error(f"Failed to search actions: {e}")
            # Return empty list on error rather than raising
            return []

        return actions

    async def get_action_info(
        self,
        action_name: str,
        entity_name: Optional[str] = None,
    ) -> Optional["ActionInfo"]:
        """Get detailed information about a specific action

        Args:
            action_name: Name of the action
            entity_name: Optional entity name for bound actions

        Returns:
            ActionInfo object or None if not found
        """
        from .models import ActionInfo

        try:
            if entity_name:
                # If entity name is provided, get that specific entity
                entity = await self.get_public_entity_info(entity_name, resolve_labels=False)
                if not entity:
                    return None

                # Find the action in this entity
                for action in entity.actions:
                    if action.name == action_name:
                        return ActionInfo(
                            name=action.name,
                            binding_kind=action.binding_kind,
                            entity_name=entity.name,
                            entity_set_name=entity.entity_set_name,
                            parameters=action.parameters,
                            return_type=action.return_type,
                            field_lookup=action.field_lookup,
                        )
            else:
                # Search across all entities for the action
                actions = await self.search_actions(pattern=f"^{re.escape(action_name)}$")
                if actions:
                    # Return the first match (actions should be unique across entities)
                    return actions[0]

        except Exception as e:
            logger.error(f"Failed to get action info for '{action_name}': {e}")

        return None
