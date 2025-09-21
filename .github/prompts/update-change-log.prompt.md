---
mode: agent
description: Update the change log file with the latest changes based on recent commits and increment version numbers for d365fo-client package.
---

# AI Assistant Instructions: Update d365fo-client Changelog and Version Numbers

## Overview
These instructions guide an AI assistant to systematically update the d365fo-client project's CHANGELOG.md and increment version numbers in pyproject.toml based on git commit history. This is a comprehensive Python package for Microsoft Dynamics 365 Finance & Operations (D365 F&O) that provides OData client library, CLI application, and MCP server functionality.

## Process Steps

### 1. Examine Current Version Files
- Read `pyproject.toml` to identify current version number (look for `version = "X.Y.Z"` around line 3)
- Read `CHANGELOG.md` to understand the last documented version and changes
- Note: This project uses `uv` for package management and has two main entry points:
  - CLI: `d365fo-client` command
  - MCP Server: `d365fo-mcp-server` command

### 2. Analyze Git History
- Use `git log --oneline --since="YYYY-MM-DD" --pretty=format:"%h %s" --reverse` to get commits since last changelog entry
- Use `git log --since="YYYY-MM-DD" --pretty=format:"%h %s%n%b" --reverse` for detailed commit messages
- Use `git show --stat <commit-hashes> --pretty=format:"%h %s"` to understand scope of changes

### 3. Determine Version Increment Strategy
Follow semantic versioning (semver.org):
- **MAJOR (X.0.0)**: Breaking changes, incompatible API changes
- **MINOR (0.X.0)**: New features, backward-compatible functionality additions
- **PATCH (0.0.X)**: Bug fixes, backward-compatible fixes

Common indicators for d365fo-client:
- New MCP tools/resources → MINOR bump
- New CLI commands/features → MINOR bump  
- New D365 F&O data entity operations → MINOR bump
- Bug fixes only → PATCH bump
- Breaking API changes → MAJOR bump
- Dependency updates (via dependabot with `deps:` prefix) → PATCH bump
- CI updates (via dependabot with `ci:` prefix) → PATCH bump
- Documentation improvements → PATCH bump

### 4. Update CHANGELOG.md
Follow "Keep a Changelog" format (already used by this project):
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features, tools, capabilities (MCP tools, CLI commands, D365 F&O operations)

### Changed
- Changes to existing functionality

### Improved
- Performance enhancements, optimizations, better implementations

### Fixed
- Bug fixes and corrections

### Removed
- Deprecated or removed functionality

### Dependencies
- Dependency updates (from dependabot or manual updates)

### Documentation
- Documentation improvements
```

Categories to look for in d365fo-client commits:
- `feat:` → Added section
- `fix:` → Fixed section  
- `deps:` (from dependabot) → Dependencies section
- `docs:` → Documentation section
- `ci:` (from dependabot) → Dependencies section
- `chore:` → May go in Changed or omit if minor
- Performance improvements → Improved section
- Breaking changes → Note as **BREAKING** in relevant section

### 5. Update Version Numbers
Update in exact order:
1. **pyproject.toml**: Change `version = "X.Y.Z"` (around line 3)

### 6. Quality Checks
- Ensure version numbers match across all files
- Verify changelog entry has proper date format (YYYY-MM-DD)
- Check that changes are categorized appropriately
- Confirm semantic versioning logic is sound

## File Locations
- **Version source**: `pyproject.toml` (line ~3, within `[project]` section)
- **Changelog**: `CHANGELOG.md` (top of file, follows "Keep a Changelog" format)
- **Package structure**: 
  - Main package: `src/d365fo_client/`
  - CLI entry point: `d365fo_client.main:main`
  - MCP server entry point: `d365fo_client.mcp.main:main`

## Git Commands Reference
```bash
# Get commits since last release (adjust date as needed)
git log --oneline --since="2025-08-31" --pretty=format:"%h %s" --reverse

# Get detailed commit info
git log --since="2025-08-31" --pretty=format:"%h %s%n%b" --reverse

# Show file changes for specific commits
git show --stat <commit1> <commit2> --pretty=format:"%h %s"

# Get commits between tags (if tags exist)
git log --oneline v0.2.2..v0.2.3 --pretty=format:"%h %s"
```

## Example Workflow
1. Read current version (e.g., 0.2.3)
2. Analyze commits → New MCP tools added + metadata improvements + dependency updates
3. Determine: MINOR bump → 0.3.0 (or PATCH → 0.2.4 for smaller changes)
4. Update CHANGELOG.md with new 0.3.0 section
5. Update pyproject.toml version to 0.3.0

## d365fo-client Specific Considerations
- **MCP Server**: Changes to MCP tools/resources typically warrant MINOR version bump
- **CLI Features**: New CLI commands or significant CLI improvements → MINOR bump
- **D365 F&O Integration**: New data entity operations, metadata features → MINOR bump
- **Authentication**: Changes to credential management, Azure AD integration → Consider impact
- **Package Structure**: This project uses `uv` for dependency management
- **Entry Points**: Two main entry points (CLI and MCP server) to consider for breaking changes


## Common Pitfalls to Avoid
- Don't mix up version numbers between files
- Don't skip dependency updates in changelog (dependabot creates many `deps:` commits)
- Don't use wrong date format (YYYY-MM-DD)
- Don't forget to categorize changes properly (use Improved section for enhancements)
- Don't increment version incorrectly for scope of changes
- Don't miss MCP-specific or CLI-specific changes
- Remember this project has comprehensive changelog sections (Added, Changed, Improved, Fixed, Removed, Dependencies, Documentation)

## Success Criteria
✅ CHANGELOG.md has new version entry with proper date (YYYY-MM-DD format)
✅ All changes from git history are documented appropriately
✅ Version number updated in pyproject.toml (line ~3)
✅ Semantic versioning logic is correctly applied
✅ Changelog follows "Keep a Changelog" format with appropriate sections
✅ MCP server and CLI changes are properly categorized
✅ Dependencies section includes dependabot updates
✅ Breaking changes are clearly marked with **BREAKING** prefix
✅ D365 F&O specific features are documented clearly
