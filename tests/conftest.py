"""
Pytest 설정 및 공통 픽스처

테스트에서 사용할 공통 설정과 픽스처들을 정의
"""

import tempfile
import os
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.config import Settings, settings
from tests.fixtures.sample_data import SampleDataGenerator
from tests.fixtures.fixture_manager import FixtureManager
from tests.fixtures.test_configs import TestConfigGenerator
from tests.fixtures.encoding_test_data import EncodingTestDataGenerator


@pytest.fixture
def temp_manga_dir() -> Generator[Path, None, None]:
    """임시 manga 디렉토리 생성"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manga_dir = Path(temp_dir) / "manga"
        manga_dir.mkdir()
        yield manga_dir


@pytest.fixture
def test_settings(temp_manga_dir: Path) -> Settings:
    """테스트용 설정 생성"""
    return Settings(
        manga_directory=str(temp_manga_dir),  # Path를 문자열로 변환
        server_port=31258,  # 다른 포트 사용
        debug_mode=True,
        log_level="DEBUG",
    )


@pytest.fixture
def override_settings(test_settings: Settings, monkeypatch):
    """설정 오버라이드"""
    # 전역 설정만 오버라이드
    monkeypatch.setattr("app.models.config.settings", test_settings)
    return test_settings


@pytest.fixture
def app(override_settings):
    """테스트용 FastAPI 앱"""
    # 테스트용 서비스들을 직접 생성
    from pathlib import Path
    from app.services import FileSystemService, ArchiveService, ImageService
    from app.api.handlers import MangaRequestHandler
    from app.api.routes import router
    from fastapi import FastAPI
    
    # 테스트용 서비스 인스턴스들 생성
    filesystem_service = FileSystemService(Path(override_settings.manga_directory))
    archive_service = ArchiveService()
    image_service = ImageService(override_settings, archive_service)
    
    # 테스트용 핸들러 생성
    manga_handler = MangaRequestHandler(
        settings=override_settings,
        filesystem_service=filesystem_service,
        archive_service=archive_service,
        image_service=image_service
    )
    
    # 테스트용 앱 생성
    app = FastAPI(title="Test Comix Server", debug=True)
    
    # 라우터에 핸들러 주입
    import app.api.routes as routes_module
    routes_module.manga_handler = manga_handler
    routes_module.settings = override_settings
    
    app.include_router(router)
    
    return app


@pytest.fixture
def client(app) -> TestClient:
    """테스트 클라이언트"""
    from app.exception_handlers import register_exception_handlers
    register_exception_handlers(app)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_manga_structure(temp_manga_dir: Path) -> Dict[str, Path]:
    """샘플 만화 디렉토리 구조 생성"""
    return SampleDataGenerator.create_sample_manga_structure(temp_manga_dir)


@pytest.fixture
def encoding_test_data(temp_manga_dir: Path) -> Dict[str, Path]:
    """문자 인코딩 테스트용 데이터 생성"""
    return SampleDataGenerator.create_character_encoding_test_data(temp_manga_dir)


@pytest.fixture
def corrupted_archive(temp_manga_dir: Path) -> Path:
    """손상된 아카이브 파일 생성"""
    archive_path = temp_manga_dir / "corrupted.zip"
    SampleDataGenerator.create_corrupted_archive(archive_path)
    return archive_path


@pytest.fixture
def large_image(temp_manga_dir: Path) -> Path:
    """큰 이미지 파일 생성 (성능 테스트용)"""
    image_path = temp_manga_dir / "large_image.jpg"
    SampleDataGenerator.create_large_image(image_path)
    return image_path


# 새로운 통합 픽스처들

@pytest.fixture
def fixture_manager() -> Generator[FixtureManager, None, None]:
    """테스트 픽스처 매니저"""
    manager = FixtureManager()
    with manager.temporary_fixture_dir():
        yield manager
    manager.cleanup()


@pytest.fixture
def complete_test_environment(fixture_manager: FixtureManager) -> Dict[str, Any]:
    """완전한 테스트 환경 (모든 테스트 데이터 포함)"""
    return fixture_manager.create_complete_test_environment()


@pytest.fixture
def minimal_test_environment(fixture_manager: FixtureManager) -> Dict[str, Any]:
    """최소한의 테스트 환경 (빠른 테스트용)"""
    return fixture_manager.create_minimal_test_environment()


@pytest.fixture
def all_image_formats(temp_manga_dir: Path) -> Dict[str, Path]:
    """모든 지원 이미지 형식의 샘플 파일들"""
    return SampleDataGenerator.create_all_image_formats(temp_manga_dir)


@pytest.fixture
def mixed_content_directory(temp_manga_dir: Path) -> Dict[str, Path]:
    """혼합 콘텐츠가 있는 디렉토리 (필터링 테스트용)"""
    return SampleDataGenerator.create_mixed_content_directory(temp_manga_dir)


@pytest.fixture
def nested_directory_structure(temp_manga_dir: Path) -> Dict[str, Path]:
    """중첩된 디렉토리 구조"""
    return SampleDataGenerator.create_nested_directory_structure(temp_manga_dir)


@pytest.fixture
def edge_case_files(temp_manga_dir: Path) -> Dict[str, Path]:
    """엣지 케이스 테스트용 파일들"""
    return SampleDataGenerator.create_edge_case_files(temp_manga_dir)


@pytest.fixture
def unicode_test_files(temp_manga_dir: Path) -> Dict[str, Path]:
    """유니코드 파일명 테스트용 파일들"""
    encoding_dir = temp_manga_dir / "unicode_tests"
    encoding_dir.mkdir(exist_ok=True)
    return EncodingTestDataGenerator.create_unicode_test_files(encoding_dir)


@pytest.fixture
def legacy_encoding_archives(temp_manga_dir: Path) -> Dict[str, Path]:
    """레거시 인코딩 아카이브 파일들"""
    encoding_dir = temp_manga_dir / "legacy_tests"
    encoding_dir.mkdir(exist_ok=True)
    return EncodingTestDataGenerator.create_legacy_encoding_archives(encoding_dir)


@pytest.fixture
def url_encoding_test_files(temp_manga_dir: Path) -> Dict[str, Path]:
    """URL 인코딩 테스트용 파일들"""
    url_dir = temp_manga_dir / "url_tests"
    url_dir.mkdir(exist_ok=True)
    return EncodingTestDataGenerator.create_url_encoding_test_data(url_dir)


@pytest.fixture
def test_config_minimal(temp_manga_dir: Path) -> Path:
    """최소 테스트 설정 파일"""
    config_path = temp_manga_dir / ".env.test"
    config = TestConfigGenerator.get_minimal_config()
    config["COMIX_MANGA_DIRECTORY"] = str(temp_manga_dir)
    TestConfigGenerator.create_test_env_file(config_path, config)
    return config_path


@pytest.fixture
def test_config_full(temp_manga_dir: Path) -> Path:
    """전체 테스트 설정 파일"""
    config_path = temp_manga_dir / ".env.full"
    config = TestConfigGenerator.get_full_config()
    config["COMIX_MANGA_DIRECTORY"] = str(temp_manga_dir)
    TestConfigGenerator.create_test_env_file(config_path, config)
    return config_path


@pytest.fixture
def test_config_invalid(temp_manga_dir: Path) -> Path:
    """유효하지 않은 테스트 설정 파일"""
    config_path = temp_manga_dir / ".env.invalid"
    config = TestConfigGenerator.get_invalid_config()
    TestConfigGenerator.create_test_env_file(config_path, config)
    return config_path


@pytest.fixture
def performance_test_data(temp_manga_dir: Path) -> Dict[str, Path]:
    """성능 테스트용 데이터"""
    perf_dir = temp_manga_dir / "performance"
    perf_dir.mkdir(exist_ok=True)
    
    # 큰 이미지
    large_image = perf_dir / "large.jpg"
    SampleDataGenerator.create_large_image(large_image)
    
    # 많은 파일이 있는 디렉토리
    many_files_dir = perf_dir / "many_files"
    many_files_dir.mkdir(exist_ok=True)
    
    files = {}
    for i in range(50):  # 50개 파일 (테스트용으로 줄임)
        file_path = many_files_dir / f"image_{i:03d}.jpg"
        img_data = SampleDataGenerator.create_sample_image(format="JPEG")
        file_path.write_bytes(img_data)
        files[f"image_{i:03d}"] = file_path
    
    return {
        "large_image": large_image,
        "many_files_dir": many_files_dir,
        **files
    }


@pytest.fixture
def error_test_data(temp_manga_dir: Path) -> Dict[str, Path]:
    """에러 테스트용 데이터"""
    error_dir = temp_manga_dir / "error_tests"
    error_dir.mkdir(exist_ok=True)
    
    # 손상된 ZIP 파일
    corrupted_zip = error_dir / "corrupted.zip"
    SampleDataGenerator.create_corrupted_archive(corrupted_zip)
    
    # 손상된 이미지 파일
    corrupted_image = error_dir / "corrupted.jpg"
    corrupted_image.write_bytes(b"This is not a valid image file")
    
    # 빈 파일
    empty_file = error_dir / "empty.jpg"
    empty_file.write_bytes(b"")
    
    # 접근 불가능한 파일 (권한 테스트)
    restricted_file = error_dir / "restricted.jpg"
    img_data = SampleDataGenerator.create_sample_image(format="JPEG")
    restricted_file.write_bytes(img_data)
    
    try:
        # Unix 시스템에서만 권한 변경
        if hasattr(os, 'chmod'):
            restricted_file.chmod(0o000)  # 모든 권한 제거
    except Exception:
        pass  # 권한 변경 실패 시 무시
    
    return {
        "corrupted_zip": corrupted_zip,
        "corrupted_image": corrupted_image,
        "empty_file": empty_file,
        "restricted_file": restricted_file
    }


# 환경 변수 관련 픽스처들

@pytest.fixture
def clean_environment(monkeypatch):
    """깨끗한 환경 변수 상태 (COMIX_ 접두사 제거)"""
    # 기존 COMIX_ 환경 변수들 백업 및 제거
    backup = {}
    for key in list(os.environ.keys()):
        if key.startswith("COMIX_"):
            backup[key] = os.environ[key]
            monkeypatch.delenv(key, raising=False)
    
    yield
    
    # 환경 변수 복원
    for key, value in backup.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_environment_minimal(monkeypatch, temp_manga_dir: Path):
    """최소한의 환경 변수 설정"""
    monkeypatch.setenv("COMIX_MANGA_DIRECTORY", str(temp_manga_dir))
    monkeypatch.setenv("COMIX_DEBUG_MODE", "true")
    monkeypatch.setenv("COMIX_LOG_LEVEL", "DEBUG")


@pytest.fixture
def mock_environment_full(monkeypatch, temp_manga_dir: Path):
    """전체 환경 변수 설정"""
    config = TestConfigGenerator.get_full_config()
    config["COMIX_MANGA_DIRECTORY"] = str(temp_manga_dir)
    
    for key, value in config.items():
        monkeypatch.setenv(key, str(value))


# 특수 목적 픽스처들

@pytest.fixture
def readonly_manga_dir(temp_manga_dir: Path) -> Path:
    """읽기 전용 만화 디렉토리 (권한 테스트용)"""
    # 샘플 데이터 생성
    SampleDataGenerator.create_sample_manga_structure(temp_manga_dir)
    
    try:
        # Unix 시스템에서만 권한 변경
        if hasattr(os, 'chmod'):
            temp_manga_dir.chmod(0o444)  # 읽기 전용
    except Exception:
        pass  # 권한 변경 실패 시 무시
    
    return temp_manga_dir


@pytest.fixture
def empty_manga_dir(temp_manga_dir: Path) -> Path:
    """빈 만화 디렉토리"""
    return temp_manga_dir


@pytest.fixture
def nonexistent_manga_dir(temp_manga_dir: Path) -> Path:
    """존재하지 않는 만화 디렉토리 경로"""
    return temp_manga_dir / "nonexistent"