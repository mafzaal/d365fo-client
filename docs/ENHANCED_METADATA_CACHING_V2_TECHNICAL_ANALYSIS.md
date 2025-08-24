# Enhanced Metadata Caching V2 - Technical Dependency Analysis

## Component Interaction Matrix

This document provides a detailed technical analysis of how the Enhanced Metadata Caching V2 components interact with each other at the method and class level.

## Interaction Matrix

| Component | database_v2 | version_detector | global_version_manager | cache_v2 | sync_manager_v2 |
|-----------|-------------|------------------|------------------------|----------|-----------------|
| **database_v2** | - | ❌ | ❌ | ✅ Direct | ❌ |
| **version_detector** | ❌ | - | ❌ | ✅ Lazy Init | ❌ |
| **global_version_manager** | ✅ DB Path | ❌ | - | ✅ Direct | ✅ Direct |
| **cache_v2** | ✅ Owner | ✅ Owner | ✅ Owner | - | ❌ |
| **sync_manager_v2** | ❌ | ❌ | ✅ Via Cache | ✅ Owner | - |

**Legend:**
- ✅ Direct - Direct instantiation and method calls
- ✅ Owner - Component creates and owns the dependency
- ✅ Via Cache - Accesses through cache instance
- ✅ Lazy Init - Initialized when first needed
- ✅ DB Path - Shares database path only
- ❌ - No direct interaction

## Detailed Component Interactions

### 1. 📦 MetadataCacheV2 - Central Hub

**Owns and Coordinates:**
```python
class MetadataCacheV2:
    def __init__(self, cache_dir: Path, base_url: str):
        # Direct ownership
        self.database = MetadataDatabaseV2(self.db_path)
        self.version_manager = GlobalVersionManager(self.db_path)
        
        # Lazy initialization
        self.version_detector = None  # Created when needed
```

**Key Interactions:**
- **→ DatabaseV2**: All metadata storage operations
- **→ GlobalVersionManager**: Version registry operations
- **→ VersionDetector**: Version detection (lazy init)

**Methods that trigger dependencies:**
```python
async def check_version_and_sync(self, fo_client):
    # Triggers version_detector initialization
    if self.version_detector is None:
        self.version_detector = ModuleVersionDetector(fo_client.metadata_api)
    
    # Uses version_detector
    modules = await self.version_detector.detect_version(fo_client)
    
    # Uses version_manager
    global_version, was_created = await self.version_manager.get_or_create_global_version(env_version)
    
    # Uses database
    await self.database.link_environment_to_version(env_id, global_version.id)
```

### 2. 🔄 SmartSyncManagerV2 - High-Level Operations

**Dependency Injection:**
```python
class SmartSyncManagerV2:
    def __init__(self, cache: MetadataCacheV2):
        self.cache = cache  # Primary dependency
        # Accesses other components through cache
```

**Key Interactions:**
- **→ Cache**: All operations go through cache
- **→ GlobalVersionManager**: Via `self.cache.version_manager`
- **→ Database**: Via `self.cache.database`

**Interaction Patterns:**
```python
async def sync_metadata(self, fo_client, global_version_id):
    # Access version manager through cache
    await self.cache.version_manager.update_sync_status(global_version_id, "in_progress")
    
    # Access database through cache
    await self.cache.database.store_data_entities(entities, global_version_id)
    
    # Use cache methods directly
    await self.cache.invalidate_cache()
```

### 3. 🌐 GlobalVersionManager - Version Registry

**Standalone Component:**
```python
class GlobalVersionManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path  # Only needs database path
        # Uses aiosqlite directly, no dependency on database_v2
```

**Database Access Pattern:**
```python
async def find_compatible_version(self, modules_hash: str):
    # Direct SQLite access
    async with aiosqlite.connect(self.db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM global_versions WHERE modules_hash = ?",
            (modules_hash,)
        )
```

**Key Design Decision**: 
- Does NOT depend on `MetadataDatabaseV2` class
- Uses raw SQLite connections for independence
- Shares database file path with other components

### 4. 🔍 ModuleVersionDetector - Version Detection

**Lazy Initialization Pattern:**
```python
# In cache_v2.py
async def check_version_and_sync(self, fo_client):
    if self.version_detector is None:
        # Late binding - requires API operations
        self.version_detector = ModuleVersionDetector(fo_client.metadata_api)
```

**External Dependency:**
```python
class ModuleVersionDetector:
    def __init__(self, api_operations):
        self.api = api_operations  # Requires external API interface
```

**Isolation Benefits:**
- Can be tested independently with mock API
- No circular dependencies with cache
- Clear separation of concerns

### 5. 🗄️ MetadataDatabaseV2 - Foundation Layer

**Pure Storage Component:**
```python
class MetadataDatabaseV2:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # No dependencies on other v2 components
```

**No Upward Dependencies:**
- Only depends on external libraries (aiosqlite, pathlib)
- Provides services to upper layers
- Foundation of the dependency stack

## Dependency Flow Patterns

### 1. Initialization Flow
```
User Code
    ↓
MetadataCacheV2.__init__()
    ↓
MetadataDatabaseV2(db_path)
GlobalVersionManager(db_path)
ModuleVersionDetector = None  # Lazy
```

### 2. Version Detection Flow
```
check_version_and_sync(fo_client)
    ↓ (lazy init)
ModuleVersionDetector(fo_client.metadata_api)
    ↓
version_detector.detect_version()
    ↓ (external API)
GetInstalledModules action
```

### 3. Version Management Flow
```
cache.check_version_and_sync()
    ↓
version_manager.get_or_create_global_version()
    ↓ (direct SQLite)
INSERT/SELECT on global_versions table
```

### 4. Sync Flow
```
SmartSyncManagerV2.sync_metadata()
    ↓
cache.database.store_data_entities()
    ↓ (SQLite operations)
INSERT into version-scoped tables
```

## Architectural Patterns

### 1. 🎯 Hub and Spoke Pattern
- **Hub**: `MetadataCacheV2` coordinates all operations
- **Spokes**: Other components provide specialized services
- **Benefits**: Single point of coordination, simplified external API

### 2. 🔄 Dependency Injection
- `SmartSyncManagerV2` receives `MetadataCacheV2` as dependency
- Enables testing with mock cache
- Clear ownership and lifecycle management

### 3. 🏗️ Lazy Initialization
- `ModuleVersionDetector` created only when needed
- Avoids circular dependencies
- Reduces initialization complexity

### 4. 📊 Shared Database Pattern
- Multiple components share same SQLite database file
- `database_v2.py` manages schema
- `global_version_manager.py` uses direct SQLite access
- Ensures consistency while maintaining independence

### 5. 🌍 External Adapter Pattern
- `ModuleVersionDetector` adapts external API operations
- Isolates external dependencies
- Facilitates testing and mocking

## Component Coupling Analysis

### Loose Coupling (Good) ✅
- `ModuleVersionDetector` ↔ External APIs (interface-based)
- `SmartSyncManagerV2` ↔ `MetadataCacheV2` (dependency injection)
- `GlobalVersionManager` ↔ Database (path-based, not object-based)

### Tight Coupling (Acceptable) ⚠️
- `MetadataCacheV2` ↔ `MetadataDatabaseV2` (ownership)
- `MetadataCacheV2` ↔ `GlobalVersionManager` (ownership)
- All components ↔ `models.py` (shared data structures)

### No Circular Dependencies ✅
- Clear layered architecture
- Dependencies flow in one direction
- Each component can be tested independently

## Testing Strategy Implications

### Unit Testing
```python
# Each component can be tested independently
def test_version_detector():
    mock_api = MockAPIOperations()
    detector = ModuleVersionDetector(mock_api)
    # Test version detection logic

def test_global_version_manager():
    temp_db_path = create_temp_database()
    manager = GlobalVersionManager(temp_db_path)
    # Test version management logic

def test_cache():
    mock_db = MockDatabase()
    mock_version_manager = MockVersionManager()
    cache = MetadataCacheV2(cache_dir, base_url)
    # Inject mocks for testing
```

### Integration Testing
```python
# Test component interactions
def test_version_detection_integration():
    cache = MetadataCacheV2(test_cache_dir, test_url)
    fo_client = create_test_client()
    
    # Tests version_detector lazy initialization
    # Tests cache → version_manager interaction
    # Tests version_manager → database interaction
    sync_needed, version_id = await cache.check_version_and_sync(fo_client)
```

## Performance Implications

### Database Access Patterns
- **Cache**: Uses `MetadataDatabaseV2` wrapper (additional abstraction)
- **Version Manager**: Direct SQLite access (optimal performance)
- **Trade-off**: Consistency vs. Performance

### Memory Management
- **Lazy initialization** reduces memory footprint
- **Shared database path** minimizes resource duplication
- **No circular references** enables proper garbage collection

### Async Coordination
- All components use async/await consistently
- No blocking operations between components
- Proper resource cleanup in context managers

This technical analysis shows that the Enhanced Metadata Caching V2 system follows solid architectural principles with clear separation of concerns, minimal coupling, and no circular dependencies.