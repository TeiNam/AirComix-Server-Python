"""테스트 픽스처들이 올바르게 작동하는지 확인하는 테스트"""

import pytest
from pathlib import Path
from typing import Dict, Any

from tests.fixtures.fixture_manager import FixtureManager
from tests.fixtures.sample_data import SampleDataGenerator
from tests.fixtures.test_configs import TestConfigGenerator
from tests.fixtures.encoding_test_data import EncodingTestDataGenerator


class TestSampleDataGenerator:
    """SampleDataGenerator 테스트"""
    
    def test_create_sample_image(self):
        """샘플 이미지 생성 테스트"""
        # JPEG 이미지 생성
        jpeg_data = SampleDataGenerator.create_sample_image(100, 100, "JPEG")
        assert isinstance(jpeg_data, bytes)
        assert len(jpeg_data) > 0
        assert jpeg_data.startswith(b'\xff\xd8')  # JPEG 시그니처
        
        # PNG 이미지 생성
        png_data = SampleDataGenerator.create_sample_image(100, 100, "PNG")
        assert isinstance(png_data, bytes)
        assert len(png_data) > 0
        assert png_data.startswith(b'\x89PNG')  # PNG 시그니처
    
    def test_create_sample_manga_structure(self, temp_manga_dir: Path):
        """샘플 만화 구조 생성 테스트"""
        paths = SampleDataGenerator.create_sample_manga_structure(temp_manga_dir)
        
        # 기본 구조 확인
        assert "series_a" in paths
        assert "series_b" in paths
        assert paths["series_a"].exists()
        assert paths["series_b"].exists()
        
        # 이미지 파일들 확인
        assert "page1" in paths
        assert paths["page1"].exists()
        assert paths["page1"].suffix == ".jpg"
        
        # 아카이브 파일들 확인
        assert "archive_zip" in paths
        assert paths["archive_zip"].exists()
        assert paths["archive_zip"].suffix == ".zip"
    
    def test_create_sample_zip_archive(self, temp_manga_dir: Path):
        """샘플 ZIP 아카이브 생성 테스트"""
        archive_path = temp_manga_dir / "test.zip"
        SampleDataGenerator.create_sample_zip_archive(archive_path, 3)
        
        assert archive_path.exists()
        
        # ZIP 파일 내용 확인
        import zipfile
        with zipfile.ZipFile(archive_path, 'r') as zf:
            files = zf.namelist()
            
            # 이미지 파일들 확인
            image_files = [f for f in files if f.endswith('.jpg')]
            assert len(image_files) == 3
            
            # 기타 파일들 확인
            assert "info.txt" in files
    
    def test_create_all_image_formats(self, temp_manga_dir: Path):
        """모든 이미지 형식 생성 테스트"""
        paths = SampleDataGenerator.create_all_image_formats(temp_manga_dir)
        
        # 기본 형식들 확인
        expected_formats = ["jpg", "jpeg", "png"]
        for fmt in expected_formats:
            if fmt in paths:  # Pillow가 없을 수도 있음
                assert paths[fmt].exists()
                assert paths[fmt].suffix == f".{fmt}"
    
    def test_create_mixed_content_directory(self, temp_manga_dir: Path):
        """혼합 콘텐츠 디렉토리 생성 테스트"""
        paths = SampleDataGenerator.create_mixed_content_directory(temp_manga_dir)
        
        # 지원되는 파일들 확인
        assert "image_jpg" in paths
        assert "archive_zip" in paths
        
        # 지원되지 않는 파일들 확인
        assert "unsupported_pdf" in paths
        assert "unsupported_txt" in paths
        
        # 시스템 파일들 확인
        assert "system_DS_Store" in paths
        assert "system_Thumbsdb" in paths
    
    def test_create_edge_case_files(self, temp_manga_dir: Path):
        """엣지 케이스 파일들 생성 테스트"""
        paths = SampleDataGenerator.create_edge_case_files(temp_manga_dir)
        
        # 빈 파일 확인
        assert "empty_file" in paths
        assert paths["empty_file"].exists()
        assert paths["empty_file"].stat().st_size == 0
        
        # 긴 파일명 확인
        assert "long_name_file" in paths
        assert paths["long_name_file"].exists()
        
        # 특수 문자 파일들 확인
        special_files = [k for k in paths.keys() if k.startswith("special_")]
        assert len(special_files) > 0


class TestTestConfigGenerator:
    """TestConfigGenerator 테스트"""
    
    def test_get_minimal_config(self):
        """최소 설정 테스트"""
        from tests.fixtures.test_configs import TestConfigGenerator
        config = TestConfigGenerator.get_minimal_config()
        
        assert "COMIX_MANGA_DIRECTORY" in config
        assert "COMIX_SERVER_PORT" in config
        assert "COMIX_DEBUG_MODE" in config
        assert config["COMIX_DEBUG_MODE"] == "true"
    
    def test_get_full_config(self):
        """전체 설정 테스트"""
        from tests.fixtures.test_configs import TestConfigGenerator
        config = TestConfigGenerator.get_full_config()
        
        # 필수 설정들 확인
        required_keys = [
            "COMIX_MANGA_DIRECTORY",
            "COMIX_SERVER_PORT", 
            "COMIX_DEBUG_MODE",
            "COMIX_LOG_LEVEL",
            "COMIX_IMAGE_EXTENSIONS",
            "COMIX_ARCHIVE_EXTENSIONS"
        ]
        
        for key in required_keys:
            assert key in config
    
    def test_create_test_env_file(self, temp_manga_dir: Path):
        """테스트 환경 파일 생성 테스트"""
        from tests.fixtures.test_configs import TestConfigGenerator
        config = TestConfigGenerator.get_minimal_config()
        env_path = temp_manga_dir / ".env.test"
        
        TestConfigGenerator.create_test_env_file(env_path, config)
        
        assert env_path.exists()
        
        # 파일 내용 확인
        content = env_path.read_text()
        for key, value in config.items():
            assert f"{key}={value}" in content
    
    def test_create_all_test_configs(self, temp_manga_dir: Path):
        """모든 테스트 설정 생성 테스트"""
        from tests.fixtures.test_configs import TestConfigGenerator
        paths = TestConfigGenerator.create_all_test_configs(temp_manga_dir)
        
        expected_configs = ["minimal", "full", "production", "invalid", "empty"]
        for config_type in expected_configs:
            assert config_type in paths
            assert paths[config_type].exists()


class TestEncodingTestDataGenerator:
    """EncodingTestDataGenerator 테스트"""
    
    def test_create_unicode_test_files(self, temp_manga_dir: Path):
        """유니코드 테스트 파일 생성 테스트"""
        paths = EncodingTestDataGenerator.create_unicode_test_files(temp_manga_dir)
        
        # 언어별 디렉토리 확인
        language_dirs = [k for k in paths.keys() if k.startswith("dir_")]
        assert len(language_dirs) > 0
        
        # 파일들 확인
        language_files = [k for k in paths.keys() if k.startswith("file_")]
        assert len(language_files) > 0
    
    def test_create_mixed_encoding_archive(self, temp_manga_dir: Path):
        """혼합 인코딩 아카이브 생성 테스트"""
        archive_path = EncodingTestDataGenerator.create_mixed_encoding_archive(temp_manga_dir)
        
        assert archive_path.exists()
        assert archive_path.suffix == ".zip"
        
        # 아카이브 내용 확인
        import zipfile
        with zipfile.ZipFile(archive_path, 'r') as zf:
            files = zf.namelist()
            
            # 다양한 언어 파일들이 포함되어 있는지 확인
            assert len(files) > 0
            
            # 일부 파일명에 유니코드 문자가 포함되어 있는지 확인
            unicode_files = [f for f in files if any(ord(c) > 127 for c in f)]
            assert len(unicode_files) > 0
    
    def test_create_url_encoding_test_data(self, temp_manga_dir: Path):
        """URL 인코딩 테스트 데이터 생성 테스트"""
        paths = EncodingTestDataGenerator.create_url_encoding_test_data(temp_manga_dir)
        
        # 특수 문자가 포함된 파일들이 생성되었는지 확인
        assert len(paths) > 0
        
        # 생성된 파일들이 실제로 존재하는지 확인
        for path in paths.values():
            assert path.exists()


class TestFixtureManager:
    """FixtureManager 테스트"""
    
    def test_temporary_fixture_dir(self):
        """임시 픽스처 디렉토리 테스트"""
        from tests.fixtures.fixture_manager import FixtureManager
        manager = FixtureManager()
        
        with manager.temporary_fixture_dir() as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            
            # 테스트 파일 생성
            test_file = temp_dir / "test.txt"
            test_file.write_text("test content")
            assert test_file.exists()
        
        # 컨텍스트 종료 후 디렉토리가 삭제되었는지 확인
        assert not temp_dir.exists()
    
    def test_create_minimal_test_environment(self):
        """최소 테스트 환경 생성 테스트"""
        from tests.fixtures.fixture_manager import FixtureManager
        manager = FixtureManager()
        
        with manager.temporary_fixture_dir():
            data = manager.create_minimal_test_environment()
            
            # 기본 구조 확인
            assert "manga_structure" in data
            assert "test_config" in data
            
            # 만화 디렉토리 확인
            manga_path = manager.get_sample_manga_path()
            assert manga_path is not None
            assert manga_path.exists()
    
    def test_create_complete_test_environment(self):
        """완전한 테스트 환경 생성 테스트"""
        from tests.fixtures.fixture_manager import FixtureManager
        manager = FixtureManager()
        
        with manager.temporary_fixture_dir():
            data = manager.create_complete_test_environment()
            
            # 모든 카테고리 확인
            expected_categories = [
                "manga_structure",
                "image_formats", 
                "mixed_content",
                "nested_structure",
                "edge_cases",
                "encoding_tests",
                "test_configs",
                "performance",
                "error_tests"
            ]
            
            for category in expected_categories:
                assert category in data, f"Missing category: {category}"


class TestFixtureIntegration:
    """픽스처 통합 테스트"""
    
    def test_fixture_manager_with_pytest_fixtures(self, fixture_manager: FixtureManager):
        """pytest 픽스처와의 통합 테스트"""
        # 최소 환경 생성
        data = fixture_manager.create_minimal_test_environment()
        
        assert "manga_structure" in data
        assert "test_config" in data
        
        # 만화 경로 확인
        manga_path = fixture_manager.get_sample_manga_path()
        assert manga_path is not None
        assert manga_path.exists()
    
    def test_complete_environment_with_pytest_fixtures(self, complete_test_environment: Dict[str, Any]):
        """완전한 환경과 pytest 픽스처 통합 테스트"""
        # 모든 데이터가 생성되었는지 확인
        assert len(complete_test_environment) > 5
        
        # 각 카테고리의 데이터 확인
        for category, data in complete_test_environment.items():
            if isinstance(data, dict):
                assert len(data) > 0, f"Empty data in category: {category}"
            else:
                # 단일 파일/경로인 경우
                if hasattr(data, 'exists'):
                    assert data.exists(), f"Missing file in category: {category}"
    
    def test_encoding_test_integration(self, unicode_test_files: Dict[str, Path]):
        """인코딩 테스트 데이터 통합 테스트"""
        # 유니코드 파일들이 생성되었는지 확인
        assert len(unicode_test_files) > 0
        
        # 각 파일이 실제로 존재하는지 확인
        for name, path in unicode_test_files.items():
            assert path.exists(), f"Missing unicode test file: {name}"
    
    def test_config_integration(self, test_config_minimal: Path, test_config_full: Path):
        """설정 파일 통합 테스트"""
        # 설정 파일들이 존재하는지 확인
        assert test_config_minimal.exists()
        assert test_config_full.exists()
        
        # 파일 내용 확인
        minimal_content = test_config_minimal.read_text()
        assert "COMIX_MANGA_DIRECTORY" in minimal_content
        assert "COMIX_DEBUG_MODE=true" in minimal_content
        
        full_content = test_config_full.read_text()
        assert "COMIX_IMAGE_EXTENSIONS" in full_content
        assert "COMIX_ARCHIVE_EXTENSIONS" in full_content