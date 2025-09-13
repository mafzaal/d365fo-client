# FastMCP Server Refactoring Specification

## Overview

This specification provides detailed instructions for refactoring the monolithic `fastmcp_server.py` file (~3,000 lines) into a modular, maintainable architecture using the mixin pattern. The refactoring will be executed in phases to ensure system stability and backward compatibility.

## Current State Analysis

### File Structure
- **Main File**: `src/d365fo_client/mcp/fastmcp_server.py` (~3,000 lines)
- **Tool Count**: 37 MCP tools across 8 categories
- **Key Issues**: 
  - Single monolithic class with mixed responsibilities
  - Duplicate code with existing `tools/` classes
  - No clear separation of concerns
  - Difficult to maintain and test

### Existing Architecture
```
src/d365fo_client/mcp/
├── fastmcp_server.py (MONOLITHIC - needs refactoring)
├── tools/
│   ├── connection_tools.py ✓ (existing, well-structured)
│   ├── crud_tools.py ✓ (existing, well-structured)
│   ├── database_tools.py ✓ (existing, well-structured)
│   ├── label_tools.py ✓ (existing, well-structured)
│   ├── metadata_tools.py ✓ (existing, well-structured)
│   ├── profile_tools.py ✓ (existing, well-structured)
│   └── sync_tools.py ✓ (existing, well-structured)
├── client_manager.py ✓
├── models.py ✓
└── resources/ ✓
```

## Phase 1: Extract Tool Mixins (IMMEDIATE PRIORITY)

### Objective
Reduce main file size by 80% (~2,400 lines → ~600 lines) while maintaining full backward compatibility.

### Implementation Plan

#### Step 1: Create Mixin Infrastructure

**1.1 Create Mixins Directory**
```bash
mkdir -p src/d365fo_client/mcp/mixins
touch src/d365fo_client/mcp/mixins/__init__.py
```

**1.2 Create Base Mixin Class**

File: `src/d365fo_client/mcp/mixins/base_tools_mixin.py`
```python
"""Base mixin class for FastMCP tool categories."""

import logging
from typing import Optional
from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class BaseToolsMixin:
    """Base mixin for FastMCP tool categories.
    
    Provides common functionality and client access patterns
    for all tool category mixins.
    """
    
    # These will be injected by the main server class
    client_manager: D365FOClientManager
    mcp: 'FastMCP'  # Forward reference
    
    async def _get_client(self, profile: str = "default"):
        """Get D365FO client for specified profile.
        
        Args:
            profile: Profile name to use
            
        Returns:
            Configured D365FO client instance
        """
        if not hasattr(self, 'client_manager') or not self.client_manager:
            raise RuntimeError("Client manager not initialized")
        return await self.client_manager.get_client(profile)
    
    def _create_error_response(self, error: Exception, tool_name: str, arguments: dict) -> str:
        """Create standardized error response.
        
        Args:
            error: Exception that occurred
            tool_name: Name of the tool that failed
            arguments: Arguments passed to the tool
            
        Returns:
            JSON string with error details
        """
        import json
        return json.dumps({
            "error": str(error),
            "tool": tool_name,
            "arguments": arguments,
            "error_type": type(error).__name__,
        }, indent=2)
```

#### Step 2: Extract Database Tools Mixin (Highest Priority)

**2.1 Create Database Tools Mixin**

File: `src/d365fo_client/mcp/mixins/database_tools_mixin.py`

Extract the following tools from `fastmcp_server.py`:
- `d365fo_execute_sql_query`
- `d365fo_get_database_schema`
- `d365fo_get_table_info`
- `d365fo_get_database_statistics`

Plus all database helper methods:
- `_setup_database_tools`
- `_validate_query_safety`
- `_get_database_path`
- `_execute_safe_query`
- `_format_query_results`
- `_get_schema_info`
- `_get_detailed_table_info`
- `_get_enhanced_statistics`

**Template Structure:**
```python
"""Database tools mixin for FastMCP server."""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class DatabaseQuerySafetyError(Exception):
    """Raised when a database query is deemed unsafe or invalid."""
    pass


class DatabaseToolsMixin(BaseToolsMixin):
    """Database analysis and query tools for FastMCP server."""
    
    def setup_database_tools(self):
        """Initialize database tools configuration."""
        # Move _setup_database_tools logic here
        pass
    
    def register_database_tools(self):
        """Register all database tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_execute_sql_query(...):
            """Execute a SELECT query against the D365FO metadata database."""
            # Move complete implementation from fastmcp_server.py
            pass
            
        @self.mcp.tool()
        async def d365fo_get_database_schema(...):
            """Get comprehensive schema information."""
            # Move complete implementation from fastmcp_server.py
            pass
            
        @self.mcp.tool()
        async def d365fo_get_table_info(...):
            """Get detailed table information."""
            # Move complete implementation from fastmcp_server.py
            pass
            
        @self.mcp.tool()
        async def d365fo_get_database_statistics(...):
            """Get database statistics and analytics."""
            # Move complete implementation from fastmcp_server.py
            pass
    
    # Move all helper methods here:
    def _validate_query_safety(self, query: str) -> None:
        # Move implementation
        pass
        
    async def _get_database_path(self, profile: str = "default") -> str:
        # Move implementation  
        pass
        
    # ... etc for all database helper methods
```

#### Step 3: Extract Metadata Tools Mixin

**3.1 Create Metadata Tools Mixin**

File: `src/d365fo_client/mcp/mixins/metadata_tools_mixin.py`

Extract these tools:
- `d365fo_search_entities`
- `d365fo_get_entity_schema`
- `d365fo_search_actions`
- `d365fo_search_enumerations`
- `d365fo_get_enumeration_fields`
- `d365fo_get_installed_modules`

Plus helper methods:
- `_try_fts_search`
- `_extract_search_terms`

#### Step 4: Extract CRUD Tools Mixin

**4.1 Create CRUD Tools Mixin**

File: `src/d365fo_client/mcp/mixins/crud_tools_mixin.py`

Extract these tools:
- `d365fo_query_entities`
- `d365fo_get_entity_record`
- `d365fo_create_entity_record`
- `d365fo_update_entity_record`
- `d365fo_delete_entity_record`
- `d365fo_call_action`

#### Step 5: Extract Remaining Tool Categories

**5.1 Profile Tools Mixin**

File: `src/d365fo_client/mcp/mixins/profile_tools_mixin.py`

Tools:
- `d365fo_list_profiles`
- `d365fo_get_profile`
- `d365fo_create_profile`
- `d365fo_update_profile`
- `d365fo_delete_profile`
- `d365fo_set_default_profile`
- `d365fo_get_default_profile`
- `d365fo_validate_profile`
- `d365fo_test_profile_connection`

**5.2 Sync Tools Mixin**

File: `src/d365fo_client/mcp/mixins/sync_tools_mixin.py`

Tools:
- `d365fo_start_sync`
- `d365fo_get_sync_progress`
- `d365fo_cancel_sync`
- `d365fo_list_sync_sessions`
- `d365fo_get_sync_history`

**5.3 Label Tools Mixin**

File: `src/d365fo_client/mcp/mixins/label_tools_mixin.py`

Tools:
- `d365fo_get_label`
- `d365fo_get_labels_batch`

**5.4 Connection Tools Mixin**

File: `src/d365fo_client/mcp/mixins/connection_tools_mixin.py`

Tools:
- `d365fo_test_connection`
- `d365fo_get_environment_info`

**5.5 Performance Tools Mixin**

File: `src/d365fo_client/mcp/mixins/performance_tools_mixin.py`

Tools:
- `d365fo_get_server_performance`
- `d365fo_reset_performance_stats`
- `d365fo_get_server_config`

#### Step 6: Update Mixins __init__.py

File: `src/d365fo_client/mcp/mixins/__init__.py`
```python
"""FastMCP tool mixins."""

from .base_tools_mixin import BaseToolsMixin
from .connection_tools_mixin import ConnectionToolsMixin
from .crud_tools_mixin import CrudToolsMixin
from .database_tools_mixin import DatabaseToolsMixin, DatabaseQuerySafetyError
from .label_tools_mixin import LabelToolsMixin
from .metadata_tools_mixin import MetadataToolsMixin
from .performance_tools_mixin import PerformanceToolsMixin
from .profile_tools_mixin import ProfileToolsMixin
from .sync_tools_mixin import SyncToolsMixin

__all__ = [
    'BaseToolsMixin',
    'ConnectionToolsMixin',
    'CrudToolsMixin',
    'DatabaseToolsMixin',
    'DatabaseQuerySafetyError',
    'LabelToolsMixin',
    'MetadataToolsMixin',
    'PerformanceToolsMixin',
    'ProfileToolsMixin',
    'SyncToolsMixin',
]
```

#### Step 7: Refactor Main Server Class

**7.1 Update FastD365FOMCPServer Class**

In `fastmcp_server.py`, replace the monolithic class with:

```python
"""FastMCP-based D365FO MCP Server implementation."""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from weakref import WeakValueDictionary

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .. import __version__
from ..profile_manager import ProfileManager
from .client_manager import D365FOClientManager
from .models import MCPServerConfig
from .mixins import (
    ConnectionToolsMixin,
    CrudToolsMixin,
    DatabaseToolsMixin,
    LabelToolsMixin,
    MetadataToolsMixin,
    PerformanceToolsMixin,
    ProfileToolsMixin,
    SyncToolsMixin,
)

logger = logging.getLogger(__name__)


class SessionContext:
    """Simple session context that can be weakly referenced."""
    # Keep existing implementation
    pass


class FastD365FOMCPServer(
    DatabaseToolsMixin,
    MetadataToolsMixin,
    CrudToolsMixin,
    ProfileToolsMixin,
    SyncToolsMixin,
    LabelToolsMixin,
    ConnectionToolsMixin,
    PerformanceToolsMixin,
):
    """FastMCP-based D365FO MCP Server with multi-transport support."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the FastMCP D365FO server."""
        # Keep existing initialization logic but remove tool registration
        self.config = config or self._load_default_config()
        self.profile_manager = ProfileManager()
        self.client_manager = D365FOClientManager(self.config, self.profile_manager)

        # Extract server configuration
        server_config = self.config.get("server", {})
        transport_config = server_config.get("transport", {})

        # Initialize FastMCP server with configuration
        self.mcp = FastMCP(
            name=server_config.get("name", "d365fo-mcp-server"),
            instructions=server_config.get(
                "instructions",
                "Microsoft Dynamics 365 Finance & Operations MCP Server providing comprehensive access to D365FO data, metadata, and operations",
            ),
            host=transport_config.get("http", {}).get("host", "127.0.0.1"),
            port=transport_config.get("http", {}).get("port", 8000),
            debug=server_config.get("debug", False),
            json_response=transport_config.get("http", {}).get("json_response", False),
            stateless_http=transport_config.get("http", {}).get("stateless", False),
        )

        # Setup dependency injection and features
        self._setup_dependency_injection()
        self._setup_production_features()
        self._setup_mixin_tools()

        # Register all components
        self._register_tools()
        self._register_resources()
        self._register_prompts()

        logger.info(f"FastD365FOMCPServer v{__version__} initialized with modular architecture")

    def _setup_mixin_tools(self):
        """Setup tool-specific configurations for mixins."""
        self.setup_database_tools()
        # Add other tool setup calls as needed

    def _register_tools(self):
        """Register all tools using mixins."""
        logger.info("Registering tools from mixins...")
        
        # Register tools from each mixin
        self.register_database_tools()
        self.register_metadata_tools()
        self.register_crud_tools()
        self.register_profile_tools()
        self.register_sync_tools()
        self.register_label_tools()
        self.register_connection_tools()
        self.register_performance_tools()
        
        logger.info("All tools registered successfully")

    # Keep existing methods that don't belong to specific tool categories:
    # - _load_default_config
    # - _setup_dependency_injection  
    # - _setup_production_features
    # - _register_resources
    # - _register_prompts
    # - Performance monitoring methods
    # - Session management methods
    # - Server lifecycle methods
```

### Implementation Guidelines for AI Agent

#### Code Movement Rules

1. **Exact Code Preservation**: When moving code from `fastmcp_server.py` to mixins, preserve:
   - Complete function signatures
   - All docstrings and comments
   - Exact implementation logic
   - Error handling patterns
   - Type hints

2. **Import Management**: When moving code, update imports to:
   - Use relative imports within mixin modules
   - Import required external dependencies
   - Maintain all existing functionality

3. **Method Naming**: Keep all existing method names unchanged to ensure backward compatibility.

#### File Creation Order

Execute in this specific order to minimize dependencies:

1. Create `mixins/__init__.py` (empty initially)
2. Create `base_tools_mixin.py`
3. Create `database_tools_mixin.py` 
4. Create `metadata_tools_mixin.py`
5. Create `crud_tools_mixin.py`
6. Create `profile_tools_mixin.py`
7. Create `sync_tools_mixin.py`
8. Create `label_tools_mixin.py`
9. Create `connection_tools_mixin.py`
10. Create `performance_tools_mixin.py`
11. Update `mixins/__init__.py` with all exports
12. Refactor `fastmcp_server.py`

#### Code Extraction Process

For each mixin file:

1. **Copy Tool Decorators**: Copy complete `@self.mcp.tool()` decorated functions
2. **Copy Helper Methods**: Copy all private methods used by the tools
3. **Copy Constants**: Copy any constants or configuration used
4. **Update Self References**: Ensure `self.mcp` and `self.client_manager` work correctly
5. **Test Imports**: Verify all imports are available in the new location

#### Testing Requirements

After each mixin creation:

1. **Import Test**: Verify the mixin can be imported
2. **Inheritance Test**: Verify the main server class can inherit from all mixins
3. **Tool Registration Test**: Verify tools register correctly with FastMCP
4. **Functionality Test**: Verify basic tool functionality works

### Verification Checklist

After Phase 1 completion:

- [ ] All 37 tools are registered and functional
- [ ] Main server file is ~600 lines (80% reduction)
- [ ] All mixins are properly structured
- [ ] No duplicate code between main file and mixins
- [ ] All imports are correctly resolved
- [ ] Server starts successfully
- [ ] Basic tool functionality works
- [ ] Performance characteristics unchanged
- [ ] No breaking changes to external API

## Phase 2: Integration with Existing Tools Classes (FUTURE)

### Objective
Eliminate duplicate code by leveraging existing `tools/` classes through adapter pattern.

### Implementation Plan

#### Step 1: Create Adapter Infrastructure

**1.1 Create Adapters Directory**
```bash
mkdir -p src/d365fo_client/mcp/adapters
touch src/d365fo_client/mcp/adapters/__init__.py
```

**1.2 Base Adapter Class**

File: `src/d365fo_client/mcp/adapters/base_adapter.py`
```python
"""Base adapter for integrating existing tools with FastMCP."""

from abc import ABC, abstractmethod
from typing import List
from mcp.types import TextContent


class BaseToolsAdapter(ABC):
    """Base adapter for tool integration."""
    
    def __init__(self, client_manager, mcp_server):
        self.client_manager = client_manager
        self.mcp = mcp_server
        
    @abstractmethod
    def register_tools(self):
        """Register tools with FastMCP server."""
        pass
        
    def _text_content_to_string(self, content: List[TextContent]) -> str:
        """Convert TextContent list to string for FastMCP compatibility."""
        if not content:
            return "{}"
        return content[0].text if content else "{}"
```

#### Step 2: Create Specific Adapters

**2.1 Database Tools Adapter**

File: `src/d365fo_client/mcp/adapters/database_adapter.py`
```python
"""Database tools adapter for FastMCP integration."""

from ..tools.database_tools import DatabaseTools
from .base_adapter import BaseToolsAdapter


class DatabaseToolsAdapter(BaseToolsAdapter):
    """Adapter for DatabaseTools integration with FastMCP."""
    
    def __init__(self, client_manager, mcp_server):
        super().__init__(client_manager, mcp_server)
        self.database_tools = DatabaseTools(client_manager)
        
    def register_tools(self):
        """Register database tools using existing implementation."""
        
        @self.mcp.tool()
        async def d365fo_execute_sql_query(
            query: str,
            limit: int = 100,
            format: str = "table",
            profile: str = "default",
        ) -> str:
            """Execute a SELECT query against the D365FO metadata database."""
            arguments = {
                "query": query,
                "limit": limit,
                "format": format,
                "profile": profile
            }
            result = await self.database_tools.execute_sql_query(arguments)
            return self._text_content_to_string(result)
            
        # Similar pattern for other database tools
```

**2.2 Metadata Tools Adapter**

Similar pattern for `MetadataToolsAdapter` using `MetadataTools` class.

#### Step 3: Update Mixins to Use Adapters

Replace mixin implementations with adapter delegations where existing tools classes are available.

### Verification for Phase 2

- [ ] All duplicate code eliminated
- [ ] Existing tools classes fully leveraged
- [ ] Consistent behavior between direct tools and FastMCP tools
- [ ] No performance degradation
- [ ] Simplified maintenance

## Phase 3: Advanced Modularization (OPTIONAL)

### Objective
Complete microservice-style architecture with lazy loading and advanced features.

### Features
- Lazy tool loading
- Plugin architecture
- Resource management optimization
- Advanced caching
- Health monitoring

### Implementation
To be detailed when Phase 1 and 2 are complete.

## Error Handling and Rollback

### Error Scenarios

1. **Import Errors**: Missing dependencies in mixin files
2. **Tool Registration Failures**: Tools not registering with FastMCP
3. **Runtime Errors**: Tools failing at execution time
4. **Performance Degradation**: Slower response times

### Rollback Strategy

1. **Immediate Rollback**: Keep original `fastmcp_server.py` as `fastmcp_server.py.backup`
2. **Incremental Rollback**: Each phase can be independently rolled back
3. **Testing Gates**: Don't proceed to next phase until current phase passes all tests

### Monitoring Points

- Server startup time
- Tool registration count
- Memory usage
- Response times
- Error rates

## Success Metrics

### Phase 1 Success Criteria

1. **File Size Reduction**: Main file reduced from ~3,000 to ~600 lines (80% reduction)
2. **Maintainability**: Each tool category in separate, focused file
3. **Functionality**: All 37 tools working identically to before
4. **Performance**: No measurable performance degradation
5. **Compatibility**: No breaking changes to FastMCP API

### Long-term Benefits

1. **Developer Productivity**: Easier to locate and modify specific tools
2. **Testing**: Isolated testing of tool categories
3. **Collaboration**: Multiple developers can work on different tool categories
4. **Extensibility**: Easy to add new tool categories
5. **Code Quality**: Reduced duplication and clearer separation of concerns

## Implementation Timeline

### Immediate (Phase 1)
- **Week 1**: Create mixin infrastructure and database tools mixin
- **Week 2**: Create metadata and CRUD tools mixins  
- **Week 3**: Create remaining tool mixins
- **Week 4**: Refactor main server class and testing

### Future (Phase 2)
- **Month 2**: Implement adapter pattern and eliminate duplication

### Optional (Phase 3)  
- **Month 3+**: Advanced modularization features

## Notes for AI Agent

1. **Preserve Functionality**: The #1 priority is maintaining exact functionality
2. **Test Frequently**: After each file creation, verify imports and basic functionality
3. **Use Multi-Replace**: When moving large blocks of code, use multi_replace_string_in_file for efficiency
4. **Follow Patterns**: Use the established patterns consistently across all mixins
5. **Document Changes**: Update any relevant documentation or comments
6. **Backup First**: Keep backups of original files before major changes

This specification provides the complete roadmap for refactoring the FastMCP server. The AI agent should execute Phase 1 systematically, following the exact order and patterns specified above.