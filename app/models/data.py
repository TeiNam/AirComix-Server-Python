"""
데이터 모델 정의

파일 정보 및 아카이브 엔트리를 위한 데이터 클래스들
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    """파일 정보를 담는 데이터 클래스"""
    
    name: str
    path: Path
    is_directory: bool
    is_archive: bool
    is_image: bool
    size: Optional[int] = None
    mime_type: Optional[str] = None
    
    def __post_init__(self):
        """초기화 후 검증"""
        if self.is_directory and (self.is_archive or self.is_image):
            raise ValueError("디렉토리는 아카이브나 이미지가 될 수 없습니다")
        
        if self.is_archive and self.is_image:
            raise ValueError("파일은 아카이브와 이미지를 동시에 가질 수 없습니다")


@dataclass
class ArchiveEntry:
    """아카이브 내부 파일 정보를 담는 데이터 클래스"""
    
    name: str
    size: int
    is_image: bool
    compressed_size: Optional[int] = None
    
    def __post_init__(self):
        """초기화 후 검증"""
        if self.size < 0:
            raise ValueError("파일 크기는 0 이상이어야 합니다")
        
        if self.compressed_size is not None and self.compressed_size < 0:
            raise ValueError("압축된 파일 크기는 0 이상이어야 합니다")


@dataclass
class ServerInfo:
    """서버 정보를 담는 데이터 클래스"""
    
    message: str = "I am a generous god!"
    allow_download: bool = True
    allow_image_process: bool = True
    
    def to_response_string(self) -> str:
        """AirComix 앱 호환 응답 문자열 생성"""
        return (
            f"{self.message}\r\n"
            f"allowDownload={self.allow_download}\r\n"
            f"allowImageProcess={self.allow_image_process}"
        )