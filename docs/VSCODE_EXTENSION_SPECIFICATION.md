# VS Code Extension Specification for d365fo-client

## Overview

This document provides a comprehensive specification for developing a Visual Studio Code extension based on the d365fo-client Python package. The extension will transform the existing command-line interface and Python client capabilities into an integrated development environment for Microsoft Dynamics 365 Finance & Operations (D365 F&O) development and integration.

## Table of Contents

1. [Extension Overview](#extension-overview)
2. [Core Features](#core-features)
3. [Architecture](#architecture)
4. [User Interface Design](#user-interface-design)
5. [Commands and Functions](#commands-and-functions)
6. [Configuration Management](#configuration-management)
7. [Integration with d365fo-client](#integration-with-d365fo-client)
8. [Technical Implementation](#technical-implementation)
9. [Development Plan](#development-plan)
10. [Testing Strategy](#testing-strategy)
11. [Deployment and Distribution](#deployment-and-distribution)

## Extension Overview

### Extension Identity
- **Name**: `d365fo-tools`
- **Display Name**: `Dynamics 365 Finance & Operations Tools`
- **Publisher**: `mafzaal`
- **Category**: `Other`
- **Keywords**: `dynamics365`, `d365`, `finance`, `operations`, `erp`, `microsoft`, `odata`
- **Description**: Comprehensive toolset for developing and integrating with Microsoft Dynamics 365 Finance & Operations

### Target Audience
- **D365 F&O Developers**: X++ developers working on customizations
- **Integration Developers**: Python/JavaScript developers building integrations
- **System Administrators**: Managing D365 F&O environments
- **Business Analysts**: Exploring data structures and capabilities
- **DevOps Engineers**: Automating deployment and testing processes

### Value Proposition
1. **Unified Development Experience**: Single VS Code extension for all D365 F&O development needs
2. **Enhanced Productivity**: IntelliSense, code completion, and automated workflows
3. **Real-time Environment Access**: Direct connectivity to D365 F&O environments
4. **Metadata Exploration**: Browse and search entity schemas, actions, and labels
5. **Data Management**: CRUD operations with visual interface
6. **Integration Acceleration**: Code generation and templates for common scenarios

## Core Features

### 1. Environment Management
- **Multi-Environment Support**: Manage connections to multiple D365 F&O environments
- **Environment Profiles**: Save and switch between development, test, and production environments
- **Connection Testing**: Validate connectivity and authentication
- **Environment Information**: Display version, build, and configuration details

### 2. Metadata Explorer
- **Entity Browser**: Hierarchical view of all data entities with search and filtering
- **Schema Viewer**: Detailed entity property information with data types and constraints
- **Action Explorer**: Browse and search OData actions with parameter details
- **Label Manager**: Search, view, and manage multilingual labels
- **Enumeration Viewer**: Browse system enumerations and their values

### 3. Data Operations
- **Data Browser**: View and filter entity data with pagination
- **Query Builder**: Visual OData query construction with IntelliSense
- **CRUD Operations**: Create, read, update, and delete records through UI
- **Batch Operations**: Import/export data in various formats (JSON, CSV, Excel)
- **Data Validation**: Real-time validation against entity schemas

### 4. Code Generation
- **Entity Models**: Generate Python/TypeScript/C# classes from entity metadata
- **API Clients**: Generate client code for specific entities and operations
- **Integration Templates**: Pre-built templates for common integration patterns
- **OData Query Generation**: Convert visual queries to OData syntax

### 5. Development Tools
- **IntelliSense**: Auto-completion for entity names, properties, and OData operators
- **Syntax Highlighting**: Custom syntax highlighting for OData queries
- **Error Detection**: Real-time validation of queries and operations
- **Debugging Support**: Step-through debugging for integration code

### 6. Workflow Automation
- **Deployment Scripts**: Generate scripts for entity deployment and configuration
- **Test Data Management**: Create and manage test datasets
- **Environment Synchronization**: Compare and sync metadata between environments
- **Backup and Restore**: Automated backup of entity data and configuration

## Architecture

### Extension Architecture

```
VS Code Extension (TypeScript/JavaScript)
├── Core Extension
│   ├── Extension Host (activation, lifecycle)
│   ├── Command Manager (VS Code commands)
│   ├── View Provider Manager (custom views)
│   └── Configuration Manager (settings, profiles)
├── User Interface
│   ├── Tree View Providers (Explorer, Metadata)
│   ├── Webview Providers (Data viewer, Query builder)
│   ├── Quick Pick Providers (Entity selection, Actions)
│   └── Input Box Providers (Filters, Parameters)
├── Backend Integration
│   ├── Python Bridge (subprocess communication)
│   ├── d365fo-client Wrapper (Python API calls)
│   ├── Cache Manager (Local data caching)
│   └── Error Handler (Error mapping and display)
├── Language Services
│   ├── IntelliSense Provider (Auto-completion)
│   ├── Hover Provider (Quick info)
│   ├── Definition Provider (Go to definition)
│   └── Validation Provider (Error checking)
└── Output Channels
    ├── D365FO Output (Operation logs)
    ├── Python Output (Backend communication)
    └── Debug Output (Development logging)
```

### Integration Layer

```
VS Code Extension (Frontend)
        ↕
   IPC Communication
        ↕
Python Backend Service
        ↕
   d365fo-client Library
        ↕
  D365 F&O Environment
```

### Data Flow

1. **User Interaction**: User performs action in VS Code UI
2. **Command Processing**: Extension processes command and validates input
3. **Backend Communication**: Extension calls Python backend via IPC
4. **D365FO Operation**: Python backend uses d365fo-client to perform operation
5. **Result Processing**: Results are processed and cached
6. **UI Update**: VS Code UI is updated with results

## User Interface Design

### 1. Activity Bar Integration

#### D365FO Explorer Icon
- **Location**: Activity Bar (left sidebar)
- **Icon**: Custom D365 F&O logo icon
- **Tooltip**: "Dynamics 365 Finance & Operations"

### 2. Explorer Panel

#### Environment Manager Section
```
🌐 Environments
├── 📁 Development
│   ├── ✅ Connection Status: Connected
│   ├── 📊 Version: 10.0.38
│   └── 🔧 Actions
│       ├── Test Connection
│       ├── Refresh Metadata
│       └── View Details
├── 📁 Test
│   ├── ❌ Connection Status: Disconnected
│   └── 🔧 Actions
└── ➕ Add Environment
```

#### Metadata Explorer Section
```
📋 Metadata
├── 📦 Entities (1,234)
│   ├── 🔍 Search Entities...
│   ├── 📊 Master Data
│   │   ├── 👥 Customers
│   │   ├── 🏪 Vendors
│   │   └── 📦 Products
│   ├── 📈 Transactions
│   │   ├── 🛒 Sales Orders
│   │   ├── 💰 Purchase Orders
│   │   └── 📋 Invoices
│   └── 📋 Reference Data
├── ⚡ Actions (567)
│   ├── 🔍 Search Actions...
│   ├── 🔄 Bound Actions
│   └── 🚀 Unbound Actions
├── 🏷️ Labels (12,345)
│   ├── 🔍 Search Labels...
│   └── 🌐 Languages
│       ├── 🇺🇸 English (en-US)
│       ├── 🇫🇷 French (fr-FR)
│       └── 🇩🇪 German (de-DE)
└── 📊 Enumerations (234)
    ├── 🔍 Search Enums...
    └── 📋 Categories
```

### 3. Editor Integration

#### Custom Editors
- **OData Query Editor**: Syntax highlighting and IntelliSense for OData queries
- **Entity Schema Viewer**: Read-only view of entity metadata with navigation
- **Data Grid Editor**: Editable grid for entity data with validation

#### Context Menus
- **Entity Context Menu**: Generate code, view data, export schema
- **Property Context Menu**: Copy name, view details, find usages
- **Action Context Menu**: Execute action, view parameters, generate code

### 4. Status Bar Integration

#### Connection Status
- **Connected**: `🔗 D365FO: Connected (Dev)`
- **Disconnected**: `❌ D365FO: Disconnected`
- **Error**: `⚠️ D365FO: Error`

#### Operation Status
- **Idle**: No additional status
- **Loading**: `⏳ Loading metadata...`
- **Syncing**: `🔄 Syncing with environment...`

### 5. Command Palette Integration

All extension commands will be available through VS Code's Command Palette (Ctrl+Shift+P):

```
D365FO: Connect to Environment
D365FO: Disconnect from Environment
D365FO: Refresh Metadata
D365FO: Search Entities
D365FO: Browse Entity Data
D365FO: Execute OData Query
D365FO: Generate Entity Model
D365FO: Export Schema
D365FO: Import Test Data
```

## Commands and Functions

### 1. Environment Commands

#### `d365fo.connectEnvironment`
- **Description**: Connect to a D365 F&O environment
- **Input**: Environment profile or connection details
- **Output**: Connection status and environment information
- **UI Integration**: Environment manager, status bar

#### `d365fo.disconnectEnvironment`
- **Description**: Disconnect from current environment
- **Output**: Disconnection confirmation
- **UI Integration**: Environment manager, status bar

#### `d365fo.testConnection`
- **Description**: Test connectivity to current environment
- **Output**: Connection test results
- **UI Integration**: Environment context menu

#### `d365fo.refreshMetadata`
- **Description**: Refresh cached metadata from environment
- **Output**: Refresh status and statistics
- **UI Integration**: Environment context menu, metadata explorer

### 2. Metadata Commands

#### `d365fo.searchEntities`
- **Description**: Search for entities by name or pattern
- **Input**: Search pattern and filters
- **Output**: List of matching entities
- **UI Integration**: Search box in metadata explorer

#### `d365fo.viewEntitySchema`
- **Description**: View detailed schema for an entity
- **Input**: Entity name
- **Output**: Entity schema in custom editor
- **UI Integration**: Entity context menu

#### `d365fo.searchActions`
- **Description**: Search for OData actions
- **Input**: Search pattern and filters
- **Output**: List of matching actions
- **UI Integration**: Actions section in metadata explorer

#### `d365fo.searchLabels`
- **Description**: Search for labels by text or ID
- **Input**: Search pattern and language
- **Output**: List of matching labels
- **UI Integration**: Labels section in metadata explorer

### 3. Data Operations Commands

#### `d365fo.browseEntityData`
- **Description**: Browse data for a specific entity
- **Input**: Entity name and optional query parameters
- **Output**: Data grid with pagination
- **UI Integration**: Entity context menu, data grid editor

#### `d365fo.executeQuery`
- **Description**: Execute a custom OData query
- **Input**: OData query string
- **Output**: Query results in data grid
- **UI Integration**: Query editor, command palette

#### `d365fo.createRecord`
- **Description**: Create a new entity record
- **Input**: Entity name and record data
- **Output**: Created record details
- **UI Integration**: Data grid toolbar

#### `d365fo.updateRecord`
- **Description**: Update an existing record
- **Input**: Entity name, record key, and update data
- **Output**: Updated record details
- **UI Integration**: Data grid row actions

#### `d365fo.deleteRecord`
- **Description**: Delete an entity record
- **Input**: Entity name and record key
- **Output**: Deletion confirmation
- **UI Integration**: Data grid row actions

### 4. Code Generation Commands

#### `d365fo.generateEntityModel`
- **Description**: Generate programming language model from entity
- **Input**: Entity name and target language
- **Output**: Generated code file
- **UI Integration**: Entity context menu

#### `d365fo.generateApiClient`
- **Description**: Generate API client code for entities
- **Input**: Entity selection and target language
- **Output**: Generated client code
- **UI Integration**: Multi-entity selection

#### `d365fo.generateIntegrationTemplate`
- **Description**: Generate integration template
- **Input**: Template type and configuration
- **Output**: Generated project structure
- **UI Integration**: Command palette

### 5. Utility Commands

#### `d365fo.exportSchema`
- **Description**: Export entity schema to file
- **Input**: Entity selection and format
- **Output**: Schema file (JSON/XML/CSV)
- **UI Integration**: Entity context menu

#### `d365fo.importTestData`
- **Description**: Import test data from file
- **Input**: Entity name and data file
- **Output**: Import results and errors
- **UI Integration**: Data grid toolbar

#### `d365fo.compareEnvironments`
- **Description**: Compare metadata between environments
- **Input**: Source and target environments
- **Output**: Comparison report
- **UI Integration**: Environment manager

## Configuration Management

### 1. Extension Settings

#### Global Settings
```json
{
  "d365fo.defaultLanguage": {
    "type": "string",
    "default": "en-US",
    "description": "Default language for labels and documentation"
  },
  "d365fo.cacheDirectory": {
    "type": "string",
    "default": "~/.d365fo-vscode",
    "description": "Directory for caching metadata and configuration"
  },
  "d365fo.pythonPath": {
    "type": "string",
    "default": "python",
    "description": "Path to Python executable with d365fo-client installed"
  },
  "d365fo.autoRefreshMetadata": {
    "type": "boolean",
    "default": true,
    "description": "Automatically refresh metadata on connection"
  },
  "d365fo.pageSize": {
    "type": "number",
    "default": 100,
    "description": "Default page size for data browsing"
  },
  "d365fo.timeout": {
    "type": "number",
    "default": 30,
    "description": "Request timeout in seconds"
  }
}
```

#### Environment Profiles
```json
{
  "d365fo.environments": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "baseUrl": { "type": "string" },
        "authMode": { "type": "string", "enum": ["default", "explicit"] },
        "clientId": { "type": "string" },
        "clientSecret": { "type": "string" },
        "tenantId": { "type": "string" },
        "verifySsl": { "type": "boolean", "default": true }
      }
    },
    "default": [],
    "description": "D365 F&O environment configurations"
  }
}
```

### 2. Configuration UI

#### Environment Manager
- **Add Environment Dialog**: Form-based environment configuration
- **Edit Environment Dialog**: Modify existing environment settings
- **Connection Test**: Validate environment connectivity
- **Import/Export**: Share environment configurations

#### Settings Panel
- **General Settings**: Global extension preferences
- **Authentication**: Azure AD configuration and credentials
- **Performance**: Caching and timeout settings
- **UI Preferences**: Display options and themes

### 3. Workspace Configuration

#### .vscode/settings.json
```json
{
  "d365fo.defaultEnvironment": "development",
  "d365fo.projectEntities": ["Customers", "SalesOrders", "Products"],
  "d365fo.codeGeneration": {
    "language": "python",
    "outputDirectory": "./generated",
    "namespace": "MyProject.D365FO"
  }
}
```

#### .d365fo/config.json
```json
{
  "projectName": "MyIntegrationProject",
  "environments": {
    "dev": {
      "name": "Development",
      "baseUrl": "https://dev.dynamics.com",
      "profile": "development"
    }
  },
  "metadata": {
    "lastSync": "2025-08-17T10:30:00Z",
    "entities": 1234,
    "actions": 567
  }
}
```

## Integration with d365fo-client

### 1. Python Backend Service

#### Service Architecture
```python
# backend/d365fo_service.py
import asyncio
import json
import sys
from typing import Dict, Any, Optional
from d365fo_client import FOClient, FOClientConfig, create_client

class D365FOService:
    """Backend service for VS Code extension integration."""
    
    def __init__(self):
        self.clients: Dict[str, FOClient] = {}
        self.configs: Dict[str, FOClientConfig] = {}
    
    async def connect_environment(self, profile_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a D365 F&O environment."""
        try:
            client_config = FOClientConfig(**config)
            client = await create_client(client_config.base_url)
            
            # Test connection
            connection_result = await client.test_connection()
            if not connection_result:
                raise ConnectionError("Failed to connect to environment")
            
            # Store client and config
            self.clients[profile_name] = client
            self.configs[profile_name] = client_config
            
            # Get environment info
            version_info = await client.get_application_version()
            
            return {
                "success": True,
                "version": version_info,
                "message": f"Connected to {profile_name}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to connect to {profile_name}"
            }
    
    async def search_entities(self, profile_name: str, pattern: str) -> Dict[str, Any]:
        """Search for entities in the specified environment."""
        try:
            client = self.clients.get(profile_name)
            if not client:
                raise ValueError(f"Not connected to {profile_name}")
            
            entities = client.search_entities(pattern)
            
            return {
                "success": True,
                "entities": [entity.__dict__ for entity in entities],
                "count": len(entities)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_entity_data(self, profile_name: str, entity_name: str, 
                            query_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get data for a specific entity."""
        try:
            client = self.clients.get(profile_name)
            if not client:
                raise ValueError(f"Not connected to {profile_name}")
            
            from d365fo_client import QueryOptions
            options = QueryOptions(**(query_options or {}))
            
            result = await client.get_entities(entity_name, options)
            
            return {
                "success": True,
                "data": result.get("value", []),
                "count": result.get("@odata.count"),
                "next_link": result.get("@odata.nextLink")
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Main service loop
async def main():
    """Main service loop for handling VS Code extension requests."""
    service = D365FOService()
    
    while True:
        try:
            # Read request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            command = request.get("command")
            
            # Route command to appropriate handler
            if command == "connect":
                result = await service.connect_environment(
                    request["profile"], request["config"]
                )
            elif command == "search_entities":
                result = await service.search_entities(
                    request["profile"], request["pattern"]
                )
            elif command == "get_entity_data":
                result = await service.get_entity_data(
                    request["profile"], request["entity"], request.get("options")
                )
            else:
                result = {"success": False, "error": f"Unknown command: {command}"}
            
            # Send response to stdout
            response = {
                "id": request.get("id"),
                "result": result
            }
            print(json.dumps(response))
            sys.stdout.flush()
        
        except Exception as e:
            error_response = {
                "id": request.get("id") if 'request' in locals() else None,
                "error": str(e)
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Extension-Backend Communication

#### IPC Protocol
```typescript
// src/backend/pythonBridge.ts
import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

interface BackendRequest {
    id: string;
    command: string;
    [key: string]: any;
}

interface BackendResponse {
    id: string;
    result?: any;
    error?: string;
}

export class PythonBridge extends EventEmitter {
    private process: ChildProcess | null = null;
    private requestId = 0;
    private pendingRequests = new Map<string, {
        resolve: (value: any) => void;
        reject: (reason: any) => void;
        timeout: NodeJS.Timeout;
    }>();

    constructor(private pythonPath: string, private servicePath: string) {
        super();
    }

    async start(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.process = spawn(this.pythonPath, [this.servicePath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: process.cwd()
            });

            this.process.stdout?.on('data', (data) => {
                const lines = data.toString().split('\n').filter((line: string) => line.trim());
                
                for (const line of lines) {
                    try {
                        const response: BackendResponse = JSON.parse(line);
                        this.handleResponse(response);
                    } catch (error) {
                        console.error('Failed to parse backend response:', error);
                    }
                }
            });

            this.process.stderr?.on('data', (data) => {
                console.error('Backend error:', data.toString());
            });

            this.process.on('exit', (code) => {
                console.log(`Backend process exited with code ${code}`);
                this.process = null;
                this.emit('exit', code);
            });

            // Wait for process to start
            setTimeout(() => resolve(), 1000);
        });
    }

    async sendRequest(command: string, params: any = {}): Promise<any> {
        if (!this.process) {
            throw new Error('Backend process not started');
        }

        const id = (++this.requestId).toString();
        const request: BackendRequest = { id, command, ...params };

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(id);
                reject(new Error('Request timeout'));
            }, 30000);

            this.pendingRequests.set(id, { resolve, reject, timeout });

            const requestJson = JSON.stringify(request) + '\n';
            this.process!.stdin?.write(requestJson);
        });
    }

    private handleResponse(response: BackendResponse): void {
        const pending = this.pendingRequests.get(response.id);
        if (!pending) {
            return;
        }

        this.pendingRequests.delete(response.id);
        clearTimeout(pending.timeout);

        if (response.error) {
            pending.reject(new Error(response.error));
        } else {
            pending.resolve(response.result);
        }
    }

    stop(): void {
        if (this.process) {
            this.process.kill();
            this.process = null;
        }
        
        // Reject all pending requests
        for (const [id, pending] of this.pendingRequests) {
            clearTimeout(pending.timeout);
            pending.reject(new Error('Backend process stopped'));
        }
        this.pendingRequests.clear();
    }
}
```

#### Service Manager
```typescript
// src/services/d365foService.ts
import { PythonBridge } from '../backend/pythonBridge';
import { ExtensionContext, workspace } from 'vscode';

export interface EnvironmentConfig {
    name: string;
    baseUrl: string;
    authMode: 'default' | 'explicit';
    clientId?: string;
    clientSecret?: string;
    tenantId?: string;
    verifySsl: boolean;
}

export interface EntityInfo {
    name: string;
    entitySetName: string;
    keys: string[];
    isReadOnly: boolean;
    labelText?: string;
}

export class D365FOService {
    private bridge: PythonBridge;
    private currentEnvironment: string | null = null;

    constructor(private context: ExtensionContext) {
        const pythonPath = workspace.getConfiguration('d365fo').get<string>('pythonPath', 'python');
        const servicePath = this.context.asAbsolutePath('backend/d365fo_service.py');
        
        this.bridge = new PythonBridge(pythonPath, servicePath);
    }

    async initialize(): Promise<void> {
        await this.bridge.start();
    }

    async connectEnvironment(profile: string, config: EnvironmentConfig): Promise<boolean> {
        try {
            const result = await this.bridge.sendRequest('connect', {
                profile: profile,
                config: {
                    base_url: config.baseUrl,
                    use_default_credentials: config.authMode === 'default',
                    client_id: config.clientId,
                    client_secret: config.clientSecret,
                    tenant_id: config.tenantId,
                    verify_ssl: config.verifySsl
                }
            });

            if (result.success) {
                this.currentEnvironment = profile;
                return true;
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Connection failed:', error);
            return false;
        }
    }

    async searchEntities(pattern: string): Promise<EntityInfo[]> {
        if (!this.currentEnvironment) {
            throw new Error('No environment connected');
        }

        const result = await this.bridge.sendRequest('search_entities', {
            profile: this.currentEnvironment,
            pattern: pattern
        });

        if (result.success) {
            return result.entities;
        } else {
            throw new Error(result.error);
        }
    }

    async getEntityData(entityName: string, options?: any): Promise<any> {
        if (!this.currentEnvironment) {
            throw new Error('No environment connected');
        }

        const result = await this.bridge.sendRequest('get_entity_data', {
            profile: this.currentEnvironment,
            entity: entityName,
            options: options
        });

        if (result.success) {
            return {
                data: result.data,
                count: result.count,
                nextLink: result.next_link
            };
        } else {
            throw new Error(result.error);
        }
    }

    dispose(): void {
        this.bridge.stop();
    }
}
```

## Technical Implementation

### 1. Extension Structure

```
d365fo-tools/
├── package.json                    # Extension manifest
├── tsconfig.json                   # TypeScript configuration
├── webpack.config.js              # Bundle configuration
├── .vscodeignore                  # Files to exclude from package
├── src/
│   ├── extension.ts               # Main extension entry point
│   ├── commands/                  # Command implementations
│   │   ├── environmentCommands.ts
│   │   ├── metadataCommands.ts
│   │   ├── dataCommands.ts
│   │   └── codeGenCommands.ts
│   ├── providers/                 # VS Code providers
│   │   ├── environmentTreeProvider.ts
│   │   ├── metadataTreeProvider.ts
│   │   ├── dataWebviewProvider.ts
│   │   └── intellisenseProvider.ts
│   ├── services/                  # Business logic services
│   │   ├── d365foService.ts
│   │   ├── configService.ts
│   │   └── cacheService.ts
│   ├── backend/                   # Python integration
│   │   ├── pythonBridge.ts
│   │   └── serviceManager.ts
│   ├── ui/                        # UI components
│   │   ├── webviews/
│   │   ├── dialogs/
│   │   └── panels/
│   └── utils/                     # Utility functions
│       ├── logger.ts
│       ├── validators.ts
│       └── formatters.ts
├── backend/                       # Python backend service
│   ├── d365fo_service.py          # Main service script
│   ├── requirements.txt           # Python dependencies
│   └── install.py                 # Setup script
├── resources/                     # Static resources
│   ├── icons/                     # Extension icons
│   ├── themes/                    # Custom themes
│   └── templates/                 # Code generation templates
├── media/                         # Webview resources
│   ├── css/
│   ├── js/
│   └── images/
└── test/                          # Tests
    ├── suite/
    └── fixtures/
```

### 2. Package.json Configuration

```json
{
  "name": "d365fo-tools",
  "displayName": "Dynamics 365 Finance & Operations Tools",
  "description": "Comprehensive toolset for D365 F&O development and integration",
  "version": "1.0.0",
  "publisher": "mafzaal",
  "engines": {
    "vscode": "^1.85.0"
  },
  "categories": ["Other"],
  "keywords": ["dynamics365", "d365", "finance", "operations", "erp", "microsoft", "odata"],
  "activationEvents": [
    "onCommand:d365fo.connectEnvironment",
    "onView:d365foExplorer"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "viewsContainers": {
      "activitybar": [
        {
          "id": "d365foExplorer",
          "title": "D365 F&O",
          "icon": "$(cloud)"
        }
      ]
    },
    "views": {
      "d365foExplorer": [
        {
          "id": "d365foEnvironments",
          "name": "Environments",
          "when": "true"
        },
        {
          "id": "d365foMetadata",
          "name": "Metadata",
          "when": "d365fo.connected"
        }
      ]
    },
    "commands": [
      {
        "command": "d365fo.connectEnvironment",
        "title": "Connect to Environment",
        "category": "D365FO"
      },
      {
        "command": "d365fo.refreshMetadata",
        "title": "Refresh Metadata",
        "category": "D365FO"
      },
      {
        "command": "d365fo.searchEntities",
        "title": "Search Entities",
        "category": "D365FO"
      }
    ],
    "configuration": {
      "title": "D365 F&O Tools",
      "properties": {
        "d365fo.pythonPath": {
          "type": "string",
          "default": "python",
          "description": "Path to Python executable"
        },
        "d365fo.environments": {
          "type": "array",
          "description": "Environment configurations"
        }
      }
    },
    "languages": [
      {
        "id": "odata-query",
        "aliases": ["OData Query"],
        "extensions": [".odata"],
        "configuration": "./language-configuration.json"
      }
    ],
    "grammars": [
      {
        "language": "odata-query",
        "scopeName": "source.odata",
        "path": "./syntaxes/odata.tmGrammar.json"
      }
    ]
  },
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./"
  },
  "devDependencies": {
    "@types/vscode": "^1.85.0",
    "@types/node": "^18.x",
    "typescript": "^5.0.0"
  },
  "dependencies": {
    "axios": "^1.0.0",
    "uuid": "^9.0.0"
  }
}
```

### 3. Main Extension Entry Point

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { D365FOService } from './services/d365foService';
import { EnvironmentTreeProvider } from './providers/environmentTreeProvider';
import { MetadataTreeProvider } from './providers/metadataTreeProvider';
import { registerCommands } from './commands';

let d365foService: D365FOService;

export async function activate(context: vscode.ExtensionContext) {
    console.log('D365 F&O Tools extension is now active');

    // Initialize services
    d365foService = new D365FOService(context);
    await d365foService.initialize();

    // Register tree data providers
    const environmentProvider = new EnvironmentTreeProvider(context, d365foService);
    const metadataProvider = new MetadataTreeProvider(context, d365foService);

    vscode.window.registerTreeDataProvider('d365foEnvironments', environmentProvider);
    vscode.window.registerTreeDataProvider('d365foMetadata', metadataProvider);

    // Register commands
    registerCommands(context, d365foService, environmentProvider, metadataProvider);

    // Set context for when conditions
    vscode.commands.executeCommand('setContext', 'd365fo.activated', true);

    // Register for disposal
    context.subscriptions.push(d365foService);
}

export function deactivate() {
    if (d365foService) {
        d365foService.dispose();
    }
}
```

## Development Plan

### Phase 1: Foundation and Core Infrastructure (Weeks 1-4)

#### Week 1-2: Project Setup and Basic Structure
- **Project Initialization**
  - Create VS Code extension project structure
  - Configure TypeScript, webpack, and build system
  - Set up development environment and tooling
  - Create basic package.json with essential contributions

- **Python Backend Integration**
  - Implement Python bridge for IPC communication
  - Create basic d365fo-client wrapper service
  - Establish request/response protocol
  - Test basic connectivity between extension and Python backend

#### Week 3-4: Environment Management
- **Environment Configuration**
  - Implement environment configuration storage
  - Create environment profile management
  - Build basic connection testing functionality
  - Implement authentication handling

- **UI Foundation**
  - Create activity bar icon and explorer views
  - Implement basic tree view for environments
  - Add status bar integration
  - Create basic command registration

### Phase 2: Metadata Explorer and Basic Operations (Weeks 5-8)

#### Week 5-6: Metadata Infrastructure
- **Metadata Tree Provider**
  - Implement entity browsing tree view
  - Add search functionality for entities
  - Create action and label browsing
  - Implement metadata caching

- **Schema Viewer**
  - Create entity schema display
  - Implement property details view
  - Add navigation between related entities
  - Create read-only schema editor

#### Week 7-8: Basic Data Operations
- **Data Browsing**
  - Implement basic data grid view
  - Add pagination support
  - Create filtering capabilities
  - Implement sort functionality

- **Query Builder Foundation**
  - Basic OData query construction
  - Simple filter building
  - Field selection interface
  - Query validation

### Phase 3: Advanced Features and IntelliSense (Weeks 9-12)

#### Week 9-10: Language Services
- **IntelliSense Implementation**
  - Auto-completion for entity names
  - Property name suggestions
  - OData operator completion
  - Function parameter hints

- **Syntax Highlighting**
  - Custom OData query language support
  - Error highlighting and validation
  - Hover information for entities and properties
  - Go-to-definition for entity references

#### Week 11-12: Code Generation
- **Model Generation**
  - Python class generation from entities
  - TypeScript interface generation
  - C# model generation
  - Template system implementation

- **Integration Templates**
  - Common integration pattern templates
  - Project scaffolding
  - Configuration file generation
  - Example code creation

### Phase 4: Advanced Data Operations and UI Polish (Weeks 13-16)

#### Week 13-14: Enhanced Data Operations
- **CRUD Operations**
  - Create, update, delete functionality
  - Batch operations support
  - Data validation
  - Error handling and user feedback

- **Import/Export**
  - CSV/Excel import functionality
  - JSON data export
  - Schema export capabilities
  - Bulk data operations

#### Week 15-16: UI Enhancement and Polish
- **Webview Components**
  - Advanced data grid with editing
  - Visual query builder
  - Dashboard-style overview
  - Settings and configuration panels

- **User Experience**
  - Progress indicators for long operations
  - Better error messages and handling
  - Keyboard shortcuts and accessibility
  - Help documentation integration

### Phase 5: Testing, Documentation, and Release (Weeks 17-20)

#### Week 17-18: Comprehensive Testing
- **Unit Testing**
  - TypeScript code unit tests
  - Python backend service tests
  - Mock service implementations
  - Integration test suite

- **Manual Testing**
  - End-to-end workflow testing
  - Performance testing with large datasets
  - Multi-environment testing
  - Error scenario testing

#### Week 19-20: Documentation and Release Preparation
- **Documentation**
  - User guide and tutorials
  - Developer documentation
  - Video demonstrations
  - API reference documentation

- **Release Preparation**
  - Extension packaging and testing
  - Marketplace listing preparation
  - Performance optimization
  - Security review and validation

## Testing Strategy

### 1. Unit Testing

#### TypeScript Tests
```typescript
// test/suite/services/d365foService.test.ts
import * as assert from 'assert';
import { D365FOService } from '../../../src/services/d365foService';

suite('D365FOService Tests', () => {
    let service: D365FOService;

    setup(() => {
        // Mock ExtensionContext
        const mockContext = {
            asAbsolutePath: (path: string) => `/mock/path/${path}`,
            subscriptions: []
        } as any;
        
        service = new D365FOService(mockContext);
    });

    test('should connect to environment', async () => {
        const config = {
            name: 'test',
            baseUrl: 'https://test.dynamics.com',
            authMode: 'default' as const,
            verifySsl: true
        };

        // Mock the bridge connection
        const result = await service.connectEnvironment('test', config);
        assert.strictEqual(result, true);
    });

    test('should search entities', async () => {
        // Setup connection first
        await service.connectEnvironment('test', {
            name: 'test',
            baseUrl: 'https://test.dynamics.com',
            authMode: 'default',
            verifySsl: true
        });

        const entities = await service.searchEntities('customer');
        assert.ok(Array.isArray(entities));
    });
});
```

#### Python Backend Tests
```python
# backend/test_service.py
import pytest
import asyncio
import json
from unittest.mock import Mock, patch
from d365fo_service import D365FOService

@pytest.fixture
def service():
    return D365FOService()

@pytest.mark.asyncio
async def test_connect_environment(service):
    """Test environment connection."""
    config = {
        "base_url": "https://test.dynamics.com",
        "use_default_credentials": True
    }
    
    with patch('d365fo_client.create_client') as mock_create:
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client.get_application_version.return_value = "10.0.38"
        mock_create.return_value = mock_client
        
        result = await service.connect_environment("test", config)
        
        assert result["success"] is True
        assert "version" in result

@pytest.mark.asyncio
async def test_search_entities(service):
    """Test entity search functionality."""
    # Setup mock client
    mock_client = Mock()
    mock_entities = [Mock(name="Customers"), Mock(name="CustomerGroups")]
    mock_client.search_entities.return_value = mock_entities
    service.clients["test"] = mock_client
    
    result = await service.search_entities("test", "customer")
    
    assert result["success"] is True
    assert result["count"] == 2
```

### 2. Integration Testing

#### Extension Integration Tests
```typescript
// test/suite/integration/extension.test.ts
import * as vscode from 'vscode';
import * as assert from 'assert';

suite('Extension Integration Tests', () => {
    test('should activate extension', async () => {
        const extension = vscode.extensions.getExtension('mafzaal.d365fo-tools');
        assert.ok(extension);
        
        await extension!.activate();
        assert.ok(extension!.isActive);
    });

    test('should register commands', async () => {
        const commands = await vscode.commands.getCommands();
        
        const d365foCommands = commands.filter(cmd => cmd.startsWith('d365fo.'));
        assert.ok(d365foCommands.length > 0);
        
        assert.ok(d365foCommands.includes('d365fo.connectEnvironment'));
        assert.ok(d365foCommands.includes('d365fo.searchEntities'));
    });

    test('should show tree views', async () => {
        // Test that tree views are properly registered
        const treeView = vscode.window.createTreeView('d365foEnvironments', {
            treeDataProvider: {} as any
        });
        
        assert.ok(treeView);
        treeView.dispose();
    });
});
```

### 3. End-to-End Testing

#### Workflow Tests
```typescript
// test/suite/e2e/workflows.test.ts
import * as vscode from 'vscode';
import * as assert from 'assert';

suite('End-to-End Workflow Tests', () => {
    test('complete entity browsing workflow', async () => {
        // 1. Connect to environment
        await vscode.commands.executeCommand('d365fo.connectEnvironment');
        
        // 2. Search for entities
        const entities = await vscode.commands.executeCommand('d365fo.searchEntities', 'customer');
        assert.ok(Array.isArray(entities));
        
        // 3. View entity schema
        if (entities.length > 0) {
            const schema = await vscode.commands.executeCommand('d365fo.viewEntitySchema', entities[0].name);
            assert.ok(schema);
        }
        
        // 4. Browse entity data
        if (entities.length > 0) {
            const data = await vscode.commands.executeCommand('d365fo.browseEntityData', entities[0].name);
            assert.ok(data);
        }
    });

    test('code generation workflow', async () => {
        // 1. Select entity
        const entityName = 'Customers';
        
        // 2. Generate Python model
        const pythonModel = await vscode.commands.executeCommand(
            'd365fo.generateEntityModel', 
            entityName, 
            'python'
        );
        assert.ok(pythonModel);
        
        // 3. Generate TypeScript interface
        const tsInterface = await vscode.commands.executeCommand(
            'd365fo.generateEntityModel', 
            entityName, 
            'typescript'
        );
        assert.ok(tsInterface);
    });
});
```

### 4. Performance Testing

#### Load Testing
```typescript
// test/suite/performance/load.test.ts
import * as assert from 'assert';
import { D365FOService } from '../../../src/services/d365foService';

suite('Performance Tests', () => {
    test('should handle large entity searches', async function() {
        this.timeout(10000); // 10 second timeout
        
        const service = new D365FOService({} as any);
        
        // Test with pattern that returns many results
        const start = Date.now();
        const entities = await service.searchEntities('');
        const duration = Date.now() - start;
        
        // Should complete within reasonable time
        assert.ok(duration < 5000, `Search took too long: ${duration}ms`);
        
        // Should return results
        assert.ok(entities.length > 0);
    });

    test('should handle concurrent requests', async () => {
        const service = new D365FOService({} as any);
        
        // Make multiple concurrent requests
        const requests = Array(10).fill(null).map(() => 
            service.searchEntities('customer')
        );
        
        const start = Date.now();
        const results = await Promise.all(requests);
        const duration = Date.now() - start;
        
        // All requests should succeed
        results.forEach(result => {
            assert.ok(Array.isArray(result));
        });
        
        // Should complete in reasonable time
        assert.ok(duration < 10000);
    });
});
```

## Deployment and Distribution

### 1. Extension Packaging

#### Build Configuration
```javascript
// webpack.config.js
const path = require('path');

module.exports = {
    target: 'node',
    entry: './src/extension.ts',
    output: {
        path: path.resolve(__dirname, 'out'),
        filename: 'extension.js',
        libraryTarget: 'commonjs2',
        devtoolModuleFilenameTemplate: '../[resource-path]'
    },
    devtool: 'source-map',
    externals: {
        vscode: 'commonjs vscode'
    },
    resolve: {
        extensions: ['.ts', '.js']
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                exclude: /node_modules/,
                use: [
                    {
                        loader: 'ts-loader'
                    }
                ]
            }
        ]
    }
};
```

#### Package Scripts
```json
{
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "webpack --mode production",
    "compile:dev": "webpack --mode development",
    "watch": "webpack --mode development --watch",
    "test": "npm run compile && node ./out/test/runTest.js",
    "package": "vsce package",
    "publish": "vsce publish"
  }
}
```

### 2. Python Dependencies

#### Bundled Python Service
```python
# backend/install.py
"""Installation script for d365fo-client dependencies."""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required Python dependencies."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", str(requirements_path)
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def verify_installation():
    """Verify that d365fo-client is properly installed."""
    try:
        import d365fo_client
        print(f"d365fo-client version: {d365fo_client.__version__}")
        return True
    except ImportError:
        print("d365fo-client not found")
        return False

if __name__ == "__main__":
    print("Installing D365 F&O Tools dependencies...")
    
    if install_dependencies():
        if verify_installation():
            print("Installation completed successfully!")
            sys.exit(0)
        else:
            print("Installation verification failed!")
            sys.exit(1)
    else:
        print("Installation failed!")
        sys.exit(1)
```

#### Requirements Management
```text
# backend/requirements.txt
d365fo-client>=0.1.0
aiohttp>=3.10.0
aiofiles>=24.1.0
azure-identity>=1.19.0
```

### 3. VS Code Marketplace

#### Extension Manifest
```json
{
  "name": "d365fo-tools",
  "displayName": "Dynamics 365 Finance & Operations Tools",
  "description": "Comprehensive toolset for D365 F&O development and integration",
  "version": "1.0.0",
  "publisher": "mafzaal",
  "author": {
    "name": "Muhammad Afzaal",
    "email": "mo@thedataguy.pro"
  },
  "license": "MIT",
  "homepage": "https://github.com/mafzaal/d365fo-vscode-extension",
  "repository": {
    "type": "git",
    "url": "https://github.com/mafzaal/d365fo-vscode-extension.git"
  },
  "bugs": {
    "url": "https://github.com/mafzaal/d365fo-vscode-extension/issues"
  },
  "icon": "resources/icons/d365fo.png",
  "galleryBanner": {
    "color": "#1e1e1e",
    "theme": "dark"
  },
  "categories": ["Other"],
  "keywords": [
    "dynamics365",
    "d365",
    "finance",
    "operations",
    "erp",
    "microsoft",
    "odata",
    "integration",
    "development"
  ],
  "engines": {
    "vscode": "^1.85.0"
  }
}
```

#### Publishing Process
1. **Preparation**
   - Complete testing and quality assurance
   - Update version numbers and changelog
   - Prepare documentation and screenshots
   - Review security and privacy considerations

2. **Packaging**
   - Build production version with webpack
   - Include Python backend and dependencies
   - Generate .vsix package file
   - Test package installation locally

3. **Publishing**
   - Create Azure DevOps organization and publisher
   - Upload to VS Code Marketplace
   - Configure automatic updates and versioning
   - Monitor download statistics and user feedback

### 4. Distribution Strategy

#### Multiple Channels
1. **VS Code Marketplace** (Primary)
   - Official VS Code extension marketplace
   - Automatic updates and installation
   - User reviews and ratings
   - Download analytics

2. **GitHub Releases** (Secondary)
   - Direct .vsix file downloads
   - Release notes and documentation
   - Issue tracking and support
   - Source code access

3. **Enterprise Distribution** (Future)
   - Private extension galleries
   - Custom deployment packages
   - Enterprise-specific configurations
   - Support and training materials

#### Version Management
- **Semantic Versioning**: Major.Minor.Patch format
- **Release Channels**: Stable, pre-release, and insider builds
- **Automatic Updates**: Enabled by default with user control
- **Compatibility**: Support for VS Code versions and Python environments

This comprehensive specification provides a solid foundation for developing a powerful VS Code extension that leverages the full capabilities of the d365fo-client library, offering D365 F&O developers and integrators a seamless and productive development experience within Visual Studio Code.