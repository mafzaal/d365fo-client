"""Tests for utility functions."""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from d365fo_client.utils import (
    get_user_cache_dir,
    get_default_cache_directory,
    ensure_directory_exists,
    extract_domain_from_url,
    get_environment_cache_dir,
    get_environment_cache_directory,
)


class TestGetUserCacheDir:
    """Test the get_user_cache_dir function."""
    
    def test_default_app_name(self):
        """Test default app name is used correctly."""
        cache_dir = get_user_cache_dir()
        assert "d365fo-client" in str(cache_dir)
    
    def test_custom_app_name(self):
        """Test custom app name is used correctly."""
        cache_dir = get_user_cache_dir("my-custom-app")
        assert "my-custom-app" in str(cache_dir)
    
    @patch('platform.system', return_value='Windows')
    def test_windows_cache_dir_with_localappdata(self, mock_platform):
        """Test Windows cache directory with LOCALAPPDATA."""
        with patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'}):
            cache_dir = get_user_cache_dir("test-app")
            expected = Path("C:\\Users\\Test\\AppData\\Local\\test-app")
            assert cache_dir == expected
    
    @patch('platform.system', return_value='Windows')
    def test_windows_cache_dir_with_appdata_fallback(self, mock_platform):
        """Test Windows cache directory falls back to APPDATA."""
        with patch.dict(os.environ, {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}, clear=True):
            cache_dir = get_user_cache_dir("test-app")
            expected = Path("C:\\Users\\Test\\AppData\\Roaming\\test-app")
            assert cache_dir == expected
    
    @patch('platform.system', return_value='Windows')
    @patch('pathlib.Path.home')
    def test_windows_cache_dir_no_env_vars(self, mock_home, mock_platform):
        """Test Windows cache directory when no environment variables are set."""
        mock_home.return_value = Path("C:\\Users\\Test")
        with patch.dict(os.environ, {}, clear=True):
            cache_dir = get_user_cache_dir("test-app")
            expected = Path("C:\\Users\\Test\\AppData\\Local\\test-app")
            assert cache_dir == expected
    
    @patch('platform.system', return_value='Darwin')
    @patch('pathlib.Path.home')
    def test_macos_cache_dir(self, mock_home, mock_platform):
        """Test macOS cache directory."""
        mock_home.return_value = Path("/Users/test")
        cache_dir = get_user_cache_dir("test-app")
        expected = Path("/Users/test/Library/Caches/test-app")
        assert cache_dir == expected
    
    @patch('platform.system', return_value='Linux')
    def test_linux_cache_dir_with_xdg_cache_home(self, mock_platform):
        """Test Linux cache directory with XDG_CACHE_HOME."""
        with patch.dict(os.environ, {'XDG_CACHE_HOME': '/home/test/.cache'}):
            cache_dir = get_user_cache_dir("test-app")
            expected = Path("/home/test/.cache/test-app")
            assert cache_dir == expected
    
    @patch('platform.system', return_value='Linux')
    @patch('pathlib.Path.home')
    def test_linux_cache_dir_default(self, mock_home, mock_platform):
        """Test Linux cache directory defaults to ~/.cache."""
        mock_home.return_value = Path("/home/test")
        with patch.dict(os.environ, {}, clear=True):
            cache_dir = get_user_cache_dir("test-app")
            expected = Path("/home/test/.cache/test-app")
            assert cache_dir == expected


class TestEnsureDirectoryExists:
    """Test the ensure_directory_exists function."""
    
    def test_create_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "new_directory"
            assert not test_path.exists()
            
            result = ensure_directory_exists(test_path)
            
            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path
    
    def test_create_nested_directories(self):
        """Test creating nested directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "level1" / "level2" / "level3"
            assert not test_path.exists()
            
            result = ensure_directory_exists(test_path)
            
            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path
    
    def test_existing_directory(self):
        """Test with an existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir)
            assert test_path.exists()
            
            result = ensure_directory_exists(test_path)
            
            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path
    
    def test_string_path_input(self):
        """Test with string path input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path_str = str(Path(temp_dir) / "string_path")
            test_path = Path(test_path_str)
            assert not test_path.exists()
            
            result = ensure_directory_exists(test_path_str)
            
            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path


class TestExtractDomainFromUrl:
    """Test the extract_domain_from_url function."""
    
    def test_standard_https_url(self):
        """Test standard HTTPS URL."""
        domain = extract_domain_from_url("https://mycompany.sandbox.operations.dynamics.com")
        assert domain == "mycompany.sandbox.operations.dynamics.com"
    
    def test_http_url(self):
        """Test HTTP URL."""
        domain = extract_domain_from_url("http://test-env.dynamics.com")
        assert domain == "test-env.dynamics.com"
    
    def test_url_with_path(self):
        """Test URL with path components."""
        domain = extract_domain_from_url("https://mycompany.dynamics.com/some/path")
        assert domain == "mycompany.dynamics.com"
    
    def test_url_with_port(self):
        """Test URL with custom port."""
        domain = extract_domain_from_url("https://localhost:8080")
        assert domain == "localhost_8080"
    
    def test_url_with_default_ports(self):
        """Test URL with default ports (should be removed)."""
        domain = extract_domain_from_url("https://example.com:443")
        assert domain == "example.com"
        
        domain = extract_domain_from_url("http://example.com:80")
        assert domain == "example.com"
    
    def test_url_with_invalid_characters(self):
        """Test URL with characters that need sanitization."""
        domain = extract_domain_from_url("https://test<domain>:8080")
        assert domain == "test_domain__8080"
    
    def test_malformed_url(self):
        """Test malformed URL fallback."""
        domain = extract_domain_from_url("not-a-valid-url")
        assert len(domain) > 0
        assert domain == "not-a-valid-url"
    
    def test_empty_url(self):
        """Test empty URL fallback."""
        domain = extract_domain_from_url("")
        assert domain == "unknown-domain"
    
    def test_case_normalization(self):
        """Test that domains are normalized to lowercase."""
        domain = extract_domain_from_url("https://MyCompany.DYNAMICS.COM")
        assert domain == "mycompany.dynamics.com"


class TestGetEnvironmentCacheDir:
    """Test the get_environment_cache_dir function."""
    
    def test_default_app_name(self):
        """Test environment cache directory with default app name."""
        cache_dir = get_environment_cache_dir("https://test.dynamics.com")
        assert "d365fo-client" in str(cache_dir)
        assert "test.dynamics.com" in str(cache_dir)
    
    def test_custom_app_name(self):
        """Test environment cache directory with custom app name."""
        cache_dir = get_environment_cache_dir("https://test.dynamics.com", "my-app")
        assert "my-app" in str(cache_dir)
        assert "test.dynamics.com" in str(cache_dir)
    
    def test_different_environments(self):
        """Test that different environments get different cache directories."""
        cache_dir1 = get_environment_cache_dir("https://prod.dynamics.com")
        cache_dir2 = get_environment_cache_dir("https://test.dynamics.com")
        
        assert cache_dir1 != cache_dir2
        assert "prod.dynamics.com" in str(cache_dir1)
        assert "test.dynamics.com" in str(cache_dir2)
    
    def test_complex_domain(self):
        """Test with complex domain structure."""
        cache_dir = get_environment_cache_dir("https://mycompany.sandbox.operations.dynamics.com")
        assert "mycompany.sandbox.operations.dynamics.com" in str(cache_dir)
    
    def test_localhost_with_port(self):
        """Test localhost with port."""
        cache_dir = get_environment_cache_dir("https://localhost:8080")
        assert "localhost_8080" in str(cache_dir)


class TestGetEnvironmentCacheDirectory:
    """Test the get_environment_cache_directory function."""
    
    def test_returns_string(self):
        """Test that function returns a string."""
        cache_dir = get_environment_cache_directory("https://test.dynamics.com")
        assert isinstance(cache_dir, str)
    
    def test_contains_domain(self):
        """Test that returned path contains the domain."""
        cache_dir = get_environment_cache_directory("https://test.dynamics.com")
        assert "test.dynamics.com" in cache_dir
    
    def test_is_absolute_path(self):
        """Test that returned path is absolute."""
        cache_dir = get_environment_cache_directory("https://test.dynamics.com")
        path = Path(cache_dir)
        assert path.is_absolute()


class TestGetDefaultCacheDirectory:
    """Test the get_default_cache_directory function."""
    
    def test_returns_string(self):
        """Test that the function returns a string."""
        cache_dir = get_default_cache_directory()
        assert isinstance(cache_dir, str)
    
    def test_contains_app_name(self):
        """Test that the returned path contains the app name."""
        cache_dir = get_default_cache_directory()
        assert "d365fo-client" in cache_dir
    
    def test_is_absolute_path(self):
        """Test that the returned path is absolute."""
        cache_dir = get_default_cache_directory()
        path = Path(cache_dir)
        assert path.is_absolute()


class TestPlatformSpecificBehavior:
    """Test platform-specific behavior on the current platform."""
    
    def test_actual_platform_cache_dir(self):
        """Test cache directory on the actual platform."""
        cache_dir = get_user_cache_dir()
        
        current_platform = platform.system()
        
        if current_platform == "Windows":
            # Should contain AppData somewhere in the path
            assert "AppData" in str(cache_dir)
        elif current_platform == "Darwin":
            # Should be in Library/Caches
            assert "Library/Caches" in str(cache_dir)
        else:  # Linux and others
            # Should be in .cache
            assert ".cache" in str(cache_dir)
    
    def test_cache_directory_is_writable(self):
        """Test that the cache directory is writable."""
        cache_dir = get_user_cache_dir("test-writable")
        
        # Create the directory
        ensure_directory_exists(cache_dir)
        
        # Test writing a file
        test_file = cache_dir / "test_write.txt"
        test_file.write_text("test content")
        
        # Verify we can read it back
        assert test_file.read_text() == "test content"
        
        # Clean up
        test_file.unlink()
        cache_dir.rmdir()


def test_integration_with_fo_client_config():
    """Test integration with FOClientConfig."""
    from d365fo_client.models import FOClientConfig
    
    # Test environment-specific cache directory is set automatically
    config = FOClientConfig(base_url="https://test.dynamics.com")
    assert config.metadata_cache_dir is not None
    assert "d365fo-client" in config.metadata_cache_dir
    assert "test.dynamics.com" in config.metadata_cache_dir
    
    # Test different environments get different cache directories
    config1 = FOClientConfig(base_url="https://prod.dynamics.com")
    config2 = FOClientConfig(base_url="https://test.dynamics.com")
    assert config1.metadata_cache_dir != config2.metadata_cache_dir
    assert "prod.dynamics.com" in config1.metadata_cache_dir
    assert "test.dynamics.com" in config2.metadata_cache_dir
    
    # Test custom cache directory is still preserved
    custom_dir = "/custom/cache/dir"
    config = FOClientConfig(base_url="https://test.dynamics.com", metadata_cache_dir=custom_dir)
    assert config.metadata_cache_dir == custom_dir


def test_environment_separation():
    """Test that different environments have completely separate cache structures."""
    # Test with different environment URLs
    urls = [
        "https://prod.dynamics.com",
        "https://test.dynamics.com", 
        "https://dev.dynamics.com",
        "https://mycompany.sandbox.operations.dynamics.com",
        "https://localhost:8080"
    ]
    
    cache_dirs = [get_environment_cache_directory(url) for url in urls]
    
    # All cache directories should be unique
    assert len(set(cache_dirs)) == len(cache_dirs)
    
    # Each should contain the appropriate domain identifier
    for i, cache_dir in enumerate(cache_dirs):
        if "localhost:8080" in urls[i]:
            assert "localhost_8080" in cache_dir
        else:
            # Extract expected domain
            domain = extract_domain_from_url(urls[i])
            assert domain in cache_dir


def test_cache_directory_structure():
    """Test the expected cache directory structure."""
    cache_dir = get_environment_cache_dir("https://test.dynamics.com")
    
    # Should follow pattern: {user_cache}/d365fo-client/{domain}
    parts = cache_dir.parts
    assert "d365fo-client" in parts
    assert "test.dynamics.com" in parts
    
    # Domain should be the last part
    assert parts[-1] == "test.dynamics.com"


def test_integration_with_metadata_manager():
    """Test integration with MetadataManager."""
    from d365fo_client.metadata import MetadataManager
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "test_cache"
        
        # Verify directory doesn't exist initially
        assert not cache_dir.exists()
        
        # Create MetadataManager which should create the directory
        manager = MetadataManager(str(cache_dir))
        
        # Verify directory was created
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        
        # Verify cache files are properly set up
        assert manager.cache_dir == str(cache_dir)
        assert manager.metadata_file == str(cache_dir / "odata_metadata.xml")
        assert manager.entities_cache == str(cache_dir / "entities.json")
        assert manager.actions_cache == str(cache_dir / "actions.json")