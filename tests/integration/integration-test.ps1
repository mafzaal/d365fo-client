# Integration Testing PowerShell Script for Windows
# D365 F&O Client Integration Tests

param(
    [Parameter(Position=0)]
    [ValidateSet("help", "setup", "deps-check", "test-mock", "test-sandbox", "test-live", "test-all", "coverage", "clean")]
    [string]$Command = "help",
    
    [string]$TestFile = "",
    [string]$Markers = "",
    [switch]$Verbose
)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Host "🔧 $Text" -ForegroundColor Green
    Write-Host ("=" * 60) -ForegroundColor Green
}

function Write-Step {
    param([string]$Text)
    Write-Host "🧪 $Text" -ForegroundColor Cyan
}

function Show-Help {
    Write-Header "D365 F`&O Client Integration Testing"
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  setup        - Setup integration testing environment" -ForegroundColor White
    Write-Host "  deps-check   - Check if dependencies are installed" -ForegroundColor White
    Write-Host "  test-mock    - Run mock server tests" -ForegroundColor White
    Write-Host "  test-sandbox - Run sandbox environment tests" -ForegroundColor White
    Write-Host "  test-live    - Run live environment tests" -ForegroundColor White
    Write-Host "  test-all     - Run all integration tests" -ForegroundColor White
    Write-Host "  coverage     - Run tests with coverage report" -ForegroundColor White
    Write-Host "  clean        - Clean up test artifacts" -ForegroundColor White
    Write-Host "  help         - Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\integration-test.ps1 setup" -ForegroundColor Gray
    Write-Host "  .\integration-test.ps1 test-mock" -ForegroundColor Gray
    Write-Host "  .\integration-test.ps1 test-mock -TestFile test_mock_server.py" -ForegroundColor Gray
    Write-Host "  .\integration-test.ps1 test-mock -Verbose" -ForegroundColor Gray
    Write-Host "  .\integration-test.ps1 coverage" -ForegroundColor Gray
}

function Invoke-Setup {
    Write-Step "Setting up integration testing environment..."
    uv run python tests\integration\setup.py
}

function Invoke-DepsCheck {
    Write-Step "Checking dependencies..."
    uv run python tests\integration\test_runner.py mock --check-deps
}

function Invoke-TestMock {
    Write-Step "Running mock server tests..."
    $args = @("tests\integration\test_runner.py", "mock")
    
    if ($TestFile) {
        $args += "--test", $TestFile
    }
    if ($Markers) {
        $args += "--markers", $Markers
    }
    if ($Verbose) {
        $args += "--verbose"
    }
    
    uv run python @args
}

function Invoke-TestSandbox {
    Write-Step "Running sandbox tests..."
    $args = @("tests\integration\test_runner.py", "sandbox")
    
    if ($Verbose) {
        $args += "--verbose"
    }
    
    uv run python @args
}

function Invoke-TestLive {
    Write-Step "Running live environment tests..."
    $args = @("tests\integration\test_runner.py", "live")
    
    if ($Verbose) {
        $args += "--verbose"
    }
    
    uv run python @args
}

function Invoke-TestAll {
    Write-Step "Running all integration tests..."
    $args = @("tests\integration\test_runner.py", "all")
    
    if ($Verbose) {
        $args += "--verbose"
    }
    
    uv run python @args
}

function Invoke-Coverage {
    Write-Step "Running tests with coverage..."
    $args = @("tests\integration\test_runner.py", "mock", "--coverage")
    
    if ($Verbose) {
        $args += "--verbose"
    }
    
    uv run python @args
}

function Invoke-Clean {
    Write-Step "Cleaning up test artifacts..."
    
    # Remove Python cache files
    Get-ChildItem -Path "tests\integration" -Recurse -Name "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "tests\integration" -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Remove pytest cache
    if (Test-Path "tests\integration\.pytest_cache") {
        Remove-Item -Path "tests\integration\.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Remove coverage files
    if (Test-Path "htmlcov") {
        Remove-Item -Path "htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path ".coverage") {
        Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

# Main execution
switch ($Command) {
    "setup" { Invoke-Setup }
    "deps-check" { Invoke-DepsCheck }
    "test-mock" { Invoke-TestMock }
    "test-sandbox" { Invoke-TestSandbox }
    "test-live" { Invoke-TestLive }
    "test-all" { Invoke-TestAll }
    "coverage" { Invoke-Coverage }
    "clean" { Invoke-Clean }
    "help" { Show-Help }
    default { Show-Help }
}

# Additional utility functions for PowerShell users

function Show-Environment {
    Write-Header "Environment Information"
    Write-Host "Python version: $(uv run python --version)" -ForegroundColor White
    Write-Host "Working directory: $(Get-Location)" -ForegroundColor White
    
    $testLevel = if ($env:INTEGRATION_TEST_LEVEL) { $env:INTEGRATION_TEST_LEVEL } else { 'mock' }
    Write-Host "Integration test level: $testLevel" -ForegroundColor White
    
    $sandboxUrl = if ($env:D365FO_SANDBOX_BASE_URL) { $env:D365FO_SANDBOX_BASE_URL } else { 'not set' }
    Write-Host "Sandbox URL: $sandboxUrl" -ForegroundColor White
    
    $liveUrl = if ($env:D365FO_LIVE_BASE_URL) { $env:D365FO_LIVE_BASE_URL } else { 'not set' }
    Write-Host "Live URL: $liveUrl" -ForegroundColor White
    
    if ($env:AZURE_CLIENT_ID) {
        Write-Host "Azure Client ID: set" -ForegroundColor White
    } else {
        Write-Host "Azure Client ID: not set" -ForegroundColor White
    }
    
    try {
        $null = Get-Command uv -ErrorAction Stop
        Write-Host "uv: installed" -ForegroundColor Green
    } catch {
        Write-Host "uv: not installed" -ForegroundColor Yellow
    }
}

function Start-MockServer {
    Write-Step "Starting mock server on http://localhost:8000"
    Write-Host "To start the mock server manually, run:" -ForegroundColor Yellow
    Write-Host "uv run python -m tests.integration.mock_server.server" -ForegroundColor White
}

# Export functions for module use
Export-ModuleMember -Function Show-Environment, Start-MockServer