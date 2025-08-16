# Version Methods Implementation

This document describes the implementation of the version-related OData action methods for the d365fo-client package.

## Overview

The client provides three dedicated methods for retrieving version information from Microsoft Dynamics 365 Finance & Operations:

1. `get_application_version()` - Gets the application version
2. `get_platform_build_version()` - Gets the platform build version  
3. `get_application_build_version()` - Gets the application build version

All three methods are wrappers for calling corresponding OData actions in D365 F&O.

## Action Analysis

### Metadata Information

All three actions share the same metadata structure:

- **Binding Type**: Collection-bound actions
- **Entity Set**: `DataManagementEntities`
- **Parameters**: None (except implicit collection parameter)
- **Return Type**: `Edm.String` - Simple string value
- **Annotations**: None

| Action Name | Description |
|-------------|-------------|
| `GetApplicationVersion` | Retrieves the current application version |
| `GetPlatformBuildVersion` | Retrieves the platform build version |
| `GetApplicationBuildVersion` | Retrieves the application build version |

## Method Signatures

```python
async def get_application_version(self) -> str:
    """Get the current application version of the D365 F&O environment"""

async def get_platform_build_version(self) -> str:
    """Get the current platform build version of the D365 F&O environment"""

async def get_application_build_version(self) -> str:
    """Get the current application build version of the D365 F&O environment"""
```

## Usage Examples

### Basic Usage

```python
from d365fo_client import FOClient, FOClientConfig

async def get_all_versions():
    config = FOClientConfig(
        base_url="https://your-d365.dynamics.com",
        use_default_credentials=True
    )
    
    async with FOClient(config) as client:
        # Get all version information
        app_version = await client.get_application_version()
        platform_version = await client.get_platform_build_version()
        app_build_version = await client.get_application_build_version()
        
        print(f"Application Version: {app_version}")
        print(f"Platform Build Version: {platform_version}")
        print(f"Application Build Version: {app_build_version}")
```

### Sequential vs Parallel Calls

```python
import asyncio
from d365fo_client import FOClient, FOClientConfig

async def compare_approaches():
    config = FOClientConfig(base_url="https://your-d365.dynamics.com")
    
    async with FOClient(config) as client:
        # Sequential approach (slower)
        app_version = await client.get_application_version()
        platform_version = await client.get_platform_build_version()
        app_build_version = await client.get_application_build_version()
        
        # Parallel approach (faster)
        app_version, platform_version, app_build_version = await asyncio.gather(
            client.get_application_version(),
            client.get_platform_build_version(),
            client.get_application_build_version()
        )
```

### Error Handling

```python
from d365fo_client import FOClient, FOClientConfig
from d365fo_client.exceptions import FOClientError

async def get_versions_with_error_handling():
    config = FOClientConfig(base_url="https://your-d365.dynamics.com")
    
    async with FOClient(config) as client:
        # Individual error handling
        version_methods = [
            (client.get_application_version, "Application Version"),
            (client.get_platform_build_version, "Platform Build Version"),
            (client.get_application_build_version, "Application Build Version")
        ]
        
        for method, label in version_methods:
            try:
                version = await method()
                print(f"✅ {label}: {version}")
            except FOClientError as e:
                print(f"❌ {label}: {e}")
```

### Parallel with Exception Handling

```python
import asyncio

async def get_versions_parallel_safe():
    config = FOClientConfig(base_url="https://your-d365.dynamics.com")
    
    async with FOClient(config) as client:
        # Parallel calls with exception handling
        results = await asyncio.gather(
            client.get_application_version(),
            client.get_platform_build_version(),
            client.get_application_build_version(),
            return_exceptions=True
        )
        
        labels = ["Application Version", "Platform Build Version", "Application Build Version"]
        
        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                print(f"❌ {label}: Error - {result}")
            else:
                print(f"✅ {label}: {result}")
```

## Response Handling

All methods handle different response formats consistently:

1. **Direct string response**: Returns the string value directly
2. **Dictionary with 'value' key**: Extracts and returns the value
3. **Other types**: Converts to string using `str()`
4. **None/null**: Returns empty string

## Implementation Architecture

The methods follow the OData action implementation pattern:

1. **Action Call**: Uses the existing `call_action` method with proper parameters
2. **Response Processing**: Handles various response formats gracefully  
3. **Error Handling**: Wraps exceptions in `FOClientError` with descriptive messages
4. **Type Safety**: Provides proper type hints and return type guarantees

## Testing

The implementation includes comprehensive unit tests covering:

- Success scenarios with different response types
- Error handling and exception propagation
- Response format variations
- Integration test structure (skipped by default)
- Parallel execution scenarios
- Method availability verification

Run tests with:
```bash
pytest tests/test_get_application_version.py tests/test_version_methods.py -v
```

## Performance Considerations

### Parallel vs Sequential

When fetching multiple version values, use parallel calls for better performance:

```python
# ❌ Slower - Sequential
app_version = await client.get_application_version()
platform_version = await client.get_platform_build_version() 
app_build_version = await client.get_application_build_version()

# ✅ Faster - Parallel
versions = await asyncio.gather(
    client.get_application_version(),
    client.get_platform_build_version(),
    client.get_application_build_version()
)
```

### Caching Considerations

Version information typically doesn't change frequently, so consider caching the results:

```python
class VersionCache:
    def __init__(self, client, cache_duration=3600):  # 1 hour cache
        self.client = client
        self.cache_duration = cache_duration
        self._cache = {}
        self._cache_time = {}
    
    async def get_cached_version(self, version_type):
        import time
        now = time.time()
        
        if (version_type in self._cache and 
            now - self._cache_time[version_type] < self.cache_duration):
            return self._cache[version_type]
        
        # Cache miss - fetch new value
        if version_type == "application":
            value = await self.client.get_application_version()
        elif version_type == "platform_build":
            value = await self.client.get_platform_build_version()
        elif version_type == "application_build":
            value = await self.client.get_application_build_version()
        
        self._cache[version_type] = value
        self._cache_time[version_type] = now
        return value
```

## Migration from Generic Call

### Before (using generic call_action)

```python
# Old way
app_version = await client.call_action(
    "GetApplicationVersion",
    entity_name="DataManagementEntities"
)
platform_version = await client.call_action(
    "GetPlatformBuildVersion",
    entity_name="DataManagementEntities"
)
app_build_version = await client.call_action(
    "GetApplicationBuildVersion",
    entity_name="DataManagementEntities"
)
```

### After (using dedicated methods)

```python
# New way
app_version = await client.get_application_version()
platform_version = await client.get_platform_build_version()
app_build_version = await client.get_application_build_version()
```

## Benefits of Dedicated Methods

1. **Type Safety**: Explicit return type annotations
2. **Simplified API**: No need to specify entity name or parameters
3. **Better Error Messages**: Custom error messages for each specific action
4. **Enhanced Documentation**: Clear docstrings explaining each method's purpose
5. **Comprehensive Testing**: Dedicated test coverage for each method
6. **IDE Support**: Methods appear in autocompletion with proper signatures
7. **Consistency**: All version methods follow the same pattern
8. **Performance**: Can be easily used in parallel operations

## Common Use Cases

### Environment Information Display

```python
async def display_environment_info():
    async with FOClient(config) as client:
        versions = await asyncio.gather(
            client.get_application_version(),
            client.get_platform_build_version(),
            client.get_application_build_version()
        )
        
        print("Environment Information:")
        print(f"  Application Version: {versions[0]}")
        print(f"  Platform Build: {versions[1]}")  
        print(f"  Application Build: {versions[2]}")
```

### Health Check Endpoint

```python
async def health_check():
    try:
        async with FOClient(config) as client:
            # Quick version check to verify connectivity
            version = await client.get_application_version()
            return {"status": "healthy", "version": version}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Deployment Verification

```python
async def verify_deployment(expected_version):
    async with FOClient(config) as client:
        actual_version = await client.get_application_version()
        
        if actual_version == expected_version:
            print(f"✅ Deployment verified: {actual_version}")
            return True
        else:
            print(f"❌ Version mismatch: expected {expected_version}, got {actual_version}")
            return False
```