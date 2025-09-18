"""
파일 시스템 서비스 간단 테스트
"""

import tempfile
from pathlib import Path
import pytest

from app.services.filesystem import FileSystemService


@pytest.mark.asyncio
async def test_filesystem_service_init():
    """FileSystemService 초기화 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        service = FileSystemService(manga_dir)
        assert service.manga_root == manga_dir


@pytest.mark.asyncio
async def test_list_empty_directory():
    """빈 디렉토리 목록 조회 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        service = FileSystemService(manga_dir)
        entries = await service.list_directory("")
        
        assert entries == []


@pytest.mark.asyncio
async def test_is_supported_file():
    """지원 파일 형식 확인 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        service = FileSystemService(manga_dir)
        
        # 이미지 파일들
        assert await service.is_supported_file("test.jpg") is True
        assert await service.is_supported_file("test.png") is True
        
        # 아카이브 파일들
        assert await service.is_supported_file("test.zip") is True
        assert await service.is_supported_file("test.cbz") is True
        
        # 지원되지 않는 파일들
        assert await service.is_supported_file("test.txt") is False


@pytest.mark.asyncio
async def test_file_exists():
    """파일 존재 확인 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        # 테스트 파일 생성
        test_file = manga_dir / "test.jpg"
        test_file.write_text("fake image")
        
        service = FileSystemService(manga_dir)
        
        # 존재하는 파일
        assert await service.file_exists("test.jpg") is True
        
        # 존재하지 않는 파일
        assert await service.file_exists("nonexistent.jpg") is False


def test_mime_type_detection():
    """MIME 타입 감지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        
        service = FileSystemService(manga_dir)
        
        # 다양한 이미지 형식
        assert service._get_mime_type("test.jpg") == "image/jpeg"
        assert service._get_mime_type("test.png") == "image/png"
        assert service._get_mime_type("test.gif") == "image/gif"