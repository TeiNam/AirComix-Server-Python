"""
설정 관리 모듈

Pydantic Settings를 사용한 환경 변수 기반 설정 관리
"""

from pathlib import Path
from typing import List, Optional

from pydantic import field_validator, Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 서버 설정
    manga_directory: Path = Field(
        default=Path.home() / "comix",
        description="만화 파일이 저장된 루트 디렉토리"
    )
    server_port: int = Field(
        default=31257,
        ge=1,
        le=65535,
        description="서버가 바인딩할 포트 번호"
    )
    server_host: str = Field(
        default="0.0.0.0",
        description="서버가 바인딩할 호스트 주소"
    )
    debug_mode: bool = Field(
        default=False,
        description="디버그 모드 활성화 여부"
    )
    log_level: str = Field(
        default="INFO",
        description="로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # 성능 설정
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="스트리밍할 최대 파일 크기 (바이트)"
    )
    chunk_size: int = Field(
        default=8192,
        description="파일 스트리밍 시 청크 크기 (바이트)"
    )
    
    # 파일 필터링 설정
    hidden_files: List[str] = Field(
        default=[".", "..", "@eaDir", "Thumbs.db", ".DS_Store", ".thumbnails"],
        description="숨김 처리할 파일명 목록"
    )
    hidden_patterns: List[str] = Field(
        default=["__MACOSX"],
        description="숨김 처리할 파일명 패턴 목록"
    )
    
    # 지원 파일 형식
    image_extensions: List[str] = Field(
        default=["jpg", "jpeg", "gif", "png", "tif", "tiff", "bmp"],
        description="지원하는 이미지 파일 확장자 목록"
    )
    archive_extensions: List[str] = Field(
        default=["zip", "cbz", "rar", "cbr"],
        description="지원하는 아카이브 파일 확장자 목록"
    )
    
    # 문자 인코딩 설정
    source_encoding: str = Field(
        default="EUC-KR",
        description="아카이브 내 파일명의 원본 인코딩"
    )
    target_encoding: str = Field(
        default="UTF-8",
        description="변환할 대상 인코딩"
    )
    fallback_encodings: List[str] = Field(
        default=["CP949", "EUC-KR", "UTF-8", "latin1"],
        description="인코딩 변환 실패 시 시도할 인코딩 목록"
    )
    
    # 서버 정보
    server_name: str = Field(
        default="Comix Server Python Port",
        description="서버 이름"
    )
    allow_download: bool = Field(
        default=True,
        description="다운로드 허용 여부"
    )
    allow_image_process: bool = Field(
        default=True,
        description="이미지 처리 허용 여부"
    )
    welcome_message: str = Field(
        default="I am a generous god!",
        description="welcome 엔드포인트에서 반환할 메시지"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="COMIX_",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("manga_directory")
    @classmethod
    def validate_manga_directory(cls, v):
        """manga 디렉토리 경로 검증"""
        if isinstance(v, str):
            v = Path(v)
        
        # 디렉토리 존재 여부만 확인 (생성하지 않음)
        if not v.exists():
            raise ValueError(f"manga 디렉토리가 존재하지 않습니다: {v}")
        
        if not v.is_dir():
            raise ValueError(f"manga_directory는 디렉토리여야 합니다: {v}")
        
        return v
    
    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v):
        """최대 파일 크기 검증"""
        if v <= 0:
            raise ValueError("최대 파일 크기는 0보다 커야 합니다")
        if v > 1024 * 1024 * 1024:  # 1GB
            raise ValueError("최대 파일 크기는 1GB를 초과할 수 없습니다")
        return v
    
    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v):
        """청크 크기 검증"""
        if v <= 0:
            raise ValueError("청크 크기는 0보다 커야 합니다")
        if v > 1024 * 1024:  # 1MB
            raise ValueError("청크 크기는 1MB를 초과할 수 없습니다")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """로그 레벨 검증"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"로그 레벨은 {valid_levels} 중 하나여야 합니다")
        return v.upper()
    
    @field_validator("image_extensions", "archive_extensions")
    @classmethod
    def validate_extensions(cls, v):
        """파일 확장자 목록 검증"""
        if not v:
            raise ValueError("최소 하나의 파일 확장자가 필요합니다")
        
        # 모든 확장자를 소문자로 변환
        return [ext.lower().lstrip('.') for ext in v]
    
    @field_validator("fallback_encodings")
    @classmethod
    def validate_fallback_encodings(cls, v):
        """폴백 인코딩 목록 검증"""
        if not v:
            raise ValueError("최소 하나의 폴백 인코딩이 필요합니다")
        return v
    
    @property
    def supported_extensions(self) -> List[str]:
        """지원되는 모든 파일 확장자 반환"""
        return self.image_extensions + self.archive_extensions
    
    def is_image_file(self, filename: str) -> bool:
        """파일이 이미지인지 확인"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in self.image_extensions
    
    def is_archive_file(self, filename: str) -> bool:
        """파일이 아카이브인지 확인"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in self.archive_extensions
    
    def is_supported_file(self, filename: str) -> bool:
        """파일이 지원되는 형식인지 확인"""
        return self.is_image_file(filename) or self.is_archive_file(filename)
    
    def is_hidden_file(self, filename: str) -> bool:
        """파일이 숨김 파일인지 확인"""
        # 숨김 파일명 체크
        if filename in self.hidden_files:
            return True
        
        # 숨김 패턴 체크
        for pattern in self.hidden_patterns:
            if pattern in filename:
                return True
        
        return False


# 전역 설정 인스턴스
settings = Settings()