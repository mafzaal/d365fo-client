# Label Resolution Utility

The d365fo-client package provides a powerful and generic utility function `resolve_labels_generic()` that can automatically resolve label IDs to label text for any object or list of objects containing `label_id` and `label_text` properties.

## Features

- **Generic**: Works with any object type that has `label_id` and `label_text` attributes
- **Flexible**: Handles both single objects and lists of objects
- **Recursive**: Automatically finds and resolves labels in nested objects and collections
- **Efficient**: Batch resolves all labels in a single operation to minimize cache lookups
- **Multi-language**: Supports label resolution in different languages
- **Safe**: Handles edge cases gracefully (None objects, missing attributes, unknown labels)

## Function Signature

```python
async def resolve_labels_generic(
    obj_or_list: Union[Any, List[Any]], 
    cache: MetadataCache, 
    language: str = "en-US"
) -> Union[Any, List[Any]]
```

### Parameters

- `obj_or_list`: Single object or list of objects with `label_id`/`label_text` properties
- `cache`: MetadataCache instance for label resolution
- `language`: Language code for label resolution (default: "en-US")

### Returns

The same object(s) with `label_text` populated from `label_id` where applicable.

## Supported Object Types

The utility automatically works with any object that has:
- `label_id` attribute (string) - the label identifier
- `label_text` attribute (string or None) - where the resolved text will be stored

Built-in support for these d365fo-client model classes:
- `DataEntityInfo`
- `PublicEntityInfo` 
- `PublicEntityPropertyInfo`
- `EnumerationInfo`
- `EnumerationMemberInfo`
- `EntityPropertyInfo`
- Any custom class with `label_id` and `label_text` attributes

### Nested Object Support

The utility automatically discovers and resolves labels in these common nested attributes:
- `properties`
- `members` 
- `navigation_properties`
- `property_groups`
- `actions`
- `parameters`
- `constraints`
- `enhanced_properties`

## Usage Examples

### Example 1: Single Entity

```python
from d365fo_client import resolve_labels_generic
from d365fo_client.metadata_cache import MetadataCache

# Initialize cache
cache = MetadataCache(base_url, cache_dir)
await cache.initialize()

# Get an entity (without labels resolved)
entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=False)

# Resolve all labels in the entity and its properties
await resolve_labels_generic(entity, cache)

print(f"Entity label: {entity.label_text}")
print(f"First property label: {entity.properties[0].label_text}")
```

### Example 2: List of Entities

```python
# Get multiple entities
entities = await cache.search_data_entities(pattern="Customer")

# Resolve labels for all entities in the list
await resolve_labels_generic(entities, cache)

for entity in entities:
    print(f"{entity.name}: {entity.label_text}")
```

### Example 3: Enumeration with Members

```python
# Get enumeration with members
enum_info = await cache.get_public_enumeration_info("CurrencyCode", resolve_labels=False)

# Resolve labels for enumeration and all its members
await resolve_labels_generic(enum_info, cache)

print(f"Enum: {enum_info.label_text}")
for member in enum_info.members:
    print(f"  {member.name}: {member.label_text}")
```

### Example 4: Multi-language Support

```python
# Resolve in different languages
await resolve_labels_generic(entity, cache, "en-US")  # English
await resolve_labels_generic(entity, cache, "de-DE")  # German
await resolve_labels_generic(entity, cache, "fr-FR")  # French
```

### Example 5: Custom Objects

```python
# Create custom class with label properties
class CustomEntity:
    def __init__(self, name: str, label_id: str = None):
        self.name = name
        self.label_id = label_id
        self.label_text = None

# Create objects
custom_objects = [
    CustomEntity("obj1", "@SYS12345"),
    CustomEntity("obj2", "@SYS67890")
]

# Resolve labels
await resolve_labels_generic(custom_objects, cache)

for obj in custom_objects:
    print(f"{obj.name}: {obj.label_text}")
```

## Logging and Debugging

The utility provides comprehensive logging to help with debugging and monitoring:

### Log Levels

- **DEBUG**: Detailed step-by-step processing information
- **INFO**: Summary statistics of batch operations  
- **WARNING**: Non-fatal errors (e.g., missing labels, cache errors)

### Enabling Logging

```python
import logging

# Enable debug logging for detailed information
logging.basicConfig(level=logging.DEBUG)

# Or just for this module
logger = logging.getLogger('d365fo_client.metadata_cache')
logger.setLevel(logging.DEBUG)

# Resolve labels with logging
await resolve_labels_generic(entities, cache)
```

### Log Output Examples

**Single Object Resolution:**
```
DEBUG - Starting generic label resolution for language: en-US
DEBUG - Processing single object of type: DataEntityInfo
DEBUG - Found label_id '@SYS123' in DataEntityInfo object
DEBUG - Collected 1 label IDs from object: ['@SYS123']
DEBUG - Starting batch resolution of 1 label IDs in language 'en-US'
DEBUG - ✅ Resolved '@SYS123' -> 'Customer Information'
INFO  - Batch label resolution completed: 1 successful, 0 failed out of 1 total
DEBUG - Applied label to DataEntityInfo: '@SYS123' -> 'Customer Information' (was: None)
DEBUG - Completed label resolution for single DataEntityInfo object
```

**Nested Object Processing:**
```
DEBUG - Recursively collecting from 3 items in properties
DEBUG -   Processing properties[0]
DEBUG - Found label_id '@SYS456' in PublicEntityPropertyInfo object
DEBUG - Applying labels to 3 items in properties
DEBUG - Applied label to PublicEntityPropertyInfo: '@SYS456' -> 'Address' (was: None)
```

**Error Handling:**
```
DEBUG - ❌ No text found for label ID '@UNKNOWN_LABEL'
INFO  - Batch label resolution completed: 2 successful, 1 failed out of 3 total
```

## Performance Considerations

The utility is designed for efficiency:

1. **Batch Resolution**: Collects all label IDs from the object(s) first, then resolves them in a single batch operation
2. **Deduplication**: Automatically removes duplicate label IDs to minimize cache lookups
3. **Recursive Discovery**: Finds all nested labels in one pass through the object structure
4. **Cache-Friendly**: Works with the multi-tier caching system (memory → disk → database)

## Error Handling

The utility handles various edge cases gracefully:

- **None objects**: Returns None unchanged
- **Empty lists**: Returns empty list unchanged  
- **Missing attributes**: Ignores objects without `label_id` or `label_text` attributes
- **Unknown labels**: Leaves `label_text` as None for unknown label IDs
- **Invalid languages**: Falls back to default behavior

## Integration with Existing Code

The utility can be seamlessly integrated into existing workflows:

```python
# Before: Manual label resolution
entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=True)

# After: Using generic utility (gives you more control)
entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=False)
await resolve_labels_generic(entity, cache, "fr-FR")  # Resolve in French
```

## Advanced Usage

### Custom Nested Attributes

If you have custom objects with different nested attribute names, you can extend the function by modifying the `nested_attrs` list in the `_collect_label_ids_from_object` function.

### Batch Processing

For large datasets, you can process objects in batches:

```python
# Process large list in chunks
batch_size = 100
for i in range(0, len(large_list), batch_size):
    batch = large_list[i:i + batch_size]
    await resolve_labels_generic(batch, cache)
```

### Conditional Resolution

```python
# Only resolve if not already resolved
if not entity.label_text:
    await resolve_labels_generic(entity, cache)
```

## Best Practices

1. **Initialize cache once**: Create the MetadataCache instance once and reuse it
2. **Batch when possible**: Process lists rather than individual objects when possible
3. **Check for existing labels**: Avoid re-resolving already resolved labels
4. **Handle different languages**: Consider your target audience's language requirements
5. **Error handling**: Wrap in try-catch blocks for production code

```python
try:
    await resolve_labels_generic(entities, cache)
except Exception as e:
    logger.warning(f"Failed to resolve labels: {e}")
    # Continue with unresolved labels
```