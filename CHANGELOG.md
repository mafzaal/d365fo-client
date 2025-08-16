# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete modular refactoring of F&O client implementation
- Comprehensive OData client with CRUD operations
- Advanced metadata management and caching
- Label operations with multilingual support
- Authentication management with Azure AD integration
- HTTP session management with proper error handling
- Query building utilities for OData operations
- Intelligent caching for labels and metadata
- Full type hints and modern async/await patterns
- Comprehensive test suite
- Detailed documentation and examples
- Platform-appropriate user cache directories following OS conventions
- Utility functions for cache directory management (`get_user_cache_dir`, `ensure_directory_exists`)

### Changed
- Refactored monolithic code into modular, maintainable packages
- Updated project structure following Python packaging best practices
- Enhanced error handling with custom exception classes
- Improved configuration management
- **BREAKING**: Default `metadata_cache_dir` now uses platform-appropriate user cache directories instead of `"./metadata_cache"`
  - **Windows**: `%LOCALAPPDATA%\d365fo-client` (e.g., `C:\Users\username\AppData\Local\d365fo-client`)
  - **macOS**: `~/Library/Caches/d365fo-client` (e.g., `/Users/username/Library/Caches/d365fo-client`)
  - **Linux**: `~/.cache/d365fo-client` (e.g., `/home/username/.cache/d365fo-client`)

### Fixed
- Cache directory creation is now more robust and follows platform best practices

## [0.1.0] - 2025-08-16

### Added
- Initial release
- Basic project setup with uv
- Microsoft Dynamics 365 Finance & Operations client foundation
- Project structure with modern Python packaging standards
- MIT License and basic documentation