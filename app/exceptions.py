"""
커스텀 예외 클래스들

Comix Server에서 사용하는 모든 커스텀 예외를 정의합니다.
"""

from typing import Optional


class ComixServerException(Exception):
    """Comix Server 기본 예외 클래스"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class FileNotFoundError(ComixServerException):
    """파일 또는 디렉토리를 찾을 수 없는 경우"""
    
    def __init__(self, path: str, detail: Optional[str] = None):
        message = f"파일 또는 디렉토리를 찾을 수 없습니다: {path}"
        super().__init__(
            message=message,
            status_code=404,
            detail=detail or message
        )


class AccessDeniedError(ComixServerException):
    """접근이 거부된 경우"""
    
    def __init__(self, path: str, detail: Optional[str] = None):
        message = f"접근이 거부되었습니다: {path}"
        super().__init__(
            message=message,
            status_code=403,
            detail=detail or "접근이 거부되었습니다"
        )


class UnsupportedFileTypeError(ComixServerException):
    """지원되지 않는 파일 형식인 경우"""
    
    def __init__(self, file_path: str, detail: Optional[str] = None):
        message = f"지원되지 않는 파일 형식입니다: {file_path}"
        super().__init__(
            message=message,
            status_code=400,
            detail=detail or "지원되지 않는 파일 형식입니다"
        )


class ArchiveError(ComixServerException):
    """아카이브 처리 중 오류가 발생한 경우"""
    
    def __init__(self, archive_path: str, detail: Optional[str] = None):
        message = f"아카이브 처리 중 오류가 발생했습니다: {archive_path}"
        super().__init__(
            message=message,
            status_code=500,
            detail=detail or "아카이브 처리 오류"
        )


class CorruptedArchiveError(ComixServerException):
    """손상된 아카이브 파일인 경우"""
    
    def __init__(self, archive_path: str, detail: Optional[str] = None):
        message = f"손상된 아카이브 파일입니다: {archive_path}"
        super().__init__(
            message=message,
            status_code=400,
            detail=detail or "손상된 아카이브 파일입니다"
        )


class ImageProcessingError(ComixServerException):
    """이미지 처리 중 오류가 발생한 경우"""
    
    def __init__(self, image_path: str, detail: Optional[str] = None):
        message = f"이미지 처리 중 오류가 발생했습니다: {image_path}"
        super().__init__(
            message=message,
            status_code=500,
            detail=detail or "이미지 처리 오류"
        )


class ConfigurationError(ComixServerException):
    """설정 오류인 경우"""
    
    def __init__(self, config_key: str, detail: Optional[str] = None):
        message = f"설정 오류: {config_key}"
        super().__init__(
            message=message,
            status_code=500,
            detail=detail or "설정 오류"
        )


class PathTraversalError(ComixServerException):
    """경로 순회 공격 시도가 감지된 경우"""
    
    def __init__(self, path: str, detail: Optional[str] = None):
        message = f"경로 순회 공격 시도가 감지되었습니다: {path}"
        super().__init__(
            message=message,
            status_code=403,
            detail=detail or "접근이 거부되었습니다"
        )


class ServiceUnavailableError(ComixServerException):
    """서비스를 사용할 수 없는 경우"""
    
    def __init__(self, service_name: str, detail: Optional[str] = None):
        message = f"서비스를 사용할 수 없습니다: {service_name}"
        super().__init__(
            message=message,
            status_code=503,
            detail=detail or "서비스를 사용할 수 없습니다"
        )