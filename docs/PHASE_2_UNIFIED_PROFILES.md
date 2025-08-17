# Phase 2 Implementation: Unified Profile System

## Status: Phase 1 Complete ✅

**Phase 1 Results:**
- ✅ Fixed immediate runtime error by adding `use_cache_first` and `timeout` to `CLIProfile`
- ✅ Updated configuration loading to handle all parameters
- ✅ MCP server now loads existing profiles correctly
- ✅ Backward compatibility maintained

## Phase 2: Unified Profile System

### Current Architecture Issues

Despite Phase 1 fix, we still have:
1. **Dual Profile Classes**: `CLIProfile` and `EnvironmentProfile` 
2. **Parameter Duplication**: Same fields defined twice
3. **Conversion Overhead**: `_cli_to_env_profile` conversion method
4. **Maintenance Burden**: Changes need to be made in multiple places

### Phase 2 Goals

1. **Single Profile Class**: One `Profile` class for both CLI and MCP
2. **Unified Storage**: Single configuration format
3. **Simplified Code**: Remove conversion methods
4. **Enhanced Features**: Support for all use cases

### Implementation Strategy

#### Step 1: Create Unified Profile Class

Create `src/d365fo_client/profiles.py`:

```python
"""Unified profile management for d365fo-client."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Profile:
    """Unified profile for CLI and MCP operations."""
    
    # Core identification
    name: str
    description: Optional[str] = None
    
    # Connection settings
    base_url: str = ""
    auth_mode: str = "default"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 60
    
    # Cache settings
    use_label_cache: bool = True
    label_cache_expiry_minutes: int = 60
    use_cache_first: bool = True
    cache_dir: Optional[str] = None
    
    # Localization
    language: str = "en-US"
    
    # CLI-specific settings (with defaults for MCP)
    output_format: str = "table"
    
    def to_client_config(self) -> 'FOClientConfig':
        """Convert profile to FOClientConfig."""
        from .models import FOClientConfig
        
        return FOClientConfig(
            base_url=self.base_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            tenant_id=self.tenant_id,
            use_default_credentials=self.auth_mode == "default",
            timeout=self.timeout,
            verify_ssl=self.verify_ssl,
            use_label_cache=self.use_label_cache,
            label_cache_expiry_minutes=self.label_cache_expiry_minutes,
            use_cache_first=self.use_cache_first,
            metadata_cache_dir=self.cache_dir
        )
    
    def validate(self) -> List[str]:
        """Validate profile configuration."""
        errors = []
        
        if not self.base_url:
            errors.append("Base URL is required")
        
        if self.auth_mode == "client_credentials":
            if not self.client_id:
                errors.append("Client ID is required for client_credentials auth mode")
            if not self.client_secret:
                errors.append("Client secret is required for client_credentials auth mode")
            if not self.tenant_id:
                errors.append("Tenant ID is required for client_credentials auth mode")
        
        if self.timeout <= 0:
            errors.append("Timeout must be greater than 0")
        
        if self.label_cache_expiry_minutes <= 0:
            errors.append("Label cache expiry must be greater than 0")
        
        return errors
```

#### Step 2: Update ConfigManager

```python
# In config.py - Update to use unified Profile

class ConfigManager:
    """Manages configuration profiles and settings."""
    
    def get_profile(self, profile_name: str) -> Optional[Profile]:
        """Get a specific configuration profile."""
        # Load and convert to unified Profile
        
    def save_profile(self, profile: Profile) -> None:
        """Save a configuration profile."""
        # Save unified Profile to configuration
        
    def list_profiles(self) -> Dict[str, Profile]:
        """List all configuration profiles."""
        # Return unified Profiles
```

#### Step 3: Update ProfileManager

```python
# In profile_manager.py - Simplify to use unified Profile

class ProfileManager:
    """Manages environment profiles for D365FO connections."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        
    def list_profiles(self) -> Dict[str, Profile]:
        """List all available profiles."""
        return self.config_manager.list_profiles()
        
    def get_profile(self, profile_name: str) -> Optional[Profile]:
        """Get a specific profile."""
        return self.config_manager.get_profile(profile_name)
        
    # Remove _cli_to_env_profile method - no longer needed
    # Simplify all other methods
```

#### Step 4: Update CLI and MCP

```python
# CLI updates - work directly with Profile
class CLIManager:
    def _handle_config_commands(self, args: argparse.Namespace) -> int:
        # Work directly with Profile objects
        
# MCP updates - work directly with Profile  
class ProfileTools:
    def execute_create_profile(self, arguments: dict) -> List[TextContent]:
        # Work directly with Profile objects
```

### Migration Strategy

#### Backward Compatibility

1. **Configuration Loading**: Support loading old `CLIProfile` configurations
2. **Automatic Conversion**: Convert old format to new unified format on first load
3. **Default Values**: Provide sensible defaults for missing parameters
4. **Validation**: Validate and fix any configuration issues

#### Migration Steps

```python
class ConfigManager:
    def _migrate_legacy_profile(self, profile_data: dict) -> Profile:
        """Migrate legacy profile to unified format."""
        
        # Handle parameter mapping
        if 'label_cache' in profile_data:
            profile_data['use_label_cache'] = profile_data.pop('label_cache')
        
        if 'label_expiry' in profile_data:
            profile_data['label_cache_expiry_minutes'] = profile_data.pop('label_expiry')
            
        # Add defaults for missing parameters
        defaults = {
            'use_cache_first': True,
            'timeout': 60,
            'description': None,
            'output_format': 'table'
        }
        
        for key, default_value in defaults.items():
            if key not in profile_data:
                profile_data[key] = default_value
                
        return Profile(**profile_data)
```

### Benefits of Phase 2

1. **Code Simplification**: 
   - Remove `EnvironmentProfile` class
   - Remove `_cli_to_env_profile` method
   - Reduce parameter duplication

2. **Enhanced Functionality**:
   - All parameters available in all contexts
   - Consistent behavior between CLI and MCP
   - Built-in validation

3. **Maintainability**:
   - Single definition of profile structure
   - Easier to add new features
   - Reduced testing surface

4. **Performance**:
   - No conversion overhead
   - Direct profile usage
   - Simplified object creation

### Implementation Timeline

#### Week 1: Core Implementation
- [ ] Create unified `Profile` class
- [ ] Update `ConfigManager` to use `Profile`
- [ ] Implement migration logic
- [ ] Update `ProfileManager` to use `Profile`

#### Week 2: Integration
- [ ] Update CLI to use unified profiles
- [ ] Update MCP to use unified profiles
- [ ] Remove deprecated classes and methods
- [ ] Update all imports and references

#### Week 3: Testing and Polish
- [ ] Comprehensive testing of all profile operations
- [ ] Test migration scenarios
- [ ] Update documentation
- [ ] Performance testing

### Risk Assessment

**Low Risk**:
- Unified `Profile` class is superset of both existing classes
- Migration maintains all existing functionality
- Backward compatibility preserved

**Medium Risk**:
- Complex migration logic needs thorough testing
- Multiple components need simultaneous updates

**Mitigation**:
- Incremental implementation with feature flags
- Comprehensive test coverage
- Rollback plan if issues arise

### Success Metrics

1. ✅ All existing profiles load correctly
2. ✅ CLI operations work without changes from user perspective
3. ✅ MCP operations work without changes from user perspective
4. ✅ No data loss during migration
5. ✅ Performance is maintained or improved
6. ✅ Code complexity is reduced (measured by cyclomatic complexity)

## Recommendation

**Proceed with Phase 2**: The benefits significantly outweigh the risks, and the implementation is straightforward with proper testing. The unified profile system will provide a solid foundation for future enhancements and significantly reduce maintenance overhead.

**Priority**: Medium-High - While not urgent (Phase 1 fixed the immediate issue), Phase 2 will prevent future issues and improve code quality substantially.