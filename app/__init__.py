"""
Comix Server Python Port

A high-performance streaming server for comic books and manga,
compatible with the AirComix iOS app.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    # 버전의 단일 출처는 pyproject.toml 이다. 'uv version --bump patch' 로 올린다.
    __version__ = _pkg_version("comix-server")
except PackageNotFoundError:
    # 설치되지 않은 소스 체크아웃에서 실행하는 경우
    __version__ = "0.0.0+unknown"
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