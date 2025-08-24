# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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