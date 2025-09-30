# Pydantic Settings Implementation

## Overview

The d365fo-client package now uses a comprehensive **Pydantic Settings** model for managing environment variables with type safety, validation, and excellent developer experience. This implementation replaces direct `os.getenv()` calls throughout the codebase with a centralized, validated, and well-documented settings system.

## Key Benefits

✅ **Type Safety**: All environment variables have proper Python types with validation  
✅ **Automatic Conversion**: String environment variables are automatically converted to appropriate types  
✅ **Validation**: Built-in validation for ports, timeouts, boolean values, etc.  
✅ **Documentation**: All settings are fully documented with descriptions  
✅ **IDE Support**: Full IntelliSense and autocompletion support  
✅ **Default Values**: Sensible defaults for all configuration options  
✅ **Environment File Support**: Supports `.env` files for local development  
✅ **Centralized Configuration**: Single source of truth for all settings  

## Usage

### Basic Usage

```python
from d365fo_client import get_settings

# Get global settings instance
settings = get_settings()

print(f"Base URL: {settings.base_url}")
print(f"HTTP Port: {settings.http_port}")
print(f"Log Level: {settings.log_level}")
print(f"Max Concurrent Requests: {settings.max_concurrent_requests}")
```

### With FOClient

```python
from d365fo_client import FOClient, FOClientConfig, get_settings
from d365fo_client.credential_sources import EnvironmentCredentialSource

# Get settings
settings = get_settings()

# Determine credential source based on settings
credential_source = None
if settings.has_client_credentials():
    credential_source = EnvironmentCredentialSource(
        client_id_var="D365FO_CLIENT_ID",
        client_secret_var="D365FO_CLIENT_SECRET", 
        tenant_id_var="D365FO_TENANT_ID"
    )

# Create FOClient configuration using settings
config = FOClientConfig(
    base_url=settings.base_url,
    credential_source=credential_source,
    verify_ssl=settings.verify_ssl,
    timeout=settings.timeout,
    use_label_cache=settings.use_label_cache,
    metadata_cache_dir=settings.cache_dir,
)

async with FOClient(config=config) as client:
    # Your code here
    pass
```

### Reloading Settings

```python
from d365fo_client import get_settings, reset_settings

# Reset settings to reload from environment
reset_settings()

# Get fresh settings instance
settings = get_settings(reload=True)
```

## Available Settings

### Core D365FO Connection Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `D365FO_BASE_URL` | `Optional[str]` | `https://usnconeboxax1aos.cloud.onebox.dynamics.com` | D365FO environment URL |

### Azure AD Authentication Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `D365FO_CLIENT_ID` | `Optional[str]` | `None` | Azure AD client ID (optional, used with client credentials flow) |
| `D365FO_CLIENT_SECRET` | `Optional[str]` | `None` | Azure AD client secret (optional, used with client credentials flow) |
| `D365FO_TENANT_ID` | `Optional[str]` | `None` | Azure AD tenant ID (optional, used with client credentials flow) |

### MCP Server Transport Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `D365FO_MCP_TRANSPORT` | `TransportProtocol` | `stdio` | Default transport protocol (stdio, sse, http, streamable-http) |
| `D365FO_HTTP_HOST` | `str` | `127.0.0.1` | Default HTTP host |
| `D365FO_HTTP_PORT` | `int` | `8000` | Default HTTP port (1-65535) |
| `D365FO_HTTP_STATELESS` | `bool` | `False` | Enable stateless mode |
| `D365FO_HTTP_JSON` | `bool` | `False` | Enable JSON response mode |

### Connection and Performance Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `D365FO_MAX_CONCURRENT_REQUESTS` | `int` | `10` | Max concurrent requests (>0) |
| `D365FO_REQUEST_TIMEOUT` | `int` | `30` | Request timeout in seconds (>0) |
| `D365FO_TIMEOUT` | `int` | `60` | General timeout in seconds (>0) |
| `D365FO_VERIFY_SSL` | `bool` | `True` | Verify SSL certificates |

### Logging Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `D365FO_LOG_LEVEL` | `LogLevel` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `D365FO_LOG_FILE` | `Optional[str]` | `~/.d365fo-mcp/logs/fastmcp-server.log` | Custom log file path |

### Cache and Metadata Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `D365FO_CACHE_DIR` | `Optional[str]` | `~/.d365fo-client` | General cache directory |
| `D365FO_META_CACHE_DIR` | `Optional[str]` | `~/.d365fo-mcp/cache` | Metadata cache directory |
| `D365FO_USE_LABEL_CACHE` | `bool` | `True` | Enable label caching |
| `D365FO_LABEL_EXPIRY` | `int` | `1440` | Label cache expiry in minutes (>0) |
| `D365FO_USE_CACHE_FIRST` | `bool` | `True` | Use cache first before making API calls |

### Debug and Development Settings

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `DEBUG` | `bool` | `False` | Enable debug mode |

## Settings Class Methods

### `has_client_credentials() -> bool`
Check if client credentials (client_id, client_secret, tenant_id) are all configured.

```python
settings = get_settings()
if settings.has_client_credentials():
    print("Client credentials are configured")
else:
    print("Using default authentication")
```

### `get_startup_mode() -> Literal["profile_only", "default_auth", "client_credentials"]`
Determine startup mode based on configuration.

```python
settings = get_settings()
mode = settings.get_startup_mode()

if mode == "client_credentials":
    print("Using explicit client credentials")
elif mode == "default_auth":
    print("Using default auth with custom base URL")
else:
    print("Using profile-based configuration")
```

### `ensure_directories() -> None`
Ensure all required directories exist (log directories, cache directories, etc.).

```python
settings = get_settings()
settings.ensure_directories()  # Called automatically in get_settings()
```

### `to_dict() -> dict`
Convert settings to a dictionary.

```python
settings = get_settings()
config_dict = settings.to_dict()
print(config_dict)
```

### `to_env_dict() -> dict`
Convert settings to environment variable dictionary format.

```python
settings = get_settings()
env_vars = settings.to_env_dict()
for key, value in env_vars.items():
    print(f"{key}={value}")
```

## Environment File Support

You can create a `.env` file in your project root or working directory:

```env
# .env file
D365FO_BASE_URL=https://your-environment.dynamics.com
D365FO_CLIENT_ID=your-client-id
D365FO_CLIENT_SECRET=your-client-secret  
D365FO_TENANT_ID=your-tenant-id
D365FO_LOG_LEVEL=DEBUG
D365FO_HTTP_PORT=9000
D365FO_MAX_CONCURRENT_REQUESTS=20
```

The settings will automatically load from this file.

## Validation

The settings model includes comprehensive validation:

### Type Validation
```python
# These will be automatically converted from strings
D365FO_HTTP_PORT=8000        # -> int
D365FO_VERIFY_SSL=true       # -> bool  
D365FO_LOG_LEVEL=DEBUG       # -> LogLevel.DEBUG
```

### Range Validation
```python
# Port must be between 1 and 65535
D365FO_HTTP_PORT=80          # ✅ Valid
D365FO_HTTP_PORT=99999       # ❌ ValidationError

# Timeouts must be positive
D365FO_TIMEOUT=30            # ✅ Valid  
D365FO_TIMEOUT=-1            # ❌ ValidationError
```

### Boolean Conversion
```python
# All of these evaluate to True
D365FO_VERIFY_SSL=true
D365FO_VERIFY_SSL=True
D365FO_VERIFY_SSL=1
D365FO_VERIFY_SSL=yes
D365FO_VERIFY_SSL=on

# All of these evaluate to False  
D365FO_VERIFY_SSL=false
D365FO_VERIFY_SSL=False
D365FO_VERIFY_SSL=0
D365FO_VERIFY_SSL=no
D365FO_VERIFY_SSL=off
```

## Migration from os.getenv()

### Before (old way)
```python
import os

base_url = os.getenv("D365FO_BASE_URL", "https://default.dynamics.com")
port = int(os.getenv("D365FO_HTTP_PORT", "8000"))
debug = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
```

### After (new way)
```python
from d365fo_client import get_settings

settings = get_settings()
base_url = settings.base_url  # Type: Optional[str], validated
port = settings.http_port     # Type: int, validated (1-65535)  
debug = settings.debug        # Type: bool, validated
```

## FastMCP Server Integration

The FastMCP server automatically uses the new settings system:

```bash
# All environment variables are automatically picked up
export D365FO_BASE_URL="https://your-env.dynamics.com"
export D365FO_LOG_LEVEL="DEBUG"
export D365FO_HTTP_PORT="9000"

# Run the server
d365fo-mcp-server --transport http
```

The server will log its configuration on startup:

```
INFO - Starting FastD365FOMCPServer v0.2.4 with transport: http
INFO - === Server Startup Configuration ===
INFO - Transport: http
INFO - Host: 127.0.0.1
INFO - Port: 9000
INFO - Debug mode: False  
INFO - JSON response: False
INFO - Stateless HTTP: False
INFO - Log level: DEBUG
INFO - Settings Base URL: https://your-env.dynamics.com
INFO - Startup Mode: default_auth
INFO - ====================================
```

## Testing

### Unit Testing with Settings

```python
import pytest
from d365fo_client.settings import reset_settings, get_settings

def test_custom_settings():
    # Reset settings before test
    reset_settings()
    
    # Set environment variables for test
    import os
    os.environ["D365FO_HTTP_PORT"] = "9999"
    os.environ["D365FO_LOG_LEVEL"] = "DEBUG"
    
    # Get fresh settings
    settings = get_settings(reload=True)
    
    assert settings.http_port == 9999
    assert settings.log_level.value == "DEBUG"
    
    # Cleanup
    del os.environ["D365FO_HTTP_PORT"]
    del os.environ["D365FO_LOG_LEVEL"]
    reset_settings()
```

### Integration Testing

```python
async def test_client_with_settings():
    from d365fo_client import FOClient, FOClientConfig, get_settings
    
    settings = get_settings()
    
    config = FOClientConfig(
        base_url=settings.base_url,
        timeout=settings.timeout,
        verify_ssl=settings.verify_ssl,
    )
    
    async with FOClient(config=config) as client:
        version = await client.get_application_version()
        assert version is not None
```

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure `pydantic-settings` is installed:
   ```bash
   uv add pydantic-settings
   ```

2. **ValidationError**: Check that environment variables have valid values:
   ```python
   # This will show validation errors
   try:
       settings = get_settings()
   except ValidationError as e:
       print(e.json(indent=2))
   ```

3. **Settings not updating**: Make sure to reset settings when testing:
   ```python
   from d365fo_client.settings import reset_settings
   reset_settings()
   ```

### Debugging Settings

```python
from d365fo_client import get_settings

settings = get_settings()

# Print all settings
print("Current settings:")
for field_name, field_info in settings.model_fields.items():
    value = getattr(settings, field_name)
    print(f"  {field_name}: {value} ({type(value).__name__})")

# Print as environment variables
print("\\nAs environment variables:")
env_dict = settings.to_env_dict()
for key, value in env_dict.items():
    print(f"  {key}={value}")
```

## Implementation Details

### File Structure

- `src/d365fo_client/settings.py` - Main settings model  
- `src/d365fo_client/mcp/fastmcp_main.py` - FastMCP server integration
- `src/d365fo_client/mcp/fastmcp_utils.py` - Utility functions using settings
- `examples/settings_example.py` - Comprehensive usage example

### Dependencies

- `pydantic-settings>=2.6.0` - Main settings framework
- `pydantic>=2.0.0` - Type validation and serialization  

### Global Settings Instance

The package maintains a global settings instance for performance and consistency:

```python
# Singleton pattern - settings are loaded once and reused
settings1 = get_settings()
settings2 = get_settings()
assert settings1 is settings2  # Same instance

# Force reload if needed
settings3 = get_settings(reload=True)  # Fresh instance
```

This implementation provides a robust, type-safe, and user-friendly way to manage all environment variables in the d365fo-client package.