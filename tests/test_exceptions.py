"""예외 클래스 테스트"""

import pytest
from app.exceptions import (
    ComixServerException, FileNotFoundError, AccessDeniedError,
    UnsupportedFileTypeError, ArchiveError, CorruptedArchiveError,
    ImageProcessingError, ConfigurationError, PathTraversalError,
    ServiceUnavailableError
)


class TestComixServerException:
    """ComixServerException 기본 클래스 테스트"""
    
    def test_basic_exception(self):
        """기본 예외 생성 테스트"""
        exc = ComixServerException("테스트 메시지")
        assert exc.message == "테스트 메시지"
        assert exc.status_code == 500
        assert exc.detail == "테스트 메시지"
        assert str(exc) == "테스트 메시지"
    
    def test_exception_with_custom_status_code(self):
        """커스텀 상태 코드 예외 테스트"""
        exc = ComixServerException("테스트 메시지", status_code=400)
        assert exc.status_code == 400
    
    def test_exception_with_custom_detail(self):
        """커스텀 상세 정보 예외 테스트"""
        exc = ComixServerException("테스트 메시지", detail="상세 정보")
        assert exc.detail == "상세 정보"


class TestFileNotFoundError:
    """FileNotFoundError 테스트"""
    
    def test_file_not_found_error(self):
        """파일 없음 예외 테스트"""
        exc = FileNotFoundError("/test/path")
        assert exc.status_code == 404
        assert "/test/path" in exc.message
        assert "파일 또는 디렉토리를 찾을 수 없습니다" in exc.message
    
    def test_file_not_found_error_with_detail(self):
        """상세 정보가 있는 파일 없음 예외 테스트"""
        exc = FileNotFoundError("/test/path", detail="커스텀 상세 정보")
        assert exc.detail == "커스텀 상세 정보"


class TestAccessDeniedError:
    """AccessDeniedError 테스트"""
    
    def test_access_denied_error(self):
        """접근 거부 예외 테스트"""
        exc = AccessDeniedError("/test/path")
        assert exc.status_code == 403
        assert "/test/path" in exc.message
        assert "접근이 거부되었습니다" in exc.message


class TestUnsupportedFileTypeError:
    """UnsupportedFileTypeError 테스트"""
    
    def test_unsupported_file_type_error(self):
        """지원되지 않는 파일 형식 예외 테스트"""
        exc = UnsupportedFileTypeError("/test/file.txt")
        assert exc.status_code == 400
        assert "/test/file.txt" in exc.message
        assert "지원되지 않는 파일 형식입니다" in exc.message


class TestArchiveError:
    """ArchiveError 테스트"""
    
    def test_archive_error(self):
        """아카이브 오류 예외 테스트"""
        exc = ArchiveError("/test/archive.zip")
        assert exc.status_code == 500
        assert "/test/archive.zip" in exc.message
        assert "아카이브 처리 중 오류가 발생했습니다" in exc.message


class TestCorruptedArchiveError:
    """CorruptedArchiveError 테스트"""
    
    def test_corrupted_archive_error(self):
        """손상된 아카이브 예외 테스트"""
        exc = CorruptedArchiveError("/test/corrupted.zip")
        assert exc.status_code == 400
        assert "/test/corrupted.zip" in exc.message
        assert "손상된 아카이브 파일입니다" in exc.message


class TestImageProcessingError:
    """ImageProcessingError 테스트"""
    
    def test_image_processing_error(self):
        """이미지 처리 오류 예외 테스트"""
        exc = ImageProcessingError("/test/image.jpg")
        assert exc.status_code == 500
        assert "/test/image.jpg" in exc.message
        assert "이미지 처리 중 오류가 발생했습니다" in exc.message


class TestConfigurationError:
    """ConfigurationError 테스트"""
    
    def test_configuration_error(self):
        """설정 오류 예외 테스트"""
        exc = ConfigurationError("manga_directory")
        assert exc.status_code == 500
        assert "manga_directory" in exc.message
        assert "설정 오류" in exc.message


class TestPathTraversalError:
    """PathTraversalError 테스트"""
    
    def test_path_traversal_error(self):
        """경로 순회 공격 예외 테스트"""
        exc = PathTraversalError("../../../etc/passwd")
        assert exc.status_code == 403
        assert "../../../etc/passwd" in exc.message
        assert "경로 순회 공격 시도가 감지되었습니다" in exc.message


class TestServiceUnavailableError:
    """ServiceUnavailableError 테스트"""
    
    def test_service_unavailable_error(self):
        """서비스 사용 불가 예외 테스트"""
        exc = ServiceUnavailableError("FileSystemService")
        assert exc.status_code == 503
        assert "FileSystemService" in exc.message
        assert "서비스를 사용할 수 없습니다" in exc.message