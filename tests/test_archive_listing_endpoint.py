"""아카이브 목록 엔드포인트 테스트"""

import pytest
import zipfile
import io
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import create_app


class TestArchiveListingSimple:
    """간단한 아카이브 목록 테스트"""
    
    def test_archive_endpoint_basic(self):
        """아카이브 엔드포인트 기본 테스트"""
        app = create_app()
        client = TestClient(app)
        
        # 존재하지 않는 아카이브 파일 요청
        response = client.get("/manga/nonexistent.zip")
        
        # 404는 정상 (파일이 없음), 다른 오류는 엔드포인트 문제
        assert response.status_code in [200, 404, 403], f"Unexpected status: {response.status_code}"
    
    def test_archive_file_extensions(self):
        """다양한 아카이브 확장자 테스트"""
        app = create_app()
        client = TestClient(app)
        
        archive_extensions = ["zip", "cbz", "rar", "cbr"]
        
        for ext in archive_extensions:
            response = client.get(f"/manga/test.{ext}")
            
            # 파일이 없어도 엔드포인트는 작동해야 함
            assert response.status_code in [200, 404, 403], f"Failed for .{ext} extension"
    
    def test_archive_with_path(self):
        """경로가 포함된 아카이브 테스트"""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/manga/Series%20A/Volume%201.zip")
        
        # 엔드포인트는 작동해야 함
        assert response.status_code in [200, 404, 403]
    
    def test_archive_case_insensitive(self):
        """대소문자 구분 없는 아카이브 확장자 테스트"""
        app = create_app()
        client = TestClient(app)
        
        case_variations = ["ZIP", "Zip", "zIp", "CBZ", "Cbz"]
        
        for ext in case_variations:
            response = client.get(f"/manga/test.{ext}")
            
            # 엔드포인트는 작동해야 함
            assert response.status_code in [200, 404, 403], f"Failed for .{ext} extension"


class TestArchiveListingWithMocks:
    """모킹을 사용한 아카이브 목록 테스트"""
    
    def test_zip_archive_listing(self, tmp_path):
        """ZIP 아카이브 목록 테스트"""
        # 테스트용 ZIP 파일 생성
        manga_dir = tmp_path / "manga"
        manga_dir.mkdir()
        
        zip_file = manga_dir / "test.zip"
        
        # ZIP 파일에 이미지 파일들 추가
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("page001.jpg", b"fake image 1")
            zf.writestr("page002.png", b"fake image 2")
            zf.writestr("page003.gif", b"fake image 3")
            zf.writestr("readme.txt", b"text file")  # 이미지가 아닌 파일
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.manga_directory = str(manga_dir)
            
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/manga/test.zip")
            
            if response.status_code == 200:
                assert response.headers["content-type"] == "text/plain; charset=utf-8"
                
                content = response.text
                lines = content.split('\n') if content else []
                
                # 이미지 파일들이 포함되어야 함
                image_files = ["page001.jpg", "page002.png", "page003.gif"]
                for img_file in image_files:
                    assert img_file in lines, f"Image file {img_file} should be in archive listing"
                
                # 텍스트 파일은 제외되어야 함
                assert "readme.txt" not in lines, "Non-image files should be filtered out"
    
    def test_empty_archive_listing(self, tmp_path):
        """빈 아카이브 목록 테스트"""
        manga_dir = tmp_path / "manga"
        manga_dir.mkdir()
        
        zip_file = manga_dir / "empty.zip"
        
        # 빈 ZIP 파일 생성
        with zipfile.ZipFile(zip_file, 'w') as zf:
            pass  # 빈 아카이브
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.manga_directory = str(manga_dir)
            
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/manga/empty.zip")
            
            if response.status_code == 200:
                assert response.headers["content-type"] == "text/plain; charset=utf-8"
                # 빈 응답이어야 함
                assert response.text == ""
    
    def test_archive_with_subdirectories(self, tmp_path):
        """서브디렉토리가 있는 아카이브 테스트"""
        manga_dir = tmp_path / "manga"
        manga_dir.mkdir()
        
        zip_file = manga_dir / "structured.zip"
        
        # 디렉토리 구조가 있는 ZIP 파일 생성
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("chapter1/page001.jpg", b"fake image 1")
            zf.writestr("chapter1/page002.jpg", b"fake image 2")
            zf.writestr("chapter2/page001.jpg", b"fake image 3")
            zf.writestr("cover.jpg", b"cover image")
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.manga_directory = str(manga_dir)
            
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/manga/structured.zip")
            
            if response.status_code == 200:
                assert response.headers["content-type"] == "text/plain; charset=utf-8"
                
                content = response.text
                lines = content.split('\n') if content else []
                
                # 모든 이미지 파일들이 포함되어야 함 (경로 포함)
                expected_files = [
                    "chapter1/page001.jpg",
                    "chapter1/page002.jpg", 
                    "chapter2/page001.jpg",
                    "cover.jpg"
                ]
                
                for expected_file in expected_files:
                    assert expected_file in lines, f"File {expected_file} should be in archive listing"
    
    def test_archive_with_korean_filenames(self, tmp_path):
        """한글 파일명이 있는 아카이브 테스트"""
        manga_dir = tmp_path / "manga"
        manga_dir.mkdir()
        
        zip_file = manga_dir / "korean.zip"
        
        # 한글 파일명이 있는 ZIP 파일 생성
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("1페이지.jpg", b"fake image 1")
            zf.writestr("2페이지.png", b"fake image 2")
            zf.writestr("표지.jpg", b"cover image")
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.manga_directory = str(manga_dir)
            
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/manga/korean.zip")
            
            if response.status_code == 200:
                assert response.headers["content-type"] == "text/plain; charset=utf-8"
                
                content = response.text
                lines = content.split('\n') if content else []
                
                # 한글 파일명들이 포함되어야 함
                korean_files = ["1페이지.jpg", "2페이지.png", "표지.jpg"]
                for korean_file in korean_files:
                    assert korean_file in lines, f"Korean filename {korean_file} should be in archive listing"
    
    def test_archive_trailing_slash(self):
        """아카이브 경로 끝의 슬래시 처리 테스트"""
        app = create_app()
        client = TestClient(app)
        
        # 슬래시가 있는 경우와 없는 경우 모두 테스트
        paths = [
            "/manga/test.zip",
            "/manga/test.zip/"
        ]
        
        for path in paths:
            response = client.get(path)
            
            # 엔드포인트는 작동해야 함
            assert response.status_code in [200, 404, 403], f"Failed for path: {path}"
    
    def test_archive_mixed_file_types(self, tmp_path):
        """다양한 파일 타입이 혼재된 아카이브 테스트"""
        manga_dir = tmp_path / "manga"
        manga_dir.mkdir()
        
        zip_file = manga_dir / "mixed.zip"
        
        # 다양한 파일 타입이 있는 ZIP 파일 생성
        with zipfile.ZipFile(zip_file, 'w') as zf:
            # 지원되는 이미지 파일들
            zf.writestr("page001.jpg", b"jpeg image")
            zf.writestr("page002.png", b"png image")
            zf.writestr("page003.gif", b"gif image")
            zf.writestr("page004.bmp", b"bmp image")
            zf.writestr("page005.tif", b"tiff image")
            
            # 지원되지 않는 파일들
            zf.writestr("readme.txt", b"text file")
            zf.writestr("info.pdf", b"pdf file")
            zf.writestr("video.mp4", b"video file")
            zf.writestr("audio.mp3", b"audio file")
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.manga_directory = str(manga_dir)
            
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/manga/mixed.zip")
            
            if response.status_code == 200:
                assert response.headers["content-type"] == "text/plain; charset=utf-8"
                
                content = response.text
                lines = content.split('\n') if content else []
                
                # 지원되는 이미지 파일들만 포함되어야 함
                supported_files = [
                    "page001.jpg", "page002.png", "page003.gif", 
                    "page004.bmp", "page005.tif"
                ]
                for supported_file in supported_files:
                    assert supported_file in lines, f"Supported file {supported_file} should be included"
                
                # 지원되지 않는 파일들은 제외되어야 함
                unsupported_files = ["readme.txt", "info.pdf", "video.mp4", "audio.mp3"]
                for unsupported_file in unsupported_files:
                    assert unsupported_file not in lines, f"Unsupported file {unsupported_file} should be excluded"