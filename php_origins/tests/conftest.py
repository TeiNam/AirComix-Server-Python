"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.config import Settings


@pytest.fixture
def test_settings(tmp_path):
    """Create test settings with temporary directory."""
    manga_dir = tmp_path / "manga"
    manga_dir.mkdir()
    
    return Settings(
        manga_directory=manga_dir,
        server_port=31257,
        debug_mode=True,
        log_level="DEBUG"
    )


@pytest.fixture
def test_app(test_settings):
    """Create test FastAPI application."""
    # Override settings for testing
    import app.models.config
    app.models.config.settings = test_settings
    
    return create_app()


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)