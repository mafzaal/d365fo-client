#!/usr/bin/env python3
"""Setup script for D365 F&O Client integration testing environment."""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🔧 {text}")
    print('='*60)


def print_step(step, text):
    """Print a formatted step."""
    print(f"\n{step}. {text}")


def run_command(cmd, description, check=True):
    """Run a command and handle errors."""
    print(f"   Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {description}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print_step(1, "Checking Python version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"   ❌ Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_uv_installation():
    """Check if uv is installed."""
    print_step(2, "Checking uv installation")
    
    if shutil.which('uv'):
        print("   ✅ uv is installed")
        return True
    else:
        print("   ❌ uv not found")
        print("   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False


def install_dependencies():
    """Install integration test dependencies."""
    print_step(3, "Installing integration test dependencies")
    
    # Install integration test dependencies
    success = run_command(
        ['uv', 'add', '--group', 'integration', 'aiohttp', 'pytest-asyncio', 'pytest-cov', 'httpx'],
        "Integration dependencies installed"
    )
    
    if not success:
        print("   Trying fallback installation...")
        success = run_command(
            ['uv', 'add', '--dev', 'aiohttp>=3.10.0', 'pytest-asyncio>=0.25.0', 'pytest-cov>=6.2.1', 'httpx>=0.27.0'],
            "Dependencies installed via fallback method"
        )
    
    return success


def setup_environment_file():
    """Setup environment configuration file."""
    print_step(4, "Setting up environment configuration")
    
    integration_dir = Path(__file__).parent
    env_example = integration_dir / '.env.example'
    env_file = integration_dir / '.env'
    
    if env_file.exists():
        print("   ⚠️  .env file already exists, skipping creation")
        print(f"   📝 Edit {env_file} to configure your environment")
        return True
    
    if env_example.exists():
        shutil.copy2(env_example, env_file)
        print(f"   ✅ Created .env file from template")
        print(f"   📝 Edit {env_file} to configure your environment")
        return True
    else:
        print("   ❌ .env.example template not found")
        return False


def test_mock_server():
    """Test the mock server setup."""
    print_step(5, "Testing mock server setup")
    
    integration_dir = Path(__file__).parent
    test_cmd = [
        'python', str(integration_dir / 'test_runner.py'), 
        'mock', 
        '--test', 'test_mock_server.py::TestConnectionMockServer::test_connection_success'
    ]
    
    return run_command(test_cmd, "Mock server test passed", check=False)


def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete! 🎉")
    
    integration_dir = Path(__file__).parent
    
    print(f"""
Next Steps:

1. 📝 Configure your environment:
   Edit: {integration_dir / '.env'}
   
   For mock server tests only:
   - No additional configuration needed
   
   For sandbox tests:
   - Set D365FO_SANDBOX_BASE_URL
   - Set Azure AD credentials (AZURE_CLIENT_ID, etc.)
   
   For live tests:
   - Set D365FO_LIVE_BASE_URL
   - Set Azure AD credentials

2. 🧪 Run your first integration tests:
   
   # Mock server tests (no external dependencies)
   python {integration_dir / 'test_runner.py'} mock
   
   # Mock tests with verbose output and coverage
   python {integration_dir / 'test_runner.py'} mock --verbose --coverage
   
   # Sandbox tests (requires environment setup)
   python {integration_dir / 'test_runner.py'} sandbox

3. 📚 Learn more:
   - Read: {integration_dir / 'README.md'}
   - Check examples in test files
   - Run: python {integration_dir / 'test_runner.py'} --help

4. 🔧 Troubleshooting:
   - Check dependencies: python {integration_dir / 'test_runner.py'} mock --check-deps
   - Verify configuration: check .env file
   - Test connectivity: az login (for Azure environments)

Happy testing! 🚀
""")


def main():
    """Main setup function."""
    print_header("D365 F&O Client Integration Testing Setup")
    
    # Check prerequisites
    if not check_python_version():
        return 1
    
    if not check_uv_installation():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        return 1
    
    # Setup environment
    setup_environment_file()
    
    # Test setup
    print("\n" + "⏳ Testing setup...")
    if test_mock_server():
        print("   ✅ Mock server test successful")
    else:
        print("   ⚠️  Mock server test failed, but setup can continue")
        print("   Check the output above for any issues")
    
    # Print next steps
    print_next_steps()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())