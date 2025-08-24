"""Label operations for D365 F&O client."""

import logging
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from .models import LabelInfo, PublicEntityInfo
from .session import SessionManager

logger = logging.getLogger(__name__)


@runtime_checkable
class LabelCacheProtocol(Protocol):
    """Protocol for label caching implementations."""

    async def get_label(self, label_id: str, language: str) -> Optional[str]:
        """Get a single label from cache."""
        ...

    async def set_label(self, label_info: LabelInfo) -> None:
        """Set a single label in cache."""
        ...

    async def set_labels_batch(self, labels: List[LabelInfo]) -> None:
        """Set multiple labels in cache."""
        ...

    async def get_labels_batch(
        self, label_ids: List[str], language: str
    ) -> Dict[str, str]:
        """Resolve multiple label IDs to their text values."""
        ...


class LabelOperations:
    """Handles label operations for F&O client"""

    def __init__(
        self,
        session_manager: SessionManager,
        metadata_url: str,
        label_cache: Optional[LabelCacheProtocol] = None,
    ):
        """Initialize label operations

        Args:
            session_manager: HTTP session manager
            metadata_url: Metadata API URL
            label_cache: Optional label cache implementing LabelCacheProtocol
        """
        self.session_manager = session_manager
        self.metadata_url = metadata_url
        self.label_cache = label_cache

    def set_label_cache(self, label_cache: LabelCacheProtocol):
        """Set the label cache for label operations

        Args:
            label_cache: Label cache implementing LabelCacheProtocol
        """
        self.label_cache = label_cache

    async def get_label_text(
        self, label_id: str, language: str = "en-US"
    ) -> Optional[str]:
        """Get actual label text for a specific label ID

        Args:
            label_id: Label ID (e.g., "@SYS13342")
            language: Language code (e.g., "en-US")

        Returns:
            Label text or None if not found
        """
        # Check cache first
        if self.label_cache:
            cached_value = await self.label_cache.get_label(label_id, language)
            if cached_value is not None:
                return cached_value

        try:
            session = await self.session_manager.get_session()
            url = f"{self.metadata_url}/Labels(Id='{label_id}',Language='{language}')"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    label_text = data.get("Value", "")

                    # Cache the result
                    if self.label_cache:
                        label_info = LabelInfo(
                            id=label_id, language=language, value=label_text
                        )
                        await self.label_cache.set_label(label_info)

                    return label_text
                else:
                    print(f"Error fetching label {label_id}: {response.status}")

        except Exception as e:
            print(f"Exception fetching label {label_id}: {e}")

        return None

    async def get_labels_batch(
        self, label_ids: List[str], language: str = "en-US"
    ) -> Dict[str, str]:
        """Get multiple labels efficiently using batch operations

        Args:
            label_ids: List of label IDs
            language: Language code

        Returns:
            Dictionary mapping label ID to label text
        """
        if not label_ids:
            return {}

        results = {}
        uncached_ids = []

        # First, check cache for all labels if available
        if self.label_cache:
            for label_id in label_ids:
                cached_value = await self.label_cache.get_label(label_id, language)
                if cached_value is not None:
                    results[label_id] = cached_value
                else:
                    uncached_ids.append(label_id)
        else:
            uncached_ids = label_ids

        # Fetch uncached labels from API
        if uncached_ids:
            # For now, use individual calls - could be optimized with batch API if available
            fetched_labels = []
            for label_id in uncached_ids:
                try:
                    session = await self.session_manager.get_session()
                    url = f"{self.metadata_url}/Labels(Id='{label_id}',Language='{language}')"

                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            label_text = data.get("Value", "")
                            results[label_id] = label_text

                            # Prepare for batch cache storage
                            fetched_labels.append(
                                LabelInfo(
                                    id=label_id, language=language, value=label_text
                                )
                            )
                        else:
                            print(f"Error fetching label {label_id}: {response.status}")

                except Exception as e:
                    print(f"Exception fetching label {label_id}: {e}")

            # Batch cache all fetched labels
            if fetched_labels and self.label_cache:
                await self.label_cache.set_labels_batch(fetched_labels)

        return results

    async def resolve_public_entity_labels(
        self, entity_info: PublicEntityInfo, language: str
    ):
        """Resolve all label IDs in a public entity to actual text

        Args:
            entity_info: Public entity information object to update
            language: Language code
        """
        # Collect all label IDs
        label_ids = []
        if entity_info.label_id:
            label_ids.append(entity_info.label_id)

        for prop in entity_info.properties:
            if prop.label_id:
                label_ids.append(prop.label_id)

        # Batch fetch all labels
        if label_ids:
            labels_map = await self.get_labels_batch(label_ids, language)

            # Apply resolved labels
            if entity_info.label_id:
                entity_info.label_text = labels_map.get(entity_info.label_id)

            for prop in entity_info.properties:
                if prop.label_id:
                    prop.label_text = labels_map.get(prop.label_id)


# Generic Label Resolution Utility Functions


async def resolve_labels_generic(
    obj_or_list: Union[Any, List[Any]],
    label_operations: LabelOperations,
    language: str = "en-US",
) -> Union[Any, List[Any]]:
    """
    Generic utility function to resolve label IDs to label text for any object(s)
    containing label_id and label_text properties.

    Args:
        obj_or_list: Single object or list of objects with label_id/label_text properties
        label_operations: LabelOperations instance for label resolution
        language: Language code for label resolution (default: "en-US")

    Returns:
        The same object(s) with label_text populated from label_id where applicable

    Examples:
        # Single object
        entity = await resolve_labels_generic(entity, label_ops)

        # List of objects
        entities = await resolve_labels_generic(entities, label_ops)

        # Works with any object type that has label_id/label_text attributes
        properties = await resolve_labels_generic(properties, label_ops, "fr-FR")
    """
    logger.debug(f"Starting generic label resolution for language: {language}")

    if obj_or_list is None:
        logger.debug("Input is None, returning unchanged")
        return obj_or_list

    # Handle list of objects
    if isinstance(obj_or_list, list):
        if not obj_or_list:
            logger.debug("Input is empty list, returning unchanged")
            return obj_or_list

        logger.debug(f"Processing list with {len(obj_or_list)} objects")

        # Collect all label IDs from all objects in the list
        label_ids = set()
        for i, obj in enumerate(obj_or_list):
            obj_type = type(obj).__name__ if obj else "None"
            logger.debug(f"Collecting labels from list item {i} (type: {obj_type})")
            _collect_label_ids_from_object(obj, label_ids)

        logger.debug(
            f"Collected {len(label_ids)} unique label IDs from list: {list(label_ids)}"
        )

        # Resolve all labels in batch
        label_texts = await _resolve_labels_batch(
            list(label_ids), label_operations, language
        )

        logger.debug(
            f"Successfully resolved {len(label_texts)} labels out of {len(label_ids)} requested"
        )

        # Apply resolved labels to all objects
        for i, obj in enumerate(obj_or_list):
            logger.debug(f"Applying labels to list item {i}")
            _apply_labels_to_object(obj, label_texts)

        logger.debug(
            f"Completed label resolution for list with {len(obj_or_list)} objects"
        )
        return obj_or_list

    # Handle single object
    else:
        obj_type = type(obj_or_list).__name__
        logger.debug(f"Processing single object of type: {obj_type}")

        # Collect label IDs from the object
        label_ids = set()
        _collect_label_ids_from_object(obj_or_list, label_ids)

        logger.debug(
            f"Collected {len(label_ids)} label IDs from object: {list(label_ids)}"
        )

        # Resolve labels in batch
        label_texts = await _resolve_labels_batch(
            list(label_ids), label_operations, language
        )

        logger.debug(
            f"Successfully resolved {len(label_texts)} labels out of {len(label_ids)} requested"
        )

        # Apply resolved labels
        _apply_labels_to_object(obj_or_list, label_texts)

        logger.debug(f"Completed label resolution for single {obj_type} object")
        return obj_or_list


def _collect_label_ids_from_object(obj: Any, label_ids: set) -> None:
    """
    Recursively collect all label_id values from an object and its nested objects/lists.

    Args:
        obj: Object to collect label IDs from
        label_ids: Set to store collected label IDs
    """
    if obj is None:
        logger.debug("Skipping None object in label collection")
        return

    obj_type = type(obj).__name__
    initial_count = len(label_ids)

    # Check if object has label_id attribute
    if hasattr(obj, "label_id") and obj.label_id:
        logger.debug(f"Found label_id '{obj.label_id}' in {obj_type} object")
        label_ids.add(obj.label_id)
    else:
        logger.debug(f"{obj_type} object has no label_id or label_id is empty")

    # Recursively check common nested attributes that might contain labeled objects
    nested_attrs = [
        "properties",
        "members",
        "navigation_properties",
        "property_groups",
        "actions",
        "parameters",
        "constraints",
        "enhanced_properties",
    ]

    for attr_name in nested_attrs:
        if hasattr(obj, attr_name):
            nested_obj = getattr(obj, attr_name)
            if isinstance(nested_obj, list):
                if nested_obj:
                    logger.debug(
                        f"Recursively collecting from {len(nested_obj)} items in {attr_name}"
                    )
                    for i, item in enumerate(nested_obj):
                        logger.debug(f"  Processing {attr_name}[{i}]")
                        _collect_label_ids_from_object(item, label_ids)
                else:
                    logger.debug(f"{attr_name} is empty list")
            elif nested_obj is not None:
                logger.debug(f"Recursively collecting from {attr_name} (single object)")
                _collect_label_ids_from_object(nested_obj, label_ids)
            else:
                logger.debug(f"{attr_name} is None")

    collected_count = len(label_ids) - initial_count
    if collected_count > 0:
        logger.debug(
            f"Collected {collected_count} new label IDs from {obj_type} object"
        )
    else:
        logger.debug(f"No new label IDs found in {obj_type} object")


async def _resolve_labels_batch(
    label_ids: List[str], label_operations: LabelOperations, language: str
) -> Dict[str, str]:
    """
    Resolve multiple label IDs to their text values in batch using LabelOperations.

    Args:
        label_ids: List of label IDs to resolve
        label_operations: LabelOperations instance
        language: Language code

    Returns:
        Dictionary mapping label_id to label_text
    """
    if not label_ids:
        logger.debug("No label IDs to resolve")
        return {}

    logger.debug(
        f"Starting batch resolution of {len(label_ids)} label IDs in language '{language}'"
    )
    logger.debug(f"Label IDs to resolve: {label_ids}")

    # Use LabelOperations batch method for efficient resolution
    try:
        label_texts = await label_operations.get_labels_batch(label_ids, language)

        successful_resolutions = len(label_texts)
        failed_resolutions = len(label_ids) - successful_resolutions

        logger.info(
            f"Batch label resolution completed: {successful_resolutions} successful, {failed_resolutions} failed out of {len(label_ids)} total"
        )

        if successful_resolutions > 0:
            logger.debug(f"Successfully resolved labels: {list(label_texts.keys())}")

        # Log individual results at debug level
        for label_id in label_ids:
            if label_id in label_texts:
                logger.debug(f"✅ Resolved '{label_id}' -> '{label_texts[label_id]}'")
            else:
                logger.debug(f"❌ No text found for label ID '{label_id}'")

        return label_texts

    except Exception as e:
        logger.warning(f"❌ Error in batch label resolution: {e}")
        return {}


def _apply_labels_to_object(obj: Any, label_texts: Dict[str, str]) -> None:
    """
    Recursively apply resolved labels to an object and its nested objects/lists.

    Args:
        obj: Object to apply labels to
        label_texts: Dictionary mapping label_id to label_text
    """
    if obj is None:
        logger.debug("Skipping None object in label application")
        return

    obj_type = type(obj).__name__
    labels_applied = 0

    # Apply label to current object if it has label_id and label_text attributes
    if (
        hasattr(obj, "label_id")
        and hasattr(obj, "label_text")
        and obj.label_id
        and obj.label_id in label_texts
    ):
        old_text = obj.label_text
        obj.label_text = label_texts[obj.label_id]
        labels_applied += 1
        logger.debug(
            f"Applied label to {obj_type}: '{obj.label_id}' -> '{obj.label_text}' (was: {old_text})"
        )
    elif hasattr(obj, "label_id") and obj.label_id:
        if not hasattr(obj, "label_text"):
            logger.debug(
                f"{obj_type} has label_id '{obj.label_id}' but no label_text attribute"
            )
        elif obj.label_id not in label_texts:
            logger.debug(
                f"{obj_type} has label_id '{obj.label_id}' but no resolved text available"
            )

    # Recursively apply to nested attributes
    nested_attrs = [
        "properties",
        "members",
        "navigation_properties",
        "property_groups",
        "actions",
        "parameters",
        "constraints",
        "enhanced_properties",
    ]

    for attr_name in nested_attrs:
        if hasattr(obj, attr_name):
            nested_obj = getattr(obj, attr_name)
            if isinstance(nested_obj, list):
                if nested_obj:
                    logger.debug(
                        f"Applying labels to {len(nested_obj)} items in {attr_name}"
                    )
                    for i, item in enumerate(nested_obj):
                        logger.debug(f"  Applying to {attr_name}[{i}]")
                        _apply_labels_to_object(item, label_texts)
            elif nested_obj is not None:
                logger.debug(f"Applying labels to {attr_name} (single object)")
                _apply_labels_to_object(nested_obj, label_texts)

    if labels_applied > 0:
        logger.debug(f"Applied {labels_applied} labels to {obj_type} object")
    else:
        logger.debug(f"No labels applied to {obj_type} object")


# Utility function for resolving labels with any cache implementation
async def resolve_labels_generic_with_cache(
    obj_or_list: Union[Any, List[Any]],
    cache: LabelCacheProtocol,
    language: str = "en-US",
) -> Union[Any, List[Any]]:
    """
    Resolve labels using any cache implementation that follows LabelCacheProtocol.

    Args:
        obj_or_list: Single object or list of objects with label_id/label_text properties
        cache: Any cache implementing LabelCacheProtocol (MetadataCache, MetadataCacheV2, etc.)
        language: Language code for label resolution (default: "en-US")

    Returns:
        The same object(s) with label_text populated from label_id where applicable

    Examples:
        # Works with any cache implementation
        entities = await resolve_labels_generic_with_cache(entities, metadata_cache_v2)
        entities = await resolve_labels_generic_with_cache(entities, old_metadata_cache)
    """

    # Create a minimal LabelOperations-like resolver using the cache
    class CacheLabelResolver:
        def __init__(self, cache: LabelCacheProtocol):
            self.cache = cache

        async def get_labels_batch(
            self, label_ids: List[str], language: str
        ) -> Dict[str, str]:
            """Get labels using the cache directly"""
            label_texts = {}
            for label_id in label_ids:
                if label_id:
                    label_text = await self.cache.get_label(label_id, language)
                    if label_text:
                        label_texts[label_id] = label_text
            return label_texts

    # Use the generic function with the cache resolver
    cache_resolver = CacheLabelResolver(cache)
    return await resolve_labels_generic(obj_or_list, cache_resolver, language)
