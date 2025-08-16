# Quick Start Guide - Windows PowerShell

## Prerequisites
- Python 3.8+ installed
- PowerShell 5.1+ (comes with Windows)
- Git (optional, for version control)

## Getting Started (5 minutes)

### 1. Setup Environment
```powershell
# Navigate to your project directory
cd c:\path\to\your\d365fo-client

# Run the setup script
.\tests\integration\integration-test.ps1 setup
```

### 2. Run Your First Integration Test
```powershell
# Test the mock server (no external dependencies)
.\tests\integration\integration-test.ps1 test-mock
```

### 3. Check Everything Works
```powershell
# Verify dependencies
.\tests\integration\integration-test.ps1 deps-check

# Run with verbose output
.\tests\integration\integration-test.ps1 test-mock -Verbose
```

## Common Windows-Specific Commands

### Environment Variables (PowerShell)
```powershell
# Set environment variables for the session
$env:INTEGRATION_TEST_LEVEL = "mock"
$env:D365FO_SANDBOX_BASE_URL = "https://your-sandbox.dynamics.com"
$env:AZURE_CLIENT_ID = "your-client-id"
$env:AZURE_CLIENT_SECRET = "your-secret"
$env:AZURE_TENANT_ID = "your-tenant-id"
```

### Persistent Environment Variables
```powershell
# Set permanently (requires admin or affects user profile)
[Environment]::SetEnvironmentVariable("INTEGRATION_TEST_LEVEL", "mock", "User")
```

### Using .env File (Recommended)
```powershell
# Copy the example file
Copy-Item tests\integration\.env.example tests\integration\.env

# Edit with notepad
notepad tests\integration\.env
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `setup` | Initialize testing environment | `.\integration-test.ps1 setup` |
| `test-mock` | Run mock server tests | `.\integration-test.ps1 test-mock` |
| `test-sandbox` | Run sandbox tests | `.\integration-test.ps1 test-sandbox` |
| `test-live` | Run production tests | `.\integration-test.ps1 test-live` |
| `coverage` | Run with coverage report | `.\integration-test.ps1 coverage` |
| `clean` | Clean test artifacts | `.\integration-test.ps1 clean` |

## Advanced Usage

### Run Specific Test File
```powershell
.\integration-test.ps1 test-mock -TestFile "test_mock_server.py"
```

### Run with Test Markers
```powershell
.\integration-test.ps1 test-mock -Markers "crud"
```

### Debug Mode
```powershell
.\integration-test.ps1 test-mock -Verbose
```

### Show Environment Info
```powershell
# Import the script as a module first
Import-Module .\tests\integration\integration-test.ps1 -Force
Show-Environment
```

### Start Mock Server Standalone
```powershell
Start-MockServer
```

## Integration with VS Code

### Tasks.json Integration
Add to your `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Integration Tests - Mock",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-File",
                "tests/integration/integration-test.ps1",
                "test-mock"
            ],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Integration Tests - Coverage",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-File",
                "tests/integration/integration-test.ps1",
                "coverage"
            ],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

### Launch.json for Debugging
Add to your `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Integration Tests",
            "type": "python",
            "request": "launch",
            "program": "tests/integration/test_runner.py",
            "args": ["mock", "--verbose"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "INTEGRATION_TEST_LEVEL": "mock"
            }
        }
    ]
}
```

## Troubleshooting

### PowerShell Execution Policy
If you get execution policy errors:
```powershell
# Check current policy
Get-ExecutionPolicy

# Allow local scripts (run as administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine

# Or for current user only
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found
```powershell
# Check if Python is in PATH
python --version

# If not found, add to PATH or use full path
C:\Python39\python.exe --version
```

### Dependencies Installation
```powershell
# Install pip dependencies
pip install -e ".[integration]"

# Or using uv (faster)
uv pip install -e ".[integration]"
```

### Common Error Solutions

**"Module not found" errors:**
```powershell
# Ensure you're in the project root
cd c:\path\to\d365fo-client

# Install in development mode
pip install -e .
```

**"Permission denied" errors:**
```powershell
# Run PowerShell as administrator
# Or use user-level installations
pip install --user -e ".[integration]"
```

**"Port already in use" errors:**
```powershell
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

## CI/CD Integration

### GitHub Actions (Windows runner)
```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e ".[integration]"
    
    - name: Run integration tests
      run: |
        .\tests\integration\integration-test.ps1 test-mock -Verbose
    
    - name: Upload coverage
      run: |
        .\tests\integration\integration-test.ps1 coverage
```

### Azure DevOps
```yaml
trigger:
- main

pool:
  vmImage: 'windows-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'
    
- script: |
    pip install -e ".[integration]"
  displayName: 'Install dependencies'
  
- powershell: |
    .\tests\integration\integration-test.ps1 test-mock -Verbose
  displayName: 'Run integration tests'
```

## Performance Tips

1. **Use SSD storage** for faster test execution
2. **Close unnecessary applications** during testing
3. **Use mock tests for development** (faster feedback)
4. **Run sandbox/live tests periodically** (realistic validation)
5. **Use coverage selectively** (adds overhead)

## Next Steps

1. ✅ **Start with mock tests** - No external dependencies
2. 🔧 **Configure sandbox environment** - Realistic testing
3. 🚀 **Set up CI/CD pipeline** - Automated testing
4. 📊 **Monitor coverage** - Ensure comprehensive testing
5. 🔍 **Add custom tests** - Test your specific use cases

Happy testing! 🎉