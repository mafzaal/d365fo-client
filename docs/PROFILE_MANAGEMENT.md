# Profile Management for D365FO Client

## Overview

The d365fo-client now supports comprehensive profile management for managing multiple D365 Finance & Operations environments. This functionality is extracted from the CLI and exposed through both command-line interface and Model Context Protocol (MCP) tools.

## Key Features

- **Unified Profile Management**: Common profile system used by both CLI and MCP
- **Environment Configurations**: Store connection details, authentication settings, and preferences
- **Default Profile Support**: Set a default environment to use when none is specified
- **Validation**: Built-in validation for profile configurations
- **Import/Export**: Backup and restore profile configurations
- **MCP Integration**: Full MCP tool support for AI assistant integration

## Profile Structure

Each profile contains:
- **Name**: Unique identifier for the profile
- **Base URL**: D365FO environment URL
- **Authentication Mode**: `default` (Azure CLI/Managed Identity) or `client_credentials`
- **Authentication Details**: Client ID, secret, and tenant ID (for client_credentials)
- **Connection Settings**: SSL verification, timeout, language
- **Cache Settings**: Label cache configuration
- **Description**: Optional description (MCP only)

## CLI Usage

### Create a Profile
```bash
d365fo-client config create production \
  --base-url https://prod-d365fo.contoso.com \
  --auth-mode client_credentials \
  --client-id your-client-id \
  --client-secret your-client-secret \
  --tenant-id your-tenant-id
```

### List Profiles
```bash
d365fo-client config list
```

### Show Profile Details
```bash
d365fo-client config show production
```

### Set Default Profile
```bash
d365fo-client config set-default production
```

### Use Profile in Commands
```bash
# Use specific profile
d365fo-client --profile production entity get Customers --top 10

# Use default profile (if set)
d365fo-client entity get Customers --top 10
```

### Delete Profile
```bash
d365fo-client config delete production
```

## Programmatic Usage

### Using ProfileManager

```python
from d365fo_client import ProfileManager

# Initialize profile manager
pm = ProfileManager()

# Create a profile
pm.create_profile(
    name="development",
    base_url="https://dev-d365fo.contoso.com",
    auth_mode="default",
    description="Development environment"
)

# List profiles
profiles = pm.list_profiles()
for name, profile in profiles.items():
    print(f"{name}: {profile.base_url}")

# Get specific profile
profile = pm.get_profile("development")
if profile:
    print(f"URL: {profile.base_url}")

# Set default
pm.set_default_profile("development")

# Validate profile
errors = pm.validate_profile(profile)
if not errors:
    print("Profile is valid")

# Delete profile
pm.delete_profile("development")
```

### Convert to Client Config

```python
from d365fo_client import ProfileManager, FOClient

pm = ProfileManager()
profile = pm.get_profile("production")

if profile:
    # Convert profile to client configuration
    config = pm.profile_to_client_config(profile)
    
    # Use with FOClient
    async with FOClient(config) as client:
        # Your operations here
        version = await client.get_application_version()
        print(f"Version: {version}")
```

## MCP Integration

The profile management is fully integrated with the MCP server, providing AI assistants with comprehensive environment management capabilities.

### Available MCP Tools

1. **d365fo_list_profiles** - List all available profiles
2. **d365fo_get_profile** - Get details of a specific profile
3. **d365fo_create_profile** - Create a new profile
4. **d365fo_update_profile** - Update an existing profile
5. **d365fo_delete_profile** - Delete a profile
6. **d365fo_set_default_profile** - Set the default profile
7. **d365fo_get_default_profile** - Get the current default profile
8. **d365fo_validate_profile** - Validate a profile configuration
9. **d365fo_test_profile_connection** - Test connection for a profile

### MCP Tool Usage Examples

#### Create a Profile via MCP
```json
{
  "tool": "d365fo_create_profile",
  "arguments": {
    "name": "sandbox",
    "baseUrl": "https://sandbox-d365fo.contoso.com",
    "authMode": "default",
    "description": "Sandbox environment for testing",
    "setAsDefault": true
  }
}
```

#### Test Profile Connection
```json
{
  "tool": "d365fo_test_profile_connection",
  "arguments": {
    "profileName": "sandbox"
  }
}
```

#### Query Entities with Profile
```json
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "Customers",
    "profile": "sandbox",
    "select": ["CustomerAccount", "Name"],
    "top": 10
  }
}
```

## Default Profile Behavior

When no profile is explicitly specified:

1. **CLI**: Uses default profile if set, otherwise requires profile or connection parameters
2. **MCP**: Uses default profile if set, falls back to "default" profile, then environment variables
3. **Programmatic**: Uses effective profile resolution through `ProfileManager.get_effective_profile()`

## Storage and Configuration

Profiles are stored in:
- **Config File**: `~/.d365fo-client/config.yaml` (CLI profiles)
- **Metadata File**: `~/.d365fo-client/profile_metadata.yaml` (descriptions and extended metadata)

## Migration from Legacy Configuration

Existing CLI configurations are automatically supported. The new profile system:
- Reads existing CLI profiles seamlessly
- Extends with additional metadata (descriptions, etc.)
- Maintains backward compatibility
- Provides upgrade path to enhanced features

## Security Considerations

- **Client Secrets**: Stored in configuration files (protect with appropriate file permissions)
- **Default Credentials**: Recommended for production use (Azure CLI, Managed Identity)
- **Profile Isolation**: Each profile maintains separate authentication context
- **Validation**: Built-in validation prevents configuration errors

## Best Practices

1. **Use Default Authentication**: Prefer Azure CLI or Managed Identity over client credentials
2. **Environment Separation**: Create separate profiles for dev, test, and production
3. **Descriptive Names**: Use clear, descriptive profile names
4. **Regular Validation**: Validate profiles after creation/updates
5. **Backup Configurations**: Export profiles before major changes
6. **Test Connections**: Use connection testing tools to verify profiles

## Troubleshooting

### Profile Not Found
- Verify profile name with `d365fo-client config list`
- Check default profile setting

### Connection Issues
- Test profile connection: `d365fo_test_profile_connection`
- Validate profile configuration: `d365fo_validate_profile`
- Check authentication credentials and permissions

### Permission Errors
- Ensure proper file permissions on config directory
- Verify Azure authentication setup for default credentials

## Example: Complete Workflow

```bash
# 1. Create profiles for different environments
d365fo-client config create dev --base-url https://dev-d365fo.contoso.com
d365fo-client config create test --base-url https://test-d365fo.contoso.com
d365fo-client config create prod --base-url https://prod-d365fo.contoso.com --auth-mode client_credentials --client-id xxx --client-secret yyy --tenant-id zzz

# 2. Set default for daily use
d365fo-client config set-default dev

# 3. Use profiles in operations
d365fo-client entity get Customers --top 5  # Uses dev (default)
d365fo-client --profile test entity get Customers --top 5  # Uses test
d365fo-client --profile prod version --application  # Uses prod

# 4. Manage profiles
d365fo-client config list
d365fo-client config show prod

# 5. Backup configurations
d365fo-client config export profiles_backup.yaml  # Future feature
```

This profile management system provides a robust foundation for managing multiple D365FO environments while maintaining simplicity and flexibility for various use cases.