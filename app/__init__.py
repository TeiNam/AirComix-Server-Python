"""
Comix Server Python Port

A high-performance streaming server for comic books and manga,
compatible with the AirComix iOS app.
"""

__version__ = "1.0.0"
__author__ = "Comix Server Team"

# 주요 컴포넌트 임포트
from .main import create_app, main
from .models import Settings, settings
from .services import FileSystemService, ArchiveService, ImageService
from .utils import get_logger, setup_logging

__all__ = [
    "create_app",
    "main", 
    "Settings",
    "settings",
    "FileSystemService",
    "ArchiveService", 
    "ImageService",
    "get_logger",
    "setup_logging"
]