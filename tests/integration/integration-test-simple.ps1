# Simple Integration Testing PowerShell Script for Windows
# D365 F&O Client Integration Tests

param(
    [Parameter(Position=0)]
    [ValidateSet("help", "setup", "deps-check", "test-mock", "test-sandbox", "test-live", "test-all", "coverage", "clean")]
    [string]$Command = "help",
    
    [string]$TestFile = "",
    [string]$Markers = "",
    [switch]$VerboseOutput
)

function Show-Help {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "D365 F&O Client Integration Testing" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
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
    Write-Host "  .\integration-test-simple.ps1 test-mock -VerboseOutput" -ForegroundColor Gray
    Write-Host "  .\integration-test-simple.ps1 coverage" -ForegroundColor Gray
}

# Main execution
switch ($Command) {
    "setup" { 
        Write-Host "Setting up integration testing environment..." -ForegroundColor Cyan
        uv run python tests\integration\setup.py
    }
    "deps-check" { 
        Write-Host "Checking dependencies..." -ForegroundColor Cyan
        uv run python tests\integration\test_runner.py mock --check-deps
    }
    "test-mock" { 
        Write-Host "Running mock server tests..." -ForegroundColor Cyan
        $args = @("tests\integration\test_runner.py", "mock")
        
        if ($TestFile) {
            $args += "--test", $TestFile
        }
        if ($Markers) {
            $args += "--markers", $Markers
        }
        if ($VerboseOutput) {
            $args += "--verbose"
        }
        
        uv run python @args
    }
    "test-sandbox" { 
        Write-Host "Running sandbox tests..." -ForegroundColor Cyan
        $args = @("tests\integration\test_runner.py", "sandbox")
        
        if ($VerboseOutput) {
            $args += "--verbose"
        }
        
        uv run python @args
    }
    "test-live" { 
        Write-Host "Running live environment tests..." -ForegroundColor Cyan
        $args = @("tests\integration\test_runner.py", "live")
        
        if ($VerboseOutput) {
            $args += "--verbose"
        }
        
        uv run python @args
    }
    "test-all" { 
        Write-Host "Running all integration tests..." -ForegroundColor Cyan
        $args = @("tests\integration\test_runner.py", "all")
        
        if ($VerboseOutput) {
            $args += "--verbose"
        }
        
        uv run python @args
    }
    "coverage" { 
        Write-Host "Running tests with coverage..." -ForegroundColor Cyan
        $args = @("tests\integration\test_runner.py", "sandbox", "--coverage")
        
        if ($VerboseOutput) {
            $args += "--verbose"
        }
        
        uv run python @args
    }
    "clean" { 
        Write-Host "Cleaning up test artifacts..." -ForegroundColor Cyan
        
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
        
        Write-Host "Cleanup complete!" -ForegroundColor Green
    }
    "help" { Show-Help }
    default { Show-Help }
}