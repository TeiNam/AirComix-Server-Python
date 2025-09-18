"""간단한 디렉토리 목록 엔드포인트 테스트"""

import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.handlers import MangaRequestHandler
from app.services import FileSystemService, ArchiveService, ImageService
from app.models.config import Settings


@pytest.fixture
def sample_manga_structure(tmp_path):
    """샘플 만화 디렉토리 구조 생성"""
    manga_dir = tmp_path / "manga"
    manga_dir.mkdir()
    
    # 시리즈 디렉토리들 생성
    series_a = manga_dir / "Series A"
    series_a.mkdir()
    
    series_b = manga_dir / "Series B"
    series_b.mkdir()
    
    # Series A에 파일들 생성
    (series_a / "Volume 1.zip").write_bytes(b"fake zip content")
    (series_a / "Volume 2.cbz").write_bytes(b"fake cbz content")
    (series_a / "cover.jpg").write_bytes(b"fake image content")
    
    return manga_dir


def test_root_directory_listing(sample_manga_structure):
    """루트 디렉토리 목록 조회 테스트"""
    # 테스트용 설정 생성
    test_settings = Settings(manga_directory=sample_manga_structure)
    
    # 테스트용 서비스들 생성
    filesystem_service = FileSystemService(test_settings.manga_directory)
    archive_service = ArchiveService()
    image_service = ImageService(test_settings, archive_service)
    
    # 테스트용 핸들러 생성
    manga_handler = MangaRequestHandler(
        settings=test_settings,
        filesystem_service=filesystem_service,
        archive_service=archive_service,
        image_service=image_service
    )
    
    # 테스트용 앱 생성
    app = FastAPI()
    
    @app.get("/manga/{path:path}")
    async def handle_manga_request(path: str):
        return await manga_handler.handle_request(path)
    
    test_client = TestClient(app)
    
    # 루트 디렉토리 요청 (빈 경로)
    response = test_client.get("/manga/")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    content = response.text
    lines = content.split('\n') if content else []
    
    # 시리즈 디렉토리들이 포함되어야 함
    assert "Series A" in lines
    assert "Series B" in lines


def test_series_directory_listing(sample_manga_structure):
    """시리즈 디렉토리 목록 조회 테스트"""
    # 테스트용 설정 생성
    test_settings = Settings(manga_directory=sample_manga_structure)
    
    # 테스트용 서비스들 생성
    filesystem_service = FileSystemService(test_settings.manga_directory)
    archive_service = ArchiveService()
    image_service = ImageService(test_settings, archive_service)
    
    # 테스트용 핸들러 생성
    manga_handler = MangaRequestHandler(
        settings=test_settings,
        filesystem_service=filesystem_service,
        archive_service=archive_service,
        image_service=image_service
    )
    
    # 테스트용 앱 생성
    app = FastAPI()
    
    @app.get("/manga/{path:path}")
    async def handle_manga_request(path: str):
        return await manga_handler.handle_request(path)
    
    test_client = TestClient(app)
    
    # Series A 디렉토리 요청
    response = test_client.get("/manga/Series%20A")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    content = response.text
    lines = content.split('\n') if content else []
    
    # 파일들이 포함되어야 함
    assert "Volume 1.zip" in lines
    assert "Volume 2.cbz" in lines
    assert "cover.jpg" in lines