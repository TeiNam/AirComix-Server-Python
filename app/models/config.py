"""
설정 관리 모듈

Pydantic Settings를 사용한 환경 변수 기반 설정 관리
"""

import logging
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    thumbnail_cache_directory: Optional[Path] = Field(
        default=None,
        description=(
            "썸네일 캐시 디렉토리 (기본값: manga_directory/.thumbnails). "
            "manga 디렉토리를 읽기 전용으로 마운트하는 경우 쓰기 가능한 경로를 지정한다."
        )
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

    # 인증 설정
    enable_auth: bool = Field(
        default=False,
        description="기본 인증 활성화 여부"
    )

    auth_password: Optional[str] = Field(
        default=None,
        description="기본 인증 패스워드 (.htaccess 방식)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COMIX_",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("manga_directory")
    @classmethod
    def validate_manga_directory(cls, v):
        """manga 디렉토리 경로 검증

        검증은 항상 수행한다. 테스트 환경을 위한 예외 처리는 전역 설정을
        만드는 _create_settings 에서만 한다 (설정 검증 자체를 테스트할 수 있도록).
        """
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
    def thumbnail_cache_dir(self) -> Path:
        """썸네일 캐시 디렉토리 (미지정 시 manga 디렉토리 하위 .thumbnails)"""
        if self.thumbnail_cache_directory:
            return Path(self.thumbnail_cache_directory)
        return Path(self.manga_directory) / ".thumbnails"

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
    
    def validate_auth_settings(self) -> None:
        """인증 설정 검증

        디버그 모드에서도 우회하지 않는다. 인증을 켰는데 패스워드가 없거나
        너무 짧으면 조용히 통과시키는 대신 기동을 실패시킨다.
        """
        if self.enable_auth:
            if not self.auth_password:
                raise ValueError("인증이 활성화된 경우 auth_password가 필요합니다")
            if len(self.auth_password) < 6:
                raise ValueError("패스워드는 최소 6자 이상이어야 합니다")


def _is_test_environment() -> bool:
    """pytest 실행 중인지 판단

    collection 단계에서는 PYTEST_CURRENT_TEST 가 설정되지 않으므로
    모듈 로드 여부로 판단한다.
    """
    return "pytest" in sys.modules


# 전역 설정 인스턴스 생성
def _create_settings() -> Settings:
    """설정 인스턴스 생성 (테스트 환경 고려)"""
    try:
        settings = Settings()
    except Exception as e:
        if not _is_test_environment():
            logging.getLogger(__name__).error(f"설정 생성 오류: {e}")
            raise

        # 테스트 환경에서만 임시 디렉토리로 최소 설정을 만든다.
        # 운영 환경에서는 설정 오류를 그대로 노출한다 (인증이 조용히 꺼지는 것 방지).
        test_dir = Path(tempfile.gettempdir()) / "test-comix"
        test_dir.mkdir(exist_ok=True)

        return Settings(
            manga_directory=test_dir,
            debug_mode=True,
            log_level="DEBUG",
            enable_auth=False
        )

    settings.validate_auth_settings()
    return settings


settings = _create_settings()