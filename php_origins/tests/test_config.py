"""Test configuration management."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from app.models.config import Settings


def test_default_settings():
    """Test default settings values."""
    # Create a temporary directory for testing
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = Settings(manga_directory=Path(tmp_dir))
        
        assert settings.server_port == 31257
        assert settings.server_host == "0.0.0.0"
        assert settings.debug_mode is False
        assert settings.log_level == "INFO"
        assert "jpg" in settings.image_extensions
        assert "zip" in settings.archive_extensions


def test_settings_validation():
    """Test settings validation."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Valid settings should work
        settings = Settings(
            manga_directory=Path(tmp_dir),
            server_port=8000,
            log_level="DEBUG"
        )
        assert settings.server_port == 8000
        assert settings.log_level == "DEBUG"
    
    # Invalid port should raise error
    with pytest.raises(ValidationError):
        Settings(server_port=70000)  # Port too high
    
    # Invalid log level should raise error
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID")


def test_manga_directory_validation():
    """Test manga directory validation."""
    # Non-existent directory should raise error
    with pytest.raises(ValidationError, match="does not exist"):
        Settings(manga_directory=Path("/nonexistent/path"))


def test_extension_normalization():
    """Test that extensions are normalized properly."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = Settings(
            manga_directory=Path(tmp_dir),
            image_extensions=[".JPG", "PNG", ".gif"],
            archive_extensions=[".ZIP", "CBZ"]
        )
        
        # Extensions should be lowercase without dots
        assert settings.image_extensions == ["jpg", "png", "gif"]
        assert settings.archive_extensions == ["zip", "cbz"]