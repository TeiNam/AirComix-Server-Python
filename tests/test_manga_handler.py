"""MangaRequestHandler 테스트"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from app.api.handlers import MangaRequestHandler
from app.models.config import Settings
from app.services import FileSystemService, ArchiveService, ImageService
from app.exceptions import FileNotFoundError, PathTraversalError


@pytest.fixture
def mock_settings():
    """테스트용 설정 객체"""
    settings = Mock(spec=Settings)
    settings.manga_directory = "/test/manga"
    return settings


@pytest.fixture
def mock_filesystem_service():
    """테스트용 파일시스템 서비스 모의 객체"""
    return Mock(spec=FileSystemService)


@pytest.fixture
def mock_archive_service():
    """테스트용 아카이브 서비스 모의 객체"""
    return Mock(spec=ArchiveService)


@pytest.fixture
def mock_image_service():
    """테스트용 이미지 서비스 모의 객체"""
    return Mock(spec=ImageService)


@pytest.fixture
def manga_handler(mock_settings, mock_filesystem_service, mock_archive_service, mock_image_service):
    """테스트용 MangaRequestHandler 인스턴스"""
    return MangaRequestHandler(
        settings=mock_settings,
        filesystem_service=mock_filesystem_service,
        archive_service=mock_archive_service,
        image_service=mock_image_service
    )


class TestMangaRequestHandler:
    """MangaRequestHandler 테스트 클래스"""
    
    def test_validate_and_normalize_path_empty(self, manga_handler):
        """빈 경로 검증 테스트"""
        assert manga_handler._validate_and_normalize_path("") == ""
        assert manga_handler._validate_and_normalize_path("/") == ""
    
    def test_validate_and_normalize_path_normal(self, manga_handler):
        """일반 경로 검증 테스트"""
        with patch('app.utils.path.PathUtils.is_safe_path', return_value=True):
            with patch('app.utils.path.PathUtils.normalize_path', return_value="series/volume1"):
                result = manga_handler._validate_and_normalize_path("/series/volume1")
                assert result == "series/volume1"
    
    def test_validate_and_normalize_path_unsafe(self, manga_handler):
        """안전하지 않은 경로 검증 테스트"""
        with patch('app.utils.path.PathUtils.is_safe_path', return_value=False):
            with pytest.raises(PathTraversalError) as exc_info:
                manga_handler._validate_and_normalize_path("../../../etc/passwd")
            
            assert exc_info.value.status_code == 403
            assert "접근이 거부되었습니다" in exc_info.value.detail
    
    def test_is_archive_image_request_true(self, manga_handler):
        """아카이브 이미지 요청 확인 테스트 (True)"""
        with patch('app.utils.path.PathUtils.extract_archive_and_image_paths', 
                   return_value=("series/volume1.zip", "page001.jpg")):
            assert manga_handler._is_archive_image_request("series/volume1.zip/page001.jpg") is True
    
    def test_is_archive_image_request_false(self, manga_handler):
        """아카이브 이미지 요청 확인 테스트 (False)"""
        with patch('app.utils.path.PathUtils.extract_archive_and_image_paths', 
                   return_value=("series/volume1.zip", "")):
            assert manga_handler._is_archive_image_request("series/volume1.zip") is False
    
    @pytest.mark.asyncio
    async def test_handle_directory_listing_success(self, manga_handler, mock_filesystem_service, tmp_path):
        """디렉토리 목록 처리 성공 테스트"""
        # manga_root 설정을 tmp_path로 변경
        manga_handler.manga_root = tmp_path
        
        # 테스트 디렉토리 생성
        test_dir = tmp_path / "test_series"
        test_dir.mkdir()
        
        # 모의 서비스 설정
        mock_filesystem_service.list_directory = AsyncMock(return_value=["volume1.zip", "volume2.zip"])
        
        # 디렉토리 목록 요청
        response = await manga_handler.handle_directory_listing(test_dir)
        
        # 응답 검증
        assert response.body.decode() == "volume1.zip\nvolume2.zip"
        mock_filesystem_service.list_directory.assert_called_once_with("test_series")
    
    @pytest.mark.asyncio
    async def test_handle_directory_listing_empty(self, manga_handler, mock_filesystem_service, tmp_path):
        """빈 디렉토리 목록 처리 테스트"""
        # manga_root 설정을 tmp_path로 변경
        manga_handler.manga_root = tmp_path
        
        # 테스트 디렉토리 생성
        test_dir = tmp_path / "empty_series"
        test_dir.mkdir()
        
        # 모의 서비스 설정 (빈 목록)
        mock_filesystem_service.list_directory = AsyncMock(return_value=[])
        
        # 디렉토리 목록 요청
        response = await manga_handler.handle_directory_listing(test_dir)
        
        # 응답 검증 (빈 문자열)
        assert response.body.decode() == ""
        mock_filesystem_service.list_directory.assert_called_once_with("empty_series")
    
    @pytest.mark.asyncio
    async def test_handle_archive_listing_success(self, manga_handler, mock_archive_service, tmp_path):
        """아카이브 목록 처리 성공 테스트"""
        # 테스트 아카이브 파일 생성
        test_archive = tmp_path / "volume1.zip"
        test_archive.write_bytes(b"fake archive")
        
        # 모의 서비스 설정
        mock_archive_service.list_archive_contents = AsyncMock(
            return_value=["page001.jpg", "page002.jpg", "page003.jpg"]
        )
        
        # 아카이브 목록 요청
        response = await manga_handler.handle_archive_listing(test_archive)
        
        # 응답 검증
        assert response.body.decode() == "page001.jpg\npage002.jpg\npage003.jpg"
        mock_archive_service.list_archive_contents.assert_called_once_with(test_archive)
    
    @pytest.mark.asyncio
    async def test_handle_direct_image_request(self, manga_handler, mock_image_service, tmp_path):
        """직접 이미지 요청 처리 테스트"""
        # 테스트 이미지 파일 생성
        test_image = tmp_path / "cover.jpg"
        test_image.write_bytes(b"fake image")
        
        # 모의 서비스 설정
        mock_response = Mock()
        mock_image_service.stream_image = AsyncMock(return_value=mock_response)
        
        # 이미지 요청
        response = await manga_handler._handle_direct_image_request(test_image)
        
        # 응답 검증
        assert response == mock_response
        mock_image_service.stream_image.assert_called_once_with(test_image)
    
    @pytest.mark.asyncio
    async def test_handle_archive_image_request(self, manga_handler, mock_image_service, tmp_path):
        """아카이브 이미지 요청 처리 테스트"""
        # 테스트 아카이브 파일 생성
        test_archive = tmp_path / "volume1.zip"
        test_archive.write_bytes(b"fake archive")
        
        # 모의 서비스 설정
        mock_response = Mock()
        mock_image_service.stream_image_from_archive = AsyncMock(return_value=mock_response)
        
        # PathUtils 모킹
        with patch('app.utils.path.PathUtils.extract_archive_and_image_paths', 
                   return_value=("volume1.zip", "page001.jpg")):
            
            # 아카이브 이미지 요청
            response = await manga_handler._handle_archive_image_request("volume1.zip/page001.jpg")
            
            # 응답 검증
            assert response == mock_response
            expected_archive_path = manga_handler.manga_root / "volume1.zip"
            mock_image_service.stream_image_from_archive.assert_called_once_with(
                expected_archive_path, "page001.jpg"
            )


class TestMangaRequestHandlerIntegration:
    """MangaRequestHandler 통합 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_handle_request_directory(self, manga_handler, mock_filesystem_service, tmp_path):
        """디렉토리 요청 통합 테스트"""
        # 테스트 디렉토리 생성
        test_dir = tmp_path / "manga" / "series"
        test_dir.mkdir(parents=True)
        
        # 모의 서비스 설정
        mock_filesystem_service.list_directory = AsyncMock(return_value=["volume1.zip"])
        
        # manga_root를 tmp_path/manga로 설정
        manga_handler.manga_root = tmp_path / "manga"
        
        # PathUtils 모킹
        with patch('app.utils.path.PathUtils.is_safe_path', return_value=True):
            with patch('app.utils.path.PathUtils.normalize_path', return_value="series"):
                
                # 요청 처리
                response = await manga_handler.handle_request("series")
                
                # 응답 검증
                assert response.body.decode() == "volume1.zip"
    
    @pytest.mark.asyncio
    async def test_handle_request_archive_file(self, manga_handler, mock_archive_service, tmp_path):
        """아카이브 파일 요청 통합 테스트"""
        # 테스트 아카이브 파일 생성
        test_archive = tmp_path / "manga" / "volume1.zip"
        test_archive.parent.mkdir(parents=True)
        test_archive.write_bytes(b"fake archive")
        
        # 모의 서비스 설정
        mock_archive_service.is_archive_file.return_value = True
        mock_archive_service.list_archive_contents = AsyncMock(return_value=["page001.jpg"])
        
        # manga_root를 tmp_path/manga로 설정
        manga_handler.manga_root = tmp_path / "manga"
        
        # PathUtils 모킹
        with patch('app.utils.path.PathUtils.is_safe_path', return_value=True):
            with patch('app.utils.path.PathUtils.normalize_path', return_value="volume1.zip"):
                
                # 요청 처리
                response = await manga_handler.handle_request("volume1.zip")
                
                # 응답 검증
                assert response.body.decode() == "page001.jpg"
    
    @pytest.mark.asyncio
    async def test_handle_request_direct_image(self, manga_handler, mock_image_service, tmp_path):
        """직접 이미지 요청 통합 테스트"""
        # 테스트 이미지 파일 생성
        test_image = tmp_path / "manga" / "cover.jpg"
        test_image.parent.mkdir(parents=True)
        test_image.write_bytes(b"fake image")
        
        # 모의 서비스 설정
        mock_archive_service = manga_handler.archive_service
        mock_archive_service.is_archive_file.return_value = False
        mock_image_service.is_image_file.return_value = True
        
        mock_response = Mock()
        mock_image_service.stream_image = AsyncMock(return_value=mock_response)
        
        # manga_root를 tmp_path/manga로 설정
        manga_handler.manga_root = tmp_path / "manga"
        
        # PathUtils 모킹
        with patch('app.utils.path.PathUtils.is_safe_path', return_value=True):
            with patch('app.utils.path.PathUtils.normalize_path', return_value="cover.jpg"):
                
                # 요청 처리
                response = await manga_handler.handle_request("cover.jpg")
                
                # 응답 검증
                assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_handle_request_file_not_found(self, manga_handler, tmp_path):
        """파일 없음 요청 통합 테스트"""
        # manga_root를 tmp_path/manga로 설정 (빈 디렉토리)
        manga_dir = tmp_path / "manga"
        manga_dir.mkdir()
        manga_handler.manga_root = manga_dir
        
        # PathUtils 모킹
        with patch('app.utils.path.PathUtils.is_safe_path', return_value=True):
            with patch('app.utils.path.PathUtils.normalize_path', return_value="nonexistent.jpg"):
                
                # 요청 처리 및 예외 확인
                with pytest.raises(FileNotFoundError) as exc_info:
                    await manga_handler.handle_request("nonexistent.jpg")
                
                assert exc_info.value.status_code == 404