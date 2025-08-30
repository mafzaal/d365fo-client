# MCP Server Startup Improvements

## Overview

The D365FO MCP Server startup behavior has been improved to handle three distinct scenarios based on environment variable configuration. This provides a more robust and flexible startup experience.

## Startup Scenarios

### 1. Profile-Only Mode (No Environment Variables)

**Trigger**: No `D365FO_BASE_URL` environment variable provided

**Behavior**:
- Server starts without any pre-configured environment
- No health checks or automatic profile creation
- All functionality available through profile management tools
- Ideal for development environments or when managing multiple environments

**Environment Variables**: None required

**Configuration Generated**:
```json
{
    "startup_mode": "profile_only",
    "has_base_url": false
}
```

**Log Output**:
```
Server started in profile-only mode
No environment variables configured - use profile management tools to configure D365FO connections
```

### 2. Default Authentication Mode

**Trigger**: Only `D365FO_BASE_URL` environment variable provided

**Behavior**:
- Server starts with default Azure authentication
- Performs health checks on startup
- Creates a default profile with default credentials
- Sets the created profile as the default

**Environment Variables**:
- `D365FO_BASE_URL` (required)

**Configuration Generated**:
```json
{
    "startup_mode": "default_auth",
    "has_base_url": true,
    "default_environment": {
        "base_url": "https://your-d365fo-url.com",
        "use_default_credentials": true
    }
}
```

**Log Output**:
```
Server started with default authentication mode
D365FO_BASE_URL configured - performing health checks and creating default profile with default auth
```

### 3. Client Credentials Mode

**Trigger**: All four environment variables provided:
- `D365FO_BASE_URL`
- `D365FO_CLIENT_ID`
- `D365FO_CLIENT_SECRET`
- `D365FO_TENANT_ID`

**Behavior**:
- Server starts with client credentials authentication
- Performs health checks on startup
- Creates a default profile with client credentials
- Sets the created profile as the default

**Environment Variables**:
- `D365FO_BASE_URL` (required)
- `D365FO_CLIENT_ID` (required)
- `D365FO_CLIENT_SECRET` (required)
- `D365FO_TENANT_ID` (required)

**Configuration Generated**:
```json
{
    "startup_mode": "client_credentials",
    "has_base_url": true,
    "default_environment": {
        "base_url": "https://your-d365fo-url.com",
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "tenant_id": "your-tenant-id",
        "use_default_credentials": false
    }
}
```

**Log Output**:
```
Server started with client credentials authentication mode
Full D365FO environment variables configured - performing health checks and creating default profile with client credentials
```

## Fallback Behavior

### Partial Credentials
If `D365FO_BASE_URL` is provided along with some but not all of the client credential variables, the server falls back to **Default Authentication Mode**.

**Example**: Having `D365FO_BASE_URL` and `D365FO_CLIENT_ID` but missing `D365FO_CLIENT_SECRET` and `D365FO_TENANT_ID` will result in default authentication mode.

## Implementation Details

### Key Changes

1. **Enhanced `load_config()` function**:
   - Determines startup mode based on available environment variables
   - Provides clear configuration structure for each scenario
   - Includes comprehensive logging

2. **Improved `_startup_initialization()` method**:
   - Handles each startup mode appropriately
   - Graceful error handling that doesn't prevent server startup
   - Clear logging for debugging

3. **Fixed `_create_default_profile_if_needed()` method**:
   - Uses correct environment variable names (`D365FO_*` instead of `AZURE_*`)
   - Handles authentication mode selection properly
   - Validates required credentials for client credentials mode

4. **Comprehensive error handling**:
   - Server startup never fails due to configuration issues
   - Falls back to profile-only mode on errors
   - Detailed logging for troubleshooting

### Profile Creation Logic

When environment variables are configured, the server automatically creates a profile named `default-from-env` with the following logic:

1. **Check for existing default profile**: If one exists, skip creation
2. **Validate environment variables**: Ensure required variables are present
3. **Create profile**: With appropriate authentication mode
4. **Set as default**: Make the new profile the default for the session

## Usage Examples

### Development Environment (Profile-Only)
```bash
# No environment variables set
d365fo-mcp-server
```

### Production with Default Auth
```bash
export D365FO_BASE_URL="https://your-environment.dynamics.com"
d365fo-mcp-server
```

### Production with Service Principal
```bash
export D365FO_BASE_URL="https://your-environment.dynamics.com"
export D365FO_CLIENT_ID="your-app-registration-id"
export D365FO_CLIENT_SECRET="your-app-secret"
export D365FO_TENANT_ID="your-tenant-id"
d365fo-mcp-server
```

## Testing

Comprehensive unit tests cover all startup scenarios:

- **TestLoadConfig**: Tests the `load_config()` function with various environment variable combinations
- **TestMCPServerStartup**: Tests server startup initialization behavior
- **TestCreateDefaultProfile**: Tests automatic profile creation logic
- **TestIntegrationScenarios**: End-to-end testing of complete startup flows

Run tests with:
```bash
uv run python -m pytest tests/mcp/test_main_startup.py -v
```

## Migration Notes

### Breaking Changes
None - this is backward compatible with existing configurations.

### Deprecated Behavior
- The old logic that created partial configurations regardless of environment variable completeness has been replaced with clear startup modes.

### Environment Variable Changes
- Fixed environment variable names from `AZURE_*` to `D365FO_*` for consistency
- All environment variables are now properly validated

## Troubleshooting

### Common Issues

1. **Server starts in profile-only mode unexpectedly**:
   - Check that `D365FO_BASE_URL` is set correctly
   - Verify environment variables are exported in the current shell

2. **Client credentials mode not working**:
   - Ensure all four environment variables are set
   - Check for typos in variable names
   - Verify the client secret is properly escaped

3. **Profile creation fails**:
   - Check server logs for detailed error messages
   - Verify Azure credentials have proper permissions
   - Test connectivity manually

### Debug Logging
Enable debug logging for detailed startup information:
```bash
export D365FO_LOG_LEVEL=DEBUG
d365fo-mcp-server
```

## Security Considerations

- Client secrets are never logged or exposed in configuration dumps
- Profiles are stored securely using the existing profile management system
- Environment variables should be properly secured in production environments
- Consider using Azure Key Vault or similar for credential management in production

## Future Enhancements

Potential future improvements:
1. Support for certificate-based authentication
2. Integration with Azure Key Vault for secret management
3. Configuration file-based startup modes
4. Health check customization options
5. Profile template system for common configurations