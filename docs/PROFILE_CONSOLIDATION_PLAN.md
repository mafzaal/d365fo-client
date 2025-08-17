# Profile Management Consolidation Plan

## Problem Statement

The d365fo-client currently has two separate profile management systems:
1. `CLIProfile` in `config.py` for CLI operations
2. `EnvironmentProfile` in `profile_manager.py` for MCP operations

This causes:
- **Parameter Mismatch**: Configuration contains `use_cache_first` parameter not in `CLIProfile`
- **Duplication**: Two similar but incompatible profile data structures
- **Maintenance Overhead**: Changes must be made in two places
- **Runtime Errors**: MCP server fails when loading existing CLI profiles

## Current State Analysis

### CLIProfile (config.py)
```python
@dataclass
class CLIProfile:
    name: str
    base_url: str
    auth_mode: str = "default"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    verify_ssl: bool = True
    output_format: str = "table"
    label_cache: bool = True
    label_expiry: int = 60
    language: str = "en-US"
    cache_dir: Optional[str] = None
    # Missing: use_cache_first, timeout, description
```

### EnvironmentProfile (profile_manager.py)
```python
@dataclass
class EnvironmentProfile:
    name: str
    base_url: str
    auth_mode: str = "default"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 60
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60
    language: str = "en-US"
    cache_dir: Optional[str] = None
    description: Optional[str] = None
    # Missing: output_format, use_cache_first
```

### Missing Parameters in Storage
Configuration contains `use_cache_first: true` but neither profile type supports it.

## Consolidation Strategy

### Phase 1: Immediate Fix (Address Runtime Error)

1. **Add Missing Parameter to CLIProfile**
   - Add `use_cache_first: bool = True` to `CLIProfile`
   - Ensure backward compatibility with existing configurations

2. **Update Configuration Loading**
   - Handle unknown parameters gracefully
   - Provide sensible defaults for missing parameters

### Phase 2: Unified Profile System

1. **Create Unified Profile Model**
   - Single `Profile` dataclass with all parameters
   - Support both CLI and MCP use cases
   - Include all current parameters from both systems

2. **Update ProfileManager**
   - Use unified `Profile` instead of `EnvironmentProfile`
   - Remove conversion methods (`_cli_to_env_profile`)
   - Simplify profile operations

3. **Update ConfigManager**
   - Work directly with unified `Profile`
   - Remove CLI-specific assumptions
   - Support all profile parameters

### Phase 3: Enhanced Functionality

1. **Validation Framework**
   - Centralized profile validation
   - Context-aware validation (CLI vs MCP)
   - Clear error messages

2. **Migration Support**
   - Automatic migration of existing configurations
   - Version tracking for profile schema
   - Backward compatibility

3. **Extended Features**
   - Profile inheritance (base profiles)
   - Environment variable substitution
   - Profile templates

## Implementation Plan

### Step 1: Fix Immediate Issue

```python
# Update CLIProfile in config.py
@dataclass
class CLIProfile:
    # ... existing fields ...
    use_cache_first: bool = True
    timeout: int = 60  # Add for completeness
```

### Step 2: Create Unified Profile

```python
# New unified profile in profiles.py
@dataclass
class Profile:
    """Unified profile for CLI and MCP operations."""
    name: str
    base_url: str
    auth_mode: str = "default"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 60
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60
    use_cache_first: bool = True
    language: str = "en-US"
    cache_dir: Optional[str] = None
    description: Optional[str] = None
    output_format: str = "table"  # CLI-specific default
```

### Step 3: Update All Components

1. **ProfileManager** - Use unified `Profile`
2. **ConfigManager** - Support all parameters
3. **CLI** - Work with unified profiles
4. **MCP** - Use same profile system
5. **FOClientConfig conversion** - Support all parameters

## Migration Strategy

### Existing Configuration Compatibility
- Support loading existing configurations
- Provide defaults for missing parameters
- Warn about deprecated parameters

### Profile Schema Versioning
- Add schema version to configuration
- Support automatic upgrades
- Maintain backward compatibility

## Benefits of Consolidation

1. **Single Source of Truth**: One profile system for all use cases
2. **Reduced Complexity**: No conversion between profile types
3. **Better Maintainability**: Changes in one place
4. **Enhanced Features**: Full parameter support everywhere
5. **Error Reduction**: No parameter mismatches
6. **Future-Proof**: Easier to add new features

## Risk Mitigation

1. **Backward Compatibility**: Existing configurations continue to work
2. **Gradual Migration**: Phase implementation to reduce risk
3. **Comprehensive Testing**: Test all profile operations
4. **Documentation Updates**: Update all documentation
5. **Version Tracking**: Clear versioning for profile schema

## Success Criteria

1. ✅ MCP server loads existing configurations without errors
2. ✅ CLI continues to work with existing profiles
3. ✅ New unified profile supports all parameters
4. ✅ Profile operations work consistently in CLI and MCP
5. ✅ Migration path is smooth and automatic
6. ✅ Documentation is updated and comprehensive

## Implementation Timeline

### Phase 1 (Immediate - 1 day)
- Fix runtime error by adding missing parameters
- Test with existing configurations
- Verify MCP server functionality

### Phase 2 (Short-term - 2-3 days)
- Create unified profile system
- Update ProfileManager and ConfigManager
- Comprehensive testing

### Phase 3 (Medium-term - 1 week)
- Enhanced validation and migration
- Documentation updates
- Additional features and polish

This consolidation will provide a robust, maintainable profile management system that serves both CLI and MCP use cases effectively.