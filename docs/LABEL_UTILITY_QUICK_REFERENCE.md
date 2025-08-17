# Label Resolution Utility - Quick Reference

## Overview

The `resolve_labels_generic()` function is a powerful utility that automatically resolves label IDs to human-readable text for any object or collection containing `label_id` and `label_text` properties.

## Quick Start

```python
from d365fo_client import resolve_labels_generic
from d365fo_client.metadata_cache import MetadataCache

# Initialize cache
cache = MetadataCache(base_url, cache_dir)
await cache.initialize()

# Single object
await resolve_labels_generic(entity, cache)

# List of objects  
await resolve_labels_generic(entities, cache)

# Different language
await resolve_labels_generic(entity, cache, "de-DE")
```

## Key Features

✅ **Generic** - Works with any object having `label_id`/`label_text` attributes  
✅ **Efficient** - Batch resolves all labels to minimize cache lookups  
✅ **Recursive** - Automatically finds nested labeled objects  
✅ **Safe** - Handles None objects, empty lists, missing attributes gracefully  
✅ **Multi-language** - Supports different language codes  
✅ **Flexible** - Works with single objects or lists  

## Supported Objects

- `DataEntityInfo`
- `PublicEntityInfo` 
- `PublicEntityPropertyInfo`
- `EnumerationInfo`
- `EnumerationMemberInfo`
- Any custom class with `label_id` and `label_text` attributes

## Common Usage Patterns

### Batch Processing
```python
# Get multiple entities
entities = await cache.search_data_entities("Customer")

# Resolve all labels at once (efficient)
await resolve_labels_generic(entities, cache)
```

### Detailed Entity Processing
```python
# Get entity with properties, actions, etc.
entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=False)

# Resolve labels for entity AND all nested objects (properties, actions, etc.)
await resolve_labels_generic(entity, cache)
```

### Custom Objects
```python
class MyEntity:
    def __init__(self, name, label_id):
        self.name = name
        self.label_id = label_id
        self.label_text = None

obj = MyEntity("test", "@SYS12345")
await resolve_labels_generic(obj, cache)
print(obj.label_text)  # Resolved label text
```

### Multi-language
```python
# Resolve in different languages
await resolve_labels_generic(entity, cache, "en-US")  # English
await resolve_labels_generic(entity, cache, "fr-FR")  # French
```

### Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now get detailed logs during resolution
await resolve_labels_generic(entities, cache)
```

## Performance Benefits

- **Batch resolution**: Collects all label IDs first, then resolves in one operation
- **Deduplication**: Eliminates duplicate label lookups automatically  
- **Cache-friendly**: Works with multi-tier caching (memory → disk → database)
- **Recursive discovery**: Finds all nested labels in single pass

## Error Handling

The function handles edge cases gracefully:
- Returns `None` unchanged for `None` input
- Returns empty list unchanged for `[]` input  
- Ignores objects without `label_id`/`label_text` attributes
- Leaves `label_text` as `None` for unknown label IDs

## Examples

See these example files for detailed usage:
- `examples/label_resolution_utility_demo.py` - Comprehensive demo
- `examples/practical_label_resolution_example.py` - Real-world scenarios

## Documentation

Full documentation: `docs/LABEL_RESOLUTION_UTILITY.md`