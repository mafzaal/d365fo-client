# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.3] - 2025-08-31

### Added
- **Enhanced Credential Management**: Complete credential source management system for D365 F&O client authentication
  - Added `CredentialSource`, `EnvironmentCredentialSource`, and `KeyVaultCredentialSource` classes for managing different credential sources
  - Implemented `CredentialProvider` interface with `EnvironmentCredentialProvider` and `KeyVaultCredentialProvider` for retrieving credentials
  - Introduced `CredentialManager` to handle credential retrieval with caching and validation
  - Azure Key Vault integration for secure credential storage and retrieval
- **Advanced Sync Session Management**: Enhanced metadata synchronization with detailed progress tracking and session management
  - Added `SyncSessionManager` to manage sync sessions with session-based progress tracking
  - Introduced `SyncSession`, `SyncActivity`, and `SyncPhase` models for detailed tracking of sync operations
  - Implemented methods for starting, executing, and canceling sync sessions with comprehensive error handling
  - Support for multiple sync strategies (`FULL`, `ENTITIES_ONLY`, `SHARING_MODE`, `LABELS`, `FULL_WITHOUT_LABELS`)
  - Enhanced label synchronization by efficiently collecting missing labels from stored metadata with fallback to fresh metadata fetch

### Improved
- **MCP Server Startup Logic**: Enhanced initialization process with multiple authentication modes and improved error handling
  - Implemented three startup scenarios: profile-only mode, default authentication mode, and client credentials mode
  - Updated `load_config()` function to determine startup mode based on environment variables
  - Improved `_startup_initialization()` method to handle each startup mode appropriately with detailed logging
  - Better error handling and status reporting during server startup
- **Authentication Configuration**: Enhanced profile creation and credential source support
  - Updated credential source management to use D365FO-specific environment variables
  - Enhanced profile creation with credential source support and validation
  - Improved authentication manager to support multiple credential sources
- **Background Synchronization**: Initialize sync session manager in FOClient for background metadata synchronization
  - Better integration between client operations and sync session management
  - Enhanced sync performance through session-based tracking and progress reporting

### Changed
- **BREAKING**: Environment variable names standardized for D365FO-specific authentication
  - Updated from `AZURE_*` to `D365FO_*` environment variables for consistency:
    - `AZURE_CLIENT_ID` → `D365FO_CLIENT_ID`
    - `AZURE_CLIENT_SECRET` → `D365FO_CLIENT_SECRET`
    - `AZURE_TENANT_ID` → `D365FO_TENANT_ID`
  - Enhanced compatibility with D365FO-specific authentication workflows
- **Metadata Field Naming**: Renamed 'sample_modules' to 'modules' for consistency in version tracking and debugging
  - Better alignment with D365FO terminology and improved debugging capabilities
  - Consistent naming across metadata operations and cache management

### Removed
- **Deprecated Demo Scripts**: Removed legacy demo scripts to simplify codebase
  - Cleaned up deprecated demonstration scripts and examples
  - Streamlined sync session manager functionality
  - Enhanced codebase maintainability by removing redundant examples

### Dependencies
- **Added**: `azure-keyvault-secrets>=4.8.0` for secure credential management with Azure Key Vault integration
- **Added**: `isodate` dependency for proper date/time handling in Azure Key Vault operations

### Fixed
- **Sync Session Management**: Improved sync session lifecycle management and error handling
- **Label Collection**: Enhanced label ID collection and processing in sync operations
- **Authentication Flow**: Better handling of different authentication scenarios in MCP server startup

## [0.2.2] - 2025-08-28

### Added
- **Environment-scoped Statistics**: Enhanced metadata cache with environment-scoped statistics methods
  - Added database and version management statistics scoping for better cache management
  - Comprehensive tests for cache statistics scoping and environment isolation
  - Improved metadata cache performance monitoring and debugging capabilities

### Improved
- **Async Context Handling**: Resolved background thread blocking issues through enhanced async operations
  - Made sync operations non-blocking to prevent thread deadlocks
  - Enhanced error management for better async context handling
  - Improved stability and performance of concurrent operations
- **Entity Category Handling**: Enhanced `DataEntityInfo.to_dict()` method for flexible entity category processing
  - Added support for handling entity_category as both enum and string values
  - Comprehensive tests for mixed entity_category scenarios
  - Better backward compatibility with different data formats
- **Connection Tools**: Updated connection tools to include client version information for better debugging

### Changed
- **BREAKING**: StrEnum refactoring across the entire d365fo-client codebase
  - Enhanced type safety and enum handling throughout the project
  - Better enum serialization and deserialization capabilities
  - Improved code maintainability and type checking

### Removed
- **BREAKING**: Deprecated MetadataCache and MetadataSearchEngine classes
  - Removed legacy metadata caching implementations
  - All functionality migrated to MetadataCacheV2 for better performance
  - Simplified codebase by removing redundant metadata handling

### Dependencies
- **Updated**: ruff from 0.12.9 to 0.12.10
- **Updated**: mcp from 1.13.0 to 1.13.1  
- **Updated**: requests from 2.32.4 to 2.32.5

## [0.2.1] - 2025-08-24

### Added
- **Action Cache Search and Lookup**: Complete action cache functionality with search and retrieval capabilities
  - Added `search_actions` and `get_action_info` methods to `MetadataCacheV2` for cached action operations
  - Integrated action search capabilities into metadata API with regex pattern matching and entity filtering
  - Enhanced `ActionInfo` model serialization to ensure JSON compatibility for enum values
  - Comprehensive unit tests for action search and lookup with robust error handling coverage
- **Label Processing Utilities**: Enhanced metadata handling with comprehensive label processing
  - New `label_utils.py` module for label processing operations
  - Improved metadata handling with fallback logic for label resolution
  - Enhanced synchronization manager with advanced label processing capabilities
- **Profile Management Enhancements**: Added profile refresh and configuration reload capabilities
  - Profile refresh functionality in `ProfileManager` for dynamic configuration updates
  - Enhanced MCP client manager with profile refresh support
  - Configuration reloading capabilities for runtime profile updates

### Improved
- **MCP Server Startup**: Enhanced initialization process with comprehensive logging and profile management
  - Improved startup logging for better debugging and monitoring
  - Enhanced profile management initialization for MCP server operations
  - Better error handling and status reporting during server startup
- **Logging Consistency**: Refactored logging messages across all modules for consistency and clarity
  - Standardized logging format and message structure
  - Improved log message clarity for better debugging experience
  - Consistent logging patterns across client, labels, main, and output modules
- **Metadata API Operations**: Enhanced FOClient to utilize new cache methods for improved performance
  - Reduced API calls through intelligent caching of action metadata
  - Better integration between client operations and metadata cache
  - Improved performance for action discovery and execution

### Changed
- **Label Caching Simplification**: Removed label expiration functionality to simplify caching logic
  - Streamlined label cache operations by removing expiration tracking
  - Simplified database schema and cache management
  - Enhanced cache performance through reduced complexity
  - Updated database schema to remove expiration-related fields

### Fixed
- **JSON Serialization**: Enhanced enum handling in ActionInfo model for proper JSON serialization
- **Cache Performance**: Optimized label cache operations through simplified logic and better database design
- **Error Handling**: Improved error handling in action cache operations and metadata processing

## [0.2.0] - 2025-08-24

### Added
- **Model Context Protocol (MCP) Server**: Complete MCP server implementation with 12 tools and 4 resource types
  - Connection testing tools (`d365fo_test_connection`)
  - CRUD operation tools (`d365fo_create_entity`, `d365fo_read_entity`, `d365fo_update_entity`, `d365fo_delete_entity`)
  - Metadata discovery tools (`d365fo_search_entities`, `d365fo_get_entity_schema`, `d365fo_search_actions`, `d365fo_call_action`)
  - Enumeration tools (`d365fo_search_enums`, `d365fo_get_enum_info`)
  - Label retrieval tools (`d365fo_resolve_labels`)
  - Database resource handlers for entity, metadata, environment, and query resources
- **Comprehensive CLI Framework**: Full command-line interface with hierarchical commands
  - Entity operations (`entities list`, `entities get`, `entities create`, `entities update`, `entities delete`)
  - Metadata operations (`metadata entities`, `metadata actions`, `metadata enums`, `metadata sync`)
  - Label operations (`labels resolve`, `labels search`)
  - Version information (`version app`, `version platform`, `version build`)
  - Demo mode and examples
- **Enhanced Metadata Caching System V2**: Complete rewrite with intelligent caching
  - Module-based version detection using `GetInstalledModules` action
  - Cross-environment cache sharing and intelligent cache management
  - FTS5 full-text search capabilities for entities and actions
  - Version-aware search engine with comprehensive indexing
  - Smart synchronization manager (`SmartSyncManagerV2`)
- **Advanced Integration Testing Framework**: Multi-tier testing with mock, sandbox, and live environments
  - Mock D365 F&O API server for isolated testing
  - Comprehensive sandbox environment testing (17/17 tests passing)
  - PowerShell automation scripts and Python test runners
  - Environment-based test filtering and performance metrics
- **Profile Management System**: Unified configuration management
  - YAML-based profile configuration with environment variable substitution
  - Cache-first functionality with background synchronization
  - Timeout and connection management parameters
- **Comprehensive Metadata Scripts**: Command-line utilities for metadata operations
  - Data entity search and schema retrieval scripts
  - Enumeration search and information scripts  
  - Action search and information scripts
  - PowerShell and Python implementations with cross-platform support
- **Label Caching V2**: Enhanced label resolution with multi-tier caching
  - Migration from `LabelCache` to `MetadataCache` integration
  - Async support and comprehensive testing
  - Performance improvements and multilingual support
- **Composite Key Support**: Full support for entities with composite primary keys
  - Enhanced URL encoding and method signatures
  - Backward compatibility with single-key entities
  - Comprehensive test coverage for key handling
- **Action Execution Framework**: Support for D365FO OData actions
  - Action discovery and parameter handling
  - Binding kind support (Unbound, BoundToEntitySet, BoundToEntity)
  - MCP prompt integration for action execution
- **Database Tools and Resources**: MCP database integration
  - Database resource handlers for metadata queries
  - SQL-based search capabilities with FTS5 indexing
  - Connection and query management tools

### Improved
- **Enhanced FOClient**: Cache-first functionality with background synchronization
- **Metadata API Operations**: Comprehensive metadata retrieval and caching
- **Entity Search Capabilities**: Improved filtering options and caching for data entities
- **Session Management**: Better connection handling and reuse logic
- **Error Handling**: Enhanced tool descriptions and error messages
- **Documentation**: Comprehensive API documentation and usage examples
- **Test Coverage**: Extensive unit and integration test suites
- **Performance**: Optimized metadata retrieval and caching strategies
- **Cross-platform Support**: Windows, macOS, and Linux compatibility
- **CI/CD Pipeline**: Automated dependency updates with Dependabot
- **Version Detection**: Module-based version tracking for intelligent cache invalidation

### Changed
- **BREAKING**: Refactored `EntityInfo` to `PublicEntityInfo` across codebase
  - Maintains backward compatibility through aliases
  - Updated all related tests and metadata modules
- **BREAKING**: Default `metadata_cache_dir` now uses platform-appropriate user cache directories
  - **Windows**: `%LOCALAPPDATA%\d365fo-client`
  - **macOS**: `~/Library/Caches/d365fo-client`  
  - **Linux**: `~/.cache/d365fo-client`
- **Metadata System Migration**: Complete migration from V1 to V2 metadata caching
  - Enhanced performance and cross-environment sharing
  - Intelligent synchronization and version management
  - FTS5 search integration for better metadata discovery
- **Label Operations**: Refactored caching mechanism for improved performance
- **Search Tools**: Simplified MCP search tools with keyword-based strategies
- **Profile System**: Consolidated `CLIProfile` and `EnvironmentProfile` into unified `Profile` class
- **Parameter Standardization**: Corrected parameter names (e.g., `order_by` to `orderby`)

### Fixed
- **Session Management**: Improved session reuse and closed session detection
- **Parameter Handling**: Fixed default parameters in search methods
- **Entity Filtering**: Updated to use correct attribute names in metadata operations
- **PyPI Publishing**: Corrected publish URLs in GitHub Actions workflow
- **SQL Pattern Conversion**: Enhanced pattern handling for metadata search
- **Enum Serialization**: Convert enum values to strings for improved compatibility
- **Connection Testing**: Improved reliability of connection tests and metadata operations
- **Cache Directory Management**: More robust directory creation following platform best practices

### Dependencies
- **Added**: `mcp` library for Model Context Protocol server support
- **Updated**: GitHub Actions dependencies (checkout v5, download-artifact v5)
- **Enhanced**: Development dependencies for comprehensive testing and quality assurance

## [0.1.0] - 2025-08-16

### Added
- Initial release
- Basic project setup with uv
- Microsoft Dynamics 365 Finance & Operations client foundation
- Project structure with modern Python packaging standards
- MIT License and basic documentation