# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.3] - 2025-10-19

### Fixed
- **OData Key Formatting**: Fixed OData date/time key formatting for D365 F&O compatibility
  - **BREAKING**: Date/time types in OData keys no longer use quotes (aligns with D365 F&O OData spec)
  - OData queries with date/time keys now work correctly with D365 F&O
  - Enhanced test coverage with comprehensive mock support for session manager
- **Docker Deployment**: Updated deployment script to use 'latest' Docker image tag
- **Docker Build**: Updated Docker build tags comments for clarity and removed unused SHA tagging

### Improved
- **Cache Organization**: Updated cache configuration to use shared base directory across environments
  - **BREAKING**: Cache directory structure changed to shared base with environment subdirectories
  - Integration tests now use environment-specific cache organization
- **Unit Testing**: Enhanced unit tests with proper SessionManager mocking to avoid initialization issues

### Dependencies
- **GitHub Actions**: Bump astral-sh/setup-uv from 6 to 7
- **Azure Dependencies**: Updated azure-core to 1.36.0, charset-normalizer to 3.4.4, pydantic to 2.12.2

## [0.3.2] - 2025-10-12

### Added
- **JSON Service Tools**: New MCP tools for calling D365 F&O JSON services
  - `d365fo_call_json_service` tool for generic JSON service operations
  - `d365fo_call_sql_diagnostic_service` tool for SQL diagnostic operations
  - JsonServiceRequest and JsonServiceResponse models for structured requests
  - Comprehensive examples in `examples/json_service_examples.py`
- **Enhanced QueryBuilder**: Advanced OData query building with schema awareness
  - Automatic type detection and serialization for entity properties
  - Support for datetime, enum, boolean, and numeric types
  - Special character handling and proper encoding
  - Composite key discovery and validation
- **Azure Container Apps Deployment**: Production-ready deployment templates
  - Azure Container Apps deployment script (`deploy-aca.sh`)
  - ARM template for infrastructure as code (`azure-deploy.json`)
  - Support for multiple authentication modes (API key, client credentials, default Azure credentials)
  - Comprehensive deployment documentation in README
- **CLI JSON Service Support**: New CLI commands for JSON service operations
  - `d365fo-client json-service call` command
  - `d365fo-client json-service sql-diagnostic` command

### Improved
- **OData Serialization**: Enhanced entity validation and serialization
  - New `ODataSerializer` class for type-safe serialization
  - Better handling of datetime, enum, and special data types
  - Improved error messages for validation failures
- **CRUD Operations**: Enhanced MCP CRUD tools with better error handling
  - Improved query validation and execution
  - Better support for composite keys
  - Enhanced error messages and diagnostics
- **Docker Workflow**: Intelligent Docker tagging strategy
  - Branch-based tags for on-demand builds (develop, feature branches)
  - SHA-based tags with branch prefix
  - Conditional `:latest` tag (only applied to main branch)
  - Semantic versioning support (v1.2.3 → :1.2.3, :1.2, :1)

### Fixed
- **Docker Build Workflow**: Removed duplicate push and tags entries
- **Profile Creation**: Enhanced warnings for profile creation in FastMCP server

### Dependencies
- Bumped `ruff` from 0.13.2 to 0.13.3
- Bumped `authlib` from 1.6.4 to 1.6.5
- Bumped `isort` from 6.0.1 to 6.1.0
- Bumped `mcp` from 1.15.0 to 1.16.0

### Documentation
- Added comprehensive Docker build workflow guide
- Enhanced Azure deployment instructions with Bash script and ARM template options
- Added entity validation test documentation (`tests/integration/ENTITY_VALIDATION_TESTS.md`)
- New QueryBuilder enhancement summary (`docs/QUERYBUILDER_ENHANCEMENT_SUMMARY.md`)
- New JSON service implementation documentation (`docs/FASTMCP_JSON_SERVICE_IMPLEMENTATION_COMPLETE.md`)

### Testing
- Added integration tests for entity validation and OData serialization
- Added integration tests for MCP CRUD tools
- Added unit tests for enhanced QueryBuilder with schema awareness
- Added comprehensive JSON service unit tests
- Expanded sandbox integration tests

## [0.3.1] - 2025-10-01

### Added
- **API Key Authentication Provider**: New authentication provider for MCP server
  - Added auth/providers/apikey.py for secure API key validation
  - Enhanced fastmcp_main.py with API key authentication support
  - Comprehensive test suite for API key functionality
  - Integration and unit tests for secure authentication flow

### Fixed
- **Azure OAuth Provider Client Persistence**: Resolved serialization and reliability issues
  - Fixed OAuthClientInformationFull serialization using Pydantic mode="json"
  - Implemented atomic write operations for client data persistence
  - Enhanced error handling and recovery for individual client failures
  - Improved _save_clients with directory creation and UTF-8 encoding
  - Enhanced _load_clients with robust validation and error recovery
  - Added graceful degradation when storage is unavailable
  - Support for Unicode characters in client data (18 comprehensive test cases added)

### Improved
- **Docker Configuration**: Enhanced container setup with environment variables
- **Test Coverage**: Added comprehensive test suites for authentication providers

## [0.3.0] - 2025-09-29

### Added
- **Pydantic Settings Model**: Comprehensive environment variable management with type safety and validation
  - Added D365FOSettings class with support for 35+ environment variables
  - Automatic type conversion and validation with pydantic-settings>=2.6.0
  - Support for .env files and IDE IntelliSense
  - Utility methods: has_client_credentials(), get_startup_mode()
- **Custom Log File Support**: D365FO_LOG_FILE environment variable for custom log file paths
  - Automatic parent directory creation
  - Backward compatibility with existing logging behavior
- **Legacy Config Migration**: Automatic detection and migration of legacy configuration files
  - Field name migration (cache_dir -> metadata_cache_dir, auth_mode -> use_default_credentials)
  - Backup creation before migration
  - Comprehensive migration logging

### Changed
- **Environment Variable Standardization**: Updated all MCP HTTP configuration variables to use D365FO_ prefix
  - MCP_HTTP_HOST → D365FO_HTTP_HOST
  - MCP_HTTP_PORT → D365FO_HTTP_PORT
  - MCP_HTTP_STATELESS → D365FO_HTTP_STATELESS
  - MCP_HTTP_JSON → D365FO_HTTP_JSON
  - MCP_MAX_CONCURRENT_REQUESTS → D365FO_MAX_CONCURRENT_REQUESTS
  - MCP_REQUEST_TIMEOUT → D365FO_REQUEST_TIMEOUT
  - Maintains backward compatibility through proper fallback handling

### Improved
- **MCP Return Type Standardization**: Changed all MCP tools to return dictionaries instead of JSON strings
  - Updated connection tools, CRUD tools, metadata tools, label tools, profile tools, sync tools, and performance tools
  - Improved type safety and consistency across MCP interface
- **FastMCP Server Enhancements**: Enhanced server initialization and configuration loading
  - Comprehensive startup configuration logging with structured output
  - Improved error handling and graceful shutdown
  - Better environment variable support and documentation
- **Parameter Naming Standardization**: Consistent naming conventions across CRUD tools mixin
- **Profile Management**: Enhanced profile handling and credential source management

### Fixed
- **Credential Source Serialization**: Resolved authentication failures in Profile.to_client_config()
  - Fixed 'dict object has no attribute to_dict' error in MCP client manager
  - Updated ProfileManager methods to handle credential source objects properly
- **Base URL Formatting**: Corrected authentication scope formatting for proper Azure AD integration
- **MCP Server Script Path**: Updated d365fo-mcp-server script path to correct module location

### Removed
- Deprecated example scripts cleanup
- Legacy credential handling simplification

### Dependencies
- Bumped `ruff` from 0.13.0 to 0.13.2 (linting tool patch updates: 0.13.0 → 0.13.1 → 0.13.2)
- Bumped `mypy` from 1.18.1 to 1.18.2 (type checking tool patch update)  
- Bumped `black` from 25.1.0 to 25.9.0 (code formatter minor update)
- Bumped `mcp` from 1.14.0 to 1.15.0 (Model Context Protocol SDK updates: 1.14.0 → 1.14.1 → 1.15.0)
- Bumped `pydantic-settings` from 2.10.1 to 2.11.0 (settings management library minor update)
- Bumped `pyyaml` from 6.0.2 to 6.0.3 (YAML parser patch update)
- Bumped `types-pyyaml` from 6.0.12.20250822 to 6.0.12.20250915 (type stubs update)
- Added `pydantic-settings>=2.6.0` (new dependency for environment variable management)
- Bumped `docker/login-action` from 3.5.0 to 3.6.0 (CI dependency for Docker workflow)

## [0.2.4] - 2025-09-21

### Added
- **Docker Support**: Added containerization support for d365fo-client package
  - Added `.dockerignore` file with comprehensive exclusion patterns for clean Docker builds
  - Added `Dockerfile` with multi-stage build process optimized for production deployment
  - Added GitHub workflow for automated Docker image building and publishing to GitHub Container Registry

### Documentation
- **Comprehensive MCP Tools Guide**: Added detailed introduction to MCP tools with usage examples and best practices
- **Enhanced Installation Instructions**: Updated README with improved installation instructions for VS Code and VS Code Insiders
- **PyPI Integration**: Added PyPI download badge and installation links to README for better discoverability

### Dependencies
- Bumped `actions/setup-python` from 5 to 6 (CI dependency)
- Bumped `ruff` from 0.12.10 to 0.13.0 (linting tool update)
- Bumped `pytest-cov` from 6.2.1 to 7.0.0 (test coverage tool major update)
- Bumped `pytest` from 8.4.1 to 8.4.2 (testing framework patch update)
- Bumped `azure-identity` from 1.24.0 to 1.25.0 (Azure authentication library update)
- Bumped `mypy` from 1.17.1 to 1.18.1 (type checking tool update)
- Bumped `mcp` from 1.13.1 to 1.14.0 (Model Context Protocol SDK update)
- Bumped `pytest-asyncio` from 1.1.0 to 1.2.0 (async testing support update)

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