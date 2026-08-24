"""ImageService 단위 테스트"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.exceptions import FileTooLargeError
from app.services.image import ImageService
from app.services.archive import ArchiveService
from app.models.config import Settings


@pytest.fixture
def mock_settings():
    """테스트용 설정 객체"""
    settings = Mock(spec=Settings)
    settings.image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'tif', 'tiff', 'bmp']
    settings.max_file_size = 100 * 1024 * 1024
    settings.chunk_size = 8192
    return settings


@pytest.fixture
def mock_archive_service():
    """테스트용 아카이브 서비스 모의 객체"""
    return Mock(spec=ArchiveService)


@pytest.fixture
def image_service(mock_settings, mock_archive_service):
    """테스트용 ImageService 인스턴스"""
    return ImageService(mock_settings, mock_archive_service)


class TestImageService:
    """ImageService 테스트 클래스"""
    
    def test_get_mime_type_jpg(self, image_service):
        """JPG 파일의 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.jpg") == "image/jpeg"
        assert image_service.get_mime_type("test.jpeg") == "image/jpeg"
    
    def test_get_mime_type_png(self, image_service):
        """PNG 파일의 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.png") == "image/png"
    
    def test_get_mime_type_gif(self, image_service):
        """GIF 파일의 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.gif") == "image/gif"
    
    def test_get_mime_type_tiff(self, image_service):
        """TIFF 파일의 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.tif") == "image/tiff"
        assert image_service.get_mime_type("test.tiff") == "image/tiff"
    
    def test_get_mime_type_bmp(self, image_service):
        """BMP 파일의 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.bmp") == "image/bmp"
    
    def test_get_mime_type_unknown(self, image_service):
        """알 수 없는 파일의 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.unknown") == "application/octet-stream"
    
    def test_get_mime_type_case_insensitive(self, image_service):
        """대소문자 구분 없는 MIME 타입 테스트"""
        assert image_service.get_mime_type("test.JPG") == "image/jpeg"
        assert image_service.get_mime_type("test.PNG") == "image/png"
    
    def test_is_image_file_supported(self, image_service):
        """지원되는 이미지 파일 형식 테스트"""
        assert image_service.is_image_file("test.jpg") is True
        assert image_service.is_image_file("test.jpeg") is True
        assert image_service.is_image_file("test.png") is True
        assert image_service.is_image_file("test.gif") is True
        assert image_service.is_image_file("test.tif") is True
        assert image_service.is_image_file("test.tiff") is True
        assert image_service.is_image_file("test.bmp") is True
    
    def test_is_image_file_unsupported(self, image_service):
        """지원되지 않는 파일 형식 테스트"""
        assert image_service.is_image_file("test.txt") is False
        assert image_service.is_image_file("test.pdf") is False
        assert image_service.is_image_file("test.zip") is False
    
    def test_is_image_file_case_insensitive(self, image_service):
        """대소문자 구분 없는 이미지 파일 확인 테스트"""
        assert image_service.is_image_file("test.JPG") is True
        assert image_service.is_image_file("test.PNG") is True
    
    @pytest.mark.asyncio
    async def test_stream_image_success(self, image_service, tmp_path):
        """이미지 스트리밍 성공 테스트"""
        # 테스트 이미지 파일 생성
        test_image = tmp_path / "test.jpg"
        test_content = b"fake image content"
        test_image.write_bytes(test_content)
        
        # 스트리밍 실행
        response = await image_service.stream_image(test_image)
        
        # 응답 검증
        assert response.media_type == "image/jpeg"
        assert response.headers["Content-Type"] == "image/jpeg"
        assert response.headers["Content-Length"] == str(len(test_content))
        assert "Accept-Ranges" in response.headers
    
    @pytest.mark.asyncio
    async def test_stream_image_file_not_found(self, image_service, tmp_path):
        """존재하지 않는 이미지 파일 스트리밍 테스트"""
        non_existent_file = tmp_path / "nonexistent.jpg"
        
        with pytest.raises(HTTPException) as exc_info:
            await image_service.stream_image(non_existent_file)
        
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_stream_image_not_a_file(self, image_service, tmp_path):
        """디렉토리를 이미지로 스트리밍하려는 경우 테스트"""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        with pytest.raises(HTTPException) as exc_info:
            await image_service.stream_image(test_dir)
        
        assert exc_info.value.status_code == 404
        assert "유효한 이미지 파일이 아닙니다" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_stream_image_from_archive_success(self, image_service, tmp_path, mock_archive_service):
        """아카이브에서 이미지 스트리밍 성공 테스트"""
        # 테스트 아카이브 파일 생성
        test_archive = tmp_path / "test.zip"
        test_archive.write_bytes(b"fake archive")
        
        # 모의 아카이브 서비스 설정 (비동기 메서드들을 AsyncMock으로 설정)
        test_image_path = "page001.jpg"
        test_image_data = b"fake image data"
        mock_archive_service.list_archive_contents = AsyncMock(return_value=[test_image_path])
        mock_archive_service.extract_file_from_archive = AsyncMock(return_value=test_image_data)
        
        # 스트리밍 실행
        response = await image_service.stream_image_from_archive(test_archive, test_image_path)
        
        # 응답 검증
        assert response.media_type == "image/jpeg"
        assert response.headers["Content-Type"] == "image/jpeg"
        assert "Accept-Ranges" in response.headers
        
        # 스트림을 실제로 소비해서 extract_file_from_archive가 호출되도록 함
        content = b""
        async for chunk in response.body_iterator:
            content += chunk
        
        # 내용 검증
        assert content == test_image_data
        
        # 모의 객체 호출 검증
        mock_archive_service.list_archive_contents.assert_called_once_with(test_archive)
        mock_archive_service.extract_file_from_archive.assert_called_once_with(test_archive, test_image_path)
    
    @pytest.mark.asyncio
    async def test_stream_image_from_archive_not_found(self, image_service, tmp_path):
        """존재하지 않는 아카이브에서 이미지 스트리밍 테스트"""
        non_existent_archive = tmp_path / "nonexistent.zip"
        
        with pytest.raises(HTTPException) as exc_info:
            await image_service.stream_image_from_archive(non_existent_archive, "test.jpg")
        
        assert exc_info.value.status_code == 404
        assert "아카이브 파일을 찾을 수 없습니다" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_stream_image_from_archive_image_not_in_archive(self, image_service, tmp_path, mock_archive_service):
        """아카이브에 없는 이미지 스트리밍 테스트"""
        # 테스트 아카이브 파일 생성
        test_archive = tmp_path / "test.zip"
        test_archive.write_bytes(b"fake archive")
        
        # 모의 아카이브 서비스 설정 (빈 목록 반환)
        mock_archive_service.list_archive_contents = AsyncMock(return_value=[])
        
        with pytest.raises(HTTPException) as exc_info:
            await image_service.stream_image_from_archive(test_archive, "nonexistent.jpg")
        
        assert exc_info.value.status_code == 404
        assert "아카이브 내 이미지를 찾을 수 없습니다" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_stream_image_from_archive_unsupported_format(self, image_service, tmp_path, mock_archive_service):
        """아카이브에서 지원되지 않는 형식 스트리밍 테스트"""
        # 테스트 아카이브 파일 생성
        test_archive = tmp_path / "test.zip"
        test_archive.write_bytes(b"fake archive")
        
        # 모의 아카이브 서비스 설정
        test_file_path = "document.txt"
        mock_archive_service.list_archive_contents = AsyncMock(return_value=[test_file_path])
        
        with pytest.raises(HTTPException) as exc_info:
            await image_service.stream_image_from_archive(test_archive, test_file_path)
        
        assert exc_info.value.status_code == 400
        assert "지원되지 않는 이미지 형식입니다" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_image_info_success(self, image_service, tmp_path):
        """이미지 정보 조회 성공 테스트"""
        # 테스트 이미지 파일 생성
        test_image = tmp_path / "test.png"
        test_content = b"fake png content"
        test_image.write_bytes(test_content)
        
        # 이미지 정보 조회
        info = await image_service.get_image_info(test_image)
        
        # 정보 검증
        assert info is not None
        assert info["name"] == "test.png"
        assert info["size"] == len(test_content)
        assert info["mime_type"] == "image/png"
        assert info["is_image"] is True
    
    @pytest.mark.asyncio
    async def test_get_image_info_file_not_found(self, image_service, tmp_path):
        """존재하지 않는 파일의 이미지 정보 조회 테스트"""
        non_existent_file = tmp_path / "nonexistent.jpg"
        
        info = await image_service.get_image_info(non_existent_file)
        
        assert info is None
    
    @pytest.mark.asyncio
    async def test_get_image_info_directory(self, image_service, tmp_path):
        """디렉토리의 이미지 정보 조회 테스트"""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        info = await image_service.get_image_info(test_dir)
        
        assert info is None


class TestImageServiceIntegration:
    """ImageService 통합 테스트 클래스"""

    @pytest.mark.asyncio
    async def test_bytes_streamer_chunks(self, image_service):
        """메모리 데이터 스트리머 청크 단위 전송 테스트"""
        test_content = b"x" * 1000  # 1KB

        chunks = []
        async for chunk in image_service._bytes_streamer(test_content, chunk_size=100):
            chunks.append(chunk)

        assert len(chunks) == 10  # 1000 bytes / 100 bytes per chunk
        assert b"".join(chunks) == test_content

    @pytest.mark.asyncio
    async def test_bytes_streamer_uses_settings_chunk_size(self, image_service, mock_settings):
        """청크 크기를 지정하지 않으면 설정값을 사용한다"""
        mock_settings.chunk_size = 250
        test_content = b"z" * 1000

        chunks = [chunk async for chunk in image_service._bytes_streamer(test_content)]

        assert len(chunks) == 4
        assert b"".join(chunks) == test_content

    @pytest.mark.asyncio
    async def test_stream_image_too_large(self, image_service, mock_settings, tmp_path):
        """최대 파일 크기를 초과하면 413 을 발생시킨다"""
        mock_settings.max_file_size = 10

        test_image = tmp_path / "big.jpg"
        test_image.write_bytes(b"x" * 100)

        with pytest.raises(FileTooLargeError) as exc_info:
            await image_service.stream_image(test_image)

        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_stream_image_from_archive_extract_failure(
        self, image_service, mock_archive_service, tmp_path
    ):
        """추출이 실패하면 스트리밍을 시작하지 않고 404 를 반환한다"""
        test_archive = tmp_path / "test.zip"
        test_archive.write_bytes(b"fake archive")

        mock_archive_service.list_archive_contents = AsyncMock(return_value=["page001.jpg"])
        mock_archive_service.extract_file_from_archive = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await image_service.stream_image_from_archive(test_archive, "page001.jpg")

        assert exc_info.value.status_code == 404

    def test_stream_image_supports_range_request(self, image_service, tmp_path):
        """직접 이미지 요청은 Range 요청을 실제로 처리한다 (206 + Content-Range)"""
        test_image = tmp_path / "page.jpg"
        test_content = bytes(range(256))
        test_image.write_bytes(test_content)

        app = FastAPI()

        @app.get("/image")
        async def serve_image():
            return await image_service.stream_image(test_image)

        client = TestClient(app)

        full = client.get("/image")
        assert full.status_code == 200
        assert full.headers["Content-Length"] == str(len(test_content))
        assert full.headers["accept-ranges"] == "bytes"

        partial = client.get("/image", headers={"Range": "bytes=0-9"})
        assert partial.status_code == 206
        assert partial.content == test_content[:10]
        assert partial.headers["content-range"] == f"bytes 0-9/{len(test_content)}"