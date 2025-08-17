# Label Cache Integration Implementation

## Overview

This document summarizes the implementation of integrated label caching functionality across `MetadataDatabase`, `MetadataCache`, and `LabelCache` classes.

## Implementation Summary

### 1. MetadataDatabase Label Methods

Added comprehensive label storage and retrieval methods to the `MetadataDatabase` class:

#### New Methods:
- `get_label(label_id, language)` - Retrieve label from database with expiration check
- `set_label(label, ttl_hours)` - Store single label with TTL
- `set_labels_batch(labels, ttl_hours)` - Batch store multiple labels efficiently
- `clear_expired_labels()` - Remove expired labels from database
- `get_labels_statistics()` - Get detailed label cache statistics

#### Database Schema:
The existing `labels_cache` table supports:
- Label ID and language combination (unique constraint)
- TTL-based expiration with `expires_at` timestamp
- Automatic indexing for performance
- Multi-language support

### 2. MetadataCache Label Methods

Enhanced `MetadataCache` with multi-tier label caching:

#### New Methods:
- `get_label(label_id, language)` - Multi-tier label retrieval (L1→L2→L3)
- `set_label(label, ttl_hours)` - Store label across all cache tiers
- `set_labels_batch(labels, ttl_hours)` - Efficient batch storage
- `clear_expired_labels()` - Clean expired labels from all tiers

#### Cache Architecture:
```
L1: Memory Cache (TTLCache) → Fast access
    ↓ (miss)
L2: Disk Cache (diskcache) → Persistent across restarts  
    ↓ (miss)
L3: SQLite Database → Long-term storage with metadata
```

### 3. Enhanced LabelCache Integration

Updated `LabelCache` to use `MetadataCache` as second-level storage:

#### Key Features:
- **Backward Compatibility**: Maintains existing API for legacy code
- **Two-Tier Architecture**: Memory cache + MetadataCache backend
- **Async Integration**: New async methods for full MetadataCache integration
- **Automatic Promotion**: L2 hits are promoted to L1 cache

#### Methods Enhanced:
- `get(label_id, language)` - Now checks MetadataCache on L1 miss
- `set_async(label_id, language, value)` - Async version for MetadataCache integration
- `set_batch_async(labels)` - Async batch operations
- `get_info()` - Extended statistics including MetadataCache status

## Usage Examples

### Direct MetadataCache Usage (Recommended)

```python
from d365fo_client.metadata_cache import MetadataCache
from d365fo_client.models import LabelInfo

# Initialize cache
cache = MetadataCache(
    environment_url="https://your-d365fo.dynamics.com",
    cache_dir=Path("./cache"),
    config={'cache_ttl_seconds': 300}
)
await cache.initialize()

# Store label
label = LabelInfo(id="@SYS12345", language="en-US", value="Customer Account")
await cache.set_label(label)

# Retrieve label
value = await cache.get_label("@SYS12345", "en-US")
print(value)  # "Customer Account"

# Batch operations
labels = [
    LabelInfo(id="@SYS12346", language="en-US", value="Vendor Account"),
    LabelInfo(id="@SYS12347", language="fr-FR", value="Compte fournisseur")
]
await cache.set_labels_batch(labels)
```

### Legacy LabelCache with MetadataCache Integration

```python
from d365fo_client.cache import LabelCache
from d365fo_client.metadata_cache import MetadataCache

# Initialize MetadataCache
metadata_cache = MetadataCache(...)
await metadata_cache.initialize()

# Initialize LabelCache with MetadataCache backend
label_cache = LabelCache(
    expiry_minutes=60,
    metadata_cache=metadata_cache
)

# Use legacy API with enhanced backend
value = await label_cache.get("@SYS12345", "en-US")  # Checks both tiers
await label_cache.set_async("@SYS12346", "en-US", "New Label")  # Stores in both tiers
```

## Performance Benefits

### Multi-Tier Caching
1. **L1 (Memory)**: Sub-millisecond access for frequently used labels
2. **L2 (Disk)**: Fast persistent storage, survives process restarts
3. **L3 (Database)**: Comprehensive metadata integration with search capabilities

### Batch Operations
- Efficient batch storage reduces database roundtrips
- Transaction-based consistency for large label sets
- Automatic cache tier population

### Expiration Management
- TTL-based expiration at database level
- Automatic cleanup of expired labels
- Memory cache respects TTL for active management

## Migration Path

### For New Applications
Use `MetadataCache` directly for full functionality:
```python
# New recommended approach
from d365fo_client.metadata_cache import MetadataCache
cache = MetadataCache(environment_url, cache_dir)
```

### For Existing Applications
Enhance existing `LabelCache` usage gradually:
```python
# Add MetadataCache backend to existing LabelCache
metadata_cache = MetadataCache(environment_url, cache_dir)
label_cache = LabelCache(metadata_cache=metadata_cache)

# Gradually migrate to async methods
await label_cache.set_async(label_id, language, value)
```

## Statistics and Monitoring

Both cache systems provide comprehensive statistics:

```python
# MetadataCache statistics (includes labels)
stats = await metadata_cache.get_statistics()
print(f"Total labels: {stats['total_labels']}")
print(f"Active labels: {stats['active_labels']}")
print(f"Languages: {stats['languages']}")

# LabelCache info
info = label_cache.get_info()
print(f"L1 cache size: {info['size']}")
print(f"Has L2 backend: {info['has_metadata_cache']}")
```

## Key Implementation Details

### Thread Safety
- `MetadataCache` uses `threading.RLock()` for thread-safe operations
- Database operations are async-safe with aiosqlite
- Memory cache operations are protected by locks

### Error Handling
- Graceful degradation when cache layers are unavailable
- Detailed logging for cache hits/misses and errors
- Exception isolation between cache tiers

### Database Schema Integration
- Labels table integrated with existing metadata schema
- Consistent indexing strategy for performance
- Foreign key relationships maintain data integrity

## Testing

The implementation includes comprehensive test coverage:
- Multi-tier cache behavior verification
- Batch operation testing
- Error condition handling
- Performance benchmarking
- Integration with existing metadata systems

## Future Enhancements

Potential areas for future development:
1. **Cache Warming**: Preload frequently accessed labels
2. **Distributed Caching**: Redis/Memcached integration for multi-instance deployments
3. **Smart Eviction**: LRU/LFU policies for memory cache optimization
4. **Compression**: Storage optimization for large label datasets
5. **Analytics**: Cache hit rate analysis and optimization recommendations