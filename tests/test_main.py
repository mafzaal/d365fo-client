"""Tests for the main module."""

import pytest

from d365fo_client.main import main


def test_main(capsys):
    """Test the main function output."""
    main()
    captured = capsys.readouterr()
    assert "Hello from d365fo-client!" in captured.out


def test_main_no_exception():
    """Test that main function runs without exceptions."""
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
