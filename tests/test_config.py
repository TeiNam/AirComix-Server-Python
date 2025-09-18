"""
설정 모델 테스트
"""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.config import Settings


def test_default_settings():
    """기본 설정 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        settings = Settings(manga_directory=manga_dir)
        
        assert settings.server_port == 31257
        assert settings.server_host == "0.0.0.0"
        assert settings.debug_mode is False
        assert settings.log_level == "INFO"
        assert "jpg" in settings.image_extensions
        assert "zip" in settings.archive_extensions


def test_manga_directory_validation():
    """manga 디렉토리 검증 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 존재하는 디렉토리
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        settings = Settings(manga_directory=manga_dir)
        assert settings.manga_directory == manga_dir
        
        # 존재하지 않는 디렉토리 (자동 생성)
        new_dir = Path(temp_dir) / "new_manga"
        settings = Settings(manga_directory=new_dir)
        assert settings.manga_directory.exists()


def test_port_validation():
    """포트 검증 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        # 유효한 포트
        settings = Settings(manga_directory=manga_dir, server_port=8080)
        assert settings.server_port == 8080
        
        # 무효한 포트
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, server_port=0)
        
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, server_port=70000)


def test_log_level_validation():
    """로그 레벨 검증 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        # 유효한 로그 레벨
        settings = Settings(manga_directory=manga_dir, log_level="debug")
        assert settings.log_level == "DEBUG"
        
        # 무효한 로그 레벨
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, log_level="INVALID")


def test_supported_extensions():
    """지원 확장자 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        settings = Settings(manga_directory=manga_dir)
        supported = settings.supported_extensions
        
        assert "jpg" in supported
        assert "zip" in supported
        assert "cbz" in supported
        assert len(supported) == len(settings.image_extensions + settings.archive_extensions)


def test_file_type_detection():
    """파일 타입 감지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        settings = Settings(manga_directory=manga_dir)
        
        # 이미지 파일 테스트
        assert settings.is_image_file("test.jpg") is True
        assert settings.is_image_file("test.JPG") is True
        assert settings.is_image_file("test.png") is True
        
        # 아카이브 파일 테스트
        assert settings.is_archive_file("test.zip") is True
        assert settings.is_archive_file("test.CBZ") is True
        assert settings.is_archive_file("test.rar") is True
        
        # 지원되지 않는 파일 테스트
        assert settings.is_image_file("test.txt") is False
        assert settings.is_archive_file("test.txt") is False
        assert settings.is_supported_file("test.txt") is False
        
        # 지원되는 파일 테스트
        assert settings.is_supported_file("test.jpg") is True
        assert settings.is_supported_file("test.zip") is True


def test_hidden_file_detection():
    """숨김 파일 감지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        settings = Settings(manga_directory=manga_dir)
        
        # 숨김 파일 테스트
        assert settings.is_hidden_file(".DS_Store") is True
        assert settings.is_hidden_file("Thumbs.db") is True
        assert settings.is_hidden_file("@eaDir") is True
        
        # 숨김 패턴 테스트
        assert settings.is_hidden_file("test__MACOSX__file") is True
        
        # 일반 파일 테스트
        assert settings.is_hidden_file("test.jpg") is False
        assert settings.is_hidden_file("manga.zip") is False


def test_performance_settings():
    """성능 설정 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        settings = Settings(
            manga_directory=manga_dir,
            max_file_size=50 * 1024 * 1024,  # 50MB
            chunk_size=4096
        )
        
        assert settings.max_file_size == 50 * 1024 * 1024
        assert settings.chunk_size == 4096


def test_performance_settings_validation():
    """성능 설정 검증 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        # 무효한 최대 파일 크기
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, max_file_size=0)
        
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, max_file_size=2 * 1024 * 1024 * 1024)  # 2GB
        
        # 무효한 청크 크기
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, chunk_size=0)
        
        with pytest.raises(ValidationError):
            Settings(manga_directory=manga_dir, chunk_size=2 * 1024 * 1024)  # 2MB