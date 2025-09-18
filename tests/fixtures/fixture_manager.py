"""테스트 픽스처 통합 관리자"""

import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

from .sample_data import SampleDataGenerator
from .test_configs import TestConfigGenerator
from .encoding_test_data import EncodingTestDataGenerator


class FixtureManager:
    """테스트 픽스처를 통합 관리하는 클래스"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Args:
            base_dir: 기본 디렉토리 경로 (None이면 임시 디렉토리 사용)
        """
        self.base_dir = base_dir
        self._temp_dir = None
        self._created_paths = {}
    
    @contextmanager
    def temporary_fixture_dir(self):
        """임시 픽스처 디렉토리 컨텍스트 매니저"""
        if self.base_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="comix_test_")
            self.base_dir = Path(self._temp_dir)
        
        try:
            yield self.base_dir
        finally:
            if self._temp_dir:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
                self._temp_dir = None
                self.base_dir = None
    
    def create_complete_test_environment(self) -> Dict[str, Any]:
        """완전한 테스트 환경을 생성합니다
        
        Returns:
            생성된 모든 테스트 데이터의 딕셔너리
        """
        if self.base_dir is None:
            raise ValueError("Base directory not set. Use temporary_fixture_dir() context manager.")
        
        results = {}
        
        # 1. 기본 만화 디렉토리 구조
        manga_dir = self.base_dir / "manga"
        manga_dir.mkdir(exist_ok=True)
        results["manga_structure"] = SampleDataGenerator.create_sample_manga_structure(manga_dir)
        
        # 2. 모든 이미지 형식
        images_dir = self.base_dir / "image_formats"
        images_dir.mkdir(exist_ok=True)
        results["image_formats"] = SampleDataGenerator.create_all_image_formats(images_dir)
        
        # 3. 혼합 콘텐츠 디렉토리
        mixed_dir = self.base_dir / "mixed_content"
        mixed_dir.mkdir(exist_ok=True)
        results["mixed_content"] = SampleDataGenerator.create_mixed_content_directory(mixed_dir)
        
        # 4. 중첩 디렉토리 구조
        nested_dir = self.base_dir / "nested_structure"
        nested_dir.mkdir(exist_ok=True)
        results["nested_structure"] = SampleDataGenerator.create_nested_directory_structure(nested_dir)
        
        # 5. 엣지 케이스 파일들
        edge_dir = self.base_dir / "edge_cases"
        edge_dir.mkdir(exist_ok=True)
        results["edge_cases"] = SampleDataGenerator.create_edge_case_files(edge_dir)
        
        # 6. 문자 인코딩 테스트 데이터
        encoding_dir = self.base_dir / "encoding_tests"
        encoding_dir.mkdir(exist_ok=True)
        results["encoding_tests"] = EncodingTestDataGenerator.create_all_encoding_test_data(encoding_dir)
        
        # 7. 테스트 설정 파일들
        config_dir = self.base_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        results["test_configs"] = TestConfigGenerator.create_all_test_configs(config_dir)
        results["docker_configs"] = TestConfigGenerator.create_docker_configs(config_dir)
        
        # 8. 성능 테스트용 큰 파일들
        performance_dir = self.base_dir / "performance"
        performance_dir.mkdir(exist_ok=True)
        
        # 큰 이미지 파일
        large_image_path = performance_dir / "large_image.jpg"
        SampleDataGenerator.create_large_image(large_image_path)
        results["performance"] = {"large_image": large_image_path}
        
        # 많은 파일이 있는 디렉토리
        many_files_dir = performance_dir / "many_files"
        many_files_dir.mkdir(exist_ok=True)
        many_files_paths = {}
        for i in range(100):  # 100개 파일 생성
            file_path = many_files_dir / f"image_{i:03d}.jpg"
            img_data = SampleDataGenerator.create_sample_image(format="JPEG")
            file_path.write_bytes(img_data)
            many_files_paths[f"image_{i:03d}"] = file_path
        results["performance"]["many_files"] = many_files_paths
        
        # 9. 손상된 파일들 (에러 테스트용)
        error_dir = self.base_dir / "error_tests"
        error_dir.mkdir(exist_ok=True)
        
        # 손상된 아카이브
        corrupted_zip = error_dir / "corrupted.zip"
        SampleDataGenerator.create_corrupted_archive(corrupted_zip)
        
        # 손상된 이미지
        corrupted_image = error_dir / "corrupted.jpg"
        corrupted_image.write_bytes(b"This is not a valid image")
        
        results["error_tests"] = {
            "corrupted_zip": corrupted_zip,
            "corrupted_image": corrupted_image
        }
        
        # 10. 권한 테스트용 파일들 (Unix 시스템에서만)
        try:
            import os
            if hasattr(os, 'chmod'):
                permission_dir = self.base_dir / "permission_tests"
                permission_dir.mkdir(exist_ok=True)
                
                # 읽기 전용 파일
                readonly_file = permission_dir / "readonly.jpg"
                img_data = SampleDataGenerator.create_sample_image(format="JPEG")
                readonly_file.write_bytes(img_data)
                readonly_file.chmod(0o444)  # 읽기 전용
                
                # 접근 불가 디렉토리
                no_access_dir = permission_dir / "no_access"
                no_access_dir.mkdir(exist_ok=True)
                (no_access_dir / "hidden.jpg").write_bytes(img_data)
                no_access_dir.chmod(0o000)  # 접근 불가
                
                results["permission_tests"] = {
                    "readonly_file": readonly_file,
                    "no_access_dir": no_access_dir
                }
        except Exception as e:
            print(f"Warning: Could not create permission test files: {e}")
        
        self._created_paths = results
        return results
    
    def create_minimal_test_environment(self) -> Dict[str, Any]:
        """최소한의 테스트 환경을 생성합니다 (빠른 테스트용)
        
        Returns:
            생성된 기본 테스트 데이터의 딕셔너리
        """
        if self.base_dir is None:
            raise ValueError("Base directory not set. Use temporary_fixture_dir() context manager.")
        
        results = {}
        
        # 기본 만화 구조만 생성
        manga_dir = self.base_dir / "manga"
        manga_dir.mkdir(exist_ok=True)
        results["manga_structure"] = SampleDataGenerator.create_sample_manga_structure(manga_dir)
        
        # 기본 설정 파일
        config_dir = self.base_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        minimal_config = TestConfigGenerator.get_minimal_config()
        env_path = config_dir / ".env.test"
        TestConfigGenerator.create_test_env_file(env_path, minimal_config)
        results["test_config"] = env_path
        
        return results
    
    def get_sample_manga_path(self) -> Optional[Path]:
        """샘플 만화 디렉토리 경로를 반환합니다"""
        if self._created_paths and "manga_structure" in self._created_paths:
            return self.base_dir / "manga"
        elif self.base_dir and (self.base_dir / "manga").exists():
            return self.base_dir / "manga"
        return None
    
    def get_test_config_path(self, config_type: str = "minimal") -> Optional[Path]:
        """테스트 설정 파일 경로를 반환합니다
        
        Args:
            config_type: 설정 타입 (minimal, full, production, invalid)
        """
        if "test_configs" in self._created_paths:
            return self._created_paths["test_configs"].get(config_type)
        return None
    
    def cleanup(self):
        """생성된 테스트 파일들을 정리합니다"""
        if self._temp_dir and Path(self._temp_dir).exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        self._created_paths.clear()


# 편의 함수들
def create_temporary_test_environment():
    """임시 테스트 환경을 생성하는 편의 함수"""
    manager = FixtureManager()
    return manager.temporary_fixture_dir()


def create_sample_manga_directory(base_path: Path) -> Dict[str, Path]:
    """샘플 만화 디렉토리를 생성하는 편의 함수"""
    return SampleDataGenerator.create_sample_manga_structure(base_path)


def create_test_config_file(config_path: Path, config_type: str = "minimal") -> None:
    """테스트 설정 파일을 생성하는 편의 함수"""
    if config_type == "minimal":
        config = TestConfigGenerator.get_minimal_config()
    elif config_type == "full":
        config = TestConfigGenerator.get_full_config()
    elif config_type == "production":
        config = TestConfigGenerator.get_production_config()
    elif config_type == "invalid":
        config = TestConfigGenerator.get_invalid_config()
    else:
        raise ValueError(f"Unknown config type: {config_type}")
    
    TestConfigGenerator.create_test_env_file(config_path, config)