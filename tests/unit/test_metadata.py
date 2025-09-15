"""Tests for package metadata functionality."""

from pathlib import Path

import pytest


class TestPackageMetadata:
    """Test package metadata loading."""

    def test_version_exists(self):
        """Test that version is loaded and not empty."""
        from d365fo_client import __version__

        assert __version__, "Version should not be empty"
        assert isinstance(__version__, str), "Version should be a string"
        assert "." in __version__, "Version should contain dots (semver format)"

    def test_author_exists(self):
        """Test that author is loaded and not empty."""
        from d365fo_client import __author__

        assert __author__, "Author should not be empty"
        assert isinstance(__author__, str), "Author should be a string"

    def test_email_exists(self):
        """Test that email is loaded and not empty."""
        from d365fo_client import __email__

        assert __email__, "Email should not be empty"
        assert isinstance(__email__, str), "Email should be a string"
        assert "@" in __email__, "Email should contain @ symbol"

    def test_metadata_consistency(self):
        """Test that metadata is consistent across imports."""
        # Re-import to ensure consistency
        import d365fo_client
        from d365fo_client import __author__, __email__, __version__

        assert d365fo_client.__version__ == __version__
        assert d365fo_client.__author__ == __author__
        assert d365fo_client.__email__ == __email__

    def test_metadata_in_package_attributes(self):
        """Test that metadata is available in package __all__."""
        import d365fo_client

        # These should be accessible as attributes
        assert hasattr(d365fo_client, "__version__")
        assert hasattr(d365fo_client, "__author__")
        assert hasattr(d365fo_client, "__email__")

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists in project root."""
        # This is important for the fallback mechanism
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # tests/unit -> tests -> project root
        pyproject_path = project_root / "pyproject.toml"

        assert pyproject_path.exists(), "pyproject.toml should exist in project root"

        # Read and verify it contains project metadata
        content = pyproject_path.read_text(encoding="utf-8")
        assert "[project]" in content, "pyproject.toml should contain [project] section"
        assert "version" in content, "pyproject.toml should contain version"
        assert "authors" in content, "pyproject.toml should contain authors"
